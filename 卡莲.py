import json
import re
from pathlib import Path

# ===================== 配置 =====================
TARGET_DIR = Path(__file__).parent / "kmf_individual_files"
SEARCH_TEXT = "卡莲"
# ===============================================

def find_key_line(file_path, key_name):
    """返回文件中所有指定键名所在的行号（基于文本扫描）"""
    lines_with_key = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # 匹配 "key_name":
            if re.search(rf'"{key_name}"\s*:', line):
                lines_with_key.append(line_num)
    return lines_with_key

def collect_all_fields(obj, current_path=""):
    """
    递归收集所有字段的 (路径, 键名, 值) 列表
    路径格式如 "specs.Known Pilots" 或 "Known Pilots"
    """
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{current_path}.{k}" if current_path else k
            results.append((new_path, k, v))
            # 递归进入嵌套结构
            if isinstance(v, (dict, list)):
                results.extend(collect_all_fields(v, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{current_path}[{i}]"
            if isinstance(item, (dict, list)):
                results.extend(collect_all_fields(item, new_path))
    return results

def contains_search_text(value, text):
    """检查值（字符串或列表）中是否包含目标文本"""
    if isinstance(value, str):
        return text in value
    elif isinstance(value, list):
        return any(text in str(item) for item in value)
    return False

def main():
    if not TARGET_DIR.exists():
        print(f"错误：目录 {TARGET_DIR} 不存在")
        return

    json_files = list(TARGET_DIR.glob("*.json"))
    if not json_files:
        print(f"在 {TARGET_DIR} 中没有找到 JSON 文件")
        return

    found_any = False
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 解析失败 {json_file.name}: {e}")
            continue

        # 1. 获取所有字段的路径、键名、值
        all_fields = collect_all_fields(data)

        # 2. 过滤：路径中不包含 'specs' 段，且值包含目标文本
        candidates = []
        for path, key, val in all_fields:
            # 排除 specs 下的所有字段（路径以 specs. 开头或包含 .specs.）
            path_segments = path.split('.')
            if 'specs' in path_segments:
                continue
            if contains_search_text(val, SEARCH_TEXT):
                candidates.append((path, key, val))

        if not candidates:
            continue

        # 3. 获取文件中所有键的行号（用于定位，每个键可能有多行，简单取第一个匹配）
        # 注意：如果同一个键名出现多次（不同路径），会共享同一行号列表，我们基于键名+路径简单处理：
        # 先获取所有键的行号映射 {键名: [行号列表]}，然后按候选顺序尝试取第一个可用的行号。
        key_to_lines = {}
        with open(json_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                m = re.search(r'"([^"]+)"\s*:', line)
                if m:
                    key_name = m.group(1)
                    key_to_lines.setdefault(key_name, []).append(line_num)

        # 输出每个候选
        for path, key, val in candidates:
            # 获取该键名的第一个行号（假设键名在同一文件内唯一，若不唯一则取第一个）
            line_numbers = key_to_lines.get(key, [])
            line_num = line_numbers[0] if line_numbers else "?"
            # 截断过长的值显示
            val_str = str(val)
            if len(val_str) > 50:
                val_str = val_str[:50] + "..."
            print(f"{json_file.name}:{line_num}  (路径: {path}) 值: {val_str}")
            found_any = True

    if not found_any:
        print(f"未在任何非 specs 字段中找到包含 '{SEARCH_TEXT}' 的内容")

if __name__ == "__main__":
    main()