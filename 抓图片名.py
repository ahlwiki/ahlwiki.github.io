import os
import json
from typing import List

GALLERY_ROOT = "images/kmf_gallery"          # 图片根目录
JSON_ROOT = "kmf_individual_files"           # JSON 详情目录
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
EXCLUDE_NAMES = ('cover', 'cover_thumb')      # 不含扩展名的文件名


def get_variants(folder_path: str) -> List[str]:
    """返回文件夹中除 exclude 外的图片文件名（不含扩展名）"""
    variants = []
    try:
        for f in os.listdir(folder_path):
            name, ext = os.path.splitext(f)
            if ext.lower() in IMAGE_EXTENSIONS and name not in EXCLUDE_NAMES:
                variants.append(name)
    except OSError as e:
        print(f"  读取文件夹失败: {e}")
    return variants


def update_json(json_path: str, variants: List[str]) -> bool:
    """更新 JSON 文件中的 image_variants 字段，返回是否成功"""
    if not os.path.exists(json_path):
        print(f"  错误: JSON 文件不存在 {json_path}")
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  读取 JSON 失败: {e}")
        return False

    # 覆盖或添加 image_variants 字段
    data['image_variants'] = variants

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"  写入 JSON 失败: {e}")
        return False


def main():
    print("开始处理 image_variants 字段（覆盖原有内容）")
    if not os.path.isdir(GALLERY_ROOT):
        print(f"错误：目录 {GALLERY_ROOT} 不存在")
        return
    if not os.path.isdir(JSON_ROOT):
        print(f"错误：目录 {JSON_ROOT} 不存在")
        return

    total = 0
    updated = 0

    for folder in os.listdir(GALLERY_ROOT):
        folder_path = os.path.join(GALLERY_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
        total += 1
        print(f"\n[{total}] 处理 {folder} ...")

        variants = get_variants(folder_path)
        json_path = os.path.join(JSON_ROOT, f"{folder}.json")
        if update_json(json_path, variants):
            print(f"  已更新 image_variants: {variants}")
            updated += 1
        else:
            print(f"  更新失败")

    print(f"\n完成。总机体: {total}, 成功更新: {updated}")


if __name__ == "__main__":
    main()