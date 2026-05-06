import json
import os
import sys
from pathlib import Path

def load_json(file_path):
    """加载 JSON 文件，若出错则返回 None"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return None

def save_json(data, file_path):
    """保存 JSON 文件（保持中文不转义，缩进为 2）"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main(list_path, details_dir):
    # 1. 加载机体列表
    kmf_list = load_json(list_path)
    if kmf_list is None:
        print("无法加载 kmf_list，脚本退出。")
        sys.exit(1)

    # 建立英文名 -> 条目索引的映射
    index_map = {}
    for idx, entry in enumerate(kmf_list):
        name = entry.get('name')
        if name:
            index_map[name] = idx

    # 2. 遍历详情目录
    details_path = Path(details_dir)
    if not details_path.exists():
        print(f"目录不存在: {details_dir}")
        sys.exit(1)

    updated_count = 0
    for json_file in details_path.glob('*.json'):
        detail = load_json(json_file)
        if not detail:
            continue

        # 获取英文名（优先使用 english_name，其次尝试用 name 字段，最后用文件名）
        eng_name = detail.get('english_name') or detail.get('name')
        if not eng_name:
            # 尝试从文件名获取（去掉 .json）
            eng_name = json_file.stem
            print(f"警告: {json_file.name} 缺少 english_name/name，使用文件名作为标识: {eng_name}")

        if eng_name not in index_map:
            print(f"警告: 未在 kmf_list 中找到匹配的机体: {eng_name}，文件: {json_file.name}")
            continue

        # 获取型号
        specs = detail.get('specs', {})
        model_number = specs.get('Model Number')
        if not model_number:
            print(f"信息: {eng_name} 没有 Model Number 字段，跳过")
            continue

        # 更新列表条目
        entry = kmf_list[index_map[eng_name]]
        entry['model_number'] = model_number
        updated_count += 1
        print(f"已更新: {eng_name} -> {model_number}")

    # 3. 保存修改后的列表
    if updated_count > 0:
        save_json(kmf_list, list_path)
        print(f"\n完成！共更新了 {updated_count} 个机体的型号，已保存至 {list_path}")
    else:
        print("\n未更新任何机体的型号，列表未修改。")

if __name__ == "__main__":
    # 默认路径：脚本所在目录下的 kmf_list_3.json 和 kmf_individual_files 文件夹
    script_dir = Path(__file__).parent
    default_list = script_dir / "kmf_list_3.json"
    default_details_dir = script_dir / "kmf_individual_files"

    # 支持命令行参数：python script.py <list_path> <details_dir>
    list_path = sys.argv[1] if len(sys.argv) > 1 else default_list
    details_dir = sys.argv[2] if len(sys.argv) > 2 else default_details_dir

    main(list_path, details_dir)