import requests
import json
import json.decoder
from dotenv import load_dotenv
import os
from pathlib import Path 
def load_env_config():
    """
    加载.env配置文件，优先加载当前目录下的.env文件
    如果当前目录没有，则加载上级目录的.env文件
    """
    # 获取当前文件所在目录
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

def send_post_request():

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
                            "fileList": [
                                {
                                    "fileName": "背景图.jpeg",
                                    "fileUrl": "https://prod-polymas.oss-cn-hangzhou.aliyuncs.com/polymas-basic-resource/202512/69394003e4b0824e3e4a424f.jpeg"  # 文档1-21节示例文件URL，确保可访问
                                }
                            ]
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

        result = response.json()
        print("请求响应：")
        print(json.dumps(result, indent=2, ensure_ascii=False))


    except json.decoder.JSONDecodeError:
        print(f"请求失败，状态码：{response.status_code}")
        print("响应内容（非JSON格式，可能为服务端错误页）：", response.text)

    except Exception as e:
        print("请求异常（如网络中断、Authorization令牌无效等）：", str(e))


if __name__ == "__main__":
    load_env_config()
    send_post_request()