import requests
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

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

def upload_png_file(file_path):
    """
    上传PNG文件到服务器
    
    Args:
        file_path: 本地文件路径，例如 'image.png'
    """
    url = "https://cloudapi.polymas.com/basic-resource/file/upload"
    
    # 生成唯一标识码
    identify_code = str(uuid.uuid4())
    
    # 打开文件
    with open(file_path, 'rb') as f:
        # 获取文件名和大小
        import os
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # 准备表单数据
        files = {
            'file': (file_name, f, 'image/png')
        }
        
        data = {
            'identifyCode': identify_code,
            'name': file_name,
            'chunk': '0',
            'chunks': '1',
            'size': str(file_size)
        }
        
        # 加载环境变量配置
        load_env_config()

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
        response = requests.post(url, headers=headers, data=data, files=files)
        
        # 返回结果
        return response.json()


# 使用示例
if __name__ == "__main__":
    try:
        # 上传文件
        result = upload_png_file('/Users/richardzhang/工作/能力训练/README/env配置1.png')

        print("上传结果:")
        print(f"状态码: {result.get('code')}")
        print(f"成功: {result.get('success')}")

        if result.get('success'):
            data = result.get('data', {})
            print(f"文件ID: {data.get('fileId')}")
            print(f"文件名: {data.get('fileName')}")
            print(f"OSS URL: {data.get('ossUrl')}")
        else:
            print(f"错误信息: {result.get('msg')}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("提示：如果使用本地测试配置，上传会失败是正常的")