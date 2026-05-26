import os
from pathlib import Path

# ===================== 在这里修改搜索词 =====================
SEARCH_TERM = "中华"  # 将这里改成你想要搜索的文本


# ===========================================================

def search_text_in_json_files(folder_path: str, search_text: str):
    """
    在指定文件夹的所有 JSON 文件中搜索指定文本，输出文件名和行号。
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return

    json_files = list(folder.glob("*.json"))
    if not json_files:
        print(f"在 '{folder_path}' 中没有找到 JSON 文件")
        return

    found = False
    for json_file in sorted(json_files):
        with open(json_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        matches = []
        for line_num, line in enumerate(lines, start=1):
            if search_text in line:
                matches.append(line_num)

        if matches:
            found = True
            for line_num in matches:
                print(f"{json_file.name}:{line_num}")

    if not found:
        print(f"未在任何 JSON 文件中找到文本: '{search_text}'")


if __name__ == "__main__":
    # 脚本所在目录下的 kmf_individual_files 文件夹
    target_dir = Path(__file__).parent / "kmf_individual_files"
    search_text_in_json_files(target_dir, SEARCH_TERM)