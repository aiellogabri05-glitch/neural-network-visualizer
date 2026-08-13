import re
from dataclasses import dataclass
from pathlib import Path
import requests

from agent.tools.filesystem import TEXT_EXTENSIONS, project_files


def ask_llm(prompt, model="llama3.2:3b"):
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=120  # con il tuo hardware può metterci un po'
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    except requests.exceptions.ConnectionError:
        return None  # Ollama non è attivo
    except requests.exceptions.Timeout:
        return None  # troppo lento, meglio fallire con grazia


STOPWORDS = {
    "a",
    "about",
    "all",
    "and",
    "are",
    "as",
    "che",
    "come",
    "con",
    "cosa",
    "da",
    "del",
    "della",
    "di",
    "do",
    "does",
    "e",
    "for",
    "funziona",
    "gli",
    "ha",
    "how",
    "i",
    "il",
    "in",
    "is",
    "it",
    "la",
    "le",
    "lo",
    "mi",
    "nel",
    "of",
    "on",
    "per",
    "project",
    "progetto",
    "qual",
    "quale",
    "rete",
    "si",
    "the",
    "to",
    "un",
    "una",
    "what",
}


@dataclass
class Chunk:
    path: str
    start_line: int
    end_line: int
    text: str


def tokenize(text):
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def build_project_chunks(workspace_root, lines_per_chunk=18):
    root = Path(workspace_root).resolve()
    chunks = []

    for file_path in project_files(root):
        path = root / file_path
        suffix = path.suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            continue
        if path.name == ".agent_memory.json":
            continue
        if path.name == "weights.json":
            continue

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index in range(0, len(lines), lines_per_chunk):
            chunk_lines = lines[index:index + lines_per_chunk]
            text = "\n".join(chunk_lines).strip()
            if text:
                chunks.append(Chunk(
                    path=file_path,
                    start_line=index + 1,
                    end_line=index + len(chunk_lines),
                    text=text,
                ))

    return chunks


def rank_chunks(workspace_root, question, limit=5):
    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    query_set = set(query_tokens)
    scored = []

    for chunk in build_project_chunks(workspace_root):
        chunk_tokens = tokenize(chunk.text + " " + chunk.path)
        if not chunk_tokens:
            continue

        chunk_set = set(chunk_tokens)
        overlap = query_set.intersection(chunk_set)
        if not overlap:
            continue

        score = len(overlap) * 4
        score += sum(chunk_tokens.count(token) for token in overlap)
        if any(token in chunk.path.lower() for token in query_set):
            score += 3
        if chunk.path.startswith("tests/"):
            score -= 6
        if chunk.path == "app-2d-backup.js":
            score -= 4
        if chunk.path in {"README.md", "JARVIS_ROADMAP.md"}:
            score += 2

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def compact_snippet(text, max_chars=700):
    text = "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[truncated]"


def relevant_points(chunks, question, limit=6):
    query_tokens = set(tokenize(question))
    points = []

    for chunk in chunks:
        for offset, line in enumerate(chunk.text.splitlines()):
            clean_line = line.strip()
            if not clean_line:
                continue
            line_tokens = set(tokenize(clean_line))
            if query_tokens.intersection(line_tokens):
                line_number = chunk.start_line + offset
                points.append(f"- {chunk.path}:{line_number}: {clean_line}")
                if len(points) >= limit:
                    return points

    return points

def format_recent_history(session_memory, max_messages=6):
    if session_memory is None or not session_memory.messages:
        return ""

    recent = session_memory.messages[-max_messages:]
    lines = [f"{message.role}: {message.content}" for message in recent]
    return "Conversazione recente:\n" + "\n".join(lines) + "\n\n"


def answer_project_question(workspace_root, question, session_memory=None):
    chunks = rank_chunks(workspace_root, question)
    if not chunks:
        return (
            "I could not find strong project context for that question yet. "
            "Try `files`, `search <text>`, or ask about a specific module."
        )

    points = relevant_points(chunks, question)
    if points:
        summary = "Relevant points:\n" + "\n".join(points) + "\n\n"
    else:
        summary = ""

    evidence_lines = []
    for chunk in chunks:
        evidence_lines.append(
            f"- {chunk.path}:{chunk.start_line}-{chunk.end_line}\n"
            f"{compact_snippet(chunk.text)}"
        )

    context_text = "\n\n".join(
        f"File {chunk.path} (lines {chunk.start_line}-{chunk.end_line}):\n{compact_snippet(chunk.text)}"
        for chunk in chunks
    )

    history_text = format_recent_history(session_memory)

    llm_prompt = f"""Sei un assistente che risponde a domande su un progetto software, basandoti SOLO sul contesto fornito qui sotto. Se il contesto non contiene la risposta, dillo chiaramente invece di inventare.

{history_text}Contesto dal progetto:
{context_text}

Domanda: {question}

Rispondi in italiano, in modo chiaro e diretto. Se la domanda fa riferimento a qualcosa detto prima nella conversazione, usa quel contesto."""

    llm_answer = ask_llm(llm_prompt)

    if llm_answer:
        return llm_answer

    # Fallback: se Ollama non risponde, torniamo al vecchio comportamento estrattivo
    lead = (
        "Ollama non e' raggiungibile: risposta locale senza LLM.\n\n"
    )
    return lead + summary + "Evidence:\n" + "\n\n".join(evidence_lines)
