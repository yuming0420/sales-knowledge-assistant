#!/usr/bin/env python3
"""何总销售知识助手 v3 - RAG检索增强版"""
import json, os, sys, requests
from pathlib import Path
from dotenv import load_dotenv
import chromadb

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
API_KEY = os.getenv("SILICONFLOW_API_KEY")
MODEL = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"
CHROMA_PATH = str(BASE_DIR / "data" / "chroma")
TOP_K = 6

# Init ChromaDB
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection("sales_knowledge")

def embed_query(text):
    resp = requests.post(EMBED_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": [text], "encoding_format": "float"},
        timeout=30)
    if resp.status_code == 200:
        return resp.json()["data"][0]["embedding"]
    return None

def retrieve(query, top_k=TOP_K):
    """RAG检索：语义搜索最相关的知识块"""
    emb = embed_query(query)
    if not emb:
        return []
    results = collection.query(query_embeddings=[emb], n_results=top_k)
    contexts = []
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        relevance = max(0, 1 - dist) if dist else 1.0
        contexts.append({
            "text": doc,
            "path": meta.get("path", ""),
            "title": meta.get("title", ""),
            "relevance": round(relevance, 3)
        })
    return contexts

SYSTEM_PROMPT = """你是何总的销售知识助手，专门为山东朱氏药业的TOB销售员提供实战指导。
你的知识来自抖音博主"何总"的销售培训内容（七步销售法、客户开发等）。

回答规则：
1. 优先使用下方检索到的何总知识来回答
2. 结合医药行业TOB销售场景给出具体建议
3. 回答简洁有力，像销售教练一样直击要点
4. 尽量引用何总的金句或核心观点
5. 如果检索结果不涵盖问题，用通用销售知识补充并诚实说明"""

def ask(question):
    # RAG retrieve
    contexts = retrieve(question)
    if not contexts:
        return "抱歉，检索暂时不可用，请稍后重试。"
    
    # Build context
    ctx_parts = []
    for c in contexts:
        label = c["title"] or c["path"]
        ctx_parts.append(f"[{label}] {c['text']}")
    
    knowledge = "\n\n".join(ctx_parts)
    
    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n## 检索到的何总知识：\n{knowledge}"},
        {"role": "user", "content": question}
    ]
    
    resp = requests.post(API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "temperature": 0.5, "max_tokens": 2048},
        timeout=60)
    
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    return f"API错误 ({resp.status_code})"

def main():
    print("=" * 50)
    print("  何总销售知识助手 v3 - RAG增强版")
    print(f"  向量库: {collection.count()}条 | 检索Top{TOP_K}")
    print("  输入 quit 退出, help 查看示例")
    print("=" * 50)
    print()
    
    try:
        test = retrieve("销售")
        if test:
            print(f"RAG就绪: 测试检索到 {len(test)} 条相关块")
        else:
            print("RAG就绪")
    except Exception as e:
        print(f"RAG警告: {e}")
    print()
    
    while True:
        try:
            q = input("问题: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not q: continue
        if q.lower() in ("quit","exit","q"): print("再见！"); break
        if q.lower() == "help":
            print("\n示例: 客户不回消息 | 怎么逼单 | 七步销售法 | 如何邀约 | 开发新客户 | 报价策略\n")
            continue
        
        print("\n思考中...\n")
        answer = ask(q)
        print(answer)
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(ask(" ".join(sys.argv[1:])))
    else:
        main()
