import subprocess
import sys


def run_command(args, workspace_root):
    completed = subprocess.run(
        args,
        cwd=workspace_root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout.strip()
    error = completed.stderr.strip()

    parts = []
    if output:
        parts.append(output)
    if error:
        parts.append(error)
    if not parts:
        parts.append(f"Command exited with code {completed.returncode}.")

    return "\n".join(parts), completed.returncode


def git_status(workspace_root):
    output, code = run_command(["git", "status", "--short"], workspace_root)
    if code == 0 and not output.strip():
        return "Git working tree is clean."
    return output


def git_diff(workspace_root):
    status = git_status(workspace_root)
    stat, _ = run_command(["git", "diff", "--stat"], workspace_root)
    check, check_code = run_command(["git", "diff", "--check"], workspace_root)

    parts = []
    parts.append("Working tree:\n" + status)
    if stat:
        parts.append("Diff stat:\n" + stat)
    else:
        parts.append("No tracked-file diff.")

    if check_code == 0:
        parts.append("Diff check: OK")
    else:
        parts.append("Diff check:\n" + check)

    return "\n\n".join(parts)


def git_commit_all(workspace_root, message):
    if not message.strip():
        return "Usage: commit <message>"

    add_output, add_code = run_command(["git", "add", "-A"], workspace_root)
    if add_code != 0:
        return add_output

    commit_output, _ = run_command(["git", "commit", "-m", message], workspace_root)
    return commit_output


def git_push(workspace_root):
    branch, branch_code = run_command(["git", "branch", "--show-current"], workspace_root)
    if branch_code != 0 or not branch.strip():
        return "Could not determine current branch."

    output, _ = run_command(["git", "push", "origin", branch.strip()], workspace_root)
    return output


def validate_weights(workspace_root):
    output, _ = run_command([sys.executable, "validate_weights.py"], workspace_root)
    return output


def train_model(workspace_root):
    output, _ = run_command([sys.executable, "train.py"], workspace_root)
    return output


def compile_agent(workspace_root):
    files = [
        "agent/__init__.py",
        "agent/agent_loop.py",
        "agent/brain.py",
        "agent/messages.py",
        "agent/permissions.py",
        "agent/planner.py",
        "agent/storage.py",
        "agent/tools/__init__.py",
        "agent/tools/filesystem.py",
        "agent/tools/shell.py",
    ]
    output, code = run_command([sys.executable, "-m", "py_compile", *files], workspace_root)
    if code == 0:
        return "Agent Python files compile."
    return output


def run_tests(workspace_root):
    output, _ = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"], workspace_root)
    return output


def health_check(workspace_root):
    parts = [
        "Git:\n" + git_status(workspace_root),
        "Weights:\n" + validate_weights(workspace_root),
        "Agent compile:\n" + compile_agent(workspace_root),
    ]
    return "\n\n".join(parts)
