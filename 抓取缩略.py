import os
import time
import cloudscraper
from bs4 import BeautifulSoup

# ================= 配置区 =================
BASE_URL = "https://codegeass.fandom.com/wiki/Category:Knightmare_Frames"
SAVE_DIR = r"E:\GeassWikiProject\网站\images\kmf_gallery"

# 代理设置（确认迷雾通 9910 开启）
PROXIES = {
    'http': 'http://127.0.0.1:9910',
    'https': 'http://127.0.0.1:9910',
}


# ==========================================

def download_thumbnails():
    print(f"[*] 正在启动 CloudScraper 绕过验证...")

    # 创建 scraper 实例，模拟 Chrome 浏览器
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:
        # 使用 scraper 发起请求
        print(f"[*] 正在访问: {BASE_URL}")
        response = scraper.get(BASE_URL, proxies=PROXIES, timeout=30)
        response.raise_for_status()
        print("[+] 成功绕过 Cloudflare 防护！")
    except Exception as e:
        print(f"[-] 访问受阻: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    members = soup.select(".category-page__member")
    print(f"[*] 发现 {len(members)} 个条目，准备下载...")

    count = 0
    for member in members:
        link_tag = member.select_one(".category-page__member-link")
        img_tag = member.select_one(".category-page__member-thumbnail")

        if not link_tag or not img_tag:
            continue

        raw_name = link_tag.get_text(strip=True)
        safe_name = raw_name.replace(':', '_').replace('/', '_').replace('"', '_').strip()

        img_url = img_tag.get('src')
        if not img_url: continue
        if '/revision' in img_url:
            img_url = img_url.split('/revision')[0]

        target_folder = os.path.join(SAVE_DIR, safe_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        save_path = os.path.join(target_folder, "cover_thumb.jpg")

        if os.path.exists(save_path):
            continue

        try:
            # 下载图片也使用 scraper
            img_res = scraper.get(img_url, proxies=PROXIES, timeout=20)
            if img_res.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(img_res.content)
                count += 1
                print(f"[OK] {count}: {safe_name}")
            else:
                print(f"[FAIL] {safe_name} (HTTP {img_res.status_code})")

            time.sleep(0.5)

        except Exception as e:
            print(f"[ERR] {safe_name} 异常: {e}")

    print(f"\n[!] 抓取结束，本次新增 {count} 张图。")


if __name__ == "__main__":
    download_thumbnails()