import json
import re
from collections import defaultdict

# 规范化映射表：将具体剧集/变体名映射到主系列名
NORMALIZE_MAP = {
    # Code Geass: Lelouch of the Rebellion 相关
    "Guren Dances": "Code Geass: Lelouch of the Rebellion",
    "Knight": "Code Geass: Lelouch of the Rebellion",
    "The White Knight Awakens (First) Re; (Last)": "Code Geass: Lelouch of the Rebellion",
    "The Princess and the Witch": "Code Geass: Lelouch of the Rebellion",
    "Refrain (first) Love Attack! (last)": "Code Geass: Lelouch of the Rebellion",
    "The Brightness Falls (First) To Beloved Ones (Last)": "Code Geass: Lelouch of the Rebellion",
    "Memories of Hatred (First) To Beloved Ones (Last)": "Code Geass: Lelouch of the Rebellion",
    "The Abandoned Mask (First) The Grip of Damocles (Final)": "Code Geass: Lelouch of the Rebellion",
    "Shirley at Gunpoint (First) Imprisoned in Campus (Last)": "Code Geass: Lelouch of the Rebellion",
    "The Black Knights (first) The Collapsing Stage (last)": "Code Geass: Lelouch of the Rebellion",
    "Plan For Independent Japan (First) Geass Hunt (Last)": "Code Geass: Lelouch of the Rebellion",
    "First: The Collapsing Stage Last: Geass Hunt": "Code Geass: Lelouch of the Rebellion",
    "United Federation of Nations Resolution Number One (first) - Emperor Lelouch (last)": "Code Geass: Lelouch of the Rebellion",
    "Declaration at the School Festival (first) One Million Miracles (last)": "Code Geass: Lelouch of the Rebellion",
    "Operation Pacific Ocean Ambush (first) Final Battle Tokyo II (last)": "Code Geass: Lelouch of the Rebellion",
    "A Bride in the Vermilion Forbidden City The Grip of Damocles": "Code Geass: Lelouch of the Rebellion",
    "Battle for Kyushu - Betrayal": "Code Geass: Lelouch of the Rebellion",
    "Emperor Lelouch - Re;": "Code Geass: Lelouch of the Rebellion",
    "Knights of the Round Emperor Lelouch": "Code Geass: Lelouch of the Rebellion",
    # Code Geass: Akito the Exiled 相关
    "The Wyvern Arrives (episode)": "Code Geass: Akito the Exiled",
    "The Wyvern Divided (first) To Beloved Ones (last)": "Code Geass: Akito the Exiled",
    # 其他可继续补充
}


def normalize_category_value(value):
    """
    对分类值进行规范化。
    - 如果值在映射表中，返回映射后的主系列名。
    - 否则尝试提取主系列名（如 "Code Geass: Lelouch of the Rebellion (Game)" -> "Code Geass: Lelouch of the Rebellion"）。
    - 原样返回（去除首尾空格）。
    """
    if not value:
        return None
    value = value.strip()
    # 直接映射
    if value in NORMALIZE_MAP:
        return NORMALIZE_MAP[value]

    # 提取 "Code Geass: XXX" 主系列名（忽略括号或短横后的内容）
    match = re.match(r'(Code Geass: [^\(\)]+(?: [^\(\)]+)*)', value)
    if match:
        main = match.group(1).strip()
        if main and main != "Code Geass:":
            return main

    # 处理包含 " - " 的情况，取前半部分
    if " - " in value and value.startswith("Code Geass:"):
        main = value.split(" - ")[0].strip()
        if main and main != "Code Geass:":
            return main

    return value


def extract_categories_from_specs(specs):
    """
    从 specs 字典中提取分类字段（Anime, Game, Manga, Manufacturer, Operators 等）。
    返回 {"Anime": ["规范后的值列表"], "Game": [...], ...}
    """
    categories = {}
    # 需要提取的字段列表（键名可能有所不同，但目标字段都大写开头）
    target_fields = ["Anime", "Game", "Manga", "Manufacturer", "Operators"]
    for field in target_fields:
        raw = specs.get(field)
        if raw is None:
            continue
        # 处理字符串（可能是多行或带分隔符）
        if isinstance(raw, str):
            # 按换行或逗号分割（若有多个值）
            parts = [p.strip() for p in re.split(r'[\n,]+', raw) if p.strip()]
        else:
            parts = [str(raw).strip()]
        # 规范化每个部分
        normalized = []
        for part in parts:
            norm = normalize_category_value(part)
            if norm and norm not in normalized:
                normalized.append(norm)
        if normalized:
            categories[field] = normalized
    return categories


def main():
    print("正在加载 kmf_details_full.json ...")
    with open('kmf_details_full_199.json', 'r', encoding='utf-8') as f:
        details = json.load(f)

    # 构建英文名到分类字典
    name_to_categories = {}
    for entry in details:
        eng_name = entry.get('name')  # 注意：文件中用的是 "name"，实际是英文名
        if not eng_name:
            print(f"警告：条目缺少 name 字段，跳过")
            continue
        specs = entry.get('specs', {})
        categories = extract_categories_from_specs(specs)
        if categories:
            name_to_categories[eng_name] = categories
            print(f"提取: {eng_name} -> {list(categories.keys())}")
        else:
            # 有的机体可能没有任何分类字段，也记录空字典
            name_to_categories[eng_name] = {}

    print(f"\n共处理 {len(name_to_categories)} 台机体的分类信息。")

    # 加载 kmf_list_3.json
    print("正在加载 kmf_list_3.json ...")
    with open('kmf_list_3.json', 'r', encoding='utf-8') as f:
        kmf_list = json.load(f)

    # 更新
    updated = 0
    for item in kmf_list:
        eng_name = item.get('name')
        if eng_name in name_to_categories:
            item['categories'] = name_to_categories[eng_name]
            updated += 1
            print(f"更新: {eng_name} 已添加分类 {list(name_to_categories[eng_name].keys())}")
        else:
            # 确保有 categories 字段（可能为空）
            if 'categories' not in item:
                item['categories'] = {}

    # 保存
    print(f"\n保存 kmf_list_3.json (更新了 {updated} 条) ...")
    with open('kmf_list_3.json', 'w', encoding='utf-8') as f:
        json.dump(kmf_list, f, ensure_ascii=False, indent=4)

    print("✅ 完成！分类信息已合并至 kmf_list_3.json")


if __name__ == "__main__":
    main()