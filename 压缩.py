import os
from pathlib import Path
from PIL import Image

# ========== 配置 ==========
TARGET_DIR = "翻转"                # 要处理的文件夹名称
QUALITY = 30                       # WebP 质量 (0-100)，建议 75-90
METHOD = 6                         # 压缩方法 (0-6)，6 最慢但质量最好
REMOVE_ORIGINAL = False            # 是否删除原始 PNG 文件（默认 False，保留）
RECURSIVE = False                  # 是否递归处理子文件夹

def convert_png_to_webp():
    base_path = Path.cwd() / TARGET_DIR
    if not base_path.exists() or not base_path.is_dir():
        print(f"错误：文件夹 '{TARGET_DIR}' 不存在")
        return

    # 收集所有 .png 文件
    if RECURSIVE:
        png_files = list(base_path.rglob("*.png"))
    else:
        png_files = list(base_path.glob("*.png"))

    if not png_files:
        print(f"在 '{TARGET_DIR}' 中没有找到 .png 文件")
        return

    print(f"找到 {len(png_files)} 个 PNG 文件，开始转换为 WebP...")
    success = 0
    for png_path in png_files:
        webp_path = png_path.with_suffix(".webp")
        try:
            with Image.open(png_path) as img:
                # 转为 RGB（如果有透明通道，保留 RGBA；PNG 常用 RGBA）
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                # 保存为 WebP（有损压缩）
                img.save(webp_path, "WEBP", quality=QUALITY, method=METHOD, lossless=False)
            print(f"✓ 转换成功: {png_path.relative_to(base_path)} -> {webp_path.name}")
            if REMOVE_ORIGINAL:
                png_path.unlink()
                print(f"  已删除原 PNG 文件")
            success += 1
        except Exception as e:
            print(f"✗ 转换失败: {png_path.relative_to(base_path)} - {e}")

    print(f"\n处理完成，成功转换 {success} 个文件")

if __name__ == "__main__":
    convert_png_to_webp()