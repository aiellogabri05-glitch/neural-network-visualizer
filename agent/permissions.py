from pathlib import Path


class PermissionError(Exception):
    pass


def resolve_inside_workspace(workspace_root, user_path):
    root = Path(workspace_root).resolve()
    candidate = (root / user_path).resolve()

    if candidate != root and root not in candidate.parents:
        raise PermissionError(f"Path outside workspace is not allowed: {user_path}")

    return candidate


def is_sensitive_action(action_name):
    return action_name in {"train", "write", "delete", "send", "push"}

