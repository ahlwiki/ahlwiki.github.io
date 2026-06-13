import os
import json
from openai import OpenAI

# ================= 配置区域 =================
DEEPSEEK_API_KEY = "sk-5ab7e810af30460e9934defb2450e48b"
FOLDER_PATH = "kmf_individual_files"   # JSON 文件所在文件夹
OUTPUT_DIR = "review_reports"          # 输出报告的文件夹
MODEL_NAME = "deepseek-chat"

# ---------- 名词对应表（按类别分组，支持模糊匹配）----------
TERMINOLOGY_MAP = {
    # === 技术类名词（系统/武器/部件）===
    # === "尤克特拉希尔驱动": "尤克特拉希尔驱动 (Yggdrasil Drive)",===
    # === "能量填充器": "能量填充器 (Energy Filler)",===
    "人型自在战斗装甲": "KMF",
    "Knightmare Frame": "KMF",
    "闪光护盾系统": "卢米纳斯护盾 (Blaze Luminous)",
    "闪光护盾": "卢米纳斯护盾 (Blaze Luminous)",
    "事实球面传感器": "事实球面传感器 (Factsphere Sensor)",
    "陆地旋轮推进系统": "陆地旋轮 (Landspinner)",
    "陆地旋轮": "陆地旋轮 (Landspinner)",
    "MVS": "MVS（Maser Vibration Sword，微波振动剑）",
    "激光波动剑": "MVS（Maser Vibration Sword，微波振动剑）",
    "悬浮系统": "悬浮系统（Float System）",
    "驾驶舱弹射系统": "驾驶舱弹射系统",
    "悬浮背包": "浮空单元（Float Unit）",
    "沙板": "沙地悬浮面板（砂パネル）",

    # === 世代/型号 ===
    "第3世代": "第三世代",
    "第4世代": "第四世代",
    "第5世代": "第五世代",
    "第6世代": "第六世代",
    "第7世代": "第七世代",
    "第8世代": "第八世代",
    "第9世代": "第九世代",
    "第10世代": "第十世代",
}
TERMINOLOGY_STR = "\n".join([f"  - {k} → {v}" for k, v in TERMINOLOGY_MAP.items()])
# =================================================

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def load_json_files(folder):
    json_files = []
    if not os.path.exists(folder):
        print(f"错误：文件夹不存在 - {folder}")
        return json_files
    for filename in os.listdir(folder):
        if filename.lower().endswith(".json"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    json_files.append((filename, data))
                except json.JSONDecodeError as e:
                    print(f"[跳过] {filename} JSON 解析失败: {e}")
    return json_files

def remove_specifications_field(data):
    data_copy = json.loads(json.dumps(data))
    keys_to_delete = []
    for key in data_copy:
        if key == "Specifications":
            keys_to_delete.append(key)
        elif isinstance(data_copy[key], dict):
            data_copy[key] = remove_specifications_field(data_copy[key])
    for key in keys_to_delete:
        del data_copy[key]
    return data_copy

def build_prompt(filename, data):
    clean_data = remove_specifications_field(data)
    json_str = json.dumps(clean_data, ensure_ascii=False, indent=2)
    prompt = f"""
你是一位精通《叛逆的鲁鲁修》系列剧情、机体设定（Knightmare Frame）的专家。请审核以下 JSON 文件（文件名：{filename}）的内容，重点关注：

1. **剧情设定一致性**：机体的名称、开发者、使用者、背景介绍、武装等是否符合原作设定？是否存在与已知剧情矛盾的地方？
2. **语义通顺性**：文本是否存在明显的翻译错误、语法不通、用词不当或逻辑混乱。
3. **术语一致性（模糊匹配）**：参考下方的【标准名词对应表】。对 JSON 中的术语进行**模糊匹配**（近义词、拼写变体、不同译名、简称等），指出不一致并建议修改为标准术语。

### 标准名词对应表
{TERMINOLOGY_STR}

**注意**：`Specifications` 字段已自动跳过。

请按以下格式输出审核意见：

### 文件：{filename}
#### 问题列表
- [字段名] 问题描述 → 修改建议

如果没有任何问题，输出：✅ 无问题。

以下是待审核的 JSON 内容：

{json_str}
"""
    return prompt

def review_with_deepseek(prompt):
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个严谨的动漫设定审核助手，只输出客观的审核意见，不添加无关内容。必须进行模糊匹配术语。输出语言为中文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[API 调用失败] {str(e)}"

def write_report(filename, review_result):
    base_name = os.path.splitext(filename)[0]
    report_path = os.path.join(OUTPUT_DIR, f"{base_name}_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 审核报告：{filename}\n\n")
        f.write(review_result)
    return report_path

def main():
    ensure_output_dir()
    json_files = load_json_files(FOLDER_PATH)
    if not json_files:
        print("未找到任何 JSON 文件，程序退出。")
        return

    print(f"共发现 {len(json_files)} 个 JSON 文件，开始审核...")
    for filename, data in json_files:
        print(f"正在审核: {filename}")
        prompt = build_prompt(filename, data)
        review_result = review_with_deepseek(prompt)
        report_path = write_report(filename, review_result)
        print(f"已生成报告: {report_path}")

    print(f"\n所有报告已保存至 {OUTPUT_DIR} 文件夹")

if __name__ == "__main__":
    main()