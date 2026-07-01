import json, os, requests
import chromadb

API_KEY = os.getenv("SILICONFLOW_API_KEY")
EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"
KB_PATH = "/app/sales-assistant/data/knowledge/何总_知识框架.json"
CHROMA_PATH = "/app/sales-assistant/data/chroma"

def chunk_knowledge(kb):
    chunks = []
    def recurse(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "博主": continue
                recurse(v, f"{path}/{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                if isinstance(item, dict):
                    lines = []
                    for dk, dv in item.items():
                        if isinstance(dv, list):
                            lines.append(f"{dk}: " + "; ".join(str(x) for x in dv))
                        elif isinstance(dv, str) and len(dv) > 5:
                            lines.append(f"{dk}: {dv}")
                    if lines:
                        chunks.append({"text": " | ".join(lines), "path": new_path, "title": item.get("步骤名") or item.get("名称") or item.get("原则") or item.get("阶段") or item.get("故事") or ""})
                elif isinstance(item, str) and len(item) > 10:
                    chunks.append({"text": item, "path": new_path, "title": ""})
        elif isinstance(obj, str) and len(obj) > 10:
            chunks.append({"text": obj, "path": path, "title": path.split("/")[-1] if "/" in path else path})
    recurse(kb)
    return chunks

def get_embeddings(texts):
    resp = requests.post(EMBED_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": texts, "encoding_format": "float"}, timeout=60)
    return [d["embedding"] for d in resp.json()["data"]]

print("Loading KB...")
with open(KB_PATH, "r", encoding="utf-8") as f:
    kb = json.load(f)

chunks = chunk_knowledge(kb)
print(f"Chunks: {len(chunks)}")

print("Generating embeddings...")
all_emb = []
for i in range(0, len(chunks), 20):
    batch = chunks[i:i+20]
    embs = get_embeddings([c["text"] for c in batch])
    all_emb.extend(embs)
    print(f"  Batch {i//20+1}/{(len(chunks)-1)//20+1}")

print("Storing in ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)
try: client.delete_collection("sales_knowledge")
except: pass
collection = client.create_collection("sales_knowledge", metadata={"hnsw:space": "cosine"})
collection.add(
    ids=[f"chunk_{i}" for i in range(len(chunks))],
    documents=[c["text"] for c in chunks],
    embeddings=all_emb,
    metadatas=[{"path": c["path"], "title": c["title"]} for c in chunks]
)
print(f"Done! {collection.count()} vectors stored")
