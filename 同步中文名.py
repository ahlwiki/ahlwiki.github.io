import json
import os
from pathlib import Path

# 配置路径
LIST_JSON_PATH = "kmf_list_3.json"
INDIVIDUAL_DIR = "kmf_individual_files"

def load_kmf_list():
    """加载 kmf_list_3.json"""
    with open(LIST_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_kmf_list(data):
    """保存 kmf_list_3.json"""
    with open(LIST_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def build_english_to_chinese_map():
    """遍历 kmf_individual_files/*.json，提取 {english_name: chinese_name} 映射"""
    mapping = {}
    individual_path = Path(INDIVIDUAL_DIR)
    if not individual_path.exists():
        print(f"警告: 目录 {INDIVIDUAL_DIR} 不存在，请检查路径。")
        return mapping

    json_files = list(individual_path.glob("*.json"))
    print(f"找到 {len(json_files)} 个机体详情文件")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            english_name = data.get("english_name")
            chinese_name = data.get("name")
            if english_name and chinese_name:
                mapping[english_name] = chinese_name
                print(f"✓ {english_name} -> {chinese_name}")
            else:
                print(f"⚠ {json_file.name} 缺少 english_name 或 name 字段，跳过")
        except Exception as e:
            print(f"✗ 读取 {json_file.name} 失败: {e}")
    return mapping

def main():
    # 获取映射
    mapping = build_english_to_chinese_map()
    if not mapping:
        print("没有可用的映射数据，退出。")
        return

    # 加载列表
    kmf_list = load_kmf_list()

    # 更新中文名
    updated_count = 0
    for item in kmf_list:
        eng_name = item.get("name")  # 列表中的英文名
        if eng_name in mapping:
            old_chinese = item.get("chinese_name", "")
            new_chinese = mapping[eng_name]
            if old_chinese != new_chinese:
                item["chinese_name"] = new_chinese
                updated_count += 1
                print(f"更新: {eng_name} 中文名 \"{old_chinese}\" -> \"{new_chinese}\"")
            else:
                print(f"未变更: {eng_name} 中文名已一致 \"{new_chinese}\"")
        else:
            # 可选：打印未找到的英文名
            print(f"未找到: {eng_name} 在详情文件夹中没有对应 JSON")

    # 保存
    if updated_count > 0:
        save_kmf_list(kmf_list)
        print(f"\n✅ 同步完成！共更新 {updated_count} 条机体的中文名。")
    else:
        print("\n✅ 未发现需要更新的中文名。")

if __name__ == "__main__":
    main()