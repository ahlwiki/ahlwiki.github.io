import os
from pathlib import Path
from PIL import Image

# 配置
TARGET_DIR = "翻转"           # 要处理的文件夹名称（相对于脚本运行目录）
QUALITY = 85                  # WebP 保存质量 (0-100)，数值越高质量越好，文件越大
RECURSIVE = False             # 是否递归处理子文件夹，False 表示仅处理根目录

def flip_webp_images():
    # 获取当前脚本所在目录下的目标文件夹路径
    base_path = Path.cwd() / TARGET_DIR
    if not base_path.exists() or not base_path.is_dir():
        print(f"错误：文件夹 '{TARGET_DIR}' 不存在或不是目录")
        return

    # 收集所有 .webp 文件
    if RECURSIVE:
        webp_files = list(base_path.rglob("*.png"))
    else:
        webp_files = list(base_path.glob("*.png"))

    if not webp_files:
        print(f"在 '{TARGET_DIR}' 中没有找到 .webp 文件")
        return

    print(f"找到 {len(webp_files)} 个 .webp 文件，开始处理...")
    success_count = 0
    for img_path in webp_files:
        try:
            with Image.open(img_path) as img:
                # 水平翻转
                flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
                # 保存覆盖原文件（保持尺寸，指定质量）
                flipped_img.save(img_path, "WEBP", quality=85, lossless=False)
            print(f"✓ 已翻转: {img_path.relative_to(base_path)}")
            success_count += 1
        except Exception as e:
            print(f"✗ 处理失败: {img_path.relative_to(base_path)} - {e}")

    print(f"\n处理完成，成功翻转 {success_count} 个文件")

if __name__ == "__main__":
    flip_webp_images()