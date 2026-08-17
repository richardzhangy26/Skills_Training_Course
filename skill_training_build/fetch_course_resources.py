"""抓取课程资源库全量文件元数据，输出结构化 JSON 供创建训练剧本使用。

遍历三层目录：学派文件夹 → 人物子文件夹 → 文件列表，
收集 fileId / fileUrl / fileName / contentType 等字段。
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

COURSE_ID = "GEaZp90NLzS9Ekwjl4xj"
ROOT_LIBRARY_FOLDER_ID = "GMoUCxcwrI"
FOLDER_API = "https://cloudapi.polymas.com/teacher-course/course/library/folderResource/page"
FILE_API = "https://cloudapi.polymas.com/teacher-course/course/library/fileResource/page"
PAGE_SIZE = 100

CONTENT_TYPE_MAP = {
    "pdf": "application/pdf",
    "mp4": "video/mp4",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def load_env_config():
    current_dir = Path(__file__).parent
    for env_path in (current_dir.parent / ".env", current_dir / ".env", Path.cwd() / ".env"):
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment config: {env_path}")
            return
    print("⚠️ No .env file found, using system environment variables.")


def get_headers():
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise ValueError("Missing AUTHORIZATION or COOKIE in environment.")
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }


def derive_content_type(suffix):
    if not suffix:
        return "application/octet-stream"
    return CONTENT_TYPE_MAP.get(suffix.lower(), f"application/{suffix.lower()}")


def build_resource_entry(file_item):
    suffix = file_item.get("suffix") or ""
    return {
        "fileId": file_item.get("resourceId", ""),
        "fileName": file_item.get("resourceName", ""),
        "fileUrl": file_item.get("ossUrl", ""),
        "contentType": derive_content_type(suffix),
        "type": "knowledge",
        "category": "知识库",
        "suffix": suffix,
        "size": file_item.get("size"),
        "isRequired": 0,
    }


def fetch_folders(library_folder_id, path=""):
    """POST folderResource/page，返回子文件夹列表（自动分页）。"""
    headers = get_headers()
    all_items = []
    page_num = 1
    while True:
        payload = {
            "courseId": COURSE_ID,
            "libraryFolderId": library_folder_id,
            "keyword": "",
            "path": path,
            "pageNum": page_num,
            "pageSize": PAGE_SIZE,
        }
        try:
            resp = requests.post(FOLDER_API, headers=headers, json=payload, timeout=20)
            result = resp.json()
        except Exception as e:
            print(f"  ❌ fetch_folders error (page {page_num}): {e}")
            break
        if not result.get("success") and result.get("code") != 200:
            print(f"  ❌ folderResource/page failed: {result.get('msg')}")
            break
        data = result.get("data", {})
        items = data.get("list", [])
        all_items.extend(items)
        if data.get("last", True) or len(items) < PAGE_SIZE:
            break
        page_num += 1
    return all_items


def fetch_files(library_folder_id, path):
    """POST fileResource/page，返回文件列表（自动分页）。"""
    headers = get_headers()
    all_items = []
    page_num = 1
    while True:
        payload = {
            "courseId": COURSE_ID,
            "libraryFolderId": library_folder_id,
            "keyword": "",
            "path": path,
            "pageNum": page_num,
            "pageSize": PAGE_SIZE,
        }
        try:
            resp = requests.post(FILE_API, headers=headers, json=payload, timeout=20)
            result = resp.json()
        except Exception as e:
            print(f"  ❌ fetch_files error (page {page_num}): {e}")
            break
        if not result.get("success") and result.get("code") != 200:
            print(f"  ❌ fileResource/page failed: {result.get('msg')}")
            break
        data = result.get("data", {})
        items = data.get("list", [])
        all_items.extend(items)
        if data.get("last", True) or len(items) < PAGE_SIZE:
            break
        page_num += 1
    return all_items


def main():
    load_env_config()

    print(f"--- 课程资源库抓取 ---")
    print(f"courseId: {COURSE_ID}")
    print(f"libraryFolderId: {ROOT_LIBRARY_FOLDER_ID}")

    # 1. 获取学派文件夹
    print(f"\n📁 获取顶层学派文件夹...")
    school_folders = fetch_folders(ROOT_LIBRARY_FOLDER_ID, path="")
    print(f"   找到 {len(school_folders)} 个学派文件夹")

    schools = []
    total_files = 0

    for school_idx, school_folder in enumerate(school_folders, start=1):
        school_name = school_folder.get("resourceName", "未命名学派")
        school_resource_id = school_folder.get("resourceId", "")
        school_path = school_folder.get("path", "")
        print(f"\n[{school_idx}/{len(school_folders)}] 📂 {school_name} (path={school_path})")

        # 2. 获取人物子文件夹
        person_folders = fetch_folders(ROOT_LIBRARY_FOLDER_ID, path=school_path)
        print(f"   找到 {len(person_folders)} 个人物子文件夹")

        persons = []
        school_file_count = 0

        for person_folder in person_folders:
            person_name = person_folder.get("resourceName", "未命名人物")
            person_resource_id = person_folder.get("resourceId", "")
            person_path = person_folder.get("path", "")

            # 3. 获取文件列表
            file_items = fetch_files(ROOT_LIBRARY_FOLDER_ID, path=person_path)
            file_entries = [build_resource_entry(f) for f in file_items]
            school_file_count += len(file_entries)

            persons.append({
                "personName": person_name,
                "resourceId": person_resource_id,
                "path": person_path,
                "fileCount": len(file_entries),
                "files": file_entries,
            })

            if file_entries:
                print(f"      👤 {person_name}: {len(file_entries)} 个文件")
            else:
                print(f"      👤 {person_name}: （无文件）")

        schools.append({
            "schoolName": school_name,
            "resourceId": school_resource_id,
            "path": school_path,
            "personCount": len(persons),
            "fileCount": school_file_count,
            "persons": persons,
        })
        total_files += school_file_count
        print(f"   → {school_name} 共 {school_file_count} 个文件")

    output = {
        "courseId": COURSE_ID,
        "libraryFolderId": ROOT_LIBRARY_FOLDER_ID,
        "totalFiles": total_files,
        "schools": schools,
    }

    output_path = Path(__file__).parent.parent / "skills_training_course" / "西南医科大学-临床心理检测与治疗" / "资源库详情.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 抓取完成！共 {total_files} 个文件")
    print(f"📄 输出文件: {output_path}")


if __name__ == "__main__":
    main()
