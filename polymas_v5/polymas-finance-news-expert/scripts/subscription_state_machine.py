#!/usr/bin/env python3
"""Executable reference contract for finance-news subscription transitions."""

from __future__ import annotations

import copy


class TransitionError(RuntimeError):
    """A transition could not be completed without violating the contract."""


def _snapshot(value):
    return copy.deepcopy(value)


def _recovery_state(subscription, *cron_ids):
    recovery = _snapshot(subscription)
    recovery["status"] = "paused"
    recovery["recovery_required"] = True
    recovery["orphaned_cron_job_ids"] = sorted(
        {cron_id for cron_id in cron_ids if cron_id}
    )
    return recovery


def activate_subscription(store, cron, draft):
    """Atomically claim a stable job key, then activate exactly one Cron."""
    pending = _snapshot(draft)
    pending["status"] = "pending_activation"
    pending["cron_job_id"] = None
    created, existing = store.create_if_absent(pending)
    if not created:
        return {"outcome": "existing", "subscription": existing}

    cron_id = None
    attached = None
    try:
        cron_id = cron.create_paused(
            job_key=pending["job_key"],
            agent_id=pending["agent_id"],
            schedule=pending["schedule"],
            plan_version=pending["plan_version"],
        )
        expected_job = {
            "job_key": pending["job_key"],
            "agent_id": pending["agent_id"],
            "schedule": pending["schedule"],
            "plan_version": pending["plan_version"],
        }
        if not cron.validate(cron_id, expected_job):
            raise TransitionError("candidate_cron_validation_failed")

        attached = {**pending, "cron_job_id": cron_id}
        if not store.replace(
            pending["job_key"],
            {"status": "pending_activation", "cron_job_id": None},
            attached,
        ):
            raise TransitionError("subscription_attach_conflict")

        cron.enable(cron_id)
        active = {**attached, "status": "active"}
        if not store.replace(
            pending["job_key"],
            {"status": "pending_activation", "cron_job_id": cron_id},
            active,
        ):
            raise TransitionError("subscription_activate_conflict")
        return {"outcome": "created", "subscription": active}
    except Exception as error:
        if cron_id is not None:
            try:
                cron.pause(cron_id)
                cron.delete(cron_id)
            except Exception:
                store.force_replace(
                    pending["job_key"],
                    _recovery_state(attached or pending, cron_id),
                )
                raise TransitionError("activation_cleanup_failed") from error
        store.delete_if_pending(pending["job_key"])
        raise


def rebind_current_session(store, cron, job_key, target_session_id):
    """Pause delivery, CAS the binding, increment its version, then resume."""
    old = store.get(job_key)
    if old["status"] != "active":
        raise TransitionError("subscription_not_active")
    cron.pause(old["cron_job_id"])
    rebound = {
        **old,
        "target_session_id": target_session_id,
        "binding_version": old["binding_version"] + 1,
    }
    expected = {
        "status": "active",
        "cron_job_id": old["cron_job_id"],
        "plan_version": old["plan_version"],
        "binding_version": old["binding_version"],
        "target_session_id": old["target_session_id"],
    }
    if not store.replace(job_key, expected, rebound):
        cron.enable(old["cron_job_id"])
        raise TransitionError("binding_compare_and_swap_failed")
    try:
        cron.enable(old["cron_job_id"])
    except Exception as error:
        store.force_replace(job_key, _recovery_state(old, old["cron_job_id"]))
        raise TransitionError("binding_resume_failed") from error
    return rebound


def switch_plan(store, cron, job_key, new_schedule):
    """Switch Cron plans and fully restore the old subscription on failure."""
    old = store.get(job_key)
    if old["status"] != "active":
        raise TransitionError("subscription_not_active")
    cron.pause(old["cron_job_id"])
    candidate_id = None
    swapped = False
    try:
        new_version = old["plan_version"] + 1
        candidate_id = cron.create_paused(
            job_key=job_key,
            agent_id=old["agent_id"],
            schedule=new_schedule,
            plan_version=new_version,
        )
        expected_job = {
            "job_key": job_key,
            "agent_id": old["agent_id"],
            "schedule": new_schedule,
            "plan_version": new_version,
        }
        if not cron.validate(candidate_id, expected_job):
            raise TransitionError("candidate_cron_validation_failed")

        replacement = {
            **old,
            "schedule": new_schedule,
            "plan_version": new_version,
            "cron_job_id": candidate_id,
        }
        expected = {
            "status": "active",
            "cron_job_id": old["cron_job_id"],
            "plan_version": old["plan_version"],
            "binding_version": old["binding_version"],
        }
        if not store.replace(job_key, expected, replacement):
            raise TransitionError("plan_compare_and_swap_failed")
        swapped = True
        cron.enable(candidate_id)
        cron.delete(old["cron_job_id"])
        return {"outcome": "switched", "subscription": replacement}
    except Exception:
        if candidate_id is not None:
            try:
                cron.pause(candidate_id)
                cron.delete(candidate_id)
            except Exception:
                store.force_replace(
                    job_key,
                    _recovery_state(
                        store.get(job_key), old["cron_job_id"], candidate_id
                    ),
                )
                return {"outcome": "recovery_required", "subscription": store.get(job_key)}
        if swapped:
            store.force_replace(job_key, old)
        try:
            cron.enable(old["cron_job_id"])
        except Exception:
            store.force_replace(job_key, _recovery_state(old, old["cron_job_id"]))
            return {"outcome": "recovery_required", "subscription": store.get(job_key)}
        return {"outcome": "rolled_back", "subscription": old}


def trigger_from_subscription(subscription):
    """Build the immutable trigger identity carried by a Cron execution."""
    return {
        "trigger_cron_job_id": subscription["cron_job_id"],
        "trigger_job_key": subscription["job_key"],
        "trigger_plan_version": subscription["plan_version"],
        "trigger_agent_id": subscription["agent_id"],
        "trigger_binding_version": subscription["binding_version"],
        "trigger_target_session_id": subscription["target_session_id"],
    }


def validate_trigger(subscription, trigger):
    """Fail closed when any task, plan, expert, or session identity is stale."""
    if subscription.get("status") != "active":
        return "skipped_stale_trigger"
    expected = trigger_from_subscription(subscription)
    if any(trigger.get(key) != value for key, value in expected.items()):
        return "skipped_stale_trigger"
    return "ready"
