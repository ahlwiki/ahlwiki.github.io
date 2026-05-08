import os

# 配置
GALLERY_ROOT = "images/kmf_gallery"   # 机体的图片根目录

def unify_cover_filename():
    """遍历机体文件夹，将 cover_thumb.jpg 统一为 cover.jpg"""
    if not os.path.isdir(GALLERY_ROOT):
        print(f"错误：目录不存在 {GALLERY_ROOT}")
        return

    renamed = 0
    skipped = 0
    missing = 0

    for folder_name in os.listdir(GALLERY_ROOT):
        folder_path = os.path.join(GALLERY_ROOT, folder_name)
        if not os.path.isdir(folder_path):
            continue

        cover_thumb = os.path.join(folder_path, "cover_thumb.jpg")
        cover = os.path.join(folder_path, "cover.jpg")

        if os.path.isfile(cover_thumb):
            # 如果 cover.jpg 已存在，可选择先删除或备份，这里直接覆盖
            if os.path.isfile(cover):
                os.remove(cover)   # 删除原有 cover.jpg
                print(f"删除原有 {folder_name}/cover.jpg")
            os.rename(cover_thumb, cover)
            print(f"重命名 {folder_name}/cover_thumb.jpg -> cover.jpg")
            renamed += 1
        elif os.path.isfile(cover):
            # 已经是 cover.jpg，无需处理
            print(f"跳过 {folder_name}：已是 cover.jpg")
            skipped += 1
        else:
            print(f"跳过 {folder_name}：无 cover_thumb.jpg 或 cover.jpg")
            missing += 1

    print("\n处理完成")
    print(f"重命名: {renamed} 个")
    print(f"已存在 cover.jpg: {skipped} 个")
    print(f"缺失封面: {missing} 个")

if __name__ == "__main__":
    unify_cover_filename()