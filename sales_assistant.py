#!/usr/bin/env python3
"""何总销售助手 CLI - DeepSeek 驱动"""
import sys, json
from pathlib import Path
from core.knowledge import KnowledgeBase
from core.llm import llm
from core.history import qa_history

kb = KnowledgeBase()
SYSTEM_PROMPT = f"""你是何总的销售知识助手，为山东朱氏药业TOB销售员提供实战指导。
知识来自抖音博主"何总"的销售培训内容。回答简洁有力，结合医药行业场景，引用何总金句。

## 何总销售知识库
{kb.format_for_prompt()}
"""

def main():
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
        if q == "history":
            items = qa_history.get_all()
            print(f"\n问答历史 ({len(items)} 条)\n")
            for h in items[-10:]:
                print(f"[{h['time']}] Q: {h['question'][:50]}")
                print(f"           A: {h['answer'][:80]}…\n")
        else:
            answer = llm.ask(SYSTEM_PROMPT, q)
            print(answer)
            qa_history.add(q, answer)
    else:
        print("何总销售助手 (DeepSeek)")
        print(f"知识库: {kb.stats['modules']} 模块")
        print("history 查看历史 | quit 退出\n")

        while True:
            try:
                q = input("问题: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！"); break
            if not q: continue
            if q.lower() in ("quit", "exit", "q"): print("再见！"); break
            if q.lower() == "history":
                items = qa_history.get_all()
                for h in items[-10:]:
                    print(f"  [{h['time']}] {h['question'][:40]}…")
                continue

            print()
            for token in llm.ask(SYSTEM_PROMPT, q, stream=True):
                print(token, end="", flush=True)
            print()

if __name__ == "__main__":
    main()
