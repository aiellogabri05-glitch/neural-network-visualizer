import tempfile
import unittest
from pathlib import Path

from agent.brain import answer_project_question, rank_chunks
from agent.permissions import PermissionError, resolve_inside_workspace
from agent.planner import plan
from agent.storage import PersistentStore
from agent.tools.filesystem import inspect_path, search_text


class PlannerTests(unittest.TestCase):
    def test_plans_guarded_git_commands(self):
        commit = plan("commit add agent v2")
        push = plan("push")

        self.assertEqual(commit.name, "git_commit")
        self.assertTrue(commit.needs_confirmation)
        self.assertEqual(push.name, "git_push")
        self.assertTrue(push.needs_confirmation)

    def test_plans_memory_commands(self):
        self.assertEqual(plan("remember use safe tools").name, "remember")
        self.assertEqual(plan("recall safe").name, "recall")
        self.assertEqual(plan("todo add add voice").name, "todo_add")


class PermissionTests(unittest.TestCase):
    def test_blocks_paths_outside_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(PermissionError):
                resolve_inside_workspace(temp_dir, "../outside.txt")


class StorageTests(unittest.TestCase):
    def test_persists_memory_and_todos(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = PersistentStore(temp_dir)
            store.remember("project prefers local tools")
            store.add_todo("add voice later")

            reloaded = PersistentStore(temp_dir)
            self.assertIn("local tools", reloaded.recall("local"))
            self.assertIn("add voice later", reloaded.list_todos())


class FilesystemToolTests(unittest.TestCase):
    def test_search_and_inspect_text_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.txt"
            path.write_text("hello agent\n", encoding="utf-8")

            self.assertIn("note.txt:1", search_text(temp_dir, "agent"))
            self.assertIn("Lines: 1", inspect_path(temp_dir, "note.txt"))


class BrainTests(unittest.TestCase):
    def test_ranks_relevant_project_chunks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "README.md"
            path.write_text("The agent has persistent memory and todos.\n", encoding="utf-8")

            chunks = rank_chunks(temp_dir, "how does memory work")

            self.assertEqual(chunks[0].path, "README.md")

    def test_answers_with_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "agent.py"
            path.write_text("The planner routes ask commands.\n", encoding="utf-8")

            answer = answer_project_question(temp_dir, "planner ask commands")

            self.assertIn("Evidence", answer)
            self.assertIn("Relevant points", answer)
            self.assertIn("agent.py", answer)


if __name__ == "__main__":
    unittest.main()
