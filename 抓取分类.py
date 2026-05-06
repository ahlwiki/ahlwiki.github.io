import requests
import time
import re
from collections import defaultdict
from bs4 import BeautifulSoup

WIKI_API = "https://codegeass.fandom.com/api.php"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def get_category_members(category_name, continue_token=None):
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'categorymembers',
        'cmtitle': f'Category:{category_name}',
        'cmtype': 'page',
        'cmlimit': 500,
        'formatversion': 2
    }
    if continue_token:
        params['cmcontinue'] = continue_token
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

def get_page_html(page_title):
    params = {
        'action': 'parse',
        'format': 'json',
        'page': page_title,
        'prop': 'text',
        'formatversion': 2
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()['parse']['text']

def extract_realworld_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    seen_labels = set()

    # 1. 扫描所有 portable infobox
    for infobox in soup.find_all('aside', class_='portable-infobox'):
        for row in infobox.find_all('div', class_='pi-data'):
            label_tag = row.find('h3', class_='pi-data-label')
            value_tag = row.find('div', class_='pi-data-value')
            if label_tag and value_tag:
                label = label_tag.get_text(strip=True)
                value = value_tag.get_text(separator=' ', strip=True)
                if label not in seen_labels:
                    info[label] = value
                    seen_labels.add(label)

    # 2. 扫描所有 wikitable，寻找可能包含现实信息的行
    for table in soup.find_all('table', class_='wikitable'):
        rows = table.find_all('tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                label = th.get_text(strip=True)
                value = td.get_text(separator=' ', strip=True)
                # 只保留看起来像现实分类的字段
                if any(keyword in label for keyword in ['Anime', 'Manga', 'Game', 'Designer', 'Novel', 'Appear']):
                    if label not in seen_labels:
                        info[label] = value
                        seen_labels.add(label)

    return info

def main():
    print("\n=== KMF 现实世界信息统计（通用版）===\n")
    # 获取列表
    pages = []
    cont = None
    while True:
        data = get_category_members("Knightmare_Frames", cont)
        pages.extend(data['query']['categorymembers'])
        if 'continue' in data and 'cmcontinue' in data['continue']:
            cont = data['continue']['cmcontinue']
            time.sleep(1)
        else:
            break

    total = len(pages)
    print(f"✅ 共发现 {total} 台机体，开始解析...")

    category_stats = defaultdict(set)
    value_counter = defaultdict(int)

    for idx, page in enumerate(pages, 1):
        title = page['title']
        print(f"  [{idx}/{total}] {title}")
        try:
            html = get_page_html(title)
            info = extract_realworld_info(html)
            if not info:
                print(f"    ⚠️ 未找到有效信息")
                continue
            for label, val in info.items():
                # 标准化标签
                label_norm = label.strip()
                category_stats[label_norm].add(val)
                value_counter[(label_norm, val)] += 1
        except Exception as e:
            print(f"    ❌ 错误: {e}")
        time.sleep(0.5)

    # 生成报告
    report = []
    report.append("=" * 70)
    report.append(f"KMF 现实世界信息统计报告 (共 {total} 台机体)")
    report.append("=" * 70)
    for label in sorted(category_stats.keys()):
        report.append(f"\n【{label}】")
        values = sorted(category_stats[label])
        report.append(f"  共 {len(values)} 项：")
        for val in values:
            count = value_counter[(label, val)]
            report.append(f"    - {val} (出现 {count} 次)")

    output_path = "kmf_realworld_stats.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n✨ 完成！报告已保存到 {output_path}")

if __name__ == "__main__":
    main()