"""核心模块 - 知识库加载与格式化"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
KB_PATH = BASE_DIR / "data" / "knowledge" / "何总_知识框架.json"

class KnowledgeBase:
    def __init__(self, path=None):
        self.path = path or KB_PATH
        self.data = {}
        self.reload()

    def reload(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @property
    def modules(self):
        return {k: v for k, v in self.data.items() if k != "博主"}

    def format_for_prompt(self):
        lines = []
        for key, val in self.modules.items():
            lines.append(f"\n## {key}")
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        title = item.get("名称") or item.get("原则") or item.get("阶段") or item.get("故事") or ""
                        if "步骤" in item:
                            title = f"第{item['步骤']}步: {title}"
                        core = item.get("核心") or item.get("核心观点") or item.get("解释") or ""
                        if core:
                            lines.append(f"- {title}: {core}")
                        for subk in ["做法", "方法", "关键动作", "技巧", "对策", "渠道", "内容"]:
                            if subk in item:
                                for a in item[subk]:
                                    lines.append(f"    - {a}")
                    elif isinstance(item, str):
                        lines.append(f"- {item}")
            elif isinstance(val, dict):
                for kk, vv in val.items():
                    if isinstance(vv, list):
                        lines.append(f"- {kk}: {'; '.join(str(x) for x in vv[:5])}")
                    elif isinstance(vv, str):
                        lines.append(f"- {kk}: {vv}")
        return "\n".join(lines)

    def get_module(self, name):
        return self.data.get(name)

    def set_module(self, name, value):
        self.data[name] = value

    @property
    def stats(self):
        return {
            "modules": len(self.modules),
            "keys": list(self.modules.keys()),
        }
