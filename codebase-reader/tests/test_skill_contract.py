import ast
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SKILL_ROOT.parent
SKILL_FILE = SKILL_ROOT / "SKILL.md"
REFERENCES = SKILL_ROOT / "references"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", read(path)).strip()


def fixture_text(name: str) -> str:
    root = SKILL_ROOT / "tests" / "fixtures" / name
    return "\n".join(
        read(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_and_lightweight_budget(self) -> None:
        text = read(SKILL_FILE)
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: codebase-reader$")
        self.assertRegex(frontmatter, r"(?m)^description: >-$")
        self.assertRegex(frontmatter, r"(?m)^compatibility: >-$")

        description_match = re.search(
            r"(?ms)^description: >-\n(?P<body>(?:  .+\n)+?)(?=compatibility:)",
            frontmatter,
        )
        self.assertIsNotNone(description_match)
        description = re.sub(r"\s+", " ", description_match.group("body")).strip()
        self.assertLess(len(description.split()), 100)
        self.assertIn("fast, source-grounded orientation", description)
        self.assertIn("deeper analysis workflow", description)

        self.assertLessEqual(len(text.splitlines()), 120)
        reference_lines = sum(
            len(read(path).splitlines()) for path in REFERENCES.glob("*.md")
        )
        self.assertLessEqual(reference_lines, 120)

    def test_every_internal_link_is_relative_and_exists(self) -> None:
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", read(SKILL_FILE))
        self.assertEqual(
            set(links),
            {
                "references/report-format.md",
                "references/runtime-mechanisms.md",
            },
        )
        for link in links:
            self.assertFalse(link.startswith(("/", "file:", "http:", "https:")))
            self.assertTrue((SKILL_ROOT / link).is_file())

    def test_default_path_is_a_concise_chat_reading_map(self) -> None:
        skill = normalized(SKILL_FILE)
        self.assertIn("Answer in chat by default", skill)
        self.assertIn("Trace One Execution Spine", skill)
        self.assertIn("one-paragraph conclusion", skill)
        self.assertIn("recommended source reading order", skill)
        self.assertIn("explicitly requests a persistent or fuller guide", skill)
        self.assertNotIn("S/A/B", skill)
        self.assertNotIn("every top-level subsystem", skill)
        self.assertNotIn("eleven", skill.lower())

    def test_references_are_genuinely_conditional(self) -> None:
        runtime = normalized(REFERENCES / "runtime-mechanisms.md")
        report = normalized(REFERENCES / "report-format.md")
        self.assertIn("Read this file only when indirection", runtime)
        self.assertIn("Read this file only when the user explicitly requests", report)
        self.assertIn("Do not create empty feature sections", report)

    def test_heavy_reference_set_did_not_survive(self) -> None:
        names = {path.name for path in REFERENCES.glob("*.md")}
        self.assertEqual(names, {"report-format.md", "runtime-mechanisms.md"})
        for removed in [
            "analysis-core.md",
            "code-shapes.md",
            "evidence-and-output.md",
            "language-adapters.md",
            "system-types.md",
        ]:
            self.assertFalse((REFERENCES / removed).exists())

    def test_runtime_reference_handles_indirection_without_a_language_whitelist(self) -> None:
        runtime = read(REFERENCES / "runtime-mechanisms.md")
        for marker in [
            "Decorator or annotation",
            "Dependency injection",
            "Registry or plugin",
            "Callback or event",
            "Macro or generated code",
            "Async work",
            "Server and Client Components",
            "tool selection/validation",
            "When the language has no named guidance",
        ]:
            self.assertIn(marker, runtime)

    def test_report_contract_is_short_and_evidence_graded(self) -> None:
        report = read(REFERENCES / "report-format.md")
        for heading in [
            "## 1. 阅读结论",
            "## 2. 分析快照",
            "## 3. 入口与初始化",
            "## 4. 主执行链",
            "## 5. 必读执行单元",
            "## 6. 推荐阅读顺序",
            "## 7. 尚未确认事项",
        ]:
            self.assertIn(heading, report)
        for label in ["Confirmed", "Runtime verified", "Inferred", "Unknown"]:
            self.assertIn(f"`{label}`", report)
        self.assertNotIn("## 8.", report)

    def test_read_only_boundary_and_no_machine_paths(self) -> None:
        documents = [SKILL_FILE, *sorted(REFERENCES.glob("*.md"))]
        skill = normalized(SKILL_FILE)
        self.assertIn(
            "Keep business source, configuration, tests, and dependencies unchanged",
            skill,
        )
        self.assertIn("rather than redesign or refactoring advice", skill)
        for path in documents:
            text = read(path)
            with self.subTest(path=path.name):
                self.assertNotIn("/" + "Users/", text)
                self.assertNotRegex(text, r"[A-Za-z]:\\\\")
                self.assertNotIn("python3 scripts/python_inventory.py", text)

    def test_python_inventory_uses_only_the_standard_library(self) -> None:
        script = SKILL_ROOT / "scripts" / "python_inventory.py"
        tree = ast.parse(read(script), filename=str(script))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        self.assertEqual(
            imported_roots,
            {
                "__future__",
                "argparse",
                "ast",
                "json",
                "os",
                "pathlib",
                "sys",
                "tokenize",
                "typing",
            },
        )
        script_text = read(script)
        self.assertNotIn("importlib", script_text)
        self.assertNotIn("runpy", script_text)
        self.assertNotRegex(script_text, r"\b(?:exec|eval)\(")

    def test_acceptance_fixtures_still_cover_six_ecosystems(self) -> None:
        expectations = {
            "python-agent": [
                "while state.rounds < MAX_ROUNDS",
                "@tool(\"lookup\")",
                "state.messages.append",
            ],
            "nextjs-app": [
                '"use client"',
                '"use server"',
                'runtime = "edge"',
                "export async function POST",
            ],
            "spring-service": [
                "@SpringBootApplication",
                "@Transactional",
                "JpaRepository",
                "@KafkaListener",
            ],
            "go-worker": [
                "func main()",
                "go func()",
                "make(chan",
                "signal.NotifyContext",
            ],
            "rust-library": [
                "pub trait Transport",
                "async fn send",
                ".await?",
                "impl Drop",
            ],
            "elixir-worker": [
                "use Application",
                "use GenServer",
                "Supervisor.start_link",
                "handle_info",
            ],
        }
        for fixture, markers in expectations.items():
            text = fixture_text(fixture)
            for marker in markers:
                with self.subTest(fixture=fixture, marker=marker):
                    self.assertIn(marker, text)

    def test_repository_index_contains_the_skill(self) -> None:
        readme = read(REPOSITORY_ROOT / "README.md")
        self.assertIn("[`codebase-reader`](codebase-reader/)", readme)


if __name__ == "__main__":
    unittest.main()
