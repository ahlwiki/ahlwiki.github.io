import json
import csv
from pathlib import Path

def import_from_csv(json_dir, csv_input, dry_run=False):
    """
    从 CSV 文件读取数据，更新对应 JSON 文件中的 specs 字段。
    若 CSV 中某字段值为空字符串，则从 specs 中移除该字段（不写入）。
    """
    updates = {}
    with open(csv_input, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if 'filename' not in reader.fieldnames:
            print("CSV 文件缺少 'filename' 列，请确认格式。")
            return
        fieldnames = [col for col in reader.fieldnames if col != 'filename']
        for row in reader:
            filename = row['filename']
            specs = {}
            for field in fieldnames:
                value = row.get(field, "").strip()
                if value != "":      # 仅当值非空时才加入
                    specs[field] = value
            updates[filename] = specs

    if not updates:
        print("CSV 中没有有效数据（全为空），退出。")
        return

    for filename, new_specs in updates.items():
        json_path = Path(json_dir) / f"{filename}.json"
        if not json_path.exists():
            print(f"警告: {json_path} 不存在，已跳过")
            continue

        try:
            with open(json_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取 {json_path.name} 失败: {e}")
            continue

        # 完全替换 specs 字段（只包含 CSV 中非空的字段）
        data["specs"] = new_specs

        if dry_run:
            print(f"[DRY RUN] 将更新 {json_path.name} 的 specs 为: {new_specs}")
        else:
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"已更新: {json_path.name}")
            except Exception as e:
                print(f"写入 {json_path.name} 失败: {e}")

    if dry_run:
        print("\n这是试运行模式，未实际修改任何文件。设置 dry_run=False 以正式导入。")

if __name__ == "__main__":
    JSON_DIR = "kmf_individual_files"
    CSV_FILE = "specs_data.csv"
    # 正式运行时将 dry_run 改为 False
    import_from_csv(JSON_DIR, CSV_FILE, dry_run=False)