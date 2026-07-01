import streamlit as st
import json, os, sys, requests
from pathlib import Path
from dotenv import load_dotenv
import chromadb

# ─── 配置 ─────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
API_KEY = os.getenv("SILICONFLOW_API_KEY")
MODEL = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"
CHROMA_PATH = str(BASE_DIR / "data" / "chroma")
TOP_K = 6

# ─── 初始化RAG ────────────────────────────
@st.cache_resource
def init_chroma():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection("sales_knowledge")

collection = init_chroma()

def embed_query(text):
    resp = requests.post(EMBED_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": [text], "encoding_format": "float"},
        timeout=30)
    if resp.status_code == 200:
        return resp.json()["data"][0]["embedding"]
    return None

def retrieve(query):
    emb = embed_query(query)
    if not emb: return []
    results = collection.query(query_embeddings=[emb], n_results=TOP_K)
    contexts = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        relevance = max(0, 1 - dist) if dist else 1.0
        contexts.append({"text": doc, "path": meta.get("path",""), "title": meta.get("title",""), "relevance": relevance})
    return contexts

SYSTEM_PROMPT = """你是何总的销售知识助手，为山东朱氏药业TOB销售员提供实战指导。
知识来自抖音博主"何总"的销售培训内容。结合医药行业场景给出具体建议。
回答简洁有力，像销售教练。尽量引用何总金句。"""

def ask(question):
    contexts = retrieve(question)
    if not contexts:
        return "检索暂时不可用", []
    
    ctx_parts = [f"[{c['title'] or c['path']}] {c['text']}" for c in contexts]
    knowledge = "\n\n".join(ctx_parts)
    
    resp = requests.post(API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n检索到的知识：\n{knowledge}"},
            {"role": "user", "content": question}
        ], "temperature": 0.5, "max_tokens": 2048}, timeout=60)
    
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"], contexts
    return f"API错误 ({resp.status_code})", []

# ─── UI ───────────────────────────────────
st.set_page_config(page_title="何总销售助手", page_icon="💼", layout="wide")

# Sidebar
with st.sidebar:
    st.title("💼 何总销售助手")
    st.caption("山东朱氏药业 · TOB专属")
    st.divider()
    
    # Stats
    col1, col2 = st.columns(2)
    with col1: st.metric("知识块", collection.count())
    with col2: st.metric("检索数", TOP_K)
    
    st.divider()
    st.subheader("📍 试试这些问题")
    examples = [
        "客户已读不回怎么办？",
        "怎么开发一家新药厂客户？",
        "报价后客户失踪了怎么追？",
        "如何提高邀约成功率？",
        "TOB和TOC销售有什么区别？",
        "客户说价格比竞品贵怎么回？",
        "七步销售法是什么？",
        "怎么做好客户转介绍？"
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_question = ex
            st.rerun()
    
    st.divider()
    st.caption(f"模型: {MODEL}")
    st.caption(f"Embedding: {EMBED_MODEL}")

# Main
st.title("💼 何总销售知识助手")
st.caption("基于何总抖音销售培训内容的个人AI助手 —— 问销售问题，得实战答案")

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "你好！我是基于何总销售培训内容的知识助手。\n\n你可以问我任何TOB销售相关问题：客户开发、追踪、促成、话术、行业选择……我会结合何总的方法论和你所在的医药行业给出实战建议。\n\n试试左边的问题，或直接输入你的销售难题 👇"
    })

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if "pending_question" in st.session_state:
    prompt = st.session_state.pending_question
    del st.session_state.pending_question
else:
    prompt = st.chat_input("输入你的销售问题...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("检索何总知识库..."):
            answer, contexts = ask(prompt)
            st.markdown(answer)
            
            if contexts:
                with st.expander(f"🔍 检索到 {len(contexts)} 条相关知识"):
                    for c in contexts:
                        pct = int(c["relevance"] * 100)
                        st.caption(f"**{c['title'] or c['path']}** (相关性 {pct}%)")
                        st.text(c["text"][:200] + "...")
    
    st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
st.caption(f"知识库: 22条视频蒸馏 · {collection.count()}个向量块 · 硅基流动 API")
