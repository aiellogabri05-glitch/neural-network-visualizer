import json
import re
from datetime import datetime
from pathlib import Path

import requests


def get_embedding(text, model="nomic-embed-text"):
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception:
        return None  # se Ollama non risponde, niente embedding (gestiamo dopo il caso)

def cosine_similarity(v1, v2):
    if v1 is None or v2 is None:
        return -1
    prodotto = sum(a * b for a, b in zip(v1, v2))
    lunghezza1 = sum(a * a for a in v1) ** 0.5
    lunghezza2 = sum(b * b for b in v2) ** 0.5
    if lunghezza1 == 0 or lunghezza2 == 0:
        return -1
    return prodotto / (lunghezza1 * lunghezza2)


def lexical_memory_matches(memories, query):
    query_tokens = set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))
    if not query_tokens:
        return []

    scored = []
    for memory in memories:
        text = memory.get("text", "")
        memory_tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        overlap = query_tokens.intersection(memory_tokens)
        if overlap:
            score = len(overlap) * 4
            score += sum(memory_tokens.count(token) for token in overlap)
            scored.append((score, memory))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [memory for _, memory in scored[:5]]


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
        temp_path = self.path.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def remember(self, text):
        entry = {
            "text": text,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "embedding": get_embedding(text),
        }
        self.data["memories"].append(entry)
        self._save()
        return f"Remembered: {text}"


    def recall(self, query=""):
        memories = self.data["memories"]

        if not memories:
            return "No persistent memories yet."

        if query:
            query_embedding = get_embedding(query)
            if query_embedding is None:
                best_matches = lexical_memory_matches(memories, query)
            else:
                scored = [
                    (cosine_similarity(query_embedding, memory.get("embedding")), memory)
                    for memory in memories
                ]
                scored.sort(key=lambda pair: pair[0], reverse=True)
                best_matches = [memory for score, memory in scored[:5] if score > 0.5]
                if not best_matches:
                    best_matches = lexical_memory_matches(memories, query)

            if not best_matches:
                return f"No memories matching: {query}"
            memories = best_matches
        else:
            memories = memories[-20:]

        lines = []
        for index, memory in enumerate(memories, start=1):
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
