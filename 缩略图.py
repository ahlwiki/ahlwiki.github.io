import os
from PIL import Image

BASE_DIR = 'images/kmf_gallery'
THUMB_SIZE = (120, 200)
# 你可以根据你的网站风格改为 (0, 0, 0) 黑色背景
BG_COLOR = (255, 255, 255)


def create_thumbnails():
    kmf_folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]

    for folder in kmf_folders:
        folder_path = os.path.join(BASE_DIR, folder)
        source_file = None

        # 寻找原图
        for ext in ['Standard.png', 'Standard.jpg']:
            if os.path.exists(os.path.join(folder_path, ext)):
                source_file = os.path.join(folder_path, ext)
                break

        if not source_file: continue

        try:
            with Image.open(source_file) as img:
                # --- 处理透明背景的核心逻辑 ---
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    # 创建一个背景色层
                    background = Image.new('RGB', img.size, BG_COLOR)
                    # 将原图粘贴到背景层，第三个参数 img 表示使用原图的 Alpha 通道作为蒙版
                    background.paste(img, (0, 0), img.convert('RGBA'))
                    img = background
                else:
                    img = img.convert('RGB')

                # --- 缩放与保存 ---
                img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
                save_path = os.path.join(folder_path, 'cover_thumb.jpg')
                img.save(save_path, "JPEG", quality=85, optimize=True)
                print(f"已修复并生成: {folder}/cover_thumb.jpg")

        except Exception as e:
            print(f"处理 {folder} 失败: {e}")


if __name__ == '__main__':
    create_thumbnails()