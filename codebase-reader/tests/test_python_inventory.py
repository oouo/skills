import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "python_inventory.py"
FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "python-agent"


class PythonInventoryTests(unittest.TestCase):
    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_help_documents_read_only_ast_inventory(self) -> None:
        result = self.run_script("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("without importing or executing target modules", result.stdout)
        self.assertIn("--json", result.stdout)

    def test_json_inventory_extracts_required_python_evidence(self) -> None:
        result = self.run_script(str(FIXTURE), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["files_scanned"], 1)
        self.assertIn("not a precise runtime call graph", inventory["disclaimer"])

        file_inventory = inventory["files"][0]
        self.assertEqual(file_inventory["path"], "agent.py")

        symbols = {item["qualname"]: item for item in file_inventory["symbols"]}
        self.assertIn("run_agent", symbols)
        self.assertEqual(symbols["run_agent"]["kind"], "async_function")
        self.assertIn("lookup_tool", symbols)
        self.assertIn("tool('lookup')", symbols["lookup_tool"]["decorators"])
        self.assertIn("FakeProvider.complete", symbols)

        environment_names = {
            item["name"] for item in file_inventory["environment_variables"]
        }
        self.assertEqual(environment_names, {"AGENT_MODE", "MODEL_NAME"})

        calls = file_inventory["candidate_calls"]
        self.assertTrue(
            any(
                call["caller"] == "run_agent"
                and call["callee"] == "provider.complete"
                and call["awaited"]
                for call in calls
            )
        )
        self.assertTrue(
            any(statement["kind"] == "If" for statement in file_inventory["top_level_code"])
        )

    def test_human_output_supports_a_single_file(self) -> None:
        result = self.run_script(str(FIXTURE / "agent.py"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## agent.py", result.stdout)
        self.assertIn("Candidate calls (static):", result.stdout)
        self.assertIn("Environment variables:", result.stdout)

    def test_target_top_level_code_is_never_executed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "must_not_run.py"
            target.write_text(
                "raise RuntimeError('inventory imported the target')\n",
                encoding="utf-8",
            )
            result = self.run_script(str(target), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["files"][0]["top_level_code"][0]["kind"], "Raise")

    def test_syntax_errors_are_reported_without_hiding_other_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "valid.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
            (root / "broken.py").write_text("def broken(:\n", encoding="utf-8")
            result = self.run_script(str(root), "--json")
        self.assertEqual(result.returncode, 1)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["files_scanned"], 2)
        self.assertEqual(
            {item["path"] for item in inventory["files"]},
            {"broken.py", "valid.py"},
        )
        broken = next(item for item in inventory["files"] if item["path"] == "broken.py")
        self.assertEqual(broken["error"]["type"], "SyntaxError")


if __name__ == "__main__":
    unittest.main()
