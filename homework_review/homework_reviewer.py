import asyncio
import json
import json.decoder
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv


def load_env_config():
    """
    加载.env配置文件，优先加载当前目录下的.env文件
    如果当前目录没有，则加载上级目录的.env文件
    """
    current_dir = Path(__file__).parent

    # 优先尝试加载当前目录下的.env文件
    local_env = current_dir / '.env'
    if local_env.exists():
        load_dotenv(local_env)
        print(f"✅ 从本地目录加载.env配置: {local_env}")
        return local_env

    # 如果当前目录没有，尝试加载上级目录的.env文件
    parent_env = current_dir.parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✅ 从上级目录加载.env配置: {parent_env}")
        return parent_env

    # 如果都没有找到，尝试从当前工作目录加载
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists():
        load_dotenv(cwd_env)
        print(f"✅ 从工作目录加载.env配置: {cwd_env}")
        return cwd_env

    raise FileNotFoundError("未找到.env配置文件，请在当前目录或上级目录创建.env文件")


def fetch_instance_details(instance_nid: str):
    """通过 agent/details 接口获取作业信息"""
    url = "https://cloudapi.polymas.com/agents/v1/agent/details"

    authorization = os.getenv('AUTHORIZATION')
    cookie = os.getenv('COOKIE')
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

    payload = {
        "instanceIds": [instance_nid],
        "needToToolSchema": False
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
        )
        result = response.json()
    except json.decoder.JSONDecodeError:
        print(f"❌ 获取USER_ID失败，状态码：{response.status_code}")
        print("响应内容（非JSON格式，可能为服务端错误页）：", response.text)
        return None
    except Exception as e:
        print(f"❌ 获取USER_ID异常：{str(e)}")
        return None

    if not result.get('success'):
        print(f"❌ 获取USER_ID失败：{result.get('msg')}")
        return None

    instance_details = result.get('data', {}).get('instanceDetails', [])
    if not instance_details:
        print("❌ 获取USER_ID失败：instanceDetails 为空")
        return None

    detail = instance_details[0] or {}
    user_id = detail.get('userId')
    if not user_id:
        print("❌ 获取USER_ID失败：响应中未找到 userId")
        return None

    return {
        "user_id": user_id,
        "instance_name": detail.get("instanceName", ""),
        "desc": detail.get("desc", ""),
    }


def ensure_user_id():
    """通过接口获取 USER_ID（仅当前进程使用，不写回.env）"""
    instance_nid = os.getenv('INSTANCE_NID', '').strip()
    if not instance_nid:
        print("❌ 未找到INSTANCE_NID环境变量，请在.env文件中配置INSTANCE_NID")
        return None

    details = fetch_instance_details(instance_nid)
    if not details:
        return None

    print(f"✅ 已获取USER_ID: {details['user_id']}")
    return details


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
        with open(file_path, 'rb') as f:
            # 获取文件名和大小
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 根据文件扩展名判断 MIME 类型
            file_ext = os.path.splitext(file_name)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            }
            mime_type = mime_types.get(file_ext, 'application/octet-stream')

            # 准备表单数据
            files = {
                'file': (file_name, f, mime_type)
            }

            data = {
                'identifyCode': identify_code,
                'name': file_name,
                'chunk': '0',
                'chunks': '1',
                'size': str(file_size)
            }

            # 从环境变量中读取配置
            authorization = os.getenv('AUTHORIZATION')
            cookie = os.getenv('COOKIE')

            if not authorization:
                raise ValueError("未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION")
            if not cookie:
                raise ValueError("未找到COOKIE环境变量，请在.env文件中配置COOKIE")

            headers = {
                'Authorization': authorization,
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'Cookie': cookie
            }

            # 发送请求
            print(f"⏳ 正在上传文件: {file_name}")
            response = requests.post(url, headers=headers, data=data, files=files)
            result = response.json()

            if result.get('success'):
                data = result.get('data', {})
                file_url = data.get('ossUrl')
                print(f"✅ 文件上传成功: {file_name}")
                return {
                    'fileName': file_name,
                    'fileUrl': file_url
                }
            else:
                print(f"❌ 文件上传失败: {file_name}, 错误信息: {result.get('msg')}")
                return None

    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return None
    except Exception as e:
        print(f"❌ 上传文件时发生错误: {file_path}, 错误: {str(e)}")
        return None


def execute_agent(file_list, user_id: Optional[str] = None):
    """
    调用 agent API 执行作业批改

    Args:
        file_list: 包含 fileName 和 fileUrl 的字典列表
    """
    url = "https://cloudapi.polymas.com/agents/v1/execute/agent"

    authorization = os.getenv('AUTHORIZATION')
    cookie = os.getenv('COOKIE')
    if not authorization:
        return False, {"error": "未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION"}
    if not cookie:
        return False, {"error": "未找到COOKIE环境变量，请在.env文件中配置COOKIE"}

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie
    }

    payload = {
        "metadata": {
            "instanceNid": os.getenv("INSTANCE_NID",""),
            "version": 1,
            "dimension": "NONE",
            "userIds": [
                user_id if user_id else os.getenv("USER_ID","")
            ]
        },
        "sendParams": {
            "message": {
                "kind": "message",
                "parts": [
                    {
                        "kind": "data",
                        "data": {
                            "submitType": "FILE_UPLOAD",
                            "fileList": file_list
                        }
                    }
                ]
            }
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
        )

        try:
            result = response.json()
        except json.decoder.JSONDecodeError:
            return False, {
                "status_code": response.status_code,
                "text": response.text
            }

        success_flag = result.get('success')
        if success_flag is None:
            success_flag = result.get('code') == 200
        return bool(success_flag), result

    except Exception as e:
        return False, {"error": str(e)}


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
    return sorted([p for p in folder_path.iterdir() if p.is_file() and not p.name.startswith('.')])


def save_result(output_dir: Path, file_info: dict, attempt_index: int, attempt_total: int, success: bool, result: dict):
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
        "response": result
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_path


def load_pdf_generator():
    """动态加载 PDF 生成模块（避免作为包导入）"""
    primary = Path(__file__).parent / "generate_report.py"
    fallback = Path(__file__).parent / "test" / "generate_report.py"
    report_path = primary if primary.exists() else fallback
    if not report_path.exists():
        print(f"❌ 未找到PDF生成脚本: {primary} 或 {fallback}")
        return None

    import importlib.util

    spec = importlib.util.spec_from_file_location("generate_report", report_path)
    if not spec or not spec.loader:
        print("❌ 无法加载PDF生成脚本")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_pdf_report(result: dict, output_path: Path):
    """根据接口返回结果生成PDF报告"""
    try:
        module = load_pdf_generator()
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
            dir=output_path.parent
        ) as tmp:
            tmp.write(json.dumps(result, ensure_ascii=False, indent=2))
            tmp_path = Path(tmp.name)

        module.generate_pdf(str(tmp_path), str(output_path))
        tmp_path.unlink(missing_ok=True)
        return True
    except Exception as exc:
        print(f"❌ 生成PDF失败：{exc}")
        return False


def save_output(output_dir: Path, file_info: dict, attempt_index: int, attempt_total: int, success: bool, result: dict, output_format: str):
    """根据输出格式保存结果"""
    if output_format == "pdf":
        if not success:
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
            print(f"⚠️ 结果失败，跳过PDF生成: {file_info.get('fileName')}{detail}")
            return None
        output_path = output_dir / f"attempt_{attempt_index:02d}.pdf"
        ok = generate_pdf_report(result, output_path)
        return output_path if ok else None

    return save_result(output_dir, file_info, attempt_index, attempt_total, success, result)


async def async_upload_file(file_path: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        return await asyncio.to_thread(upload_file, file_path)


async def async_execute_agent(file_info: dict, user_id: Optional[str], semaphore: asyncio.Semaphore):
    async with semaphore:
        return await asyncio.to_thread(execute_agent, [file_info], user_id)


async def evaluate_and_save(file_info: dict, user_id: Optional[str], output_dir: Path, attempt_index: int, attempt_total: int, output_format: str, semaphore: asyncio.Semaphore):
    print(f"⏳ 批改中: {file_info['fileName']} ({attempt_index}/{attempt_total})")
    success, result = await async_execute_agent(file_info, user_id, semaphore)
    output_path = save_output(output_dir, file_info, attempt_index, attempt_total, success, result, output_format)
    if output_path:
        print(f"✅ 完成: {file_info['fileName']} ({attempt_index}/{attempt_total}) -> {output_path}")
    else:
        print(f"⚠️ 完成: {file_info['fileName']} ({attempt_index}/{attempt_total}) -> 未生成文件")
    return success


async def run_batch(file_paths, attempts: int, user_id: Optional[str], output_root: Optional[Path], output_format: str, max_concurrency: int = 5):
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

    tasks = []
    for path, file_info in file_infos:
        file_root = output_root if output_root else (path.parent / "review_results")
        file_output_dir = file_root / path.stem
        file_output_dir.mkdir(parents=True, exist_ok=True)
        for attempt_index in range(1, attempts + 1):
            tasks.append(
                evaluate_and_save(file_info, user_id, file_output_dir, attempt_index, attempts, output_format, semaphore)
            )

    results = await asyncio.gather(*tasks)
    success_count = sum(1 for item in results if item)
    print(f"\n✅ 已完成 {len(results)} 次测评（成功 {success_count}）")


def main():
    """主函数：处理用户交互和文件上传"""
    print("=" * 60)
    print("作业批改系统 - 文件上传与批改")
    print("=" * 60)

    # 加载环境配置
    try:
        load_env_config()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return

    # 自动获取 USER_ID（不写回.env）
    details = ensure_user_id()
    if not details:
        return
    user_id = details["user_id"]

    instance_name = (details.get("instance_name") or "").strip()
    desc = (details.get("desc") or "").strip()
    if instance_name or desc:
        print("\n📌 作业信息：")
        if instance_name:
            print(f"名称: {instance_name}")
        if desc:
            print(f"描述: {desc}")

    # 选择上传方式
    print("\n请选择上传方式：")
    print("1) 单个/多个文件")
    print("2) 文件夹")
    upload_choice = input("请输入选项 (1/2，默认2): ").strip()

    file_paths = []
    output_root = None

    if upload_choice == "" or upload_choice == "2":
        folder_input = input("请输入文件夹路径: ").strip()
        if not folder_input:
            print("❌ 未输入文件夹路径")
            return
        folder_path = normalize_input_path(folder_input)
        file_paths = collect_files_from_folder(folder_path)
        if not file_paths:
            print("❌ 文件夹中未找到可上传的文件")
            return
        output_root = folder_path / "review_results"
    else:
        print("\n请输入要上传的文件路径（多个文件用逗号分隔）：")
        print("示例: /path/to/file1.png,/path/to/file2.jpeg")
        file_paths_input = input("文件路径: ").strip()
        if not file_paths_input:
            print("❌ 未输入文件路径")
            return
        file_paths = [normalize_input_path(path.strip()) for path in file_paths_input.split(',') if path.strip()]
        if not file_paths:
            print("❌ 未输入有效文件路径")
            return
        output_root = None

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
    print("2) PDF 报告（生成慢，但是好看）")
    report_choice = input("请输入选项 (1/2): ").strip().lower()
    output_format = "pdf" if report_choice in {"2", "pdf"} else "json"

    print(f"\n📂 共需要上传 {len(file_paths)} 个文件，每个文件测评 {attempts} 次，输出格式: {output_format}\n")

    asyncio.run(run_batch(file_paths, attempts, user_id, output_root, output_format))


if __name__ == "__main__":
    main()
