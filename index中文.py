import json

def main():
    # 读取详情文件，提取英文名->中文名映射
    with open('kmf_details_final.json', 'r', encoding='utf-8') as f:
        details = json.load(f)
    name_map = {item['english_name']: item['name'] for item in details}

    # 读取原始列表文件
    with open('kmf_list_3.json', 'r', encoding='utf-8') as f:
        kmf_list = json.load(f)

    # 更新每个条目：添加中文名，删除 url 字段
    for item in kmf_list:
        eng_name = item['name']
        if eng_name in name_map:
            item['chinese_name'] = name_map[eng_name]
        # 删除 url 字段（如果存在）
        if 'url' in item:
            del item['url']

    # 写回文件（保持原顺序，格式美观）
    with open('kmf_list_3.json', 'w', encoding='utf-8') as f:
        json.dump(kmf_list, f, ensure_ascii=False, indent=4)

    print(f"处理完成！共处理 {len(kmf_list)} 条机体，其中 {len(name_map)} 条已添加中文名。")

if __name__ == '__main__':
    main()