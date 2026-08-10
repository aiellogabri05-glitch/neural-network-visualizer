import json
from datetime import datetime
from pathlib import Path


class PersistentStore:
    def __init__(self, workspace_root, filename=".agent_memory.json"):
        self.path = Path(workspace_root).resolve() / filename
        self.data = self._load()

    def _load(self):
        if not self.path.exists():
            return {"memories": [], "todos": [], "next_todo_id": 1}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"memories": [], "todos": [], "next_todo_id": 1}

        data.setdefault("memories", [])
        data.setdefault("todos", [])
        data.setdefault("next_todo_id", 1)
        return data

    def _save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def remember(self, text):
        entry = {
            "text": text,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.data["memories"].append(entry)
        self._save()
        return f"Remembered: {text}"

    def recall(self, query=""):
        memories = self.data["memories"]
        if query:
            query_lower = query.lower()
            memories = [memory for memory in memories if query_lower in memory["text"].lower()]

        if not memories:
            if query:
                return f"No memories matching: {query}"
            return "No persistent memories yet."

        lines = []
        for index, memory in enumerate(memories[-20:], start=1):
            lines.append(f"{index}. [{memory['created_at']}] {memory['text']}")
        return "\n".join(lines)

    def add_todo(self, text):
        todo_id = self.data["next_todo_id"]
        self.data["next_todo_id"] += 1
        self.data["todos"].append({
            "id": todo_id,
            "text": text,
            "done": False,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        self._save()
        return f"Added todo #{todo_id}: {text}"

    def list_todos(self):
        todos = self.data["todos"]
        if not todos:
            return "No todos yet."

        lines = []
        for todo in todos:
            marker = "x" if todo["done"] else " "
            lines.append(f"[{marker}] #{todo['id']} {todo['text']}")
        return "\n".join(lines)

    def complete_todo(self, todo_id_text):
        try:
            todo_id = int(todo_id_text)
        except ValueError:
            return "Usage: todo done <id>"

        for todo in self.data["todos"]:
            if todo["id"] == todo_id:
                todo["done"] = True
                self._save()
                return f"Completed todo #{todo_id}: {todo['text']}"

        return f"Todo not found: {todo_id}"

