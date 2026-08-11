import argparse
from pathlib import Path

from agent.brain import answer_project_question
from agent.messages import SessionMemory
from agent.permissions import PermissionError as AgentPermissionError
from agent.planner import HELP_TEXT, plan
from agent.storage import PersistentStore
from agent.tools.filesystem import inspect_path, read_text_file, search_text, summarize_project
from agent.tools.shell import (
    git_commit_all,
    git_diff,
    git_push,
    git_status,
    health_check,
    run_tests,
    train_model,
    validate_weights,
)


EXPLANATION = """This project has two connected parts:
1. Python trains a neural network on 8x8 handwritten digits.
2. The browser loads weights.json and runs the forward pass in JavaScript.

The current model is 64 -> 64 -> 64 -> 10:
- 64 input pixels.
- 2 hidden layers with 64 neurons each.
- 10 output probabilities, one for each digit.
"""


ROADMAP = """Next useful steps:
1. Stabilize the visualizer with small validation checks.
2. Grow this text agent with more tools.
3. Add persistent memory with SQLite or JSON.
4. Add voice only after the text loop feels reliable.
5. Add controlled autonomy with approvals for risky actions.
"""


class LocalAgent:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root).resolve()
        self.memory = SessionMemory()
        self.store = PersistentStore(self.workspace_root)

    def handle(self, user_text, assume_yes=False):
        self.memory.add("user", user_text)
        action = plan(user_text)

        if action.needs_confirmation and not assume_yes:
            response = f"Action '{action.name}' changes project state. Re-run with confirmation."
        else:
            try:
                response = self._execute(action)
            except AgentPermissionError as error:
                response = f"Permission denied: {error}"
            except OSError as error:
                response = f"Tool error: {error}"

        self.memory.add("assistant", response)
        return response

    def _execute(self, action):
        if action.name == "help":
            return HELP_TEXT
        if action.name == "exit":
            return "Goodbye."
        if action.name == "git_status":
            return git_status(self.workspace_root)
        if action.name == "git_diff":
            return git_diff(self.workspace_root)
        if action.name == "health_check":
            return health_check(self.workspace_root)
        if action.name == "run_tests":
            return run_tests(self.workspace_root)
        if action.name == "ask_project":
            if not action.argument:
                return "Usage: ask <question>"
            return answer_project_question(self.workspace_root, action.argument)
        if action.name == "summarize_project":
            return summarize_project(self.workspace_root)
        if action.name == "inspect_path":
            if not action.argument:
                return "Usage: inspect <path>"
            return inspect_path(self.workspace_root, action.argument)
        if action.name == "read_file":
            if not action.argument:
                return "Usage: read <path>"
            return read_text_file(self.workspace_root, action.argument)
        if action.name == "search_text":
            if not action.argument:
                return "Usage: search <text>"
            return search_text(self.workspace_root, action.argument)
        if action.name == "validate_weights":
            return validate_weights(self.workspace_root)
        if action.name == "train_model":
            return train_model(self.workspace_root)
        if action.name == "remember":
            if not action.argument:
                return "Usage: remember <text>"
            return self.store.remember(action.argument)
        if action.name == "recall":
            return self.store.recall(action.argument)
        if action.name == "todo_add":
            if not action.argument:
                return "Usage: todo add <text>"
            return self.store.add_todo(action.argument)
        if action.name == "todo_list":
            return self.store.list_todos()
        if action.name == "todo_done":
            return self.store.complete_todo(action.argument)
        if action.name == "git_commit":
            return git_commit_all(self.workspace_root, action.argument)
        if action.name == "git_push":
            return git_push(self.workspace_root)
        if action.name == "explain_project":
            return EXPLANATION
        if action.name == "roadmap":
            return ROADMAP
        if action.name == "memory":
            return self.memory.summary()
        return f"Unknown action: {action.name}"

    def interactive(self):
        print("Local Jarvis shell. Type 'help' for commands, 'exit' to quit.")
        while True:
            try:
                user_text = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            action = plan(user_text)
            if action.name == "exit":
                print("Goodbye.")
                break

            if action.needs_confirmation:
                answer = input("This action changes project state. Continue? [y/N] ").strip().lower()
                assume_yes = answer in {"y", "yes", "s", "si"}
            else:
                assume_yes = False

            print(self.handle(user_text, assume_yes=assume_yes))


def main():
    parser = argparse.ArgumentParser(description="Local text agent for the neural visualizer project.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--once", help="Run one command and exit.")
    parser.add_argument("--yes", action="store_true", help="Allow state-changing commands in --once mode.")
    args = parser.parse_args()

    agent = LocalAgent(args.workspace)
    if args.once:
        print(agent.handle(args.once, assume_yes=args.yes))
    else:
        agent.interactive()


if __name__ == "__main__":
    main()
