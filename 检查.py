import os
import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI

# ===================== 配置区域 =====================
# 请在这里填写你的 DeepSeek API Key
DEEPSEEK_API_KEY = "sk-2869db41fb084822a939334862b6a3af"

# JSON 文件存放目录（相对于脚本所在目录）
JSON_DIR = "./kmf_individual_files"

# 是否启用 API 审查（若为 False，则只扫描并输出包含"日本"的文本，不调用 API）
ENABLE_API_AUDIT = True
# ===================================================

def setup_client() -> OpenAI:
    """初始化 DeepSeek OpenAI 客户端"""
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "你的 DeepSeek API Key":
        print("❌ 错误：请在脚本中设置 DEEPSEEK_API_KEY")
        exit(1)
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )

def load_json_files(directory: str) -> Dict[str, List[Dict[str, Any]]]:
    """加载目标目录下的所有 JSON 文件，返回文件名到内容的映射"""
    json_files = {}
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        print("   请确保当前工作目录下存在 kmf_individual_files 文件夹，且包含需要审查的 JSON 文件。")
        return json_files

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                json_files[filename] = data
            except json.JSONDecodeError as e:
                print(f"⚠️ 警告: {filename} 解析失败 - {e}")
            except Exception as e:
                print(f"⚠️ 警告: 读取 {filename} 时出错 - {e}")
    return json_files

def extract_japan_mentions(data: Dict[str, Any], file_name: str) -> List[Dict[str, Any]]:
    """递归提取 JSON 中所有包含 '日本' 的文本段，并附带结构路径"""
    hits = []

    def extract_recur(obj, path):
        if isinstance(obj, str):
            if '日本' in obj:
                idx = obj.find('日本')
                start = max(0, idx - 100)
                end = min(len(obj), idx + 100)
                context = obj[start:end].strip()

                hits.append({
                    "file": file_name,
                    "path": " → ".join(map(str, path)),
                    "full_field": obj,
                    "context": context,
                    "hit_index": idx
                })
        elif isinstance(obj, dict):
            for k, v in obj.items():
                extract_recur(v, path + [k])
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_recur(item, path + [i])

    extract_recur(data, [])
    return hits

def build_audit_prompt(hits: List[Dict[str, Any]]) -> str:
    """构建用于内容审查的提示词"""
    prompt = """你是一位网站内容合规审查专家，精通中国《计算机信息网络国际联网安全保护管理办法》等相关法律法规。
你将收到一系列从网站 JSON 数据中提取的文本片段，其中包含“日本”一词。你的任务是：
1. 结合提供的前后上下文，判断该内容是否会因“涉及日本”而被公安联网备案审核判定为违规。
2. 仅根据内容是否违反中国法律法规进行评估，不考虑其他因素。例如：篡改历史、歪曲事实、宣扬军国主义、侮辱性称呼、煽动民族仇恨等属于违规；虚构作品中的客观背景描述则不属于违规。
3. 对每个条目输出：该句的 hash、审核结论（approve 或 reject）、风险等级（high、medium 或 low），以及简短的修改建议（结论为 reject 时必填）。

返回格式为 JSON 数组，每个元素包含以下字段：
[
  {
    "hash": "...",
    "conclusion": "approve 或 reject",
    "risk_level": "high / medium / low",
    "reason": "判断理由，简短说明",
    "suggestion": "如需修改，提供具体修改文案；若无需修改则为空字符串"
  }
]

以下是待审查的内容条目列表（每条包含 hash 和 context）：

"""
    for hit in hits:
        hash_id = f"{hit['file']}_{hash(hit['full_field'])}"
        prompt += f"\n- hash: {hash_id}\n  context: {hit['context']}\n"

    prompt += "\n请输出结果。"
    return prompt

def audit_with_deepseek(client: OpenAI, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """调用 DeepSeek API 审查所有命中内容"""
    if not hits:
        return []

    prompt = build_audit_prompt(hits)

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位内容合规审查专家，只输出 JSON 格式结果，不输出任何额外说明。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        result_text = response.choices[0].message.content

        # 解析 JSON 结果
        result_json = json.loads(result_text)
        if isinstance(result_json, dict) and "results" in result_json:
            return result_json["results"]
        elif isinstance(result_json, list):
            return result_json
        else:
            print("⚠️ 警告: API 返回格式异常")
            print(result_text[:500])
            return []
    except Exception as e:
        print(f"❌ DeepSeek API 调用失败: {e}")
        return []

def generate_report(results: List[Dict[str, Any]], hits: List[Dict[str, Any]]):
    """生成审查报告，按文件分组显示需要修改和无需修改的内容"""
    print("\n" + "=" * 60)
    print("           KMF 图鉴内容合规审查报告 (涉及'日本'文本)")
    print("=" * 60)
    print()

    # 创建 hash 到命中条目的映射
    hash_to_hit = {}
    for hit in hits:
        hash_id = f"{hit['file']}_{hash(hit['full_field'])}"
        hash_to_hit[hash_id] = hit

    # 按文件分组
    need_modify = []
    safe_entries = []

    for result in results:
        hash_id = result.get("hash")
        conclusion = result.get("conclusion", "unknown")
        hit = hash_to_hit.get(hash_id)

        if not hit:
            continue

        entry_info = {
            "file": hit["file"],
            "path": hit["path"],
            "context": hit["context"],
            "full_field": hit["full_field"],
            "conclusion": conclusion,
            "risk_level": result.get("risk_level", ""),
            "reason": result.get("reason", ""),
            "suggestion": result.get("suggestion", "")
        }

        if conclusion == "reject":
            need_modify.append(entry_info)
        else:
            safe_entries.append(entry_info)

    # 输出需要修改的内容
    print(f"⚠️  建议修改的条目 ({len(need_modify)} 条):")
    print("-" * 40)
    for idx, entry in enumerate(need_modify, 1):
        print(f"\n{idx}. 文件: {entry['file']}")
        print(f"   路径: {entry['path']}")
        print(f"   上下文: {entry['context']}")
        print(f"   风险等级: {entry['risk_level']}")
        print(f"   判断理由: {entry['reason']}")
        print(f"   💡 修改建议: {entry['suggestion']}")
        if len(entry['full_field']) > 200:
            print(f"   📄 原文片段: {entry['full_field'][:200]}...")
        else:
            print(f"   📄 原文: {entry['full_field']}")
        print()

    # 输出安全的内容
    print(f"\n✅ 无需修改的条目 ({len(safe_entries)} 条):")
    print("-" * 40)
    for idx, entry in enumerate(safe_entries, 1):
        print(f"\n{idx}. 文件: {entry['file']}")
        print(f"   路径: {entry['path']}")
        print(f"   上下文: {entry['context']}")
        print(f"   判断理由: {entry['reason']}")
        print()

    # 生成修改计划摘要
    if need_modify:
        print("\n" + "=" * 60)
        print("📋 修改计划摘要")
        print("=" * 60)
        modify_plan = {}
        for entry in need_modify:
            file_name = entry['file']
            if file_name not in modify_plan:
                modify_plan[file_name] = []
            modify_plan[file_name].append({
                "path": entry['path'],
                "original": entry['full_field'],
                "suggestion": entry['suggestion']
            })

        for file_name, items in modify_plan.items():
            print(f"\n📁 {file_name}:")
            for item in items:
                print(f"   🔹 路径: {item['path']}")
                print(f"      原文: {item['original'][:150]}...")
                print(f"      建议: {item['suggestion']}")
                print()

    # 统计摘要
    print("\n" + "=" * 60)
    print("📊 审核统计")
    print("=" * 60)
    print(f"   总命中条目: {len(hits)}")
    print(f"   建议修改: {len(need_modify)}")
    print(f"   无需修改: {len(safe_entries)}")
    print(f"   API 缺失结果: {len(hits) - len(results)}")
    print("=" * 60)

def main():
    print(f"🔍 正在扫描目录: {JSON_DIR}")
    json_files = load_json_files(JSON_DIR)
    if not json_files:
        print("❌ 未找到有效的 JSON 文件，程序退出。")
        return

    print(f"✅ 发现 {len(json_files)} 个 JSON 文件，开始提取包含'日本'的内容...")
    all_hits = []
    for file_name, data in json_files.items():
        hits = extract_japan_mentions(data, file_name)
        if hits:
            print(f"  → {file_name}: 发现 {len(hits)} 处包含'日本'")
        all_hits.extend(hits)

    if not all_hits:
        print("\n🎉 未在任何 JSON 文件中找到'日本'相关内容，无需修改。")
        return

    print(f"\n📝 总共提取 {len(all_hits)} 条包含'日本'的文本条目。")

    if not ENABLE_API_AUDIT:
        print("\n⚠️  未启用 API 审查（ENABLE_API_AUDIT = False），以下为所有命中条目（供人工检查）：")
        for idx, hit in enumerate(all_hits, 1):
            print(f"\n{idx}. 文件: {hit['file']}")
            print(f"   路径: {hit['path']}")
            print(f"   上下文: {hit['context']}")
        return

    print("🤖 正在调用 DeepSeek API 进行合规审核...")
    client = setup_client()

    # 分批处理，避免请求过大
    batch_size = 20
    results = []
    for i in range(0, len(all_hits), batch_size):
        batch = all_hits[i:i+batch_size]
        print(f"  审核第 {i//batch_size + 1} 批，共 {len(batch)} 条...")
        batch_results = audit_with_deepseek(client, batch)
        results.extend(batch_results)

    generate_report(results, all_hits)

if __name__ == "__main__":
    # 检查当前工作目录下是否有 kmf_individual_files 文件夹
    if not os.path.isdir(JSON_DIR):
        print(f"❌ 错误：当前目录下找不到 '{JSON_DIR}' 文件夹。")
        print("   请确保脚本与 'kmf_individual_files' 文件夹在同一目录下，或修改脚本中的 JSON_DIR 变量。")
        exit(1)
    main()