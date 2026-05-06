import os
import json
import requests
import re
from time import sleep
from urllib.parse import unquote

# === 配置区 ===
JSON_SOURCE_DIR = 'kmf_individual_files'  # 存放199个JSON详情的目录
SAVE_BASE_DIR = 'images/kmf_gallery'  # 图片存储根目录
PLACEHOLDER_IMAGE = "https://via.placeholder.com/600x400/000000/d4af37?text=NO+IMAGE"

# 模拟浏览器请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def clean_url(url):
    """移除 Fandom 图片 URL 的缩略图后缀，获取原图"""
    if not url: return None
    return url.split('/revision/')[0]


def sanitize_name(name):
    """处理非法文件名字符"""
    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()


def download_image(url, save_path):
    """执行下载动作"""
    if os.path.exists(save_path):
        return True
    try:
        url = clean_url(url)
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  下载失败: {e}")
    return False


def process_kmf_project():
    if not os.path.exists(SAVE_BASE_DIR):
        os.makedirs(SAVE_BASE_DIR)

    files = [f for f in os.listdir(JSON_SOURCE_DIR) if f.endswith('.json')]
    print(f"检测到 {len(files)} 个机体档案，准备开始同步数据...")

    for filename in files:
        file_path = os.path.join(JSON_SOURCE_DIR, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                continue

        eng_name = data.get('english_name', filename.replace('.json', ''))
        folder_name = sanitize_name(eng_name)
        target_folder = os.path.join(SAVE_BASE_DIR, folder_name)

        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        print(f"\n正在处理机体: {eng_name}")

        # --- 核心逻辑：处理带标签的图集 ---
        # 假设你的 JSON 结构中有 gallery 数组: [{"label": "Standard", "url": "..."}, ...]
        gallery = data.get('gallery', [])

        # 如果没有 gallery 数组，则回退到单张 image_url 模式
        if not gallery and data.get('image_url'):
            gallery = [{"label": "Standard", "url": data.get('image_url')}]

        # 记录成功的标签，用于后续前端索引
        successful_variants = []

        for item in gallery:
            label = sanitize_name(item.get('label', 'Standard'))
            image_url = item.get('url')

            if not image_url: continue

            # 决定扩展名
            ext = ".png" if ".png" in image_url.lower() else ".jpg"
            save_filename = f"{label}{ext}"
            save_path = os.path.join(target_folder, save_filename)

            if download_image(image_url, save_path):
                print(f"  [成功] 保存版本: {label}")
                successful_variants.append(label)
                sleep(0.2)  # 稍微停顿，保护 Wiki 服务器
            else:
                print(f"  [失败] 无法下载: {label}")

        # --- 自动同步更新 JSON (可选) ---
        # 为了方便前端调用，可以将下载成功的标签写回 JSON
        data['image_folder'] = folder_name
        data['image_variants'] = successful_variants
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    process_kmf_project()