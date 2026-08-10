from pathlib import Path

from agent.permissions import resolve_inside_workspace


TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
}


def project_files(workspace_root):
    root = Path(workspace_root).resolve()
    files = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file():
            files.append(path.relative_to(root).as_posix())
    return files


def summarize_project(workspace_root):
    files = project_files(workspace_root)
    groups = {}
    for file_path in files:
        suffix = Path(file_path).suffix or "[no extension]"
        groups.setdefault(suffix, 0)
        groups[suffix] += 1

    group_lines = [f"- {suffix}: {count}" for suffix, count in sorted(groups.items())]
    file_lines = [f"- {file_path}" for file_path in files]
    return "Project files by type:\n" + "\n".join(group_lines) + "\n\nFiles:\n" + "\n".join(file_lines)


def inspect_path(workspace_root, user_path):
    path = resolve_inside_workspace(workspace_root, user_path)
    if not path.exists():
        return f"Path not found: {user_path}"

    if path.is_dir():
        children = sorted(path.iterdir())
        visible_children = [child.name + ("/" if child.is_dir() else "") for child in children[:40]]
        return (
            f"Directory: {path.name}\n"
            f"Items: {len(children)}\n"
            + "\n".join(f"- {name}" for name in visible_children)
        )

    size = path.stat().st_size
    suffix = path.suffix or "[no extension]"
    line_count = "unknown"
    if suffix.lower() in TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8", errors="replace")
        line_count = str(len(text.splitlines()))

    return (
        f"File: {path.name}\n"
        f"Extension: {suffix}\n"
        f"Size: {size} bytes\n"
        f"Lines: {line_count}"
    )


def read_text_file(workspace_root, user_path, max_chars=6000):
    path = resolve_inside_workspace(workspace_root, user_path)
    if not path.exists():
        return f"File not found: {user_path}"
    if not path.is_file():
        return f"Not a file: {user_path}"
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return f"Refusing to read non-text file: {user_path}"

    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[truncated]"
    return text


def search_text(workspace_root, query, max_results=30):
    query_lower = query.lower()
    results = []
    root = Path(workspace_root).resolve()

    for file_path in project_files(root):
        path = root / file_path
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if query_lower in line.lower():
                results.append(f"{file_path}:{line_number}: {line.strip()}")
                if len(results) >= max_results:
                    return "\n".join(results)

    if not results:
        return f"No matches for: {query}"
    return "\n".join(results)
