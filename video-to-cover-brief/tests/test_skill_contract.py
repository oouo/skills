#!/usr/bin/env python3

"""Portable contract tests for the video-to-cover-brief skill."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_and_size(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        frontmatter = skill.split("---\n", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: video-to-cover-brief$")
        self.assertRegex(frontmatter, r"(?m)^description:")
        self.assertRegex(frontmatter, r"(?m)^compatibility:")
        self.assertIn("Bash", frontmatter)
        self.assertNotIn("zsh", frontmatter)
        self.assertLessEqual(len(skill.splitlines()), 500)

    def test_validated_contract_and_old_pattern_rejection(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        topbar = (ROOT / "references" / "top-bar-system.md").read_text(
            encoding="utf-8"
        )
        presets = (ROOT / "resources" / "cover-presets.yaml").read_text(
            encoding="utf-8"
        )
        routing = (ROOT / "references" / "preset-routing.md").read_text(
            encoding="utf-8"
        )
        brief = (ROOT / "references" / "brief-contract.md").read_text(
            encoding="utf-8"
        )
        combined = "\n".join((skill, topbar, presets, routing, brief))
        for marker in (
            "1086×1448",
            "centered-adaptive-cream-card",
            "outside_mask_max_pixel_difference: 0",
            "source-material preservation",
            "deterministic-font",
            "render-main-title.sh",
            "uniform-visible-height",
            "source-led-neutral",
            "Content Profile",
        ):
            self.assertIn(marker, combined)
        self.assertIn("split-pill", presets)
        self.assertRegex(presets, r"forbidden_fallbacks:[\s\S]*split-pill")
        self.assertNotIn("glyph_scaling: forbidden", presets)
        self.assertNotIn(
            "Mark this package as the only current release in the project README and\n"
            "   agent rules",
            skill,
        )
        self.assertIn("visible_glyph_height_px: 72", presets)
        renderer = (SCRIPTS / "render-cover-type.sh").read_text()
        self.assertIn("VISIBLE_TEXT_H:-72", renderer)
        self.assertIn("Legacy published covers", topbar)
        self.assertRegex(skill, r"48px.*legacy published-cover value")

    def test_genre_is_a_routing_signal_not_an_eligibility_gate(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        routing = (ROOT / "references" / "preset-routing.md").read_text(
            encoding="utf-8"
        )
        presets = (ROOT / "resources" / "cover-presets.yaml").read_text(
            encoding="utf-8"
        )
        combined = "\n".join((skill, routing, presets))
        self.assertIn("local short video of any subject", skill)
        self.assertRegex(skill, r"Genre\s+never determines eligibility")
        self.assertIn("Presets are adapters behind the routing seam", routing)
        self.assertIn("source-led-neutral:", presets)
        self.assertIn("travel-family:", presets)
        self.assertIn("dog-protagonist:", presets)
        self.assertNotIn("Reject unrelated genres", combined)
        self.assertNotIn("Choose exactly one category", combined)

    def test_eval_file(self) -> None:
        data = json.loads((ROOT / "evals" / "evals.json").read_text("utf-8"))
        self.assertGreaterEqual(len(data["evals"]), 9)
        for item in data["evals"]:
            self.assertIn("prompt", item)
            self.assertIn("expected_output", item)
            self.assertIn("files", item)

    def test_shell_syntax(self) -> None:
        for script in sorted(SCRIPTS.glob("*.sh")):
            subprocess.run(["bash", "-n", str(script)], check=True)

    def _require_raster_font(self) -> pathlib.Path:
        for dependency in ("magick", "hb-shape", "shasum"):
            if not shutil.which(dependency):
                self.skipTest(f"{dependency} is required for raster QA")
        font = os.environ.get("VIDEO_COVER_TEST_FONT")
        if not font or not pathlib.Path(font).is_file():
            self.skipTest("Set VIDEO_COVER_TEST_FONT to a Chinese font for raster QA")
        return pathlib.Path(font)

    def _make_source(self, path: pathlib.Path) -> None:
        subprocess.run(
            [
                "magick",
                "-size",
                "1086x1448",
                "gradient:#19283f-#f4b766",
                "-colorspace",
                "sRGB",
                "-alpha",
                "off",
                "-type",
                "TrueColor",
                "+repage",
                "-define",
                "png:color-type=2",
                str(path),
            ],
            check=True,
        )

    def _outside_max(
        self,
        source: pathlib.Path,
        output: pathlib.Path,
        rectangle: tuple[int, int, int, int],
        tmp_path: pathlib.Path,
    ) -> str:
        x, y, width, height = rectangle
        mask = tmp_path / "outside-mask.png"
        subprocess.run(
            [
                "magick",
                "-size",
                "1086x1448",
                "xc:white",
                "-fill",
                "black",
                "-stroke",
                "none",
                "-draw",
                f"rectangle {x},{y} {x + width - 1},{y + height - 1}",
                "-alpha",
                "off",
                str(mask),
            ],
            check=True,
        )
        return subprocess.check_output(
            [
                "magick",
                str(source),
                str(output),
                "-compose",
                "Difference",
                "-composite",
                "-alpha",
                "off",
                str(mask),
                "-compose",
                "Multiply",
                "-composite",
                "-format",
                "%[fx:maxima]",
                "info:",
            ],
            text=True,
        )

    def _write_hash_manifest(
        self, directory: pathlib.Path, names: list[str], output: pathlib.Path
    ) -> None:
        lines = []
        for name in names:
            digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
            lines.append(f"{digest}  {name}\n")
        output.write_text("".join(lines), encoding="utf-8")

    def _build_release_fixture(
        self, tmp_path: pathlib.Path, font: pathlib.Path
    ) -> tuple[pathlib.Path, pathlib.Path, dict[str, str]]:
        project = tmp_path / "project"
        package = project / "release"
        source_dir = project / "sources"
        meta = package / "meta"
        qa = package / "qa"
        source_dir.mkdir(parents=True)
        meta.mkdir(parents=True)
        qa.mkdir(parents=True)

        source = source_dir / "cover-source.png"
        cover_name = "01-test-cover.png"
        self._make_source(source)
        shutil.copyfile(source, package / cover_name)
        (meta / "SOURCES.tsv").write_text(
            "sequence\tfilename\tvideo_id\ttheme\tsource\tnote\n"
            f"01\t{cover_name}\tvideo-01\ttest\tsources/cover-source.png\tapproved\n",
            encoding="utf-8",
        )
        (meta / "TOPBAR-TEXT.txt").write_text("江苏 · 兴化\n", encoding="utf-8")
        self._write_hash_manifest(package, [cover_name], meta / "SHA256SUMS")

        qa_image = qa / "overview.png"
        shutil.copyfile(source, qa_image)
        self._write_hash_manifest(qa, [qa_image.name], qa / "QA-SHA256SUMS")

        env = dict(
            os.environ,
            PROJECT_ROOT=str(project),
            TOP_FONT=str(font),
            TOP_FONT_SHA256=hashlib.sha256(font.read_bytes()).hexdigest(),
        )
        return project, package, env

    def test_renderer_preserves_everything_outside_topbar(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-skill-test-") as tmp:
            tmp_path = pathlib.Path(tmp)
            source = tmp_path / "source.png"
            output = tmp_path / "output.png"
            self._make_source(source)
            env = dict(os.environ, TOP_FONT=str(font), CARD_WIDTH="700")
            result = subprocess.run(
                [
                    str(SCRIPTS / "render-cover-type.sh"),
                    str(source),
                    str(output),
                    "江苏",
                    "兴化",
                ],
                check=True,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertIn("outside-max=0", result.stdout)
            self.assertIn("visible-text=72px", result.stdout)
            self.assertEqual(
                self._outside_max(source, output, (193, 38, 700, 96), tmp_path),
                "0",
            )

    def test_renderer_rejects_off_canvas_topbar(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-offcanvas-") as tmp:
            tmp_path = pathlib.Path(tmp)
            source = tmp_path / "source.png"
            output = tmp_path / "output.png"
            self._make_source(source)
            env = dict(os.environ, TOP_FONT=str(font), CARD_TOP="1448")
            result = subprocess.run(
                [
                    str(SCRIPTS / "render-cover-type.sh"),
                    str(source),
                    str(output),
                    "江苏",
                    "兴化",
                ],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside the canvas", result.stderr)

    def test_renderer_rejects_pathological_visible_height_scaling(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-ink-height-") as tmp:
            tmp_path = pathlib.Path(tmp)
            source = tmp_path / "source.png"
            output = tmp_path / "output.png"
            self._make_source(source)
            env = dict(os.environ, TOP_FONT=str(font))
            result = subprocess.run(
                [
                    str(SCRIPTS / "render-cover-type.sh"),
                    str(source),
                    str(output),
                    "一",
                ],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source ink height", result.stderr)

    def test_new_main_title_has_a_deterministic_compositor(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-main-title-") as tmp:
            tmp_path = pathlib.Path(tmp)
            source = tmp_path / "source.png"
            output = tmp_path / "output.png"
            repeated_output = tmp_path / "output-repeated.png"
            self._make_source(source)
            env = dict(
                os.environ,
                TITLE_FONT=str(font),
                TITLE_FONT_SHA256=hashlib.sha256(font.read_bytes()).hexdigest(),
                TITLE_POINT_SIZE="116",
                TITLE_FILL="#FFFFFF",
                TITLE_STROKE="#4B285F",
            )
            result = subprocess.run(
                [
                    str(SCRIPTS / "render-main-title.sh"),
                    str(source),
                    str(output),
                    r"春日\n花田",
                    "190",
                ],
                check=True,
                env=env,
                text=True,
                capture_output=True,
            )
            match = re.search(r"title=(\d+)x(\d+)\+(\d+)\+(\d+)", result.stdout)
            self.assertIsNotNone(match)
            width, height, x, y = (int(value) for value in match.groups())
            self.assertEqual(
                self._outside_max(source, output, (x, y, width, height), tmp_path),
                "0",
            )
            subprocess.run(
                [
                    str(SCRIPTS / "render-main-title.sh"),
                    str(source),
                    str(repeated_output),
                    r"春日\n花田",
                    "190",
                ],
                check=True,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), repeated_output.read_bytes())

    def test_release_checker_accepts_complete_package(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-release-pass-") as tmp:
            _, package, env = self._build_release_fixture(pathlib.Path(tmp), font)
            result = subprocess.run(
                [str(SCRIPTS / "check-cover-release.sh"), str(package), "1"],
                check=True,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertIn("provenance=verified", result.stdout)

    def test_release_checker_rejects_extra_png_and_wrong_manifest(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-release-fail-") as tmp:
            _, package, env = self._build_release_fixture(pathlib.Path(tmp), font)
            candidate = package / "candidate.png"
            shutil.copyfile(package / "01-test-cover.png", candidate)
            self._write_hash_manifest(
                package, [candidate.name], package / "meta" / "SHA256SUMS"
            )
            result = subprocess.run(
                [str(SCRIPTS / "check-cover-release.sh"), str(package), "1"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected root-level PNG", result.stderr)

    def test_release_checker_rejects_manifest_for_a_non_cover(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-release-hash-") as tmp:
            _, package, env = self._build_release_fixture(pathlib.Path(tmp), font)
            other = package / "other.txt"
            shutil.copyfile(package / "01-test-cover.png", other)
            self._write_hash_manifest(
                package, [other.name], package / "meta" / "SHA256SUMS"
            )
            result = subprocess.run(
                [str(SCRIPTS / "check-cover-release.sh"), str(package), "1"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must name 01-test-cover.png exactly once", result.stderr)

    def test_release_checker_reports_missing_qa_manifest_cleanly(self) -> None:
        font = self._require_raster_font()
        with tempfile.TemporaryDirectory(prefix="video-cover-release-qa-") as tmp:
            _, package, env = self._build_release_fixture(pathlib.Path(tmp), font)
            (package / "qa" / "QA-SHA256SUMS").unlink()
            result = subprocess.run(
                [str(SCRIPTS / "check-cover-release.sh"), str(package), "1"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("needs at least one qa/*SHA256SUMS", result.stderr)


if __name__ == "__main__":
    unittest.main()
