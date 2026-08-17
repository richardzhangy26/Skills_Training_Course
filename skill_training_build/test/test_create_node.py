import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import uuid
from nanoid import generate

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

def send_create_script_step_request():
    """
    调用创建脚本节点接口
    """
    load_env_config()

    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/createScriptStep"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")

    if not authorization:
        raise ValueError("未找到AUTHORIZATION环境变量，请在.env文件中配置AUTHORIZATION")
    if not cookie:
        raise ValueError("未找到COOKIE环境变量，请在.env文件中配置COOKIE")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    payload = {
        "trainTaskId": "L9dyJGpkboi7J6p30a54",
        "stepId": generate(size=21),
        "stepDetailDTO": {
            "nodeType": "SCRIPT_NODE",
            "stepName": "你好",
            "description": "",
            "prologue": "",
            "modelId": "",
            "llmPrompt": "",
            "trainerName": "",
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": 0,
            "searchEngineSwitch": 0,
            "trainSubType": "ability"
        },
        "positionDTO": {
            "x": 570,
            "y": 300
        },
        "courseId": "GEaZpzlbP2uXve4vExjM"
    }

    try:
        print("⏳ 正在创建脚本节点...")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=20
        )
        result = response.json()
        print("✅ 接口响应：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except json.decoder.JSONDecodeError:
        print(f"❌ 请求失败，状态码：{response.status_code}")
        print("响应内容（非JSON格式，可能为服务端错误页）：", response.text)
    except Exception as e:
        print("❌ 请求异常（如网络中断、Authorization或Cookie无效等）：", str(e))

if __name__ == "__main__":
    send_create_script_step_request()
