import copy
import importlib.util
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
CONTRACT_SCRIPT = ROOT / "scripts" / "subscription_state_machine.py"


def load_contract():
    assert CONTRACT_SCRIPT.is_file(), "缺少可执行订阅状态机合同"
    spec = importlib.util.spec_from_file_location("finance_subscription_contract", CONTRACT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeStore:
    def __init__(self):
        self._lock = threading.Lock()
        self.subscriptions = {}

    def create_if_absent(self, draft):
        with self._lock:
            existing = self.subscriptions.get(draft["job_key"])
            if existing is not None:
                return False, copy.deepcopy(existing)
            self.subscriptions[draft["job_key"]] = copy.deepcopy(draft)
            return True, copy.deepcopy(draft)

    def get(self, job_key):
        with self._lock:
            return copy.deepcopy(self.subscriptions[job_key])

    def replace(self, job_key, expected, replacement):
        with self._lock:
            current = self.subscriptions[job_key]
            if any(current.get(key) != value for key, value in expected.items()):
                return False
            self.subscriptions[job_key] = copy.deepcopy(replacement)
            return True

    def delete_if_pending(self, job_key):
        with self._lock:
            current = self.subscriptions.get(job_key)
            if current and current["status"] == "pending_activation":
                del self.subscriptions[job_key]
                return True
            return False

    def force_replace(self, job_key, subscription):
        with self._lock:
            self.subscriptions[job_key] = copy.deepcopy(subscription)


class FakeCron:
    def __init__(self):
        self._lock = threading.Lock()
        self.jobs = {}
        self.created_count = 0
        self.fail_enable_for = set()

    def create_paused(self, *, job_key, agent_id, schedule, plan_version):
        with self._lock:
            self.created_count += 1
            cron_id = f"cron-{self.created_count}"
            self.jobs[cron_id] = {
                "job_key": job_key,
                "agent_id": agent_id,
                "schedule": schedule,
                "plan_version": plan_version,
                "enabled": False,
            }
            return cron_id

    def validate(self, cron_id, expected):
        return all(self.jobs[cron_id].get(key) == value for key, value in expected.items())

    def pause(self, cron_id):
        self.jobs[cron_id]["enabled"] = False

    def enable(self, cron_id):
        if cron_id in self.fail_enable_for:
            raise RuntimeError("enable failed")
        self.jobs[cron_id]["enabled"] = True

    def delete(self, cron_id):
        self.jobs.pop(cron_id, None)


def draft():
    return {
        "status": "pending_activation",
        "job_key": "finance-news:school-1:user-1:agent-1",
        "agent_id": "agent-1",
        "target_session_id": "session-1",
        "binding_version": 1,
        "plan_version": 1,
        "cron_job_id": None,
        "schedule": "0 8 * * *",
        "timezone": "Asia/Shanghai",
        "topics": ["综合财经"],
        "recovery_required": False,
    }


def test_concurrent_first_subscription_creates_only_one_cron():
    contract = load_contract()
    store = FakeStore()
    cron = FakeCron()
    barrier = threading.Barrier(2)

    def activate():
        barrier.wait()
        return contract.activate_subscription(store, cron, draft())

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: activate(), range(2)))

    assert sorted(result["outcome"] for result in results) == ["created", "existing"]
    assert cron.created_count == 1
    assert store.get(draft()["job_key"])["status"] == "active"


def test_rebind_increments_binding_version_and_invalidates_old_trigger():
    contract = load_contract()
    store = FakeStore()
    cron = FakeCron()
    activated = contract.activate_subscription(store, cron, draft())["subscription"]
    old_trigger = contract.trigger_from_subscription(activated)

    rebound = contract.rebind_current_session(store, cron, draft()["job_key"], "session-2")

    assert rebound["target_session_id"] == "session-2"
    assert rebound["binding_version"] == 2
    assert rebound["plan_version"] == 1
    assert contract.validate_trigger(store.get(draft()["job_key"]), old_trigger) == "skipped_stale_trigger"
    assert contract.validate_trigger(
        store.get(draft()["job_key"]), contract.trigger_from_subscription(rebound)
    ) == "ready"


def test_plan_switch_enable_failure_restores_old_subscription_and_cron():
    contract = load_contract()
    store = FakeStore()
    cron = FakeCron()
    old = contract.activate_subscription(store, cron, draft())["subscription"]
    cron.fail_enable_for.add("cron-2")

    result = contract.switch_plan(store, cron, draft()["job_key"], "0 9 * * *")
    restored = store.get(draft()["job_key"])

    assert result["outcome"] == "rolled_back"
    assert restored == old
    assert cron.jobs[old["cron_job_id"]]["enabled"] is True
    assert "cron-2" not in cron.jobs


def test_final_trigger_check_compares_bound_session_and_binding_version():
    contract = load_contract()
    subscription = {
        **draft(),
        "status": "active",
        "cron_job_id": "cron-1",
    }
    trigger = contract.trigger_from_subscription(subscription)

    assert contract.validate_trigger(subscription, trigger) == "ready"
    assert contract.validate_trigger(
        subscription, {**trigger, "trigger_target_session_id": "session-other"}
    ) == "skipped_stale_trigger"
    assert contract.validate_trigger(
        subscription, {**trigger, "trigger_binding_version": 2}
    ) == "skipped_stale_trigger"


def test_rebind_resume_failure_restores_old_binding_in_paused_recovery_state():
    contract = load_contract()
    store = FakeStore()
    cron = FakeCron()
    old = contract.activate_subscription(store, cron, draft())["subscription"]
    cron.fail_enable_for.add(old["cron_job_id"])

    with pytest.raises(contract.TransitionError, match="binding_resume_failed"):
        contract.rebind_current_session(store, cron, draft()["job_key"], "session-2")

    recovered = store.get(draft()["job_key"])
    assert recovered["status"] == "paused"
    assert recovered["recovery_required"] is True
    assert recovered["target_session_id"] == old["target_session_id"]
    assert recovered["binding_version"] == old["binding_version"]
