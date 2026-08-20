import difflib
import json

import requests

from agent.permissions import resolve_inside_workspace


MAX_LLM_EDIT_CHARS = 20000


def read_edit_target(workspace_root, user_path):
    target = resolve_inside_workspace(workspace_root, user_path)
    if target.exists():
        return target.read_text(encoding="utf-8")
    return ""


def preview_file_change(workspace_root, user_path, new_content):
    old_content = read_edit_target(workspace_root, user_path)

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{user_path} (current)",
        tofile=f"{user_path} (proposed)",
        lineterm="",
    )
    diff_text = "\n".join(diff)

    if not diff_text:
        return None

    return diff_text


def apply_file_change(workspace_root, user_path, new_content):
    target = resolve_inside_workspace(workspace_root, user_path)

    target.parent.mkdir(parents=True, exist_ok=True)

    temp_path = target.with_suffix(target.suffix + ".tmp")
    temp_path.write_text(new_content, encoding="utf-8")
    temp_path.replace(target)

    return f"Updated: {user_path}"


def append_line_to_file(workspace_root, user_path, new_line):
    old_content = read_edit_target(workspace_root, user_path)

    if old_content and not old_content.endswith("\n"):
        old_content += "\n"

    return old_content + new_line + "\n"


def replace_text_in_file(workspace_root, user_path, old_text, new_text):
    target = resolve_inside_workspace(workspace_root, user_path)

    if not target.exists():
        raise FileNotFoundError(user_path)
    if not old_text:
        raise ValueError("Text to replace cannot be empty.")

    old_content = target.read_text(encoding="utf-8")
    if old_text not in old_content:
        raise ValueError(f"Text not found in {user_path}.")

    return old_content.replace(old_text, new_text, 1)


def propose_instruction_edit(workspace_root, user_path, instruction, model="llama3.2:3b"):
    old_content = read_edit_target(workspace_root, user_path)
    instruction = instruction.strip()

    if not instruction:
        raise ValueError("Edit instruction cannot be empty.")
    if len(old_content) > MAX_LLM_EDIT_CHARS:
        raise ValueError(f"{user_path} is too large for a single edit proposal.")

    prompt = f"""You are editing one project file.

Return ONLY a JSON object with this exact shape:
{{"updated_content": "the complete updated file content"}}

Rules:
- Preserve the existing style and formatting.
- Make the smallest change that satisfies the instruction.
- Return the whole file content, not a diff.
- Do not include explanations, Markdown, or code fences.

File path: {user_path}

Instruction:
{instruction}

Current file content:
{old_content}
"""

    updated_content = request_edit_from_llm(prompt, model=model)
    if updated_content is None:
        raise ValueError("Could not generate edit proposal. Is Ollama running?")

    return updated_content


def request_edit_from_llm(prompt, model="llama3.2:3b"):
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json()["message"]["content"].strip()
    except Exception:
        return None

    return parse_updated_content(raw)


def parse_updated_content(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    updated_content = parsed.get("updated_content")
    if not isinstance(updated_content, str):
        return None
    return updated_content
