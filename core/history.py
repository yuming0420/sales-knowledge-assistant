"""核心模块 - 问答历史与训练进度管理"""
import json
from pathlib import Path
from datetime import datetime, date, timedelta

BASE_DIR = Path(__file__).parent.parent
HISTORY_FILE = BASE_DIR / "data" / "qa_history.json"
PROGRESS_FILE = BASE_DIR / "data" / "progress.json"
CONVERSATIONS_DIR = BASE_DIR / "data" / "conversations"

class QaHistory:
    def __init__(self, max_items=200):
        self.max_items = max_items

    def _load(self):
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self, data):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, question, answer):
        history = self._load()
        history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "date": date.today().isoformat(),
            "question": question,
            "answer": answer
        })
        if len(history) > self.max_items:
            history = history[-self.max_items:]
        self._save(history)

    def get_all(self):
        return self._load()

    def search(self, keyword):
        kw = keyword.lower()
        return [h for h in self._load()
                if kw in h["question"].lower() or kw in h["answer"].lower()]

    def delete(self, index):
        history = self._load()
        if 0 <= index < len(history):
            history.pop(index)
            self._save(history)

    def clear(self):
        self._save([])

    @property
    def stats(self):
        history = self._load()
        today = date.today().isoformat()
        return {
            "total": len(history),
            "today": sum(1 for h in history if h["date"] == today)
        }


class TrainingProgress:
    def _load(self):
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"streak": 0, "best_streak": 0, "total_days": 0, "history": {}}

    def _save(self, data):
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def checkin(self):
        data = self._load()
        today = date.today().isoformat()
        if today not in data.get("history", {}):
            data.setdefault("history", {})[today] = {
                "checkin": datetime.now().isoformat(),
                "tasks": {},
                "note": "",
                "completed": False
            }
            self._save(data)
        return data

    def checkout(self, tasks_completed=None):
        """晚间复盘，标记完成"""
        data = self._load()
        today = date.today().isoformat()
        record = data.get("history", {}).get(today, {})
        if not record:
            return data

        if tasks_completed:
            record["tasks"] = tasks_completed

        # 检查最小可行日
        min_tasks = ["1_金句", "2_电话", "3_复盘"]
        all_done = all(record.get("tasks", {}).get(t, False) for t in min_tasks)

        if all_done:
            record["completed"] = True
            # 计算连胜
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            if yesterday in data.get("history", {}) and data["history"][yesterday].get("completed"):
                data["streak"] = data.get("streak", 0) + 1
            else:
                data["streak"] = 1
            data["best_streak"] = max(data.get("best_streak", 0), data["streak"])
            data["total_days"] = data.get("total_days", 0) + 1

        self._save(data)
        return data

    def get(self):
        data = self._load()
        today = date.today().isoformat()
        return {
            "streak": data.get("streak", 0),
            "best_streak": data.get("best_streak", 0),
            "total_days": data.get("total_days", 0),
            "checked_in": today in data.get("history", {}),
            "today_completed": data.get("history", {}).get(today, {}).get("completed", False),
            "today_tasks": data.get("history", {}).get(today, {}).get("tasks", {}),
            "recent": self._recent_7days(data)
        }

    def _recent_7days(self, data):
        result = []
        for i in range(6, -1, -1):
            d = (date.today() - timedelta(days=i)).isoformat()
            record = data.get("history", {}).get(d)
            if record:
                result.append({
                    "date": d,
                    "status": "completed" if record.get("completed") else "checked_in",
                })
            else:
                result.append({"date": d, "status": "empty"})
        return result


class ConversationManager:
    """多会话管理"""
    def __init__(self):
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

    def list(self):
        return sorted(
            [f.stem for f in CONVERSATIONS_DIR.glob("*.json")],
            key=lambda x: (CONVERSATIONS_DIR / f"{x}.json").stat().st_mtime,
            reverse=True
        )

    def load(self, name):
        path = CONVERSATIONS_DIR / f"{name}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save(self, name, messages):
        path = CONVERSATIONS_DIR / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def delete(self, name):
        path = CONVERSATIONS_DIR / f"{name}.json"
        if path.exists():
            path.unlink()

# 全局单例
qa_history = QaHistory()
training = TrainingProgress()
conversations = ConversationManager()
