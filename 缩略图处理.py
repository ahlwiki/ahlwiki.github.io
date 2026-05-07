import os
from PIL import Image

def process_cover_images(root_dir="images/kmf_gallery"):
    """
    遍历 root_dir 下的所有子文件夹，处理 cover_thumb.jpg
    """
    if not os.path.isdir(root_dir):
        print(f"目录不存在: {root_dir}")
        return

    target_w, target_h = 120, 170
    target_ratio = target_w / target_h   # 0.70588...

    # 遍历每个机体文件夹
    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        img_path = os.path.join(folder_path, "cover_thumb.jpg")
        if not os.path.isfile(img_path):
            print(f"跳过 {folder_name}: 找不到 cover_thumb.jpg")
            continue

        try:
            with Image.open(img_path) as img:
                # 确保图片模式为 RGB (JPEG 需要)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                w, h = img.size
                ratio = w / h

                # 仅当宽高比小于目标比例时处理 (图片过于瘦高)
                if ratio < target_ratio:
                    print(f"处理: {folder_name}/cover_thumb.jpg ({w}x{h})")

                    # 高度缩放到 170，宽度等比例缩放
                    new_h = target_h
                    new_w = int(w * new_h / h)

                    # 高质量缩放图片
                    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

                    # 创建白色画布
                    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))

                    # 计算居中偏移 (y 方向刚好是 0)
                    x_offset = (target_w - new_w) // 2
                    y_offset = (target_h - new_h) // 2   # 始终为0

                    canvas.paste(img_resized, (x_offset, y_offset))

                    # 覆盖保存原文件
                    canvas.save(img_path, "JPEG", quality=95)
                    print(f"  已替换为新图片 (120x170)，缩放后尺寸 {new_w}x{new_h}，居中偏移 x={x_offset}")
                else:
                    print(f"跳过 {folder_name}: 宽高比 {ratio:.3f} >= {target_ratio:.3f}，无需处理")

        except Exception as e:
            print(f"处理 {folder_name} 时出错: {e}")

if __name__ == "__main__":
    process_cover_images()