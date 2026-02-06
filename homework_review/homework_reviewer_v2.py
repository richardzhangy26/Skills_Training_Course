import asyncio
import json
import json.decoder
import os
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

# 兼容两种运行方式：
# 1) 仓库根目录：python homework_review/homework_reviewer_v2.py
# 2) 进入目录：  cd homework_review && python homework_reviewer_v2.py
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
# 确保能 import utils.*（utils 位于 homework_review/utils 下）
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.excel_summary import (  # pyright: ignore[reportImplicitRelativeImport]
    extract_core_data,
    generate_excel_summary,
)


def load_env_config():
    """
    加载.env配置文件，优先加载当前目录下的.env文件
    如果当前目录没有，则加载上级目录的.env文件
    """
    current_dir = Path(__file__).parent

    # 优先尝试加载当前目录下的.env文件
    local_env = current_dir / ".env"
    if local_env.exists():
        load_dotenv(local_env)
        print(f"✅ 从本地目录加载.env配置: {local_env}")
        return local_env

    # 如果当前目录没有，尝试加载上级目录的.env文件
    parent_env = current_dir.parent / ".env"
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✅ 从上级目录加载.env配置: {parent_env}")
        return parent_env

    # 如果都没有找到，尝试从当前工作目录加载
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        print(f"✅ 从工作目录加载.env配置: {cwd_env}")
        return cwd_env

    raise FileNotFoundError("未找到.env配置文件，请在当前目录或上级目录创建.env文件")


def safe_json_loads(value: Any):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def extract_writing_requirement(detail: dict[str, Any]) -> str:
    business_config = safe_json_loads(detail.get("businessConfig"))
    writing_requirement = ""
    if isinstance(business_config, dict):
        composition = business_config.get("compositionRequirement") or {}
        writing_requirement = composition.get("writingRequirement") or ""
        if not writing_requirement:
            requirement_file = composition.get("requirementFile") or {}
            writing_requirement = requirement_file.get("content") or ""
    if not writing_requirement:
        writing_requirement = detail.get("desc") or ""
    return writing_requirement


def query_agent_list() -> list[dict[str, Any]]:
    """查询智能体类型列表"""
    url = "https://cloudapi.polymas.com/basic-course/courseAgent/queryAgentList"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not authorization or not cookie:
        print("⚠️ 查询智能体列表跳过：缺少 AUTHORIZATION 或 COOKIE")
        return []

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        if result.get("success") or result.get("code") == 200:
            data = result.get("data", [])
            if not data:
                print("⚠️ 智能体列表为空（接口返回成功但 data 为空）")
            return data
        print(
            f"⚠️ 查询智能体列表失败: code={result.get('code')}, msg={result.get('msg')}"
        )
        return []
    except Exception as e:
        print(f"⚠️ 查询智能体列表异常: {e}")
        return []


def detect_agent_code(agent_nid: str, agent_list: list[dict[str, Any]]) -> str:
    """根据 agentNid 匹配智能体类型代码"""
    for agent in agent_list:
        if agent.get("agentId") == agent_nid:
            return agent.get("agentCode", "")
    return ""


def fetch_instance_details(instance_nid: str):
    """通过 agent/details 接口获取作业信息"""
    url = "https://cloudapi.polymas.com/agents/v1/agent/details"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not authorization:
        print("❌ 未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION")
        return None
    if not cookie:
        print("❌ 未找到COOKIE环境变量，请在.env文件中配置COOKIE")
        return None

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
    }

    payload = {"instanceIds": [instance_nid], "needToToolSchema": False}

    response = None
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        result = response.json()
    except json.decoder.JSONDecodeError:
        status_code = getattr(response, "status_code", "unknown")
        text = getattr(response, "text", "")
        print(f"❌ 获取作业信息失败，状态码：{status_code}")
        print("响应内容（非JSON格式，可能为服务端错误页）：", text)
        return None
    except Exception as e:
        print(f"❌ 获取作业信息异常：{str(e)}")
        return None

    if not result.get("success"):
        print(f"❌ 获取作业信息失败：{result.get('msg')}")
        return None

    instance_details = result.get("data", {}).get("instanceDetails", [])
    if not instance_details:
        print("❌ 获取作业信息失败：instanceDetails 为空")
        return None

    detail = instance_details[0] or {}
    user_id = detail.get("userId")
    agent_id = detail.get("agentNid") or detail.get("agentId")
    if not user_id:
        print("❌ 获取作业信息失败：响应中未找到 userId")
        return None
    if not agent_id:
        print("❌ 获取作业信息失败：响应中未找到 agentNid")
        return None

    agent_list = query_agent_list()
    agent_code = detect_agent_code(agent_id, agent_list)

    if agent_code == "exam_paper":
        writing_requirement = ""
        version = detail.get("version") or 1
    else:
        writing_requirement = extract_writing_requirement(detail)
        version = detail.get("version") or 2

    return {
        "user_id": user_id,
        "agent_id": agent_id,
        "agent_code": agent_code,
        "instance_name": detail.get("instanceName", ""),
        "desc": detail.get("desc", ""),
        "writing_requirement": writing_requirement,
        "version": version,
    }


def ensure_instance_context():
    """通过接口获取实例信息（仅当前进程使用，不写回.env）"""
    instance_nid = os.getenv("INSTANCE_NID", "").strip().strip('"').strip("'")
    if not instance_nid:
        print("❌ 未找到INSTANCE_NID环境变量，请在.env文件中配置INSTANCE_NID")
        return None

    details = fetch_instance_details(instance_nid)
    if not details:
        return None

    user_id = details.get("user_id") or os.getenv("USER_ID", "").strip().strip(
        '"'
    ).strip("'")
    agent_id = details.get("agent_id") or os.getenv("AGENT_ID", "").strip().strip(
        '"'
    ).strip("'")
    if not user_id:
        print("❌ 未获取到 userId，请检查 INSTANCE_NID 是否正确")
        return None
    if not agent_id:
        print("❌ 未获取到 agentId，请检查 INSTANCE_NID 是否正确")
        return None

    print(f"✅ 已获取USER_ID: {user_id}")
    print(f"✅ 已获取AGENT_ID: {agent_id}")

    agent_code = str(details.get("agent_code", "") or "")
    agent_code_display_map = {
        "exam_paper": "题卷",
        "essay_writing": "语言写作",
        "thesis_writing": "论文/报告",
    }
    agent_code_display = agent_code_display_map.get(agent_code) or agent_code or "未知"
    print(f"✅ 智能体类型: {agent_code_display}")

    return {
        "instance_nid": instance_nid,
        "user_id": user_id,
        "agent_id": agent_id,
        "agent_code": agent_code,
        "writing_requirement": details.get("writing_requirement", ""),
        "version": details.get("version") or 2,
        "instance_name": details.get("instance_name", ""),
        "desc": details.get("desc", ""),
    }


def upload_file(file_path):
    """
    上传文件到服务器

    Args:
        file_path: 本地文件路径

    Returns:
        dict: 包含 fileName 和 fileUrl 的字典，如果上传失败返回 None
    """
    url = "https://cloudapi.polymas.com/basic-resource/file/upload"

    # 生成唯一标识码
    identify_code = str(uuid.uuid4())

    try:
        # 打开文件
        with open(file_path, "rb") as f:
            # 获取文件名和大小
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 根据文件扩展名判断 MIME 类型
            file_ext = os.path.splitext(file_name)[1].lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".pdf": "application/pdf",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }
            mime_type = mime_types.get(file_ext, "application/octet-stream")

            # 准备表单数据
            files = {"file": (file_name, f, mime_type)}

            data = {
                "identifyCode": identify_code,
                "name": file_name,
                "chunk": "0",
                "chunks": "1",
                "size": str(file_size),
            }

            # 从环境变量中读取配置
            authorization = os.getenv("AUTHORIZATION")
            cookie = os.getenv("COOKIE")

            if not authorization:
                raise ValueError(
                    "未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION"
                )
            if not cookie:
                raise ValueError("未找到COOKIE环境变量，请在.env文件中配置COOKIE")

            headers = {
                "Authorization": authorization,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Cookie": cookie,
            }

            # 发送请求
            print(f"⏳ 正在上传文件: {file_name}")
            response = requests.post(url, headers=headers, data=data, files=files)
            result = response.json()

            if result.get("success"):
                data = result.get("data", {})
                file_url = data.get("ossUrl")
                print(f"✅ 文件上传成功: {file_name}")
                return {"fileName": file_name, "fileUrl": file_url}
            else:
                print(f"❌ 文件上传失败: {file_name}, 错误信息: {result.get('msg')}")
                return None

    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return None
    except Exception as e:
        print(f"❌ 上传文件时发生错误: {file_path}, 错误: {str(e)}")
        return None


def is_success_response(result: dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    if "success" in result:
        return bool(result.get("success"))
    return result.get("code") == 200


def fetch_task_result(task_id: str, context: dict[str, Any]):
    """轮询获取任务结果"""
    url = "https://cloudapi.polymas.com/agents/v1/get/task"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not authorization:
        return False, {
            "error": "未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION"
        }
    if not cookie:
        return False, {"error": "未找到COOKIE环境变量，请在.env文件中配置COOKIE"}

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
    }

    payload = {
        "taskId": task_id,
        "metadata": {"instanceNid": context.get("instance_nid", "")},
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        try:
            result = response.json()
        except json.decoder.JSONDecodeError:
            return False, {"status_code": response.status_code, "text": response.text}

        return is_success_response(result), result

    except Exception as e:
        return False, {"error": str(e)}


def poll_task_until_complete(
    task_id: str,
    context: dict[str, Any],
    interval_seconds: int = 10,
    timeout_seconds: int = 300,
):
    start_time = time.monotonic()
    last_result = None

    while True:
        success, result = fetch_task_result(task_id, context)
        last_result = result

        if success and isinstance(result, dict):
            data = result.get("data") or {}
            if isinstance(data, dict):
                if data.get("artifacts"):
                    return True, result
                status = data.get("status") or {}
                state = status.get("state")
                if state == "completed":
                    return True, result
                if state in {"failed", "error", "cancelled"}:
                    return False, result
        else:
            return False, result

        if time.monotonic() - start_time >= timeout_seconds:
            return False, {
                "error": "任务超时",
                "taskId": task_id,
                "last_response": last_result,
            }

        time.sleep(interval_seconds)


def normalize_text_input(raw_data: Any) -> Optional[str]:
    parsed = raw_data
    if isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError:
            return raw_data

    if isinstance(parsed, dict) and "content" in parsed:
        items = parsed.get("content") or []
        return json.dumps(_normalize_content_items(items), ensure_ascii=False)

    if isinstance(parsed, list):
        return json.dumps(_normalize_content_items(parsed), ensure_ascii=False)

    if isinstance(parsed, dict):
        return json.dumps(parsed, ensure_ascii=False)

    return str(parsed) if parsed is not None else None


def _normalize_content_items(items: Any) -> list[dict[str, Any]]:
    normalized = []
    if not isinstance(items, list):
        return normalized

    for item in items:
        if isinstance(item, dict):
            normalized.append(
                {
                    "itemId": item.get("itemId") or item.get("item_id") or "",
                    "itemName": item.get("itemName") or item.get("item_name") or "",
                    "stuAnswerContent": item.get("stuAnswerContent")
                    or item.get("stu_answer_content")
                    or item.get("content")
                    or "",
                }
            )
        else:
            normalized.append(
                {
                    "itemId": "",
                    "itemName": "",
                    "stuAnswerContent": str(item),
                }
            )

    return normalized


def homework_file_analysis(file_info: dict[str, Any], context: dict[str, Any]):
    """调用 homeworkFileAnalysis 接口解析作业文件"""
    url = "https://cloudapi.polymas.com/agents/v1/file/homeworkFileAnalysis"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not authorization:
        return (
            False,
            {"error": "未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION"},
            None,
        )
    if not cookie:
        return False, {"error": "未找到COOKIE环境变量，请在.env文件中配置COOKIE"}, None

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
    }

    payload = {
        "agentId": context.get("agent_id", ""),
        "instanceNid": context.get("instance_nid", ""),
        "userNid": context.get("user_id", ""),
        "version": context.get("version") or 2,
        "writingRequirement": context.get("writing_requirement", ""),
        "activeMode": "upload",
        "editorContent": "",
        "fileList": [file_info],
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

        try:
            result = response.json()
        except json.decoder.JSONDecodeError:
            return (
                False,
                {"status_code": response.status_code, "text": response.text},
                None,
            )

        if not is_success_response(result):
            return False, result, None

        text_input = normalize_text_input(result.get("data"))
        if not text_input:
            return (
                False,
                {"error": "解析成功但未提取到可用的 textInput", "response": result},
                None,
            )

        return True, result, text_input

    except Exception as e:
        return False, {"error": str(e)}, None


def execute_agent_text(text_input: str, context: dict[str, Any]):
    """调用 agent API 执行作业批改（TEXT_INPUT）"""
    url = "https://cloudapi.polymas.com/agents/v1/execute/agent"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not authorization:
        return False, {
            "error": "未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION"
        }
    if not cookie:
        return False, {"error": "未找到COOKIE环境变量，请在.env文件中配置COOKIE"}

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
    }

    user_id = context.get("user_id") or os.getenv("USER_ID", "")
    instance_nid = context.get("instance_nid") or os.getenv("INSTANCE_NID", "")
    if not user_id:
        return False, {"error": "未获取到userId，请检查INSTANCE_NID"}
    if not instance_nid:
        return False, {"error": "未获取到instanceNid，请检查INSTANCE_NID"}

    if not isinstance(text_input, str):
        text_input = json.dumps(text_input, ensure_ascii=False)

    payload = {
        "metadata": {
            "dimension": "NONE",
            "instanceNid": instance_nid,
            "userIds": [user_id],
            "version": context.get("version") or 2,
            "async": True,
        },
        "sendParams": {
            "message": {
                "kind": "message",
                "parts": [
                    {
                        "kind": "data",
                        "data": {
                            "writingRequirement": context.get(
                                "writing_requirement", ""
                            ),
                            "fileList": None,
                            "textInput": text_input,
                            "submitType": "TEXT_INPUT",
                        },
                    }
                ],
            }
        },
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

        try:
            result = response.json()
        except json.decoder.JSONDecodeError:
            return False, {"status_code": response.status_code, "text": response.text}

        return is_success_response(result), result

    except Exception as e:
        return False, {"error": str(e)}


def execute_agent_text_with_poll(
    text_input: str,
    context: dict[str, Any],
    interval_seconds: int = 2,
    timeout_seconds: int = 600,
    max_retries: int = 1,
):
    result: dict[str, Any] = {}
    for attempt in range(1 + max_retries):
        if attempt > 0:
            print(f"🔄 重试提交批改任务 ({attempt}/{max_retries})")
        success, result = execute_agent_text(text_input, context)
        if not success:
            return False, result

        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict) and data.get("kind") == "task":
            task_id = data.get("id")
            if not task_id:
                return False, {"error": "未获取到taskId", "response": result}
            ok, poll_result = poll_task_until_complete(
                task_id, context, interval_seconds, timeout_seconds
            )
            if ok:
                return True, poll_result
            is_timeout = (
                isinstance(poll_result, dict) and poll_result.get("error") == "任务超时"
            )
            if is_timeout and attempt < max_retries:
                continue
            return False, poll_result

        return success, result

    return False, result


def normalize_input_path(path_str: str) -> Path:
    """规范化用户输入路径"""
    path_str = path_str.strip().strip('"').strip("'")
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def collect_files_from_folder(folder_path: Path):
    """从文件夹中收集文件（忽略隐藏文件）"""
    if not folder_path.exists() or not folder_path.is_dir():
        return []
    return sorted(
        [p for p in folder_path.iterdir() if p.is_file() and not p.name.startswith(".")]
    )


def save_analysis_result(
    output_dir: Path,
    file_info: dict[str, Any],
    result: dict[str, Any],
    text_input: str,
):
    """保存 homeworkFileAnalysis 结果"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "analysis.json"
    payload = {
        "fileName": file_info.get("fileName"),
        "fileUrl": file_info.get("fileUrl"),
        "savedAt": datetime.now().isoformat(timespec="seconds"),
        "textInput": text_input,
        "response": result,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return output_path


def save_result(
    output_dir: Path,
    file_info: dict[str, Any],
    attempt_index: int,
    attempt_total: int,
    success: bool,
    result: dict[str, Any],
):
    """保存测评结果到文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"attempt_{attempt_index:02d}.json"
    payload = {
        "fileName": file_info.get("fileName"),
        "fileUrl": file_info.get("fileUrl"),
        "attempt": attempt_index,
        "attemptTotal": attempt_total,
        "success": success,
        "savedAt": datetime.now().isoformat(timespec="seconds"),
        "response": result,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return output_path


def load_pdf_generator(agent_code: str = ""):
    """动态加载 PDF 生成模块（根据智能体类型选择）"""
    base_dir = Path(__file__).parent
    if agent_code == "exam_paper":
        primary = base_dir / "utils" / "generate_report_exam.py"
        fallback = base_dir / "generate_report_exam.py"
        module_name = "generate_report_exam"
    else:
        primary = base_dir / "utils" / "generate_report.py"
        fallback = base_dir / "generate_report.py"
        module_name = "generate_report"

    report_path = primary if primary.exists() else fallback
    if not report_path.exists():
        print(f"❌ 未找到PDF生成脚本: {primary} 或 {fallback}")
        return None

    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, report_path)
    if not spec or not spec.loader:
        print("❌ 无法加载PDF生成脚本")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_pdf_report(
    result: dict[str, Any], output_path: Path, agent_code: str = ""
):
    """根据接口返回结果生成PDF报告"""
    try:
        module = load_pdf_generator(agent_code)
        if not module:
            return False
    except SystemExit as exc:
        print(f"❌ PDF依赖缺失：{exc}")
        return False
    except Exception as exc:
        print(f"❌ 加载PDF生成模块失败：{exc}")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
            dir=output_path.parent,
        ) as tmp:
            tmp.write(json.dumps(result, ensure_ascii=False, indent=2))
            tmp_path = Path(tmp.name)

        module.generate_pdf(str(tmp_path), str(output_path))
        tmp_path.unlink(missing_ok=True)
        return True
    except Exception as exc:
        print(f"❌ 生成PDF失败：{exc}")
        return False


def can_generate_pdf(result: dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    data = result.get("data")
    return isinstance(data, dict) and "artifacts" in data


def save_output(
    output_dir: Path,
    file_info: dict[str, Any],
    attempt_index: int,
    attempt_total: int,
    success: bool,
    result: dict[str, Any],
    output_format: str,
    agent_code: str = "",
):
    """根据输出格式保存结果"""
    if output_format == "pdf":
        if not success or not can_generate_pdf(result):
            reason = result.get("msg") or result.get("error")
            status_code = result.get("status_code")
            code = result.get("code")
            trace_id = result.get("traceId")
            extra = []
            if status_code:
                extra.append(f"status={status_code}")
            if code:
                extra.append(f"code={code}")
            if trace_id:
                extra.append(f"traceId={trace_id}")
            if reason:
                extra.append(f"reason={reason}")
            detail = f" ({', '.join(extra)})" if extra else ""
            print(
                f"⚠️ 结果失败或不支持PDF，跳过PDF生成: {file_info.get('fileName')}{detail}"
            )
            return None
        output_path = output_dir / f"attempt_{attempt_index:02d}.pdf"
        ok = generate_pdf_report(result, output_path, agent_code)
        return output_path if ok else None

    return save_result(
        output_dir, file_info, attempt_index, attempt_total, success, result
    )


async def async_upload_file(file_path: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        return await asyncio.to_thread(upload_file, file_path)


async def async_homework_analysis(
    file_info: dict[str, Any], context: dict[str, Any], semaphore: asyncio.Semaphore
):
    async with semaphore:
        return await asyncio.to_thread(homework_file_analysis, file_info, context)


async def async_execute_agent_text(
    text_input: str, context: dict[str, Any], semaphore: asyncio.Semaphore
):
    async with semaphore:
        return await asyncio.to_thread(
            execute_agent_text_with_poll, text_input, context
        )


async def evaluate_and_save(
    file_path: Path,
    file_info: dict[str, Any],
    text_input: str,
    context: dict[str, Any],
    output_dir: Path,
    attempt_index: int,
    attempt_total: int,
    output_format: str,
    semaphore: asyncio.Semaphore,
):
    print(f"⏳ 批改中: {file_info['fileName']} ({attempt_index}/{attempt_total})")
    success, result = await async_execute_agent_text(text_input, context, semaphore)
    output_path = save_output(
        output_dir,
        file_info,
        attempt_index,
        attempt_total,
        success,
        result,
        output_format,
        context.get("agent_code", ""),
    )
    if output_path:
        print(
            f"✅ 完成: {file_info['fileName']} ({attempt_index}/{attempt_total}) -> {output_path}"
        )
    else:
        print(
            f"⚠️ 完成: {file_info['fileName']} ({attempt_index}/{attempt_total}) -> 未生成文件"
        )
    return {
        "file_path": str(file_path),
        "attempt_index": attempt_index,
        "attempt_total": attempt_total,
        "success": success,
        "result": result,
    }


async def run_batch(
    file_paths: list[Path],
    attempts: int,
    context: dict[str, Any],
    output_root: Optional[Path],
    output_format: str,
    max_concurrency: int = 10,
):
    semaphore = asyncio.Semaphore(max_concurrency)

    upload_tasks = [async_upload_file(str(path), semaphore) for path in file_paths]
    upload_results = await asyncio.gather(*upload_tasks)

    file_infos = []
    for path, result in zip(file_paths, upload_results):
        if result:
            file_infos.append((path, result))

    if not file_infos:
        print("\n❌ 没有成功上传的文件，无法执行批改")
        return

    print(f"\n✅ 成功上传 {len(file_infos)} 个文件，共 {len(file_paths)} 个")

    analysis_tasks = [
        async_homework_analysis(file_info, context, semaphore)
        for _, file_info in file_infos
    ]
    analysis_results = await asyncio.gather(*analysis_tasks)

    prepared_files = []
    for (path, file_info), (success, analysis_result, text_input) in zip(
        file_infos, analysis_results
    ):
        if not success or not text_input:
            reason = "解析失败"
            if isinstance(analysis_result, dict):
                reason = (
                    analysis_result.get("msg") or analysis_result.get("error") or reason
                )
            print(f"❌ 解析失败: {file_info.get('fileName')} ({reason})")
            continue

        file_root = output_root if output_root else (path.parent / "review_results")
        file_output_dir = file_root / path.stem
        file_output_dir.mkdir(parents=True, exist_ok=True)
        analysis_path = save_analysis_result(
            file_output_dir, file_info, analysis_result, text_input
        )
        print(f"✅ 解析完成: {file_info.get('fileName')} -> {analysis_path}")

        prepared_files.append((path, file_info, text_input, file_output_dir))

    if not prepared_files:
        print("\n❌ 没有成功解析的文件，无法执行批改")
        return

    tasks = []
    for path, file_info, text_input, file_output_dir in prepared_files:
        for attempt_index in range(1, attempts + 1):
            tasks.append(
                evaluate_and_save(
                    path,
                    file_info,
                    text_input,
                    context,
                    file_output_dir,
                    attempt_index,
                    attempts,
                    output_format,
                    semaphore,
                )
            )

    results = await asyncio.gather(*tasks)
    success_count = sum(1 for item in results if item and item.get("success"))
    print(f"\n✅ 已完成 {len(results)} 次测评（成功 {success_count}）")
    generate_excel_summary(
        results,
        [item[0] for item in prepared_files],
        attempts,
        output_root,
        context.get("agent_code", ""),
    )


def main():
    """主函数：处理用户交互和文件上传"""
    print("=" * 60)
    print("作业批改系统 - v2 (统一版 | 自动检测智能体类型)")
    print("=" * 60)

    # 加载环境配置
    try:
        load_env_config()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return

    # 自动获取实例信息（不写回.env）
    context = ensure_instance_context()
    if not context:
        return

    instance_name = str(context.get("instance_name") or "").strip()
    desc = str(context.get("desc") or "").strip()
    agent_code = str(context.get("agent_code") or "").strip()
    agent_code_display_map = {
        "exam_paper": "题卷",
        "essay_writing": "语言写作",
        "thesis_writing": "论文/报告",
    }
    agent_code_display = agent_code_display_map.get(agent_code) or agent_code or "未知"
    if instance_name or desc:
        print("\n📌 作业信息：")
        print(f"智能体类型: {agent_code_display}")
        if instance_name:
            print(f"名称: {instance_name}")
        if desc:
            print(f"描述: {desc}")

    # 输入路径，自动判断文件/文件夹
    print("\n请输入文件或文件夹路径（多个文件用逗号分隔）：")
    print("  📁 文件夹：自动扫描其中所有文件，结果保存到 文件夹/review_results/")
    print("  📄 文件：直接上传指定文件，结果保存到 文件所在目录/review_results/")
    path_input = input("路径: ").strip()
    if not path_input:
        print("❌ 未输入路径")
        return

    file_paths: list[Path] = []
    output_root: Optional[Path] = None

    # 逗号分隔 → 多文件模式
    raw_paths = [p.strip() for p in path_input.split(",") if p.strip()]
    if len(raw_paths) == 1:
        single = normalize_input_path(raw_paths[0])
        if single.is_dir():
            file_paths = collect_files_from_folder(single)
            if not file_paths:
                print("❌ 文件夹中未找到可上传的文件")
                return
            output_root = single / "review_results"
            print(f"📁 检测到文件夹，已扫描到 {len(file_paths)} 个文件")
        elif single.is_file():
            file_paths = [single]
            print("📄 检测到单个文件")
        else:
            print(f"❌ 路径不存在: {single}")
            return
    else:
        for raw in raw_paths:
            p = normalize_input_path(raw)
            if p.is_file():
                file_paths.append(p)
            elif p.is_dir():
                found = collect_files_from_folder(p)
                file_paths.extend(found)
                if found:
                    print(f"📁 文件夹 {p.name}/ 扫描到 {len(found)} 个文件")
            else:
                print(f"⚠️ 跳过不存在的路径: {raw}")
        if not file_paths:
            print("❌ 未找到任何有效文件")
            return
        print(f"📄 共收集到 {len(file_paths)} 个文件")

    # 询问测评次数
    attempts_input = input("每个文档需要测评几次？(默认5): ").strip()
    attempts = 5
    if attempts_input:
        try:
            attempts = int(attempts_input)
        except ValueError:
            print("❌ 测评次数必须为整数")
            return
        if attempts <= 0:
            print("❌ 测评次数必须大于0")
            return

    print("\n请选择报告格式：")
    print("1) JSON 报告（默认,生成速度快）")
    print("2) PDF 报告（需要完整评分结果）")
    report_choice = input("请输入选项 (1/2): ").strip().lower()
    output_format = "pdf" if report_choice in {"2", "pdf"} else "json"

    print(
        f"\n📂 共需要上传 {len(file_paths)} 个文件，每个文件测评 {attempts} 次，输出格式: {output_format}\n"
    )

    asyncio.run(run_batch(file_paths, attempts, context, output_root, output_format))


if __name__ == "__main__":
    main()
