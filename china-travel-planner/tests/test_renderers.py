from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "wan-nan-roadtrip.json"
SCRIPT = SKILL_ROOT / "scripts" / "render_roadbook.py"
WECHAT_SCRIPT = SKILL_ROOT / "scripts" / "render_wechat.py"
BUNDLE_SCRIPT = SKILL_ROOT / "scripts" / "render_review_bundle.py"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from render_roadbook import make_share_safe_trip, render_html  # noqa: E402
import render_review_bundle  # noqa: E402
import render_wechat  # noqa: E402


def load_fixture() -> dict:
    with FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)


def embedded_trip(document: str) -> dict:
    match = re.search(
        r'<script id="trip-data" type="application/json">(.*?)</script>',
        document,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("trip-data block is missing")
    return json.loads(match.group(1))


def visible_document(document: str) -> str:
    return document.split('<script id="trip-data"', 1)[0]


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted(
        [luminance(foreground), luminance(background)], reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


class RoadbookRendererTests(unittest.TestCase):
    def test_fixture_renders_required_sections_and_responsive_css(self) -> None:
        document = render_html(load_fixture())

        for marker in [
            "皖南川藏线两日亲子自驾",
            "测试数据 · 非真实行程",
            "行程总览",
            "DAY 1",
            "DAY 2",
            "办理入住并结束当日行程",
            "吃住安排",
            "行前清单",
            "核验与来源",
            "来源新鲜度",
            "自驾",
        ]:
            self.assertIn(marker, document)
        self.assertNotIn("出行方式待定", document)
        self.assertIn('name="viewport"', document)
        self.assertIn("@media (max-width: 720px)", document)
        self.assertIn("@media (max-width: 430px)", document)
        self.assertIn("@media print", document)

    def test_h5_has_wechat_mobile_reading_guards(self) -> None:
        document = render_html(load_fixture())

        self.assertIn("viewport-fit=cover", document)
        self.assertIn("env(safe-area-inset-top)", document)
        self.assertIn("env(safe-area-inset-bottom)", document)
        self.assertIn("-webkit-text-size-adjust: 100%", document)
        self.assertIn("body { font-size: 16px; line-height: 1.72; }", document)
        self.assertIn("min-height: 44px", document)
        self.assertIn("-webkit-overflow-scrolling: touch", document)

    def test_h5_review_has_share_metadata_and_day_navigation(self) -> None:
        document = render_html(load_fixture())

        self.assertIn('name="robots" content="noindex,nofollow,noarchive"', document)
        self.assertIn('property="og:type" content="website"', document)
        self.assertIn('property="og:title"', document)
        self.assertIn('property="og:description"', document)
        self.assertIn('aria-label="行程目录"', document)
        self.assertIn('href="#overview"', document)
        self.assertIn('href="#day-1"', document)
        self.assertIn('href="#day-2"', document)
        self.assertIn('href="#checklist"', document)
        self.assertIn('href="#evidence"', document)
        self.assertIn('class="review-spine"', document)
        self.assertIn('D1', document)
        self.assertIn('D2', document)

    def test_evidence_ledger_is_collapsed_without_removing_content(self) -> None:
        document = render_html(load_fixture())

        self.assertIn('<details class="evidence-details">', document)
        self.assertIn('<summary>展开核验账本', document)
        self.assertIn("来源新鲜度", document)

    def test_share_safe_trip_json_is_embedded_without_mutating_input(self) -> None:
        trip = load_fixture()
        before = copy.deepcopy(trip)

        document = render_html(trip)
        embedded = embedded_trip(document)

        self.assertEqual(trip, before)
        self.assertEqual(embedded, make_share_safe_trip(trip))
        private_place = embedded["places"][0]
        self.assertEqual(private_place["name"], "私人集合点（已隐藏）")
        self.assertTrue(private_place["private"])
        self.assertNotIn("details", private_place)
        self.assertEqual(document.count('id="trip-data"'), 1)

    def test_statuses_are_rendered_in_chinese(self) -> None:
        document = visible_document(render_html(load_fixture()))

        for label in [
            "草案",
            "已核验",
            "待确认",
            "待核实",
            "已固定",
            "已规划",
            "待处理",
        ]:
            self.assertIn(label, document)
        for internal_status in [">verified<", ">candidate<", ">unknown<"]:
            self.assertNotIn(internal_status, document)

    def test_html_is_self_contained_and_has_no_executable_script(self) -> None:
        document = render_html(load_fixture())

        self.assertNotIn("<link ", document)
        self.assertNotRegex(document, r"<script[^>]+src=")
        self.assertEqual(document.count("<script"), 1)
        self.assertIn('type="application/json"', document)

    def test_visible_output_redacts_private_and_sensitive_text(self) -> None:
        trip = load_fixture()
        private_place = trip["places"][0]
        private_place.update(
            {
                "private": True,
                "name": "秘密家庭集合点",
                "public_name": "秘密家庭地址",
                "address": "某市秘密路 99 号",
                "coordinates": {"lat": 31.1234, "lon": 118.5678},
                "details": {
                    "private": True,
                    "phone": "13812345678",
                    "note": "门禁口令 SECRET-DOOR",
                },
            }
        )
        trip["subtitle"] = "联系人 13812345678 · 订单号 ABCD-123456"
        trip["days"][0]["segments"][0]["notes"] = [
            "司机证件 11010519900101123X，邮箱 person@example.com"
        ]
        trip["sources"][0]["url"] = (
            "https://example.com/route?safe=keep&xsec_token=TOP-SECRET-TOKEN"
        )
        trip["booking_code"] = "BOOKING-SECRET-42"

        document = render_html(trip)
        visible = visible_document(document)
        embedded = embedded_trip(document)

        self.assertIn("私人集合点（已隐藏）", visible)
        self.assertIn("[已隐藏手机号]", visible)
        self.assertIn("订单号：[已隐藏]", visible)
        self.assertIn("[已隐藏证件号]", visible)
        self.assertIn("[已隐藏邮箱]", visible)
        for secret in [
            "13812345678",
            "ABCD-123456",
            "11010519900101123X",
            "person@example.com",
            "秘密家庭集合点",
            "秘密家庭地址",
            "某市秘密路 99 号",
            "31.1234",
            "118.5678",
            "SECRET-DOOR",
            "TOP-SECRET-TOKEN",
            "BOOKING-SECRET-42",
        ]:
            self.assertNotIn(secret, document)
        self.assertEqual(embedded, make_share_safe_trip(trip))
        self.assertEqual(embedded["booking_code"], "[已隐藏]")
        self.assertNotIn("xsec_token", embedded["sources"][0]["url"])
        self.assertIn("safe=keep", embedded["sources"][0]["url"])
        safe_private_place = embedded["places"][0]
        for key in ["public_name", "address", "coordinates", "details"]:
            self.assertNotIn(key, safe_private_place)

    def test_script_like_text_cannot_break_out_of_trip_data(self) -> None:
        trip = load_fixture()
        trip["title"] = "</script><script>alert('x')</script>"

        document = render_html(trip)

        self.assertEqual(document.count("<script"), 1)
        self.assertNotIn("<script>alert", document)
        self.assertIn("&lt;/script&gt;", document)
        embedded = embedded_trip(document)
        self.assertEqual(embedded, make_share_safe_trip(trip))
        self.assertEqual(embedded["title"], trip["title"])

    def test_unknown_transport_uses_its_public_value(self) -> None:
        trip = load_fixture()
        trip["brief"]["transport"] = "camper-van"

        visible = visible_document(render_html(trip))

        self.assertIn("camper-van", visible)
        self.assertNotIn("出行方式待定", visible)

    def test_cli_writes_output_without_changing_input_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "trip.json"
            input_path.write_bytes(FIXTURE.read_bytes())
            output_path = root / "roadbook.html"
            before = input_path.read_bytes()

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(input_path), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(input_path.read_bytes(), before)
            self.assertTrue(output_path.is_file())
            self.assertEqual(
                embedded_trip(output_path.read_text(encoding="utf-8")),
                make_share_safe_trip(load_fixture()),
            )

    def test_render_html_and_cli_refuse_invalid_fixture(self) -> None:
        trip = load_fixture()
        trip.pop("schema_version")

        with self.assertRaisesRegex(ValueError, r"trip validation failed.*E_REQUIRED"):
            render_html(trip)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "invalid-trip.json"
            input_path.write_text(json.dumps(trip, ensure_ascii=False), encoding="utf-8")
            output_path = root / "roadbook.html"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(input_path), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("trip validation failed", result.stderr)
            self.assertIn("E_REQUIRED", result.stderr)
            self.assertFalse(output_path.exists())

    def test_cli_refuses_to_overwrite_input_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "trip.json"
            input_path.write_bytes(FIXTURE.read_bytes())
            before = input_path.read_bytes()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(input_path),
                    "--output",
                    str(input_path),
                    "--force",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not overwrite", result.stderr)
            self.assertEqual(input_path.read_bytes(), before)


class ReviewBundleTests(unittest.TestCase):
    def test_default_bundle_keeps_upload_guide_outside_public_h5(self) -> None:
        def fake_cards(_data: dict, directory: Path) -> dict:
            (directory / "cards").mkdir(parents=True)
            (directory / "summary.txt").write_text("摘要\n", encoding="utf-8")
            (directory / "manifest.json").write_text("{}\n", encoding="utf-8")
            return {"card_count": 1}

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "2026-08-wannan-chuanzangxian"
            with mock.patch.object(
                render_review_bundle.render_wechat,
                "render_pack",
                side_effect=fake_cards,
            ):
                manifest = render_review_bundle.render_bundle(load_fixture(), output)

            self.assertEqual(manifest["card_count"], 1)
            self.assertTrue((output / "wechat" / "summary.txt").is_file())
            self.assertTrue((output / "h5" / "index.html").is_file())
            self.assertTrue((output / "UPLOAD.md").is_file())
            self.assertFalse((output / "h5" / "UPLOAD.md").exists())

            upload_guide = (output / "UPLOAD.md").read_text(encoding="utf-8")
            public_h5 = (output / "h5" / "index.html").read_text(encoding="utf-8")
            self.assertIn("请你自己完成发布", upload_guide)
            self.assertIn("静态网站托管平台", upload_guide)
            self.assertIn("直接上传", upload_guide)
            self.assertIn("Git 发布", upload_guide)
            self.assertIn("对象存储", upload_guide)
            self.assertIn("复用", upload_guide)
            self.assertIn("travel-roadbook", upload_guide)
            self.assertNotIn("EdgeOne", upload_guide)
            self.assertNotIn("Cloudflare", upload_guide)
            self.assertNotIn("GitHub", upload_guide)
            self.assertNotIn("手动发布说明", public_h5)
            self.assertNotIn("EdgeOne", public_h5)
            self.assertNotIn("Cloudflare", public_h5)
            self.assertNotIn("GitHub", public_h5)

    def test_bundle_cli_reminds_user_to_upload_manually(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "trip.json"
            input_path.write_bytes(FIXTURE.read_bytes())
            output = root / "2026-08-wannan-chuanzangxian"

            with mock.patch.object(
                render_review_bundle,
                "render_bundle",
                return_value={"card_count": 7},
            ):
                stdout = mock.patch("sys.stdout")
                with stdout as stream:
                    result = render_review_bundle.main(
                        [str(input_path), "--out", str(output)]
                    )

            self.assertEqual(result, 0)
            emitted = "".join(call.args[0] for call in stream.write.call_args_list)
            self.assertIn("Upload manually", emitted)
            self.assertIn("UPLOAD.md", emitted)

    def test_bundle_cli_rejects_a_generic_output_directory_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "trip.json"
            input_path.write_bytes(FIXTURE.read_bytes())

            with mock.patch.object(render_review_bundle, "render_bundle") as render:
                result = render_review_bundle.main(
                    [str(input_path), "--out", str(root / "review-bundle")]
                )

            self.assertEqual(result, 2)
            render.assert_not_called()

    def test_bundle_cli_rejects_an_output_month_different_from_start_date(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "trip.json"
            input_path.write_bytes(FIXTURE.read_bytes())

            with mock.patch.object(render_review_bundle, "render_bundle") as render:
                result = render_review_bundle.main(
                    [
                        str(input_path),
                        "--out",
                        str(root / "2026-09-wannan-chuanzangxian"),
                    ]
                )

            self.assertEqual(result, 2)
            render.assert_not_called()


class WeChatRendererTests(unittest.TestCase):
    def test_fixture_uses_shanghai_as_the_public_test_origin(self) -> None:
        trip = load_fixture()
        origin_id = trip["brief"]["origin_place_id"]
        origin = next(place for place in trip["places"] if place["id"] == origin_id)

        self.assertEqual(origin_id, "shanghai-test-origin")
        self.assertIn("上海", origin["name"])

    def test_fixture_splits_dense_days_and_exposes_open_evidence_work(self) -> None:
        trip = load_fixture()
        before = copy.deepcopy(trip)

        safe_trip = render_wechat._share_safe_copy(trip)
        view = render_wechat.TripView(safe_trip)
        cards = render_wechat.build_card_specs(view)
        summary = render_wechat._summary_text(view, cards)
        attention = render_wechat._open_attention_items(view)[:3]

        self.assertEqual(trip, before)
        self.assertEqual(safe_trip, make_share_safe_trip(trip))
        self.assertEqual(len(cards), 7)
        self.assertEqual(
            [card.kind for card in cards],
            [
                "overview",
                "day",
                "day",
                "day",
                "day",
                "food_and_stay",
                "checklist",
            ],
        )
        self.assertEqual(
            [len(card.payload["segments"]) for card in cards if card.kind == "day"],
            [7, 1, 7, 1],
        )
        self.assertFalse(
            any("续2" in card.title for card in cards if card.continuation > 1)
        )
        self.assertTrue(any("午餐" in item and "营业" in item for item in attention))
        self.assertTrue(any("停车" in item for item in attention))
        self.assertIn("午餐", summary)
        self.assertIn("营业", summary)
        self.assertIn("停车", summary)
        self.assertNotIn("中途", summary)
        self.assertIn("青龙湾", summary)
        self.assertIn("桃岭", summary)
        route_line = next(line for line in summary.splitlines() if line.startswith("路线："))
        self.assertEqual(route_line.count("私人集合点（已隐藏）"), 2)

    def test_long_day_splits_instead_of_shrinking_the_card(self) -> None:
        trip = make_share_safe_trip(load_fixture())
        extra = copy.deepcopy(trip["days"][0]["segments"][-1])
        extra["id"] = "d1-extra-long-node"
        extra["title"] = (
            "额外安排的较长行程节点用于验证图卡必须拆页而不能继续缩小正文"
        )
        trip["days"][0]["segments"].append(extra)

        cards = render_wechat.build_card_specs(render_wechat.TripView(trip))
        day_one_cards = [card for card in cards if card.slug.startswith("day-1")]

        self.assertGreaterEqual(len(day_one_cards), 2)
        self.assertEqual(day_one_cards[0].continuation, 1)
        self.assertEqual(day_one_cards[1].continuation, 2)

    def test_hidden_notes_do_not_control_visible_day_card_splitting(self) -> None:
        short = make_share_safe_trip(load_fixture())
        verbose = copy.deepcopy(short)
        for day in verbose["days"]:
            for segment in day["segments"]:
                segment["notes"] = [
                    "这段内部说明很长，但微信日程卡并不会渲染它，因此不能拿它控制拆卡。"
                ]

        short_cards = render_wechat.build_card_specs(render_wechat.TripView(short))
        verbose_cards = render_wechat.build_card_specs(render_wechat.TripView(verbose))

        self.assertEqual(
            [card.slug for card in short_cards if card.kind == "day"],
            [card.slug for card in verbose_cards if card.kind == "day"],
        )

    def test_visible_long_titles_split_before_daily_layout_overflows(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))
        trip = make_share_safe_trip(load_fixture())
        template = copy.deepcopy(trip["days"][0]["segments"][0])
        segments = []
        for index in range(7):
            segment = copy.deepcopy(template)
            segment["id"] = f"dense-visible-segment-{index}"
            segment["title"] = "较长但会被旧权重误判的行车节点"
            segment["plan_status"] = "candidate"
            segments.append(segment)
        trip["days"][0]["segments"] = segments
        view = render_wechat.TripView(trip)
        cards = [
            card
            for card in render_wechat.build_card_specs(view)
            if card.slug.startswith("day-1")
        ]

        for card in cards:
            render_wechat._render_day(
                render_wechat.CardCanvas(fonts),
                view,
                card,
                360,
            )

        self.assertGreaterEqual(len(cards), 2)

    def test_curated_checklist_does_not_expand_every_low_level_task(self) -> None:
        trip = make_share_safe_trip(load_fixture())
        expected = [item["item"] for item in trip["checklist"]]
        for index in range(20):
            trip["verification_tasks"].append(
                {
                    "id": f"nonblocking-detail-{index}",
                    "evidence_id": "ev-ningguo-lunch-hours",
                    "action": f"核验不需要铺进群聊卡片的底层细节 {index}",
                    "due": "T-48h",
                    "blocking": False,
                    "status": "open",
                }
            )

        items = render_wechat._checklist_items(trip)

        self.assertEqual([item["item"] for item in items], expected)
        cards = render_wechat.build_card_specs(render_wechat.TripView(trip))
        self.assertEqual(sum(card.kind == "checklist" for card in cards), 1)

    def test_seven_grouped_checklist_actions_fit_one_readable_card(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))
        trip = make_share_safe_trip(load_fixture())
        trip["checklist"] = [
            {
                "group": group,
                "item": item,
                "status": "open",
                "task_ids": [],
            }
            for group, item in [
                ("now", "先确认车辆是5座还是7座及以上"),
                ("now", "补充儿童年龄、身高和安全座椅需求"),
                ("now", "若坚持不赶路，优先改为三天两晚"),
                ("t-48h", "复核天气、地灾预警与道路通行；强降雨取消山路"),
                ("t-48h", "用公开地图重算全部路段并把休息点落到具体服务区"),
                ("t-48h", "确认住宿、停车及三顿正餐的具体门店与营业状态"),
                ("pack", "儿童安全座椅、雨具、防滑鞋、饮水、晕车和应急用品"),
            ]
        ]
        view = render_wechat.TripView(trip)
        checklist_cards = [
            card for card in render_wechat.build_card_specs(view) if card.kind == "checklist"
        ]

        self.assertEqual(len(checklist_cards), 1)
        render_wechat._render_checklist(
            render_wechat.CardCanvas(fonts),
            checklist_cards[0],
            330,
        )

    def test_chinese_wrapping_avoids_single_character_orphans_and_leading_separators(
        self,
    ) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))
        canvas = render_wechat.CardCanvas(fonts)
        checklist_lines = render_wechat._wrap_text(
            canvas.draw,
            "补充儿童年龄、身高和安全座椅需求",
            fonts.get(39),
            615,
        )
        detail_x = (
            render_wechat.TEXT_X + canvas.chip_width("已安排", "neutral") + 12
        )
        detail_lines = render_wechat._wrap_text(
            canvas.draw,
            "休息 · 沪皖方向第一休息与返程晚餐候选 · 30分钟",
            fonts.get(render_wechat.SECONDARY_TEXT_SIZE),
            render_wechat.RIGHT - detail_x,
        )

        self.assertFalse(len(checklist_lines[-1].strip()) == 1)
        self.assertFalse(any(line.lstrip().startswith("·") for line in detail_lines))

    def test_day_details_start_after_the_measured_status_chip(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))
        trip = make_share_safe_trip(load_fixture())
        evidence = next(
            item
            for item in trip["evidence"]
            if item["target_id"] == "d1-drive-1" and item["aspect"] == "route"
        )
        evidence["status"] = "unknown"
        evidence["source_ids"] = []
        evidence["note"] = "测试状态胶囊布局。"
        segment = trip["days"][0]["segments"][0]
        canvas = render_wechat.CardCanvas(fonts)
        spec = render_wechat.CardSpec(
            kind="day",
            slug="day-layout-test",
            title="日程布局测试",
            subtitle="",
            payload={"day": trip["days"][0], "segments": [segment]},
        )
        detail_origins: list[tuple[int, int]] = []
        original_draw_lines = render_wechat._draw_lines

        def capture_lines(draw, origin, lines, font, fill, line_height):
            if fill == render_wechat.COLORS["muted"]:
                detail_origins.append(origin)
            return original_draw_lines(draw, origin, lines, font, fill, line_height)

        with mock.patch.object(render_wechat, "_draw_lines", side_effect=capture_lines):
            render_wechat._render_day(
                canvas,
                render_wechat.TripView(trip),
                spec,
                360,
            )

        chip_font = fonts.get(render_wechat.CHIP_TEXT_SIZE, bold=True)
        chip_width = (
            render_wechat._text_width(canvas.draw, "待核实", chip_font) + 36 + 36
        )
        self.assertEqual(len(detail_origins), 1)
        self.assertGreaterEqual(
            detail_origins[0][0],
            render_wechat.TEXT_X + chip_width + 12,
        )

    def test_food_and_stay_label_keeps_a_measured_gap_before_the_name(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))

        class DrawSpy:
            def __init__(self, delegate):
                self.delegate = delegate
                self.samples: list[tuple[str, tuple[int, int], object]] = []

            def text(self, xy, value, *args, **kwargs):
                self.samples.append((str(value), xy, kwargs.get("font")))
                return self.delegate.text(xy, value, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self.delegate, name)

        trip = make_share_safe_trip(load_fixture())
        view = render_wechat.TripView(trip)
        spec = next(
            card
            for card in render_wechat.build_card_specs(view)
            if card.kind == "food_and_stay"
        )
        canvas = render_wechat.CardCanvas(fonts)
        spy = DrawSpy(canvas.draw)
        canvas.draw = spy
        render_wechat._render_food_and_stay(canvas, view, spec, 330)

        label = next(sample for sample in spy.samples if sample[0] == "D1 · 午餐")
        venue_name = str(spec.payload[0]["name"])
        name = next(sample for sample in spy.samples if sample[0] == venue_name)
        label_right = label[1][0] + render_wechat._text_width(
            canvas.draw, label[0], label[2]
        )
        self.assertGreaterEqual(name[1][0] - label_right, 24)

    def test_phone_preview_typography_has_readable_weight_size_and_contrast(
        self,
    ) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))

        class DrawSpy:
            def __init__(self, delegate):
                self.delegate = delegate
                self.samples: list[tuple[str, int, str | None]] = []

            def text(self, xy, value, *args, **kwargs):
                font = kwargs.get("font")
                self.samples.append(
                    (str(value), int(getattr(font, "size", 0)), kwargs.get("fill"))
                )
                return self.delegate.text(xy, value, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self.delegate, name)

        trip = make_share_safe_trip(load_fixture())
        segment = trip["days"][0]["segments"][0]
        canvas = render_wechat.CardCanvas(fonts)
        spy = DrawSpy(canvas.draw)
        canvas.draw = spy
        canvas.header(
            trip["title"],
            "每日",
            "D1 · 手机预览测试",
            "8月15日",
            1,
            1,
            False,
        )
        render_wechat._render_day(
            canvas,
            render_wechat.TripView(trip),
            render_wechat.CardSpec(
                kind="day",
                slug="phone-preview-test",
                title="手机预览测试",
                subtitle="",
                payload={"day": trip["days"][0], "segments": [segment]},
            ),
            360,
        )
        canvas.footer(trip["last_verified_at"], 1, 1)

        visible_sizes = [size for text, size, _ in spy.samples if text.strip()]
        detail_sizes = [
            size
            for text, size, fill in spy.samples
            if fill == render_wechat.COLORS["muted"] and "自驾" in text
        ]
        self.assertGreaterEqual(min(visible_sizes), 36)
        self.assertTrue(detail_sizes)
        self.assertGreaterEqual(min(detail_sizes), 39)
        self.assertGreaterEqual(
            contrast_ratio(
                render_wechat.COLORS["muted"], render_wechat.COLORS["canvas"]
            ),
            6.5,
        )
        self.assertNotIn("Light", fonts.manifest_value()["regular"])

    def test_long_header_meta_uses_a_complete_fallback_label(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))

        class DrawSpy:
            def __init__(self, delegate):
                self.delegate = delegate
                self.texts: list[str] = []

            def text(self, xy, text, *args, **kwargs):
                self.texts.append(str(text))
                return self.delegate.text(xy, text, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self.delegate, name)

        canvas = render_wechat.CardCanvas(fonts)
        spy = DrawSpy(canvas.draw)
        canvas.draw = spy
        canvas.header(
            "HOLD｜上海出发皖南川藏线两日亲子自驾发布前复核版本",
            "每日",
            "D1 · 上海出发与宁国东段",
            "8月15日",
            2,
            6,
            False,
        )

        self.assertTrue(spy.texts)
        self.assertNotIn("…", spy.texts[0])
        self.assertIn("HOLD", spy.texts[0])

    def test_overview_driving_metric_is_not_truncated(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))

        class DrawSpy:
            def __init__(self, delegate):
                self.delegate = delegate
                self.texts: list[str] = []

            def text(self, xy, text, *args, **kwargs):
                self.texts.append(str(text))
                return self.delegate.text(xy, text, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self.delegate, name)

        data = {
            "status": "draft",
            "brief": {"origin_place_id": "origin"},
            "places": [{"id": "origin", "name": "上海", "kind": "origin"}],
            "days": [
                {
                    "segments": [
                        {
                            "type": "travel",
                            "mode": "drive",
                            "start_at": "2026-08-15T06:00:00+08:00",
                            "end_at": "2026-08-15T20:20:00+08:00",
                        }
                    ]
                }
            ],
            "overview": {"decisions": [], "risks": []},
            "evidence": [],
            "verification_tasks": [],
        }
        canvas = render_wechat.CardCanvas(fonts)
        spy = DrawSpy(canvas.draw)
        canvas.draw = spy
        spec = render_wechat.CardSpec(
            kind="overview",
            slug="overview-metric-test",
            title="测试",
            subtitle="",
            payload={"route": ["上海"]},
        )

        render_wechat._render_overview(
            canvas,
            render_wechat.TripView(data),
            spec,
            360,
        )

        self.assertIn("14小时20分", spy.texts)
        self.assertFalse(any("14小时" in text and "…" in text for text in spy.texts))

    def test_overview_attention_wraps_without_ellipsis(self) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            fonts = render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))

        class DrawSpy:
            def __init__(self, delegate):
                self.delegate = delegate
                self.texts: list[str] = []

            def text(self, xy, text, *args, **kwargs):
                self.texts.append(str(text))
                return self.delegate.text(xy, text, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self.delegate, name)

        trip = make_share_safe_trip(load_fixture())
        question = "用公开地图选定第一高速休息与返程晚餐候选并核对正式名称和绕行距离"
        trip["overview"]["decisions"] = [
            {"id": "long-question", "question": question, "status": "open"}
        ]
        trip["verification_tasks"] = []
        for evidence in trip["evidence"]:
            evidence["status"] = "verified"
        view = render_wechat.TripView(trip)
        canvas = render_wechat.CardCanvas(fonts)
        spy = DrawSpy(canvas.draw)
        canvas.draw = spy
        spec = render_wechat.CardSpec(
            kind="overview",
            slug="overview-attention-test",
            title="测试",
            subtitle="",
            payload={"route": view.overview_route_names()},
        )

        render_wechat._render_overview(canvas, view, spec, 360)

        drawn = "".join(spy.texts).replace("○ ", "")
        self.assertIn(question, drawn)
        self.assertFalse(any("…" in text for text in spy.texts if text.startswith("○")))

    def test_renderer_receives_only_the_common_share_safe_copy(self) -> None:
        trip = load_fixture()
        private_place = trip["places"][0]
        private_place.update(
            {
                "private": True,
                "name": "秘密家庭集合点",
                "public_name": "秘密家庭地址",
                "address": "某市秘密路 99 号",
                "coordinates": {"lat": 31.1234, "lon": 118.5678},
                "details": {
                    "private": True,
                    "phone": "13812345678",
                    "note": "门禁口令 SECRET-DOOR",
                },
            }
        )
        trip["subtitle"] = "联系人 13812345678 · 订单号 ABCD-123456"
        trip["days"][0]["segments"][0]["notes"] = [
            "司机证件 11010519900101123X，邮箱 person@example.com"
        ]
        trip["booking_code"] = "BOOKING-SECRET-42"
        before = copy.deepcopy(trip)
        captured: dict[str, object] = {}

        def fake_render(data: dict, directory: Path) -> dict:
            captured["data"] = copy.deepcopy(data)
            (directory / "summary.txt").write_text("safe\n", encoding="utf-8")
            return {"card_count": 0}

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "wechat"
            with (
                mock.patch.object(render_wechat, "Image", object()),
                mock.patch.object(render_wechat, "_validate_source"),
                mock.patch.object(render_wechat, "_render_pack_into", side_effect=fake_render),
            ):
                render_wechat.render_pack(trip, output)

        self.assertEqual(trip, before)
        self.assertEqual(captured["data"], make_share_safe_trip(trip))
        serialized = json.dumps(captured["data"], ensure_ascii=False)
        for secret in [
            "13812345678",
            "ABCD-123456",
            "11010519900101123X",
            "person@example.com",
            "秘密家庭集合点",
            "秘密家庭地址",
            "某市秘密路 99 号",
            "31.1234",
            "118.5678",
            "SECRET-DOOR",
            "BOOKING-SECRET-42",
        ]:
            self.assertNotIn(secret, serialized)

    def test_nonempty_output_requires_force_and_keeps_user_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "wechat"
            output.mkdir()
            marker = output / "owned-by-user.txt"
            marker.write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(render_wechat.RenderError, "not empty"):
                render_wechat.render_pack(load_fixture(), output)

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_force_publishes_atomically_and_a_failed_render_keeps_old_output(self) -> None:
        def successful_render(_data: dict, directory: Path) -> dict:
            (directory / "new.txt").write_text("complete", encoding="utf-8")
            return {"card_count": 5}

        def failed_render(_data: dict, directory: Path) -> dict:
            (directory / "partial.txt").write_text("partial", encoding="utf-8")
            raise render_wechat.RenderError("render failed")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "wechat"
            output.mkdir()
            old = output / "old.txt"
            old.write_text("old", encoding="utf-8")
            common_patches = (
                mock.patch.object(render_wechat, "Image", object()),
                mock.patch.object(render_wechat, "_validate_source"),
            )
            with common_patches[0], common_patches[1], mock.patch.object(
                render_wechat, "_render_pack_into", side_effect=failed_render
            ):
                with self.assertRaisesRegex(render_wechat.RenderError, "render failed"):
                    render_wechat.render_pack(load_fixture(), output, force=True)
            self.assertEqual(old.read_text(encoding="utf-8"), "old")
            self.assertFalse((output / "partial.txt").exists())

            with (
                mock.patch.object(render_wechat, "Image", object()),
                mock.patch.object(render_wechat, "_validate_source"),
                mock.patch.object(
                    render_wechat, "_render_pack_into", side_effect=successful_render
                ),
            ):
                manifest = render_wechat.render_pack(load_fixture(), output, force=True)
            self.assertEqual(manifest["card_count"], 5)
            self.assertFalse((output / "old.txt").exists())
            self.assertEqual((output / "new.txt").read_text(encoding="utf-8"), "complete")

    def test_missing_validator_blocks_rendering(self) -> None:
        with mock.patch.dict(sys.modules, {"validate_trip": None}):
            with self.assertRaisesRegex(render_wechat.RenderError, "validate_trip"):
                render_wechat._validate_source(load_fixture())

    def test_pillow_runtime_writes_readable_rgb_srgb_pngs_without_touching_input(
        self,
    ) -> None:
        if render_wechat.Image is None:
            self.skipTest("Pillow is not installed in this Python environment")
        try:
            render_wechat.FontBook.discover()
        except render_wechat.RenderError as exc:
            self.skipTest(str(exc))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "trip.json"
            input_path.write_bytes(FIXTURE.read_bytes())
            before = input_path.read_bytes()
            output = root / "wechat"

            result = subprocess.run(
                [
                    sys.executable,
                    str(WECHAT_SCRIPT),
                    str(input_path),
                    "--out",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(input_path.read_bytes(), before)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            summary = (output / "summary.txt").read_text(encoding="utf-8")
            self.assertEqual(manifest["card_count"], 7)
            self.assertEqual(len(manifest["cards"]), 7)
            self.assertIn("午餐", summary)
            self.assertIn("营业", summary)
            self.assertIn("停车", summary)
            for card in manifest["cards"]:
                path = output / card["file"]
                with render_wechat.Image.open(path) as image:
                    self.assertEqual(image.size, (1080, 1440))
                    self.assertEqual(image.mode, "RGB")
                self.assertTrue(render_wechat._png_has_srgb_chunk(path))


if __name__ == "__main__":
    unittest.main()
