import os
from pathlib import Path
from PIL import Image

# ===================== 配置 =====================
INPUT_DIR = Path("翻转")                 # 输入文件夹（透明底 PNG）
OUTPUT_DIR = Path("翻转_webp")           # 输出文件夹（压缩后的 WebP）
TARGET_MAX_KB = 40                      # 目标最大大小（KB）
QUALITY_STEP = 1                        # 步进精度（可调整：1, 2, 5, 10 等）
# ===============================================

def ensure_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)

def add_white_background(png_path):
    """为透明 PNG 添加白底，返回 RGB 模式的 PIL Image"""
    img = Image.open(png_path).convert("RGBA")
    white_bg = Image.new("RGB", img.size, (255, 255, 255))
    white_bg.paste(img, (0, 0), img.split()[-1])  # alpha 通道作为 mask
    return white_bg

def get_webp_size(img, quality):
    """返回使用指定 quality 保存为 WebP 时的文件大小（字节）"""
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=quality, method=6)
    return buffer.tell()

def compress_webp_stepwise(img, output_path, max_kb, step):
    """
    从 quality=100 开始，每次降低 step，直到文件大小 <= max_kb。
    返回最终文件大小（KB）。
    """
    max_bytes = max_kb * 1024
    best_quality = None
    final_size = None

    # 从最高质量向下尝试
    for q in range(100, 0, -step):
        size_bytes = get_webp_size(img, q)
        if size_bytes <= max_bytes:
            best_quality = q
            final_size = size_bytes / 1024
            break

    # 如果一直没有成功（即 q=1 时仍大于 max_kb），则使用 q=1
    if best_quality is None:
        best_quality = 1
        final_size = get_webp_size(img, 1) / 1024
        print(f"   ⚠️ 警告: 即使 quality=1，文件仍为 {final_size:.1f} KB，超过 {max_kb} KB")

    # 保存最终文件
    img.save(output_path, format="WEBP", quality=best_quality, method=6)
    return final_size

def main():
    ensure_output_dir()
    png_files = list(INPUT_DIR.glob("*.png")) + list(INPUT_DIR.glob("*.PNG"))
    if not png_files:
        print(f"在 '{INPUT_DIR}' 文件夹中没有找到 PNG 图片")
        return

    for png_path in png_files:
        print(f"处理: {png_path.name}")
        img_with_bg = add_white_background(png_path)
        output_path = OUTPUT_DIR / f"{png_path.stem}.webp"
        final_size_kb = compress_webp_stepwise(img_with_bg, output_path, TARGET_MAX_KB, QUALITY_STEP)
        status = "✅" if final_size_kb <= TARGET_MAX_KB else "⚠️"
        print(f"    {status} 已保存: {output_path.name} (质量步进 {QUALITY_STEP}, 大小: {final_size_kb:.1f} KB)")

    print("所有图片处理完成！")

if __name__ == "__main__":
    main()