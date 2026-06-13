import json
from pathlib import Path

# ===================== 配置区 =====================
TARGET_DIR = Path(__file__).parent / "kmf_individual_files"  # JSON 文件夹路径
FIND_TEXT = "公吨"  # 要查找的文本
REPLACE_TEXT = "吨"  # 替换后的文本


# =================================================

def replace_in_value(obj, find_str, replace_str):
    """
    递归替换所有字符串值中的指定文本。
    返回 (修改后的对象, 是否进行了任何修改)
    """
    modified = False

    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            new_key, key_modified = replace_in_value(key, find_str, replace_str) if isinstance(key, str) else (key,
                                                                                                               False)
            new_value, val_modified = replace_in_value(value, find_str, replace_str)
            new_dict[new_key] = new_value
            if key_modified or val_modified:
                modified = True
        return new_dict, modified

    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            new_item, item_modified = replace_in_value(item, find_str, replace_str)
            new_list.append(new_item)
            if item_modified:
                modified = True
        return new_list, modified

    elif isinstance(obj, str):
        if find_str in obj:
            return obj.replace(find_str, replace_str), True
        else:
            return obj, False

    else:
        # 数字、布尔、None 等不可替换的类型
        return obj, False


def process_file(file_path, find_str, replace_str):
    """处理单个 JSON 文件，返回是否进行了修改"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取失败 {file_path.name}: {e}")
        return False

    new_data, modified = replace_in_value(data, find_str, replace_str)

    if not modified:
        return False

    # 只有真正修改时才写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    return True


def main():
    if not TARGET_DIR.exists():
        print(f"错误：目录 {TARGET_DIR} 不存在")
        return

    json_files = list(TARGET_DIR.glob("*.json"))
    if not json_files:
        print(f"在 {TARGET_DIR} 中没有找到 JSON 文件")
        return

    modified_count = 0
    for json_file in sorted(json_files):
        if process_file(json_file, FIND_TEXT, REPLACE_TEXT):
            print(f"✅ 已替换 {json_file.name}")
            modified_count += 1
        else:
            # 不显示未修改的文件，避免刷屏；如需显示可取消注释
            # print(f"⏺ 无变化: {json_file.name}")
            pass

    print(f"\n处理完成，共修改 {modified_count} 个文件")


if __name__ == "__main__":
    main()