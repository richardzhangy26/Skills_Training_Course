import requests
import json
import json.decoder
import uuid
import os
from pathlib import Path
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
        return

    # 如果当前目录没有，尝试加载上级目录的.env文件
    parent_env = current_dir.parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✅ 从上级目录加载.env配置: {parent_env}")
        return

    # 如果都没有找到，尝试从当前工作目录加载
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists():
        load_dotenv(cwd_env)
        print(f"✅ 从工作目录加载.env配置: {cwd_env}")
        return

    raise FileNotFoundError("未找到.env配置文件，请在当前目录或上级目录创建.env文件")


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


def execute_agent(file_list):
    """
    调用 agent API 执行作业批改

    Args:
        file_list: 包含 fileName 和 fileUrl 的字典列表
    """
    url = "https://cloudapi.polymas.com/agents/v1/execute/agent"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": os.getenv("AUTHORIZATION"),
        "Cookie": os.getenv("COOKIE")
    }

    payload = {
        "metadata": {
            "instanceNid": os.getenv("INSTANCE_NID"),
            "version": 1,
            "dimension": "NONE",
            "userIds": [
                os.getenv("USER_ID")
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
        print("\n⏳ 正在调用 Agent API 进行作业批改...")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
        )

        result = response.json()
        print("\n✅ Agent API 响应：")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except json.decoder.JSONDecodeError:
        print(f"\n❌ 请求失败，状态码：{response.status_code}")
        print("响应内容（非JSON格式，可能为服务端错误页）：", response.text)

    except Exception as e:
        print(f"\n❌ 请求异常（如网络中断、Authorization令牌无效等）：{str(e)}")


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

    # 获取用户输入的文件路径
    print("\n请输入要上传的文件路径（多个文件用逗号分隔）：")
    print("示例: /path/to/file1.png,/path/to/file2.jpeg")
    file_paths_input = input("文件路径: ").strip()

    if not file_paths_input:
        print("❌ 未输入文件路径")
        return

    # 分割文件路径
    file_paths = [path.strip() for path in file_paths_input.split(',')]
    print(f"\n📂 共需要上传 {len(file_paths)} 个文件\n")

    # 上传所有文件
    file_list = []
    for file_path in file_paths:
        result = upload_file(file_path)
        if result:
            file_list.append(result)

    # 检查是否有成功上传的文件
    if not file_list:
        print("\n❌ 没有成功上传的文件，无法执行批改")
        return

    print(f"\n✅ 成功上传 {len(file_list)} 个文件，共 {len(file_paths)} 个")

    # 显示上传结果
    print("\n📋 上传文件列表：")
    for i, file_info in enumerate(file_list, 1):
        print(f"  {i}. {file_info['fileName']}")
        print(f"     URL: {file_info['fileUrl']}")

    # 调用 Agent API
    execute_agent(file_list)


if __name__ == "__main__":
    main()
