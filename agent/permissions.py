from pathlib import Path

from pathlib import Path

ALLOWED_EXTRA_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
]

class PermissionError(Exception):
    pass


def resolve_inside_workspace(workspace_root, user_path):
    root = Path(workspace_root).resolve()

    # Se il percorso e' assoluto (es. "C:\Users\aiell\Desktop\file.txt"),
    # lo usiamo cosi' com'e'. Se e' relativo (es. "file.txt"), lo interpretiamo
    # rispetto alla cartella del progetto.
    raw_path = Path(user_path)
    if raw_path.is_absolute():
        candidate = raw_path.resolve()
    else:
        candidate = (root / user_path).resolve()

    allowed_roots = [root] + ALLOWED_EXTRA_ROOTS
    is_allowed = any(
        candidate == allowed_root or allowed_root in candidate.parents
        for allowed_root in allowed_roots
    )

    if not is_allowed:
        raise PermissionError(f"Path outside allowed locations is not allowed: {user_path}")

    return candidate


def is_sensitive_action(action_name):
    return action_name in {"train", "write", "delete", "send", "push"}

