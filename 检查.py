import os
import json
import re
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI

# ===================== 配置区域 =====================
DEEPSEEK_API_KEY = "sk-77112f212c6a4ac4a78f7c4694ed46c1"          # 请替换为真实 Key
JSON_DIR = "./kmf_individual_files"                 # JSON 文件目录
ENABLE_API_AUDIT = True                             # 是否调用 API（若 False 只提取文本）
BATCH_SIZE = 15                                     # 每批发送的片段数量
SKIP_FIELD = "Specifications"                       # 需要完全跳过的字段名（大小写敏感）
# ===================================================

def setup_client() -> OpenAI:
    api_key = DEEPSEEK_API_KEY or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key or api_key == "你的 DeepSeek API Key":
        print("❌ 错误：请在脚本中设置 DEEPSEEK_API_KEY 或设置环境变量 DEEPSEEK_API_KEY")
        exit(1)
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def load_json_files(directory: str) -> Dict[str, Any]:
    json_files = {}
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return json_files
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                json_files[filename] = data
            except Exception as e:
                print(f"⚠️ 警告: 读取 {filename} 失败 - {e}")
    return json_files

def should_skip_path(path: List[Union[str, int]]) -> bool:
    """判断当前路径是否应该跳过（包括 Specifications 字段及其所有后代）"""
    for segment in path:
        if isinstance(segment, str) and segment == SKIP_FIELD:
            return True
    return False

def extract_text_chunks(data: Any, file_name: str, path: List[Union[str, int]] = None,
                        max_chunk_length: int = 400) -> List[Dict[str, Any]]:
    """
    递归提取 JSON 中所有字符串值，但跳过路径中包含 SKIP_FIELD 的子树。
    对长文本自动分块，保留上下文。
    """
    if path is None:
        path = []
    chunks = []

    def add_chunk(text: str, full_text: str, start_char: int, context: str):
        chunks.append({
            "file": file_name,
            "path": " → ".join(str(p) for p in path),
            "full_text": full_text,
            "text": text,
            "context": context,
            "start_char": start_char
        })

    def extract_recur(obj, current_path):
        # 如果当前路径应该跳过，直接返回
        if should_skip_path(current_path):
            return

        if isinstance(obj, str):
            if not obj.strip():
                return
            text = obj
            if len(text) > max_chunk_length:
                start = 0
                while start < len(text):
                    end = min(start + max_chunk_length, len(text))
                    # 尝试在句号或换行处分割
                    if end < len(text):
                        last_period = text.rfind('。', start, end)
                        if last_period > start:
                            end = last_period + 1
                    chunk_text = text[start:end].strip()
                    if chunk_text:
                        ctx_start = max(0, start - 50)
                        ctx_end = min(len(text), end + 50)
                        context = text[ctx_start:ctx_end].strip()
                        add_chunk(chunk_text, obj, start, context)
                    start = end
            else:
                add_chunk(text, obj, 0, text)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                extract_recur(v, current_path + [k])
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_recur(item, current_path + [str(i)])

    extract_recur(data, path)
    return chunks

def build_audit_prompt(chunks: List[Dict[str, Any]]) -> str:
    prompt = """你是一位网站内容合规审查专家，精通中国《计算机信息网络国际联网安全保护管理办法》、《网络信息内容生态治理规定》等法律法规。
你需要对以下从网站 JSON 数据中提取的文本片段进行审查，判断其是否可能因违反中国法律法规而导致公安联网备案失败或引发处罚。
重点关注以下违规类型：
1. 政治敏感：攻击国家制度、领导人、政策；煽动颠覆国家政权；破坏民族团结；宣扬分裂主义（如藏独、疆独、港独、台独等）。
2. 历史虚无主义：歪曲党史、国史、军史；否定英雄烈士；美化侵华战争或军国主义。
3. 民族歧视与仇恨：侮辱、歧视任何民族（包括汉族、藏族、维吾尔族、回族等）；煽动民族仇恨。
4. 宣扬暴力、恐怖、极端主义：详细描写血腥残暴场景；宣扬杀人、虐待；煽动暴力行为。
5. 色情低俗：淫秽色情描写、性暗示、招嫖信息。
6. 赌博、毒品：宣传赌博、吸毒、制毒。
7. 侵犯他人合法权益：诽谤、侮辱他人；侵犯隐私；非法人肉搜索。
8. 其他违法违规内容：如传播虚假信息、扰乱金融秩序、危害未成年人等。

对于每个文本片段，你需要结合上下文（完整字段内容或邻近文字），判断该内容是否属于上述违规类型。
如果存在违规，结论为 "reject"，并给出具体修改建议（替换成什么文字）；如果内容安全，结论为 "pass"。

请以 JSON 数组格式返回，每个元素包含：
{
  "hash": "片段的唯一标识（使用 file_path_startChar）",
  "conclusion": "pass 或 reject",
  "risk_level": "high / medium / low",
  "reason": "判断理由（简短）",
  "suggestion": "修改建议（结论为 reject 时必填，否则空字符串）"
}

以下是待审查的文本片段列表（每条包含 hash 和 context）：

"""
    for chunk in chunks:
        hash_id = f"{chunk['file']}_{chunk['path']}_{chunk['start_char']}"
        # 截取前 600 字符作为上下文
        short_ctx = chunk['context'][:600]
        prompt += f"\n- hash: {hash_id}\n  context: {short_ctx}\n"

    prompt += "\n请输出结果，不要包含任何额外说明。"
    return prompt

def audit_with_deepseek(client: OpenAI, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not chunks:
        return []
    prompt = build_audit_prompt(chunks)
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个内容合规审查专家，只输出 JSON 数组，不输出其他内容。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        if isinstance(result_json, dict) and "results" in result_json:
            return result_json["results"]
        elif isinstance(result_json, list):
            return result_json
        else:
            print("⚠️ API 返回格式异常:", result_text[:200])
            return []
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return []

def generate_report(all_chunks: List[Dict[str, Any]], audit_results: List[Dict[str, Any]]):
    # 建立 hash 映射
    hash_map = {}
    for chunk in all_chunks:
        hash_id = f"{chunk['file']}_{chunk['path']}_{chunk['start_char']}"
        hash_map[hash_id] = chunk

    rejects = []
    passes = []
    for res in audit_results:
        hash_id = res.get("hash")
        chunk = hash_map.get(hash_id)
        if not chunk:
            continue
        entry = {
            "file": chunk["file"],
            "path": chunk["path"],
            "context": chunk["context"],
            "full_text": chunk["full_text"],
            "conclusion": res.get("conclusion"),
            "risk_level": res.get("risk_level"),
            "reason": res.get("reason"),
            "suggestion": res.get("suggestion", "")
        }
        if res.get("conclusion") == "reject":
            rejects.append(entry)
        else:
            passes.append(entry)

    print("\n" + "=" * 80)
    print("     内容合规审查报告（公安联网备案专项 - 跳过 Specifications 字段）")
    print("=" * 80)

    if rejects:
        print(f"\n⚠️ 发现 {len(rejects)} 条可能需要修改的内容：")
        print("-" * 80)
        for idx, entry in enumerate(rejects, 1):
            print(f"\n【{idx}】文件: {entry['file']}")
            print(f"    路径: {entry['path']}")
            print(f"    风险等级: {entry['risk_level']}")
            print(f"    判断理由: {entry['reason']}")
            print(f"    💡 修改建议: {entry['suggestion']}")
            print(f"    问题上下文: {entry['context'][:200]}...")
            if len(entry['full_text']) > 300:
                print(f"    完整原文: {entry['full_text'][:300]}...")
            else:
                print(f"    完整原文: {entry['full_text']}")
            print()

        print("\n📋 修改计划（按文件分组）")
        print("=" * 80)
        file_mods = {}
        for entry in rejects:
            fname = entry['file']
            if fname not in file_mods:
                file_mods[fname] = []
            file_mods[fname].append({
                "path": entry['path'],
                "original_snippet": entry['full_text'][:150],
                "suggestion": entry['suggestion']
            })
        for fname, items in file_mods.items():
            print(f"\n📁 {fname}")
            for it in items:
                print(f"   🔹 路径: {it['path']}")
                print(f"      原文片段: {it['original_snippet']}...")
                print(f"      建议修改: {it['suggestion']}")
                print()
    else:
        print("\n🎉 未发现需要修改的内容，你的网站内容基本合规！")

    print("\n" + "=" * 80)
    print("📊 审查统计")
    print("=" * 80)
    print(f"   总文本片段数: {len(all_chunks)}")
    print(f"   建议修改数: {len(rejects)}")
    print(f"   通过数: {len(passes)}")
    if audit_results:
        print(f"   API 返回结果数: {len(audit_results)}")
    else:
        print("   ⚠️ API 未返回有效结果，请检查网络和 API Key。")

def main():
    print(f"🔍 正在扫描目录: {JSON_DIR}")
    json_files = load_json_files(JSON_DIR)
    if not json_files:
        print("未找到 JSON 文件，程序退出。")
        return

    print(f"✅ 发现 {len(json_files)} 个 JSON 文件，正在提取文本片段（跳过 {SKIP_FIELD} 字段）...")
    all_chunks = []
    for fname, data in json_files.items():
        chunks = extract_text_chunks(data, fname)
        if chunks:
            print(f"   {fname}: 提取 {len(chunks)} 个片段")
        all_chunks.extend(chunks)

    if not all_chunks:
        print("未提取到任何文本内容。")
        return

    print(f"\n总共提取 {len(all_chunks)} 个文本片段。")

    if not ENABLE_API_AUDIT:
        print("\n未启用 API 审查（ENABLE_API_AUDIT=False），以下为所有片段（供人工检查）：")
        for idx, chunk in enumerate(all_chunks[:20], 1):
            print(f"{idx}. [{chunk['file']}] {chunk['path']}: {chunk['text'][:100]}...")
        return

    print("🤖 正在调用 DeepSeek API 进行内容合规审查...")
    client = setup_client()

    all_results = []
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i+BATCH_SIZE]
        print(f"   审查第 {i//BATCH_SIZE + 1} 批，共 {len(batch)} 个片段...")
        results = audit_with_deepseek(client, batch)
        if results:
            all_results.extend(results)
        else:
            print("      ⚠️ 该批次返回空结果")

    generate_report(all_chunks, all_results)

if __name__ == "__main__":
    main()