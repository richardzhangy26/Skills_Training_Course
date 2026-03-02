#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import requests
from pathlib import Path
from urllib.parse import urlparse

def download_videos(csv_path, output_dir):
    """
    从 CSV 文件下载视频并保存到目标目录

    Args:
        csv_path: CSV 文件路径
        output_dir: 输出目录路径
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        video_list = []
        for row in reader:
            if len(row) >= 2 and row[0] and row[1]:
                filename = row[0].strip()
                url = row[1].strip()
                video_list.append((filename, url))

    print(f"找到 {len(video_list)} 个视频需要下载")
    print(f"目标目录: {output_path}")
    print("-" * 60)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    filename_counts = {}

    for idx, (filename, url) in enumerate(video_list, 1):
        original_filename = filename

        filename_counts[filename] = filename_counts.get(filename, 0) + 1
        if filename_counts[filename] > 1:
            name_without_ext = Path(filename).stem
            ext = Path(filename).suffix
            filename = f"{name_without_ext}_{filename_counts[filename]}{ext}"

        output_file = output_path / filename

        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"[{idx}/{len(video_list)}] 跳过已存在: {filename} ({file_size:,} bytes)")
            skipped_count += 1
            continue

        print(f"[{idx}/{len(video_list)}] 下载中: {original_filename} -> {filename}")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = output_file.stat().st_size
            print(f"  ✓ 完成 ({file_size:,} bytes)")
            success_count += 1

        except Exception as e:
            print(f"  ✗ 失败: {e}")
            failed_count += 1

    print("-" * 60)
    print(f"下载完成！")
    print(f"成功: {success_count}")
    print(f"跳过: {skipped_count}")
    print(f"失败: {failed_count}")
    print(f"总计: {len(video_list)}")

if __name__ == "__main__":
    CSV_PATH = "/Users/richardzhang/工作/能力训练/viedo_download.csv"
    OUTPUT_DIR = "/Users/richardzhang/工作/能力训练/哈工程-水声换能器及基阵"

    download_videos(CSV_PATH, OUTPUT_DIR)
