from dataclasses import dataclass

import json
import requests


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
- ask <question>
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
    if lower.startswith("ask "):
        return PlannedAction("ask_project", text[4:].strip())
    if lower.startswith("domanda "):
        return PlannedAction("ask_project", text[8:].strip())
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
        return PlannedAction("search_text", clean_argument(text[7:].strip()))
    if lower.startswith("cerca "):
        return PlannedAction("search_text", clean_argument(text[6:].strip()))
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

    return llm_plan(text)


LLM_ACTIONS = """
help, status, diff, health, test, files, validate, train, recall, todo_list, push, explain, roadmap, memory, exit
ask_project (argument: the question)
inspect_path (argument: a file or folder path)
read_file (argument: a file path)
search_text (argument: text to search)
remember (argument: text to remember)
todo_add (argument: the todo text)
todo_done (argument: the todo id)
commit (argument: the commit message)"""

VALID_ACTIONS = {
    "help", "status", "diff", "health", "test", "files", "validate",
    "train", "recall", "todo_list", "push", "explain", "roadmap",
    "memory", "exit", "ask_project", "inspect_path", "read_file",
    "search_text", "remember", "todo_add", "todo_done", "commit",
}

# Alcune azioni hanno nomi diversi tra quello che l'LLM può scrivere
# e il nome interno usato da agent_loop.py — li mappiamo qui
ACTION_ALIASES = {
    "status": "git_status",
    "diff": "git_diff",
    "health": "health_check",
    "test": "run_tests",
    "files": "summarize_project",
    "validate": "validate_weights",
    "train": "train_model",
    "push": "git_push",
    "commit": "git_commit",
}

ACTIONS_REQUIRING_ARGUMENT = {
    "ask_project", "inspect_path", "read_file",
    "search_text", "remember", "todo_add", "commit",
}

FILLER_PHRASES = [
    "cerca la parola", "cerca dove uso la parola", "cerca dove uso",
    "cerca", "nel progetto", "nel codice", "la parola",
    "search for", "search", "in the project", "in the code",
]

def clean_argument(text):
    cleaned = text.strip()
    lowered = cleaned.lower()
    for phrase in sorted(FILLER_PHRASES, key=len, reverse=True):
        if phrase in lowered:
            idx = lowered.find(phrase)
            cleaned = (cleaned[:idx] + cleaned[idx + len(phrase):]).strip()
            lowered = cleaned.lower()
    return cleaned.strip(" :,-")


def llm_plan(user_text):
    prompt = f"""You are a command interpreter for a coding assistant. Given the user's message, pick the single best matching action from this list:

{LLM_ACTIONS}

Reply with ONLY a JSON object, no other text, in this exact format:
{{"action": "action_name", "argument": "extracted argument or empty string"}}

The argument must be ONLY the relevant piece of information (a file path, a search term, a short text), never the full sentence.

Examples:
User message: cerca dove uso la parola softmax nel progetto
{{"action": "search_text", "argument": "softmax"}}

User message: puoi leggermi il file README.md?
{{"action": "read_file", "argument": "README.md"}}

User message: aggiungi alla lista delle cose da fare: sistemare i colori
{{"action": "todo_add", "argument": "sistemare i colori"}}

User message: segnati che devo sistemare i colori dei neuroni
{{"action": "todo_add", "argument": "sistemare i colori dei neuroni"}}

User message: ricordati che il mio modello ha 64 neuroni per layer
{{"action": "remember", "argument": "il modello ha 64 neuroni per layer"}}

User message: fammi vedere cosa contiene train.py
{{"action": "read_file", "argument": "train.py"}}

User message: quali sono le cose ancora da fare?
{{"action": "todo_list", "argument": ""}}

User message: {user_text}"""

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        raw = response.json()["message"]["content"].strip()

        # I modelli a volte aggiungono testo extra o backtick attorno al JSON: ripuliamo
        raw = raw.strip("`").strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

        parsed = json.loads(raw)

        action_name = parsed.get("action", "").strip()
        argument = parsed.get("argument", "").strip()

        # Validazione 1: l'azione dev'essere tra quelle che conosciamo
        if action_name not in VALID_ACTIONS:
            return PlannedAction("ask_project", user_text)
        # Validazione 2: le azioni che richiedono un argomento non possono averlo vuoto
        if action_name in ACTIONS_REQUIRING_ARGUMENT and not argument:
            return PlannedAction("ask_project", user_text)

        if action_name == "search_text":
            argument = clean_argument(argument)

        # Traduciamo il nome pubblico nel nome interno atteso da agent_loop.py
        internal_name = ACTION_ALIASES.get(action_name, action_name)
        needs_confirmation = internal_name in {"train_model", "git_commit", "git_push"}

        return PlannedAction(internal_name, argument, needs_confirmation)
    except Exception:
        return PlannedAction("ask_project", user_text)