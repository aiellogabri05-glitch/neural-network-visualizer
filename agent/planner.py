from dataclasses import dataclass


@dataclass
class PlannedAction:
    name: str
    argument: str = ""
    needs_confirmation: bool = False


HELP_TEXT = """Available commands:
- help
- status
- diff
- health
- test
- files
- inspect <path>
- read <path>
- search <text>
- validate
- train
- remember <text>
- recall [text]
- todo add <text>
- todo list
- todo done <id>
- commit <message>
- push
- explain
- roadmap
- memory
- exit
"""


def plan(user_text):
    text = user_text.strip()
    lower = text.lower()

    if lower in {"help", "aiuto", "comandi"}:
        return PlannedAction("help")
    if lower in {"exit", "quit", "esci"}:
        return PlannedAction("exit")
    if lower in {"status", "git status", "stato"}:
        return PlannedAction("git_status")
    if lower in {"diff", "git diff", "differenze"}:
        return PlannedAction("git_diff")
    if lower in {"health", "diagnose", "diagnosi", "controllo"}:
        return PlannedAction("health_check")
    if lower in {"test", "tests"}:
        return PlannedAction("run_tests")
    if lower in {"files", "file", "summary", "riassunto"}:
        return PlannedAction("summarize_project")
    if lower.startswith("inspect "):
        return PlannedAction("inspect_path", text[8:].strip())
    if lower.startswith("ispeziona "):
        return PlannedAction("inspect_path", text[10:].strip())
    if lower.startswith("read "):
        return PlannedAction("read_file", text[5:].strip())
    if lower.startswith("leggi "):
        return PlannedAction("read_file", text[6:].strip())
    if lower.startswith("search "):
        return PlannedAction("search_text", text[7:].strip())
    if lower.startswith("cerca "):
        return PlannedAction("search_text", text[6:].strip())
    if lower in {"validate", "valida", "controlla pesi"}:
        return PlannedAction("validate_weights")
    if lower in {"train", "allena", "retrain", "riaddestra"}:
        return PlannedAction("train_model", needs_confirmation=True)
    if lower.startswith("remember "):
        return PlannedAction("remember", text[9:].strip())
    if lower.startswith("ricorda "):
        return PlannedAction("remember", text[8:].strip())
    if lower == "recall":
        return PlannedAction("recall")
    if lower.startswith("recall "):
        return PlannedAction("recall", text[7:].strip())
    if lower in {"cosa ricordi", "che cosa ricordi"}:
        return PlannedAction("recall")
    if lower in {"todo", "todo list"}:
        return PlannedAction("todo_list")
    if lower.startswith("todo add "):
        return PlannedAction("todo_add", text[9:].strip())
    if lower.startswith("todo done "):
        return PlannedAction("todo_done", text[10:].strip())
    if lower.startswith("commit "):
        return PlannedAction("git_commit", text[7:].strip(), needs_confirmation=True)
    if lower.startswith("committa "):
        return PlannedAction("git_commit", text[9:].strip(), needs_confirmation=True)
    if lower in {"push", "pusha", "pubblica"}:
        return PlannedAction("git_push", needs_confirmation=True)
    if lower in {"explain", "spiega", "spiegami la rete", "come funziona"}:
        return PlannedAction("explain_project")
    if lower in {"roadmap", "jarvis", "prossimi passi"}:
        return PlannedAction("roadmap")
    if lower in {"memory", "memoria"}:
        return PlannedAction("memory")

    return PlannedAction("fallback", text)
