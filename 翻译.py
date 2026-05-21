import json
import os
import time
from openai import OpenAI

# ==================== 配置区域 ====================
DEEPSEEK_API_KEY = "sk-5f561417d0744700904358b6244d7288"  # 替换为你的真实 API Key
RAW_DATA_FILE = "kmf_details_full_10.json"  # 待翻译的10台机甲文件
MY_KMF_FILE = "kmf_list_3.json"  # 机甲名字典真理库
GLOSSARY_FILE = "final_chinese_glossary.json"  # 先前生成的术语/组织字典（若有则加载，若无不影响）
OUTPUT_FILE = "kmf_details_translated_10.json"  # 最终输出的中文文件
# ==================================================

# 清空系统代理，确保国内直连 DeepSeek API 稳定
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)


def build_flatten_dictionary():
    """融合成全量扁平中英文对照字典"""
    flatten_dict = {}

    # 1. 优先载入 kmf_list_3.json
    if os.path.exists(MY_KMF_FILE):
        with open(MY_KMF_FILE, 'r', encoding='utf-8') as f:
            my_kmf_data = json.load(f)
        if isinstance(my_kmf_data, list):
            for item in my_kmf_data:
                eng = item.get("name")
                zh = item.get("chinese_name")
                if eng and zh:
                    flatten_dict[eng.strip()] = zh.strip()
        print(f"成功从 kmf_list_3.json 加载了 {len(flatten_dict)} 个机甲命名真理词条。")

    # 2. 补入术语、组织、地名、人名等 final_chinese_glossary.json
    if os.path.exists(GLOSSARY_FILE):
        with open(GLOSSARY_FILE, 'r', encoding='utf-8') as f:
            ai_glossary = json.load(f)
        for category, items in ai_glossary.items():
            if category == "mecha_names":
                continue  # 机甲名以上面的真实人工数据为最高准则
            if isinstance(items, list):
                for item in items:
                    main_en = item.get("main_en")
                    zh_trans = item.get("zh_translation")
                    if main_en and zh_trans:
                        flatten_dict[main_en.strip()] = zh_trans.strip()
                    if "aliases" in item and isinstance(item["aliases"], list):
                        for alias in item["aliases"]:
                            if zh_trans: flatten_dict[alias.strip()] = zh_trans.strip()
        print(f"追加通用术语字典完成，当前全量绑定词条共：{len(flatten_dict)} 个。")

    return flatten_dict


def translate_single_kmf(kmf_data, glossary):
    """将单台机甲的数据发送给 DeepSeek 进行翻译"""
    kmf_str_dump = json.dumps(kmf_data, ensure_ascii=False)

    # 动态匹配当前机甲文本包含的本地规则，精简 Prompt
    local_rules = {}
    for eng_word, zh_word in glossary.items():
        if eng_word in kmf_str_dump:
            local_rules[eng_word] = zh_word

    dict_rules_str = ""
    for eng, zh in local_rules.items():
        dict_rules_str += f"- {eng} -> {zh}\n"

    system_prompt = f"""
你是一个精通日本动漫《叛逆的鲁鲁修》（Code Geass）的专业翻译官和机甲设定集主编。
现在你需要把我提供给你的某一台 Knightmare Frame（机甲）的英文详细 JSON 数据翻译成高水平的中文 JSON。

【必须严格遵守的翻译真理字典】：
在翻译这台机甲的数据时，如果遇到以下英文词汇，你【必须】毫无条件地采用指定的中文，绝对不允许自行发明或前后不一致：
{dict_rules_str if dict_rules_str else "- 暂无特定术语绑定"}

【数据及单位翻译红线（参考 Agravain.json 标准）】：
1. 顶层结构中，英文原数据的 "name" 字段对应的 Value 必须翻译为中文（优先采用上方字典中提供的名称）。
2. 在 "specs" 字典中：
   - "Overall Height"（全高）的 Value 必须转换为以“米”为单位（例如: "4.44 meters" -> "4.44 米"）。
   - "Gross Weight"（全备重量）的 Value 必须转换为以“吨”为单位（例如: "7.01 metric tonnes" -> "7.01 吨"）。
3. 后缀型号严格规范：Type-Hei -> 丙型/丙式；Kai -> 改；Mass-Production Model -> 量产型；Commander Model -> 指挥官型；Standard -> 标准型；Normal form -> 普通形态；Close Combat Mode -> 近战模式。

【翻译原则】：
1. 保持原 JSON 的所有【键名（Key）】（如 "name", "specs", "introduction", "Design and Development" 等）完全不变，只翻译【键值（Value）】里的英文文本。
2. 翻译风格要求充满科幻、机甲感，用词热血、严谨（例如：Yggdrasil Drive 翻为 "尤克特拉希尔驱动"、Energy Filler 翻为 "能量填充器"、Factsphere Sensors 翻为 "事实球感应器/红外感应器"）。
3. 必须直接返回一个合法的 JSON 字符串，不要包含任何 Markdown 格式包裹（如 ```json）。
"""

    for retry in range(3):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请翻译以下这台机甲的数据：\n{kmf_str_dump}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=120
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"    [重试提示] 翻译失败: {e}，正在进行第 {retry + 1} 次重试...")
            time.sleep(3)
    return None


def main():
    print("1. 正在构建中英文真理映射字典...")
    master_glossary = build_flatten_dictionary()

    if not os.path.exists(RAW_DATA_FILE):
        print(f"错误：未找到输入文件 {RAW_DATA_FILE}")
        return

    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        raw_list = json.load(f)

    print(f"2. 成功加载原始数据，共检测到 {len(raw_list)} 台机甲。开始逐台进行翻译...")

    translated_output = []

    for idx, kmf_data in enumerate(raw_list):
        eng_name = kmf_data.get("name", f"Index_{idx}")
        print(f"   正在翻译 [{idx + 1}/{len(raw_list)}] -> {eng_name}...", end="", flush=True)

        # 执行翻译
        translated_data = translate_single_kmf(kmf_data, master_glossary)

        if translated_data:
            translated_output.append(translated_data)
            print("【成功】")
        else:
            print("【失败，保留原英文】")
            translated_output.append(kmf_data)

        time.sleep(0.5)

    # 最终保存文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(translated_output, f, ensure_ascii=False, indent=2)

    print(f"\n=================== 翻译任务圆满完成 ===================")
    print(f"翻译结果已完美对齐规范，保存在: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()