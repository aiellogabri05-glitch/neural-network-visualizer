import argparse
from pathlib import Path

from agent.tools.editing import (
    append_line_to_file,
    apply_file_change,
    preview_file_change,
    propose_instruction_edit,
    read_edit_target,
    replace_text_in_file,
)
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
from agent.tools.spreadsheet import (
    apply_append_row,
    apply_create_workbook,
    apply_set_cell,
    get_cell_value,
    get_sheet_max_row,
    list_sheets,
    parse_comma_values,
    parse_excel_location,
    preview_append_row,
    preview_create_workbook,
    preview_set_cell,
    read_range,
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
3. Add task mode so the agent tracks the current objective.
4. Add voice only after the text loop feels reliable.
5. Add controlled autonomy with approvals for risky actions.
"""


def parse_replace_argument(argument):
    if not argument or ":" not in argument or "=>" not in argument:
        return None

    file_path, replacement = argument.split(":", 1)
    old_text, new_text = replacement.split("=>", 1)
    file_path = file_path.strip()
    old_text = old_text.strip()
    new_text = new_text.strip()

    if not file_path or not old_text:
        return None

    return file_path, old_text, new_text


def parse_edit_argument(argument):
    if not argument or ":" not in argument:
        return None

    file_path, instruction = argument.split(":", 1)
    file_path = file_path.strip()
    instruction = instruction.strip()

    if not file_path or not instruction:
        return None

    return file_path, instruction


def parse_excel_range_argument(argument):
    if not argument or ":" not in argument:
        return None

    file_path, location = argument.split(":", 1)
    file_path = file_path.strip()
    parsed_location = parse_excel_location(location)

    if not file_path or parsed_location is None:
        return None

    sheet_name, range_ref = parsed_location
    return file_path, sheet_name, range_ref


def parse_excel_set_argument(argument):
    if not argument or ":" not in argument or "=" not in argument:
        return None

    file_path, rest = argument.split(":", 1)
    location, value = rest.split("=", 1)
    file_path = file_path.strip()
    value = value.strip()
    parsed_location = parse_excel_location(location)

    if not file_path or parsed_location is None:
        return None

    sheet_name, cell_ref = parsed_location
    return file_path, sheet_name, cell_ref, value


def parse_excel_create_argument(argument):
    if not argument or ":" not in argument or "=" not in argument:
        return None

    file_path, rest = argument.split(":", 1)
    sheet_name, headers_text = rest.split("=", 1)
    file_path = file_path.strip()
    sheet_name = sheet_name.strip().strip("'").strip('"')
    headers = parse_comma_values(headers_text)

    if not file_path or not sheet_name or not headers:
        return None

    return file_path, sheet_name, headers


def parse_excel_append_argument(argument):
    if not argument or ":" not in argument or "=" not in argument:
        return None

    file_path, rest = argument.split(":", 1)
    sheet_name, values_text = rest.split("=", 1)
    file_path = file_path.strip()
    sheet_name = sheet_name.strip().strip("'").strip('"')
    values = parse_comma_values(values_text)

    if not file_path or not sheet_name or not values:
        return None

    return file_path, sheet_name, values


class LocalAgent:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root).resolve()
        self.memory = SessionMemory()
        self.store = PersistentStore(self.workspace_root)
        self.pending_edit = None
        self.pending_excel_change = None

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
            except ValueError as error:
                response = f"Invalid edit: {error}"
            except RuntimeError as error:
                response = f"Tool unavailable: {error}"
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
            return answer_project_question(self.workspace_root, action.argument, self.memory)
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
        if action.name == "excel_sheets":
            if not action.argument:
                return "Usage: excel sheets <path.xlsx>"
            return list_sheets(self.workspace_root, action.argument)
        if action.name == "excel_create":
            parsed = parse_excel_create_argument(action.argument)
            if parsed is None:
                return "Usage: excel create <path.xlsx>: <Sheet> = <column>, <column>"

            file_path, sheet_name, headers = parsed
            self.pending_excel_change = {
                "operation": "create",
                "path": file_path,
                "sheet": sheet_name,
                "headers": headers,
            }
            preview = preview_create_workbook(self.workspace_root, file_path, sheet_name, headers)
            return f"{preview}\n\nRun `apply excel` to create it."
        if action.name == "excel_read":
            parsed = parse_excel_range_argument(action.argument)
            if parsed is None:
                return "Usage: excel read <path.xlsx>: <Sheet>!<range>"

            file_path, sheet_name, range_ref = parsed
            return read_range(self.workspace_root, file_path, sheet_name, range_ref)
        if action.name == "excel_append_row":
            parsed = parse_excel_append_argument(action.argument)
            if parsed is None:
                return "Usage: excel append <path.xlsx>: <Sheet> = <value>, <value>"

            file_path, sheet_name, values = parsed
            old_max_row = get_sheet_max_row(self.workspace_root, file_path, sheet_name)
            self.pending_excel_change = {
                "operation": "append",
                "path": file_path,
                "sheet": sheet_name,
                "old_max_row": old_max_row,
                "values": values,
            }
            preview = preview_append_row(self.workspace_root, file_path, sheet_name, values)
            return f"{preview}\n\nRun `apply excel` to apply it."
        if action.name == "excel_set_cell":
            parsed = parse_excel_set_argument(action.argument)
            if parsed is None:
                return "Usage: excel set <path.xlsx>: <Sheet>!<cell> = <value>"

            file_path, sheet_name, cell_ref, value = parsed
            old_value = get_cell_value(self.workspace_root, file_path, sheet_name, cell_ref)
            self.pending_excel_change = {
                "operation": "set_cell",
                "path": file_path,
                "sheet": sheet_name,
                "cell": cell_ref,
                "old_value": old_value,
                "new_value": value,
            }
            preview = preview_set_cell(self.workspace_root, file_path, sheet_name, cell_ref, value)
            return f"{preview}\n\nRun `apply excel` to apply it."
        if action.name == "apply_excel_change":
            if self.pending_excel_change is None:
                return (
                    "No pending Excel change. Run `excel create`, "
                    "`excel append`, or `excel set` first."
                )

            change = self.pending_excel_change
            operation = change.get("operation")
            if operation == "create":
                result = apply_create_workbook(
                    self.workspace_root,
                    change["path"],
                    change["sheet"],
                    change["headers"],
                )
                self.pending_excel_change = None
                return result

            if operation == "append":
                current_max_row = get_sheet_max_row(
                    self.workspace_root,
                    change["path"],
                    change["sheet"],
                )
                if current_max_row != change["old_max_row"]:
                    self.pending_excel_change = None
                    return "Pending Excel change was discarded because the sheet changed after the preview."

                result = apply_append_row(
                    self.workspace_root,
                    change["path"],
                    change["sheet"],
                    change["values"],
                )
                self.pending_excel_change = None
                return result

            current_value = get_cell_value(
                self.workspace_root,
                change["path"],
                change["sheet"],
                change["cell"],
            )
            if current_value != change["old_value"]:
                self.pending_excel_change = None
                return "Pending Excel change was discarded because the cell changed after the preview."

            result = apply_set_cell(
                self.workspace_root,
                change["path"],
                change["sheet"],
                change["cell"],
                change["new_value"],
            )
            self.pending_excel_change = None
            return result
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
        if action.name == "edit_file":
            parsed = parse_edit_argument(action.argument)
            if parsed is None:
                return "Usage: edit <path>: <instruction>"

            file_path, instruction = parsed
            old_content = read_edit_target(self.workspace_root, file_path)
            new_content = propose_instruction_edit(self.workspace_root, file_path, instruction)
            diff = preview_file_change(self.workspace_root, file_path, new_content)

            if diff is None:
                self.pending_edit = None
                return "No changes to apply."

            self.pending_edit = {
                "path": file_path,
                "instruction": instruction,
                "old_content": old_content,
                "new_content": new_content,
            }
            return f"Proposed edit for {file_path}:\n{diff}\n\nRun `apply edit` to apply it."

        if action.name == "apply_pending_edit":
            if self.pending_edit is None:
                return "No pending edit. Run `edit <path>: <instruction>` first."

            file_path = self.pending_edit["path"]
            old_content = self.pending_edit["old_content"]
            new_content = self.pending_edit["new_content"]
            current_content = read_edit_target(self.workspace_root, file_path)

            if current_content != old_content:
                self.pending_edit = None
                return "Pending edit was discarded because the file changed after the preview."

            result = apply_file_change(self.workspace_root, file_path, new_content)
            self.pending_edit = None
            return result

        if action.name == "append_to_file":
            if not action.argument or ":" not in action.argument:
                return "Usage: append <path>: <line to add>"

            file_path, new_line = action.argument.split(":", 1)
            file_path = file_path.strip()
            new_line = new_line.strip()

            new_content = append_line_to_file(self.workspace_root, file_path, new_line)
            diff = preview_file_change(self.workspace_root, file_path, new_content)

            if diff is None:
                return "No changes to apply."

            return f"Proposed change:\n{diff}\n\nRun `apply append {action.argument}` to apply it."

        if action.name == "apply_append_to_file":
            if not action.argument or ":" not in action.argument:
                return "Usage: apply append <path>: <line to add>"

            file_path, new_line = action.argument.split(":", 1)
            file_path = file_path.strip()
            new_line = new_line.strip()

            new_content = append_line_to_file(self.workspace_root, file_path, new_line)
            return apply_file_change(self.workspace_root, file_path, new_content)

        if action.name == "replace_in_file":
            parsed = parse_replace_argument(action.argument)
            if parsed is None:
                return "Usage: replace <path>: <old text> => <new text>"

            file_path, old_text, new_text = parsed
            new_content = replace_text_in_file(self.workspace_root, file_path, old_text, new_text)
            diff = preview_file_change(self.workspace_root, file_path, new_content)

            if diff is None:
                return "No changes to apply."

            return f"Proposed change:\n{diff}\n\nRun `apply replace {action.argument}` to apply it."

        if action.name == "apply_replace_in_file":
            parsed = parse_replace_argument(action.argument)
            if parsed is None:
                return "Usage: apply replace <path>: <old text> => <new text>"

            file_path, old_text, new_text = parsed
            new_content = replace_text_in_file(self.workspace_root, file_path, old_text, new_text)
            return apply_file_change(self.workspace_root, file_path, new_content)

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
