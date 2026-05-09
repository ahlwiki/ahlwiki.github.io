import json
import os
import csv
from pathlib import Path

def collect_all_specs_fields(json_dir):
    """遍历所有 JSON 文件，收集 specs 中所有字段名的并集"""
    field_set = set()
    json_files = Path(json_dir).glob("*.json")
    for json_path in json_files:
        try:
            with open(json_path, 'r', encoding='utf-8-sig') as f:  # 自动处理 BOM
                data = json.load(f)
                specs = data.get("specs", {})
                field_set.update(specs.keys())
        except Exception as e:
            print(f"读取 {json_path.name} 失败: {e}")
    return sorted(field_set)

def export_to_csv(json_dir, csv_output):
    all_fields = collect_all_specs_fields(json_dir)
    if not all_fields:
        print("未找到任何 specs 字段，退出。")
        return

    print(f"共发现 {len(all_fields)} 个字段: {all_fields}")

    # 准备写入 CSV（带 BOM 以便 Excel 正确识别中文）
    with open(csv_output, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        # 表头：第一列是文件名，后面是所有字段
        writer.writerow(['filename'] + all_fields)

        json_files = Path(json_dir).glob("*.json")
        for json_path in json_files:
            row = [json_path.stem]  # 不含扩展名的文件名
            try:
                with open(json_path, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    specs = data.get("specs", {})
                    # 按照 all_fields 顺序取值，缺失时留空字符串
                    for field in all_fields:
                        value = specs.get(field, "")
                        # 处理值可能包含换行符或特殊字符，直接写入
                        row.append(value)
                writer.writerow(row)
                print(f"已处理: {json_path.name}")
            except Exception as e:
                print(f"处理 {json_path.name} 时出错: {e}")
                # 写入空行占位
                writer.writerow([json_path.stem] + [''] * len(all_fields))

    print(f"\n导出完成，文件保存为: {csv_output}")

if __name__ == "__main__":
    # 配置路径
    JSON_DIR = "kmf_individual_files"   # JSON 文件所在目录
    CSV_FILE = "specs_data.csv"         # 输出的 CSV 文件名

    export_to_csv(JSON_DIR, CSV_FILE)