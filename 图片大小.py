import os
import math
from collections import defaultdict

# 配置
TARGET_DIR = "images"                     # 要统计的根目录
SUPPORTED_EXTS = {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp'}  # 支持的图片扩展名
COVER_SIZE_THRESHOLD_KB = 8               # cover 图片大小阈值（KB）
OTHER_SIZE_THRESHOLD_KB = 90              # 其他图片大小阈值（KB）

def format_kb(byte_size: int) -> float:
    """字节转 KB（1 KB = 1024 字节）"""
    return byte_size / 1024.0

def main():
    if not os.path.isdir(TARGET_DIR):
        print(f"错误：目录 '{TARGET_DIR}' 不存在")
        return

    cover_sizes = []          # 封面图片大小（KB）
    other_sizes = []          # 其他图片大小（KB）
    large_cover_files = []    # 大小 ≥ COVER_SIZE_THRESHOLD_KB 的 cover 文件路径
    large_other_files = []    # 大小 ≥ OTHER_SIZE_THRESHOLD_KB 的其他图片文件路径

    for dirpath, _, filenames in os.walk(TARGET_DIR):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTS:
                continue

            filepath = os.path.join(dirpath, filename)
            size_kb = format_kb(os.path.getsize(filepath))

            # 判断是否为封面（基本名为 cover，不区分大小写）
            base_name = os.path.splitext(filename)[0].lower()
            if base_name == "cover":
                cover_sizes.append(size_kb)
                if size_kb >= COVER_SIZE_THRESHOLD_KB:
                    large_cover_files.append((filepath, size_kb))
            else:
                other_sizes.append(size_kb)
                if size_kb >= OTHER_SIZE_THRESHOLD_KB:
                    large_other_files.append((filepath, size_kb))

    if not cover_sizes and not other_sizes:
        print("未找到任何图片文件，请检查目录。")
        return

    # 封面图片统计（1KB 档位）
    cover_counts = defaultdict(int)
    for sz in cover_sizes:
        bucket = int(math.floor(sz))
        cover_counts[bucket] += 1

    # 其他图片统计（5KB 档位）
    other_counts = defaultdict(int)
    for sz in other_sizes:
        bucket = int(math.floor(sz / 5.0)) * 5
        other_counts[bucket] += 1

    # 输出到控制台
    print("=" * 60)
    print("封面图片 (文件名 = cover.*) 大小分布 (档位: 1KB)")
    print("=" * 60)
    print(f"{'档位(KB)':<10} {'数量':<10}")
    for bucket in sorted(cover_counts.keys()):
        print(f"{bucket:<10} {cover_counts[bucket]:<10}")
    print(f"\n总计: {len(cover_sizes)} 个文件")

    if large_cover_files:
        print(f"\n大小 ≥ {COVER_SIZE_THRESHOLD_KB} KB 的 cover 图片:")
        for path, size in large_cover_files:
            print(f"  {size:.2f} KB - {path}")
    else:
        print(f"\n没有大小 ≥ {COVER_SIZE_THRESHOLD_KB} KB 的 cover 图片")

    print("\n" + "=" * 60)
    print("其他图片大小分布 (档位: 5KB)")
    print("=" * 60)
    print(f"{'档位(KB)':<10} {'数量':<10}")
    for bucket in sorted(other_counts.keys()):
        print(f"{bucket:<10} {other_counts[bucket]:<10}")
    print(f"\n总计: {len(other_sizes)} 个文件")

    if large_other_files:
        print(f"\n大小 ≥ {OTHER_SIZE_THRESHOLD_KB} KB 的其他图片:")
        for path, size in large_other_files:
            print(f"  {size:.2f} KB - {path}")
    else:
        print(f"\n没有大小 ≥ {OTHER_SIZE_THRESHOLD_KB} KB 的其他图片")

    # 保存到文件
    with open("cover_size_stats.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("封面图片 (文件名 = cover.*) 大小分布 (档位: 1KB)\n")
        f.write("=" * 60 + "\n")
        f.write(f"{'档位(KB)':<10} {'数量':<10}\n")
        for bucket in sorted(cover_counts.keys()):
            f.write(f"{bucket:<10} {cover_counts[bucket]:<10}\n")
        f.write(f"\n总计: {len(cover_sizes)} 个文件\n")

        if large_cover_files:
            f.write(f"\n大小 ≥ {COVER_SIZE_THRESHOLD_KB} KB 的 cover 图片:\n")
            for path, size in large_cover_files:
                f.write(f"  {size:.2f} KB - {path}\n")
        else:
            f.write(f"\n没有大小 ≥ {COVER_SIZE_THRESHOLD_KB} KB 的 cover 图片\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("其他图片大小分布 (档位: 5KB)\n")
        f.write("=" * 60 + "\n")
        f.write(f"{'档位(KB)':<10} {'数量':<10}\n")
        for bucket in sorted(other_counts.keys()):
            f.write(f"{bucket:<10} {other_counts[bucket]:<10}\n")
        f.write(f"\n总计: {len(other_sizes)} 个文件\n")

        if large_other_files:
            f.write(f"\n大小 ≥ {OTHER_SIZE_THRESHOLD_KB} KB 的其他图片:\n")
            for path, size in large_other_files:
                f.write(f"  {size:.2f} KB - {path}\n")
        else:
            f.write(f"\n没有大小 ≥ {OTHER_SIZE_THRESHOLD_KB} KB 的其他图片\n")

    print("\n统计结果已保存到 cover_size_stats.txt")

if __name__ == "__main__":
    main()