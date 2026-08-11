#!/usr/bin/env python3
"""Render a validated trip.json as a WeChat-ready sharing pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
except ModuleNotFoundError:  # Keep --help and py_compile useful without Pillow.
    Image = ImageDraw = ImageFont = PngImagePlugin = None  # type: ignore[assignment]


WIDTH = 1080
HEIGHT = 1440
SAFE = 72
BODY_BOTTOM = 1296
FOOTER_Y = 1314
ROUTE_X = 114
TEXT_X = 168
RIGHT = WIDTH - SAFE
MIN_TEXT_SIZE = 36
SECONDARY_TEXT_SIZE = 39
TIMELINE_TIME_SIZE = 45
CHIP_TEXT_SIZE = 36

COLORS = {
    "canvas": "#F3F7F5",
    "surface": "#FFFFFF",
    "ink": "#18343C",
    "muted": "#465B61",
    "divider": "#CBDAD5",
    "pine": "#0F6B62",
    "river": "#0F6B62",
    "road": "#D89B1D",
    "road_ink": "#6F4A00",
    "road_bg": "#F6E7BD",
    "clay": "#B64232",
    "clay_bg": "#F3D6D1",
}

TRANSPORT_LABELS = {
    "self-drive": "自驾",
    "drive": "自驾",
    "rail": "铁路",
    "flight": "飞机",
    "bus": "巴士",
    "metro": "地铁",
    "ferry": "轮渡",
    "taxi": "出租车",
    "walk": "步行",
}
SEGMENT_LABELS = {
    "travel": "移动",
    "activity": "游览",
    "meal": "用餐",
    "rest": "休息",
    "buffer": "缓冲",
    "checkin": "入住",
}
MEAL_LABELS = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}
EVIDENCE_LABELS = {
    "verified": "已核验",
    "candidate": "待确认",
    "unknown": "待核实",
}
PLAN_LABELS = {
    "fixed": "已固定",
    "planned": "已安排",
    "candidate": "待确认",
}
ACTION_LABELS = {
    "done": "已完成",
    "open": "待处理",
    "not_needed": "无需处理",
}
CHECKLIST_GROUP_LABELS = {
    "now": "现在确认",
    "t-48h": "出发前 48 小时",
    "pack": "随车带上",
}
ASPECT_LABELS = {
    "identity": "名称",
    "location": "位置",
    "route": "路线",
    "duration": "用时",
    "distance": "里程",
    "hours": "营业状态",
    "price": "价格",
    "reservation": "预约",
    "parking": "停车",
    "queue": "排队",
    "policy": "政策",
    "weather": "天气",
    "experience": "体验",
}

FONT_CANDIDATES = (
    (
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        0,
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        2,
    ),
    (
        "/System/Library/Fonts/STHeiti Medium.ttc",
        0,
        "/System/Library/Fonts/STHeiti Medium.ttc",
        0,
    ),
    (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        0,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        0,
    ),
    (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
        0,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
        0,
    ),
    (
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        0,
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        0,
    ),
    ("C:/Windows/Fonts/msyh.ttc", 0, "C:/Windows/Fonts/msyhbd.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0, "C:/Windows/Fonts/simhei.ttf", 0),
)

UTILITY_FONT_CANDIDATES = (
    ("/System/Library/Fonts/Avenir Next Condensed.ttc", 5),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", 0),
    ("C:/Windows/Fonts/bahnschrift.ttf", 0),
)


class RenderError(RuntimeError):
    """A user-actionable rendering failure."""


@dataclass(frozen=True)
class CardSpec:
    kind: str
    slug: str
    title: str
    subtitle: str
    payload: Any
    continuation: int = 1


class FontBook:
    def __init__(
        self,
        regular: Path,
        regular_index: int,
        bold: Path,
        bold_index: int,
        utility: Path | None = None,
        utility_index: int = 0,
    ) -> None:
        self.regular_path = regular
        self.regular_index = regular_index
        self.bold_path = bold
        self.bold_index = bold_index
        self.utility_path = utility or regular
        self.utility_index = utility_index if utility else regular_index
        self._cache: dict[tuple[int, str], Any] = {}

    @classmethod
    def discover(cls) -> "FontBook":
        if ImageFont is None:
            raise RenderError(
                "Pillow is required. Install it in the active Python environment "
                "before running render_wechat.py."
            )
        utility_path: Path | None = None
        utility_index = 0
        for utility, index in UTILITY_FONT_CANDIDATES:
            candidate = Path(utility)
            if candidate.is_file():
                utility_path = candidate
                utility_index = index
                break
        for regular, regular_index, bold, bold_index in FONT_CANDIDATES:
            regular_path = Path(regular)
            bold_path = Path(bold)
            if regular_path.is_file() and bold_path.is_file():
                book = cls(
                    regular_path,
                    regular_index,
                    bold_path,
                    bold_index,
                    utility_path,
                    utility_index,
                )
                try:
                    book.get(42, bold=False)
                    book.get(42, bold=True)
                    book.utility(TIMELINE_TIME_SIZE)
                except OSError:
                    continue
                return book
        raise RenderError(
            "No CJK font was found. Install Noto Sans CJK, Source Han Sans, "
            "PingFang-compatible fonts, or Microsoft YaHei."
        )

    def get(self, size: int, *, bold: bool = False) -> Any:
        role = "bold" if bold else "regular"
        key = (size, role)
        if key not in self._cache:
            path = self.bold_path if bold else self.regular_path
            index = self.bold_index if bold else self.regular_index
            self._cache[key] = ImageFont.truetype(str(path), size=size, index=index)
        return self._cache[key]

    def utility(self, size: int) -> Any:
        key = (size, "utility")
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(
                str(self.utility_path), size=size, index=self.utility_index
            )
        return self._cache[key]

    def manifest_value(self) -> dict[str, str]:
        return {
            "regular": f"{self.regular_path.name}#{self.regular_index}",
            "bold": f"{self.bold_path.name}#{self.bold_index}",
            "utility": f"{self.utility_path.name}#{self.utility_index}",
        }


class TripView:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.places = {
            item["id"]: item
            for item in data.get("places", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.evidence = [
            item for item in data.get("evidence", []) if isinstance(item, dict)
        ]
        self.evidence_by_target: dict[str, list[dict[str, Any]]] = {}
        for item in self.evidence:
            target_id = item.get("target_id")
            if isinstance(target_id, str):
                self.evidence_by_target.setdefault(target_id, []).append(item)
        self.segment_titles: dict[str, str] = {}
        for day in data.get("days", []):
            if not isinstance(day, dict):
                continue
            for segment in day.get("segments", []):
                if (
                    isinstance(segment, dict)
                    and isinstance(segment.get("id"), str)
                    and _text(segment.get("title"))
                ):
                    self.segment_titles[str(segment["id"])] = _public_text(segment["title"])

    def place_name(self, place_id: Any) -> str:
        if isinstance(place_id, str):
            place = self.places.get(place_id)
            if place:
                if _is_private_place(place):
                    public_name = place.get("public_name")
                    if _text(public_name):
                        return _public_text(public_name).strip()
                    return _private_place_label(place)
                if _text(place.get("name")):
                    return _public_text(place["name"]).strip()
        return "地点待核实"

    def target_label(self, target_id: Any) -> str:
        if not isinstance(target_id, str):
            return "相关事项"
        if target_id in self.places:
            return self.place_name(target_id)
        return self.segment_titles.get(target_id, "相关行程")

    def place_status(self, place_id: Any, aspects: set[str] | None = None) -> str:
        if not isinstance(place_id, str):
            return "unknown"
        items = self.evidence_by_target.get(place_id, [])
        if aspects is not None:
            items = [item for item in items if item.get("aspect") in aspects]
        return _combined_evidence_status(items)

    def segment_status(self, segment: dict[str, Any]) -> str | None:
        segment_type = segment.get("type")
        if segment_type == "travel":
            items = [
                item
                for item in self.evidence_by_target.get(str(segment.get("id")), [])
                if item.get("aspect") in {"route", "duration", "distance"}
            ]
        elif segment_type == "meal":
            place_id = segment.get("place_id")
            items = [
                item
                for item in self.evidence_by_target.get(str(place_id), [])
                if item.get("aspect") in {"hours", "price", "parking", "reservation"}
            ]
        elif segment_type == "checkin":
            place_id = segment.get("place_id")
            items = [
                item
                for item in self.evidence_by_target.get(str(place_id), [])
                if item.get("aspect") in {"reservation", "hours"}
            ]
        else:
            items = self.evidence_by_target.get(str(segment.get("id")), [])
        evidence_status = _combined_evidence_status(items)
        if evidence_status != "unknown" or items:
            return EVIDENCE_LABELS[evidence_status]
        return PLAN_LABELS.get(str(segment.get("plan_status")))

    def ordered_route_names(self) -> list[str]:
        route: list[str] = []
        brief = self.data.get("brief", {})
        if isinstance(brief, dict):
            route.append(self.place_name(brief.get("origin_place_id")))
        for day in self.data.get("days", []):
            if not isinstance(day, dict):
                continue
            for segment in day.get("segments", []):
                if not isinstance(segment, dict):
                    continue
                if segment.get("type") == "travel":
                    route.extend(
                        [
                            self.place_name(segment.get("from_place_id")),
                            self.place_name(segment.get("to_place_id")),
                        ]
                    )
                elif segment.get("type") in {"meal", "activity", "checkin"}:
                    route.append(self.place_name(segment.get("place_id")))
        return _dedupe_adjacent([name for name in route if name])

    def overview_route_names(self) -> list[str]:
        brief = self.data.get("brief", {})
        if not isinstance(brief, dict):
            return self.ordered_route_names()
        place_ids: list[Any] = [brief.get("origin_place_id")]
        destinations = brief.get("destination_place_ids", [])
        if isinstance(destinations, list):
            place_ids.extend(destinations)
        names: list[str] = []
        for place_id in place_ids:
            name = self.place_name(place_id)
            if name not in names:
                names.append(name)
        days = [day for day in self.data.get("days", []) if isinstance(day, dict)]
        if days:
            final_name = self.place_name(days[-1].get("end_place_id"))
            if not names or final_name != names[-1]:
                names.append(final_name)
        return names or self.ordered_route_names()


class CardCanvas:
    def __init__(self, fonts: FontBook) -> None:
        self.fonts = fonts
        self.image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
        self.draw = ImageDraw.Draw(self.image)
        self._draw_atlas_ticks()

    def _draw_atlas_ticks(self) -> None:
        for x in range(SAFE, RIGHT + 1, 72):
            self.draw.line((x, 42, x, 54), fill=COLORS["divider"], width=3)
            self.draw.line((x, HEIGHT - 54, x, HEIGHT - 42), fill=COLORS["divider"], width=3)

    def header(
        self,
        trip_title: str,
        card_label: str,
        title: str,
        subtitle: str,
        page: int,
        total: int,
        fixture: bool,
    ) -> int:
        meta_font = self.fonts.get(MIN_TEXT_SIZE, bold=True)
        label = _header_meta_label(self.draw, trip_title, meta_font, 600)
        self.draw.text((SAFE, SAFE), label, font=meta_font, fill=COLORS["pine"])
        counter_prefix = "示例 · " if fixture else ""
        counter = f"{counter_prefix}{card_label}  ·  {page:02d}/{total:02d}"
        self.draw.text(
            (RIGHT, SAFE),
            counter,
            font=meta_font,
            fill=COLORS["muted"],
            anchor="ra",
        )
        y = 126
        title_font, lines = _fit_wrapped(
            self.draw,
            title,
            self.fonts,
            max_width=936,
            start_size=66,
            min_size=48,
            max_lines=2,
            bold=True,
        )
        line_height = int(title_font.size * 1.18)
        y = _draw_lines(
            self.draw,
            (SAFE, y),
            lines,
            title_font,
            COLORS["ink"],
            line_height,
        )
        if subtitle:
            sub_font = self.fonts.get(39)
            sub_lines = _wrap_text(self.draw, subtitle, sub_font, 936)
            if len(sub_lines) > 2:
                sub_lines = sub_lines[:2]
                sub_lines[-1] = _fit_single_line(
                    self.draw, sub_lines[-1] + "…", sub_font, 936
                )
            y = _draw_lines(
                self.draw,
                (SAFE, y + 9),
                sub_lines,
                sub_font,
                COLORS["muted"],
                54,
            )
        return max(294, y + 30)

    def footer(self, verified_at: str, page: int, total: int) -> None:
        self.draw.line((SAFE, FOOTER_Y, RIGHT, FOOTER_Y), fill=COLORS["divider"], width=3)
        font = self.fonts.get(MIN_TEXT_SIZE)
        label = f"核验：{_format_verified_at(verified_at)}"
        self.draw.text((SAFE, FOOTER_Y + 18), label, font=font, fill=COLORS["muted"])
        count = f"{page:02d} / {total:02d}"
        self.draw.text(
            (RIGHT, FOOTER_Y + 18),
            count,
            font=font,
            fill=COLORS["muted"],
            anchor="ra",
        )

    def panel(self, box: tuple[int, int, int, int], *, fill: str = "surface") -> None:
        self.draw.rounded_rectangle(
            box,
            radius=24,
            fill=COLORS[fill],
            outline=COLORS["divider"],
            width=3,
        )

    def status_icon(self, x: int, y: int, style: str, color: str) -> None:
        if style == "verified":
            self.draw.line(
                ((x - 9, y), (x - 2, y + 7), (x + 11, y - 9)),
                fill=color,
                width=5,
                joint="curve",
            )
        elif style == "candidate":
            self.draw.ellipse((x - 10, y - 10, x + 10, y + 10), outline=color, width=4)
        elif style == "unknown":
            self.draw.text(
                (x, y),
                "?",
                font=self.fonts.get(CHIP_TEXT_SIZE, bold=True),
                fill=color,
                anchor="mm",
            )
        elif style == "risk":
            self.draw.line((x, y - 10, x, y + 3), fill=color, width=5)
            self.draw.ellipse((x - 2, y + 8, x + 2, y + 12), fill=color)

    def chip(
        self,
        x: int,
        y: int,
        label: str,
        style: str,
        *,
        align_right: bool = False,
    ) -> int:
        font = self.fonts.get(CHIP_TEXT_SIZE, bold=True)
        styles = {
            "verified": (COLORS["river"], "#FFFFFF"),
            "candidate": (COLORS["road_bg"], COLORS["road_ink"]),
            "unknown": (COLORS["surface"], COLORS["muted"]),
            "risk": (COLORS["clay_bg"], "#7F2D24"),
            "neutral": (COLORS["surface"], COLORS["muted"]),
        }
        background, foreground = styles.get(style, styles["neutral"])
        icon_width = 36 if style != "neutral" else 0
        width = self.chip_width(label, style)
        if align_right:
            x -= width
        box = (x, y, x + width, y + 51)
        self.draw.rounded_rectangle(
            box,
            radius=24,
            fill=background,
            outline=COLORS["divider"] if style in {"unknown", "neutral"} else None,
            width=3,
        )
        text_x = x + 18
        if icon_width:
            self.status_icon(x + 26, y + 25, style, foreground)
            text_x += icon_width
        self.draw.text((text_x, y + 7), label, font=font, fill=foreground)
        return width

    def chip_width(self, label: str, style: str) -> int:
        font = self.fonts.get(CHIP_TEXT_SIZE, bold=True)
        icon_width = 36 if style != "neutral" else 0
        return _text_width(self.draw, label, font) + 36 + icon_width

    def route_spine(self, top: int, bottom: int) -> None:
        self.draw.line((ROUTE_X, top, ROUTE_X, bottom), fill=COLORS["pine"], width=12)

    def route_node(self, y: int, *, style: str = "route") -> None:
        fill = {
            "route": COLORS["pine"],
            "meal": COLORS["road"],
            "risk": COLORS["clay"],
            "verified": COLORS["river"],
        }.get(style, COLORS["pine"])
        self.draw.ellipse(
            (ROUTE_X - 18, y - 18, ROUTE_X + 18, y + 18),
            fill=COLORS["canvas"],
            outline=fill,
            width=9,
        )

    def save(self, path: Path) -> None:
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add(b"sRGB", b"\x00")
        pnginfo.add_text("Software", "china-travel-planner/render_wechat.py")
        self.image.save(path, format="PNG", optimize=True, pnginfo=pnginfo)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _public_text(value: Any) -> str:
    return "" if value is None else str(value)


def _is_private_place(place: dict[str, Any]) -> bool:
    details = place.get("details") if isinstance(place.get("details"), dict) else {}
    return (
        place.get("private") is True
        or details.get("private") is True
        or _text(details.get("privacy"))
    )


def _private_place_label(place: dict[str, Any]) -> str:
    return (
        "私人集合点（已隐藏）"
        if place.get("kind") == "origin"
        else "私人地点（已隐藏）"
    )


def _share_safe_copy(data: dict[str, Any]) -> dict[str, Any]:
    try:
        from render_roadbook import make_share_safe_trip
    except ImportError as exc:
        raise RenderError(
            "Could not import render_roadbook.make_share_safe_trip; sharing is "
            "blocked until the common privacy boundary is available."
        ) from exc
    try:
        safe = make_share_safe_trip(data)
    except (TypeError, ValueError) as exc:
        raise RenderError(f"Could not create a share-safe trip copy: {exc}") from exc
    return safe


def _combined_evidence_status(items: Sequence[dict[str, Any]]) -> str:
    statuses = {item.get("status") for item in items}
    if "unknown" in statuses:
        return "unknown"
    if "candidate" in statuses:
        return "candidate"
    if "verified" in statuses:
        return "verified"
    return "unknown"


def _dedupe_adjacent(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if not result or result[-1] != value:
            result.append(value)
    return result


def _display_units(value: str) -> int:
    units = 0
    for char in value:
        units += 2 if unicodedata.east_asian_width(char) in {"W", "F", "A"} else 1
    return units


def _weighted_chunks(
    items: Sequence[Any], weights: Sequence[int], capacity: int
) -> list[list[Any]]:
    if len(items) != len(weights):
        raise ValueError("items and weights must have equal length")
    chunks: list[list[Any]] = []
    current: list[Any] = []
    current_weight = 0
    for item, raw_weight in zip(items, weights):
        weight = max(1, raw_weight)
        if current and current_weight + weight > capacity:
            chunks.append(current)
            current = []
            current_weight = 0
        current.append(item)
        current_weight += min(weight, capacity)
    if current:
        chunks.append(current)
    return chunks or [[]]


def _text_width(draw: Any, text: str, font: Any) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return int(right - left)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\s+|[A-Za-z0-9]+(?:[./:+-][A-Za-z0-9]+)*|.", text)


def _wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for token in _tokenize(paragraph.strip()):
            if not current and token.isspace():
                continue
            candidate = current + token
            if current and _text_width(draw, candidate.rstrip(), font) > max_width:
                if token and token[0] in "，。；：！？、）》】」』":
                    current += token
                    continue
                if current[-1:] in "（《【「『":
                    opener = current[-1]
                    current = current[:-1].rstrip()
                    if current:
                        lines.append(current)
                    current = opener + token.lstrip()
                else:
                    lines.append(current.rstrip())
                    current = token.lstrip()
                if _text_width(draw, current, font) > max_width:
                    pieces = _split_oversized_token(draw, current, font, max_width)
                    lines.extend(pieces[:-1])
                    current = pieces[-1]
            else:
                current = candidate
        if current:
            lines.append(current.rstrip())
        elif not paragraph:
            lines.append("")
    lines = [re.sub(r"^\s*·\s*", "", line) for line in lines]
    for index in range(1, len(lines)):
        current = lines[index].strip()
        previous = lines[index - 1].rstrip()
        if (
            len(current) == 1
            and len(previous) > 1
            and unicodedata.east_asian_width(current) in {"W", "F", "A"}
            and unicodedata.east_asian_width(previous[-1]) in {"W", "F", "A"}
        ):
            lines[index - 1] = previous[:-1].rstrip()
            lines[index] = previous[-1] + current
    return lines


def _split_oversized_token(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and _text_width(draw, candidate, font) > max_width:
            pieces.append(current)
            current = char
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces or [""]


def _fit_single_line(draw: Any, text: str, font: Any, max_width: int) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    suffix = "…"
    result = text
    while result and _text_width(draw, result + suffix, font) > max_width:
        result = result[:-1]
    return result.rstrip() + suffix


def _header_meta_label(draw: Any, title: str, font: Any, max_width: int) -> str:
    if _text_width(draw, title, font) <= max_width:
        return title
    match = re.match(r"^\s*(HOLD|DRAFT|READY)\b", title, flags=re.IGNORECASE)
    status = match.group(1).upper() if match else ""
    return f"{status} · 行程路书" if status else "行程路书"


def _fit_complete_single_line(
    draw: Any,
    text: str,
    fonts: FontBook,
    *,
    max_width: int,
    start_size: int,
    min_size: int,
    bold: bool,
) -> Any:
    for size in range(start_size, min_size - 1, -3):
        font = fonts.get(size, bold=bold)
        if _text_width(draw, text, font) <= max_width:
            return font
    raise RenderError(f"Text does not fit on one line without truncation: {text!r}")


def _fit_wrapped(
    draw: Any,
    text: str,
    fonts: FontBook,
    *,
    max_width: int,
    start_size: int,
    min_size: int,
    max_lines: int,
    bold: bool,
) -> tuple[Any, list[str]]:
    for size in range(start_size, min_size - 1, -3):
        font = fonts.get(size, bold=bold)
        lines = _wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    raise RenderError(f"Text does not fit without truncation: {text!r}")


def _draw_lines(
    draw: Any,
    origin: tuple[int, int],
    lines: Sequence[str],
    font: Any,
    fill: str,
    line_height: int,
) -> int:
    x, y = origin
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_date(value: Any) -> str:
    parsed = _parse_datetime(value)
    if parsed:
        return f"{parsed.month}月{parsed.day}日"
    if isinstance(value, str):
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d")
            return f"{parsed_date.month}月{parsed_date.day}日"
        except ValueError:
            return value
    return "日期待确认"


def _format_date_range(brief: dict[str, Any]) -> str:
    start = _format_date(brief.get("start_date"))
    end = _format_date(brief.get("end_date"))
    return start if start == end else f"{start}—{end}"


def _format_time(value: Any) -> str:
    parsed = _parse_datetime(value)
    return parsed.strftime("%H:%M") if parsed else "待定"


def _format_verified_at(value: Any) -> str:
    parsed = _parse_datetime(value)
    return parsed.strftime("%m-%d %H:%M") if parsed else "待复核"


def _format_minutes(minutes: Any) -> str:
    if not isinstance(minutes, (int, float)) or isinstance(minutes, bool):
        return "时长待核实"
    rounded = int(round(minutes))
    hours, remainder = divmod(rounded, 60)
    if hours and remainder:
        return f"{hours}小时{remainder}分"
    if hours:
        return f"{hours}小时"
    return f"{remainder}分钟"


def _scheduled_minutes(segment: dict[str, Any]) -> int | None:
    start = _parse_datetime(segment.get("start_at"))
    end = _parse_datetime(segment.get("end_at"))
    if not start or not end:
        return None
    return max(0, int((end - start).total_seconds() // 60))


def _party_label(brief: dict[str, Any]) -> str:
    party = brief.get("party", {})
    if not isinstance(party, dict):
        return "成员待确认"
    parts: list[str] = []
    adults = party.get("adults", 0)
    seniors = party.get("seniors", 0)
    children = party.get("children", [])
    if isinstance(adults, int) and adults:
        parts.append(f"{adults}位成人")
    if isinstance(seniors, int) and seniors:
        parts.append(f"{seniors}位老人")
    if isinstance(children, list) and children:
        parts.append(f"{len(children)}名儿童")
    return "、".join(parts) or "成员待确认"


def _trip_nights(data: dict[str, Any]) -> int:
    days = len(data.get("days", []))
    return max(0, days - 1)


def _trip_duration_label(data: dict[str, Any]) -> str:
    days = len(data.get("days", []))
    nights = _trip_nights(data)
    return f"{days}天{nights}夜" if nights else f"{days}天"


def _compact_route(route: Sequence[str], limit: int = 6) -> list[str]:
    if len(route) <= limit:
        return list(route)
    head = list(route[:3])
    tail = list(route[-2:])
    return head + [f"中途 {len(route) - 5} 站"] + tail


def _summary_route(route: Sequence[str], limit: int = 5) -> str:
    compact = _compact_route(route, limit)
    return " → ".join(compact) if compact else "路线待确认"


def _segment_detail(view: TripView, segment: dict[str, Any]) -> str:
    segment_type = str(segment.get("type"))
    scheduled = _scheduled_minutes(segment)
    duration = _format_minutes(scheduled) if scheduled is not None else "时长待确认"
    if segment_type == "travel":
        mode = TRANSPORT_LABELS.get(str(segment.get("mode")), "移动")
        parts = [mode]
        exact_duration = segment.get("route_duration_minutes")
        if isinstance(exact_duration, (int, float)) and not isinstance(exact_duration, bool):
            parts.append(_format_minutes(exact_duration))
        else:
            parts.append(f"计划{duration}")
        distance = segment.get("distance_km")
        if isinstance(distance, (int, float)) and not isinstance(distance, bool):
            parts.append(f"{distance:g}公里")
        return " · ".join(parts)
    kind = SEGMENT_LABELS.get(segment_type, "安排")
    if segment_type == "meal":
        kind = MEAL_LABELS.get(str(segment.get("meal_kind")), "用餐")
    return f"{kind} · {duration}"


def _segment_weight(view: TripView, segment: dict[str, Any]) -> int:
    title_units = max(1, math.ceil(_display_units(str(segment.get("title", ""))) / 26))
    detail_units = max(1, math.ceil(_display_units(_segment_detail(view, segment)) / 36))
    return 2 + max(0, title_units - 1) + min(1, detail_units - 1)


def _day_subtitle(view: TripView, day: dict[str, Any]) -> str:
    return (
        f"{_format_date(day.get('date'))} · "
        f"{view.place_name(day.get('start_place_id'))} → "
        f"{view.place_name(day.get('end_place_id'))}"
    )


def _venue_items(view: TripView) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    by_place: dict[str, dict[str, Any]] = {}
    for day in view.data.get("days", []):
        if not isinstance(day, dict):
            continue
        day_number = day.get("day", "?")
        for segment in day.get("segments", []):
            if not isinstance(segment, dict) or segment.get("type") not in {"meal", "checkin"}:
                continue
            place_id = segment.get("place_id")
            if not isinstance(place_id, str):
                continue
            place = view.places.get(place_id, {})
            place_kind = place.get("kind") if isinstance(place, dict) else None
            kind = (
                "stay"
                if place_kind == "stay" or segment.get("type") == "checkin"
                else "restaurant"
            )
            meal = MEAL_LABELS.get(str(segment.get("meal_kind")), "用餐")
            slot = "住宿" if segment.get("type") == "checkin" else meal
            occurrence = f"D{day_number} · {slot}"
            if place_id in by_place:
                existing = by_place[place_id]
                if occurrence not in existing["occurrences"]:
                    existing["occurrences"].append(occurrence)
                continue
            item = {
                "day": day_number,
                "kind": kind,
                "slot": slot,
                "occurrences": [occurrence],
                "place_id": place_id,
                "name": view.place_name(place_id),
                "details": place.get("details", {}) if isinstance(place, dict) else {},
            }
            by_place[place_id] = item
            result.append(item)
    return result


def _venue_detail_lines(item: dict[str, Any]) -> list[str]:
    details = item.get("details", {})
    if not isinstance(details, dict):
        details = {}
    lines: list[str] = []
    occurrences = item.get("occurrences")
    if isinstance(occurrences, list) and len(occurrences) > 1:
        lines.append("安排：" + "、".join(str(value) for value in occurrences))
    must_order = details.get("must_order")
    if isinstance(must_order, list):
        dishes = "、".join(str(value).strip() for value in must_order if _text(value))
        if dishes:
            lines.append(f"必点：{dishes}")
    for key, label in (
        ("price_note", "预算"),
        ("parking_note", "停车"),
        ("child_fit", "儿童"),
    ):
        value = details.get(key)
        if _text(value):
            lines.append(f"{label}：{str(value).strip()}")
    backup_for = details.get("backup_for")
    if _text(backup_for):
        lines.append(f"备用：{str(backup_for).strip()}")
    return lines or ["具体信息待确认"]


def _venue_weight(item: dict[str, Any]) -> int:
    units = _display_units(str(item.get("name", "")))
    units += sum(_display_units(line) for line in _venue_detail_lines(item))
    return max(3, 2 + math.ceil(units / 42))


def _checklist_items(data: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen_actions: set[str] = set()
    for item in data.get("checklist", []):
        if not isinstance(item, dict) or not _text(item.get("item")):
            continue
        action = str(item["item"]).strip()
        seen_actions.add(action)
        items.append(
            {
                "group": str(item.get("group", "now")),
                "item": action,
                "status": str(item.get("status", "open")),
            }
        )
    order = {"now": 0, "t-48h": 1, "pack": 2}
    if items:
        return sorted(items, key=lambda item: order.get(item["group"], 9))
    for task in data.get("verification_tasks", []):
        if not isinstance(task, dict) or not _text(task.get("action")):
            continue
        action = str(task["action"]).strip()
        if action in seen_actions or task.get("status") == "not_needed":
            continue
        due = str(task.get("due", ""))
        group = "t-48h" if "48" in due else "now"
        items.append(
            {
                "group": group,
                "item": action,
                "status": str(task.get("status", "open")),
            }
        )
    return sorted(items, key=lambda item: order.get(item["group"], 9))


def _open_attention_items(view: TripView) -> list[str]:
    """Merge every decision and evidence gap into one de-duplicated queue."""
    data = view.data
    result: list[str] = []
    seen: set[str] = set()

    def add(value: Any) -> None:
        if not _text(value):
            return
        text = _public_text(value).strip().rstrip("。")
        key = re.sub(r"\s+", "", text)
        if key and key not in seen:
            seen.add(key)
            result.append(text)

    overview = data.get("overview", {}) if isinstance(data.get("overview"), dict) else {}
    for decision in overview.get("decisions", []):
        if isinstance(decision, dict) and decision.get("status") == "open":
            add(decision.get("question"))

    covered_evidence: set[str] = set()
    tasks = [
        task
        for task in data.get("verification_tasks", [])
        if isinstance(task, dict) and task.get("status") == "open"
    ]
    tasks.sort(key=lambda task: (not bool(task.get("blocking")), str(task.get("due", ""))))
    for task in tasks:
        evidence_id = task.get("evidence_id")
        if isinstance(evidence_id, str):
            covered_evidence.add(evidence_id)
        add(task.get("action"))

    for evidence in data.get("evidence", []):
        if not isinstance(evidence, dict) or evidence.get("status") not in {
            "candidate",
            "unknown",
        }:
            continue
        if evidence.get("id") in covered_evidence:
            continue
        target = view.target_label(evidence.get("target_id"))
        aspect = ASPECT_LABELS.get(str(evidence.get("aspect")), "信息")
        suffix = "待确认" if evidence.get("status") == "candidate" else "待核实"
        add(f"{target}的{aspect}{suffix}")
    return result


def build_card_specs(view: TripView) -> list[CardSpec]:
    data = view.data
    brief = data.get("brief", {}) if isinstance(data.get("brief"), dict) else {}
    route = view.overview_route_names()
    transport = TRANSPORT_LABELS.get(
        str(brief.get("transport")), str(brief.get("transport", "交通待确认"))
    )
    specs = [
        CardSpec(
            kind="overview",
            slug="overview",
            title=str(data.get("title", "行程总览")),
            subtitle=(
                f"{_format_date_range(brief)} · {_party_label(brief)} · "
                f"{transport}"
            ),
            payload={"route": route},
        )
    ]

    for day in data.get("days", []):
        if not isinstance(day, dict):
            continue
        segments = [item for item in day.get("segments", []) if isinstance(item, dict)]
        weights = [_segment_weight(view, segment) for segment in segments]
        chunks = _weighted_chunks(segments, weights, capacity=15)
        for continuation, chunk in enumerate(chunks, start=1):
            day_number = int(day.get("day", len(specs)))
            specs.append(
                CardSpec(
                    kind="day",
                    slug=f"day-{day_number}" + ("" if continuation == 1 else f"-{continuation}"),
                    title=f"D{day_number} · {str(day.get('title', '每日行程'))}",
                    subtitle=_day_subtitle(view, day),
                    payload={"day": day, "segments": chunk},
                    continuation=continuation,
                )
            )

    venues = _venue_items(view)
    venue_chunks = _weighted_chunks(
        venues,
        [_venue_weight(item) for item in venues],
        capacity=18,
    )
    for continuation, chunk in enumerate(venue_chunks, start=1):
        specs.append(
            CardSpec(
                kind="food_and_stay",
                slug="food-and-stay" + ("" if continuation == 1 else f"-{continuation}"),
                title="沿途吃住",
                subtitle="把餐厅和住宿放回路线，而不是放在推荐清单里",
                payload=chunk,
                continuation=continuation,
            )
        )

    checklist = _checklist_items(data)
    checklist_chunks = _weighted_chunks(
        checklist,
        [max(1, math.ceil(_display_units(item["item"]) / 34)) for item in checklist],
        capacity=11,
    )
    for continuation, chunk in enumerate(checklist_chunks, start=1):
        specs.append(
            CardSpec(
                kind="checklist",
                slug="checklist" + ("" if continuation == 1 else f"-{continuation}"),
                title="出发前清单",
                subtitle="现在决定、临行复核、随车携带",
                payload=chunk,
                continuation=continuation,
            )
        )
    return specs


def _render_overview(canvas: CardCanvas, view: TripView, spec: CardSpec, y: int) -> None:
    data = view.data
    route = _compact_route(spec.payload["route"])
    route = route or ["路线待确认"]
    route_top = y + 18
    route_step = 63 if len(route) > 4 else 72
    route_bottom = route_top + route_step * max(0, len(route) - 1)
    canvas.route_spine(route_top, route_bottom)
    route_font = canvas.fonts.get(42, bold=True)
    for index, name in enumerate(route):
        node_y = route_top + index * route_step
        canvas.route_node(node_y)
        canvas.draw.text((TEXT_X, node_y - 27), name, font=route_font, fill=COLORS["ink"])
    y = route_bottom + 54

    days = len(data.get("days", []))
    drive_minutes = 0
    total_distance = 0.0
    distance_known = False
    for day in data.get("days", []):
        if not isinstance(day, dict):
            continue
        for segment in day.get("segments", []):
            if not isinstance(segment, dict) or segment.get("type") != "travel":
                continue
            if segment.get("mode") == "drive":
                drive_minutes += _scheduled_minutes(segment) or 0
            distance = segment.get("distance_km")
            if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                distance_known = True
                total_distance += float(distance)
    metrics = [
        ("行程", _trip_duration_label(data)),
        ("驾驶", _format_minutes(drive_minutes) if drive_minutes else "待核实"),
        ("里程", f"{total_distance:g}公里" if distance_known else "待核实"),
        ("方案", "可执行" if data.get("status") == "ready" else "待确认"),
    ]
    gap = 18
    metrics_width = 936 - gap * (len(metrics) - 1)
    label_font = canvas.fonts.get(MIN_TEXT_SIZE, bold=True)
    minimum_value_font = canvas.fonts.get(MIN_TEXT_SIZE, bold=True)
    box_widths = [
        max(
            _text_width(canvas.draw, label, label_font),
            _text_width(canvas.draw, value, minimum_value_font),
        )
        + 36
        for label, value in metrics
    ]
    spare_width = metrics_width - sum(box_widths)
    if spare_width < 0:
        raise RenderError("Overview metrics do not fit without unreadably small text.")
    for index in range(spare_width):
        box_widths[index % len(box_widths)] += 1
    x = SAFE
    for (label, value), box_width in zip(metrics, box_widths):
        canvas.panel((x, y, x + box_width, y + 105))
        canvas.draw.text((x + 18, y + 12), label, font=label_font, fill=COLORS["muted"])
        value_font = _fit_complete_single_line(
            canvas.draw,
            value,
            canvas.fonts,
            max_width=box_width - 36,
            start_size=42,
            min_size=MIN_TEXT_SIZE,
            bold=True,
        )
        canvas.draw.text((x + 18, y + 54), value, font=value_font, fill=COLORS["ink"])
        x += box_width + gap
    y += 135

    overview = data.get("overview", {}) if isinstance(data.get("overview"), dict) else {}
    attention_items = _open_attention_items(view)[:3]
    risks = [item for item in overview.get("risks", []) if isinstance(item, dict)]
    risks.sort(key=lambda item: ({"high": 0, "medium": 1, "low": 2}.get(item.get("level"), 3)))
    if attention_items:
        attention_font = canvas.fonts.get(SECONDARY_TEXT_SIZE)
        attention_lines = [
            _wrap_text(canvas.draw, question, attention_font, 790)
            for question in attention_items
        ]
        panel_height = (
            66
            + sum(max(1, len(lines)) * 54 for lines in attention_lines)
            + max(0, len(attention_lines) - 1) * 6
        )
        canvas.panel((SAFE, y, RIGHT, y + panel_height))
        canvas.draw.text(
            (SAFE + 24, y + 15),
            "群内待确认",
            font=canvas.fonts.get(SECONDARY_TEXT_SIZE, bold=True),
            fill=COLORS["road_ink"],
        )
        line_y = y + 62
        for lines in attention_lines:
            for line_index, line in enumerate(lines or ["待确认"]):
                prefix = "○ " if line_index == 0 else ""
                canvas.draw.text(
                    (SAFE + (30 if line_index == 0 else 74), line_y),
                    f"{prefix}{line}",
                    font=attention_font,
                    fill=COLORS["ink"],
                )
                line_y += 54
            line_y += 6
        y += panel_height + 18
    if risks and y + 105 <= BODY_BOTTOM:
        risk = risks[0]
        canvas.draw.rounded_rectangle(
            (SAFE, y, RIGHT, y + 96), radius=24, fill=COLORS["clay_bg"]
        )
        risk_title = str(risk.get("title", "风险待复核"))
        risk_label = f"! {risk_title}"
        risk_font = _fit_complete_single_line(
            canvas.draw,
            risk_label,
            canvas.fonts,
            max_width=888,
            start_size=SECONDARY_TEXT_SIZE,
            min_size=MIN_TEXT_SIZE,
            bold=True,
        )
        canvas.draw.text(
            (SAFE + 24, y + 24),
            risk_label,
            font=risk_font,
            fill="#7F2D24",
        )


def _render_day(canvas: CardCanvas, view: TripView, spec: CardSpec, y: int) -> None:
    segments: list[dict[str, Any]] = spec.payload["segments"]
    if not segments:
        canvas.draw.text(
            (TEXT_X, y + 24),
            "当天安排待确认",
            font=canvas.fonts.get(48, bold=True),
            fill=COLORS["ink"],
        )
        return
    title_font = canvas.fonts.get(45, bold=True)
    detail_font = canvas.fonts.get(SECONDARY_TEXT_SIZE)
    time_font = canvas.fonts.utility(TIMELINE_TIME_SIZE)
    available_width = RIGHT - TEXT_X
    time_ranges = [
        (
            f"{_format_time(segment.get('start_at'))}—"
            f"{_format_time(segment.get('end_at'))}"
        )
        for segment in segments
    ]
    time_column_width = max(
        (_text_width(canvas.draw, value, time_font) for value in time_ranges),
        default=0,
    ) + 24
    row_layouts: list[
        tuple[dict[str, Any], str, list[str], list[str], int, str | None, str, int]
    ] = []
    for segment, time_range in zip(segments, time_ranges):
        status = view.segment_status(segment)
        style_key = {
            "已核验": "verified",
            "待确认": "candidate",
            "待核实": "unknown",
        }.get(status or "", "neutral")
        detail_x = TEXT_X
        if status:
            detail_x += canvas.chip_width(status, style_key) + 12
        title_lines = _wrap_text(
            canvas.draw,
            str(segment.get("title", "安排待确认")),
            title_font,
            available_width - time_column_width,
        )
        detail_lines = _wrap_text(
            canvas.draw,
            _segment_detail(view, segment),
            detail_font,
            RIGHT - detail_x,
        )
        row_height = max(124, len(title_lines) * 57 + len(detail_lines) * 51 + 16)
        row_layouts.append(
            (
                segment,
                time_range,
                title_lines,
                detail_lines,
                row_height,
                status,
                style_key,
                detail_x,
            )
        )
    total_height = sum(item[4] for item in row_layouts)
    if y + total_height > BODY_BOTTOM:
        raise RenderError(
            f"Daily card {spec.title!r} overflows after semantic splitting; "
            "shorten descriptive titles or split the source day."
        )
    canvas.route_spine(y + 24, y + total_height - 36)
    for (
        segment,
        time_range,
        title_lines,
        detail_lines,
        row_height,
        status,
        style_key,
        detail_x,
    ) in row_layouts:
        node_y = y + 24
        style = "meal" if segment.get("type") == "meal" else "route"
        canvas.route_node(node_y, style=style)
        canvas.draw.text((TEXT_X, y - 11), time_range, font=time_font, fill=COLORS["pine"])
        title_x = TEXT_X + time_column_width
        _draw_lines(
            canvas.draw,
            (title_x, y - 6),
            title_lines,
            title_font,
            COLORS["ink"],
            57,
        )
        detail_y = y + len(title_lines) * 57
        if status:
            canvas.chip(TEXT_X, detail_y, status, style_key)
        _draw_lines(
            canvas.draw,
            (detail_x, detail_y + 3),
            detail_lines,
            detail_font,
            COLORS["muted"],
            51,
        )
        y += row_height


def _render_food_and_stay(canvas: CardCanvas, view: TripView, spec: CardSpec, y: int) -> None:
    items: list[dict[str, Any]] = spec.payload
    if not items:
        canvas.panel((SAFE, y + 18, RIGHT, y + 220))
        canvas.draw.text(
            (SAFE + 30, y + 48),
            "吃住安排待确认",
            font=canvas.fonts.get(51, bold=True),
            fill=COLORS["ink"],
        )
        canvas.chip(SAFE + 30, y + 126, "待确认", "candidate")
        return
    title_font = canvas.fonts.get(45, bold=True)
    detail_font = canvas.fonts.get(SECONDARY_TEXT_SIZE)
    label_font = canvas.fonts.get(MIN_TEXT_SIZE, bold=True)
    layouts: list[
        tuple[dict[str, Any], str, int, int, list[str], list[str], int]
    ] = []
    for item in items:
        label = f"D{item['day']} · {item['slot']}"
        label_width = _text_width(canvas.draw, label, label_font) + 30
        name_x = SAFE + 24 + label_width + 24
        name_lines = _wrap_text(
            canvas.draw,
            str(item["name"]),
            title_font,
            RIGHT - name_x - 18,
        )
        detail_lines: list[str] = []
        for line in _venue_detail_lines(item):
            detail_lines.extend(_wrap_text(canvas.draw, line, detail_font, 720))
        height = max(162, len(name_lines) * 57 + len(detail_lines) * 51 + 57)
        layouts.append(
            (item, label, label_width, name_x, name_lines, detail_lines, height)
        )
    total_height = sum(layout[6] for layout in layouts) + 18 * (len(layouts) - 1)
    if y + total_height > BODY_BOTTOM:
        raise RenderError(
            f"Food/stay card {spec.title!r} overflows after semantic splitting; "
            "move optional prose out of place.details."
        )
    for item, label, label_width, name_x, name_lines, detail_lines, height in layouts:
        canvas.panel((SAFE, y, RIGHT, y + height))
        is_stay = item["kind"] == "stay"
        canvas.draw.rounded_rectangle(
            (SAFE + 24, y + 24, SAFE + 24 + label_width, y + 69),
            radius=21,
            fill=COLORS["pine"] if is_stay else COLORS["road_bg"],
        )
        canvas.draw.text(
            (SAFE + 39, y + 30),
            label,
            font=label_font,
            fill="#FFFFFF" if is_stay else COLORS["road_ink"],
        )
        name_y = y + 20
        _draw_lines(
            canvas.draw,
            (name_x, name_y),
            name_lines,
            title_font,
            COLORS["ink"],
            57,
        )
        detail_y = y + max(75, len(name_lines) * 57 + 18)
        _draw_lines(
            canvas.draw,
            (SAFE + 30, detail_y),
            detail_lines,
            detail_font,
            COLORS["muted"],
            51,
        )
        relevant = {"reservation", "hours"} if is_stay else {"hours", "price", "parking"}
        status = view.place_status(item["place_id"], relevant)
        canvas.chip(
            RIGHT - 18,
            y + height - 63,
            EVIDENCE_LABELS[status],
            status,
            align_right=True,
        )
        y += height + 18


def _render_checklist(canvas: CardCanvas, spec: CardSpec, y: int) -> None:
    items: list[dict[str, str]] = spec.payload
    if not items:
        canvas.panel((SAFE, y + 18, RIGHT, y + 220))
        canvas.draw.text(
            (SAFE + 30, y + 48),
            "暂无行前事项",
            font=canvas.fonts.get(51, bold=True),
            fill=COLORS["ink"],
        )
        canvas.chip(SAFE + 30, y + 126, "已完成", "verified")
        return
    grouped: dict[str, list[dict[str, str]]] = {}
    for item in items:
        grouped.setdefault(item["group"], []).append(item)
    group_font = canvas.fonts.get(39, bold=True)
    item_font = canvas.fonts.get(39)
    for group in ("now", "t-48h", "pack"):
        group_items = grouped.get(group, [])
        if not group_items:
            continue
        canvas.draw.text(
            (SAFE, y),
            CHECKLIST_GROUP_LABELS[group],
            font=group_font,
            fill=COLORS["pine"],
        )
        y += 54
        for item in group_items:
            lines = _wrap_text(canvas.draw, item["item"], item_font, 615)
            height = max(66, len(lines) * 51 + 15)
            if y + height > BODY_BOTTOM:
                raise RenderError(
                    f"Checklist card {spec.title!r} overflows after semantic splitting."
                )
            canvas.panel((SAFE, y, RIGHT, y + height))
            status = item.get("status", "open")
            style = "verified" if status in {"done", "not_needed"} else "candidate"
            canvas.status_icon(
                SAFE + 42,
                y + 35,
                style,
                COLORS["river"] if style == "verified" else COLORS["road_ink"],
            )
            _draw_lines(
                canvas.draw,
                (SAFE + 84, y + 9),
                lines,
                item_font,
                COLORS["ink"],
                51,
            )
            label = ACTION_LABELS.get(status, "待处理")
            canvas.chip(
                RIGHT - 18,
                y + 11,
                label,
                style,
                align_right=True,
            )
            y += height + 9
        y += 9


def _render_card(
    view: TripView,
    spec: CardSpec,
    fonts: FontBook,
    page: int,
    total: int,
    output: Path,
) -> None:
    labels = {
        "overview": "总览",
        "day": "每日",
        "food_and_stay": "吃住",
        "checklist": "清单",
    }
    canvas = CardCanvas(fonts)
    card_label = labels[spec.kind]
    if spec.continuation > 1:
        card_label = f"{card_label}续{spec.continuation}"
    y = canvas.header(
        str(view.data.get("title", "旅行路书")),
        card_label,
        spec.title,
        spec.subtitle,
        page,
        total,
        bool(view.data.get("fixture")),
    )
    if spec.kind == "overview":
        _render_overview(canvas, view, spec, y)
    elif spec.kind == "day":
        _render_day(canvas, view, spec, y)
    elif spec.kind == "food_and_stay":
        _render_food_and_stay(canvas, view, spec, y)
    elif spec.kind == "checklist":
        _render_checklist(canvas, spec, y)
    else:
        raise RenderError(f"Unknown card type: {spec.kind}")
    canvas.footer(str(view.data.get("last_verified_at", "")), page, total)
    canvas.save(output)


def _summary_text(view: TripView, specs: Sequence[CardSpec]) -> str:
    data = view.data
    brief = data.get("brief", {}) if isinstance(data.get("brief"), dict) else {}
    transport = TRANSPORT_LABELS.get(
        str(brief.get("transport")), str(brief.get("transport", "交通待确认"))
    )
    lines: list[str] = []
    if data.get("fixture"):
        lines.append("【示例数据｜不可用于实际出行】")
    lines.extend(
        [
            f"【{data.get('title', '旅行路书')}｜{_trip_duration_label(data)}{transport}】",
            f"日期：{_format_date_range(brief)}",
            f"成员：{_party_label(brief)}",
            f"路线：{_summary_route(view.overview_route_names())}",
        ]
    )
    attention_items = _open_attention_items(view)[:3]
    if attention_items:
        lines.append("还需群里确认：")
        numbers = "①②③"
        for index, item in enumerate(attention_items):
            lines.append(f"{numbers[index]} {item}")
    day_cards = sum(spec.kind == "day" for spec in specs)
    venue_cards = sum(spec.kind == "food_and_stay" for spec in specs)
    checklist_cards = sum(spec.kind == "checklist" for spec in specs)
    parts = [
        "总览",
        f"每日×{day_cards}",
        f"吃住×{venue_cards}",
        f"清单×{checklist_cards}",
    ]
    lines.append(f"共{len(specs)}张：{' / '.join(parts)}")
    return "\n".join(lines).rstrip() + "\n"


def _validate_source(data: dict[str, Any]) -> None:
    try:
        from validate_trip import validate_trip
    except ImportError as exc:
        raise RenderError(
            "Could not import the bundled validate_trip.py; rendering is blocked "
            "until the validator is available."
        ) from exc
    errors = [issue for issue in validate_trip(data) if issue.severity == "ERROR"]
    if errors:
        preview = "; ".join(
            f"{issue.path} {issue.code} {issue.message}" for issue in errors[:5]
        )
        suffix = "" if len(errors) <= 5 else f"; plus {len(errors) - 5} more"
        raise RenderError(f"trip.json has {len(errors)} validation error(s): {preview}{suffix}")


def _load_trip(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise RenderError(f"trip.json does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderError(f"Could not read trip.json: {exc}") from exc
    if not isinstance(data, dict):
        raise RenderError("trip.json root must be an object")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def _png_has_srgb_chunk(path: Path) -> bool:
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset = 8
    while offset + 12 <= len(payload):
        length = int.from_bytes(payload[offset : offset + 4], "big")
        chunk_type = payload[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        if data_end + 4 > len(payload):
            return False
        if chunk_type == b"sRGB":
            return length == 1 and payload[data_start:data_end] == b"\x00"
        if chunk_type == b"IEND":
            break
        offset = data_end + 4
    return False


def _render_pack_into(data: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fonts = FontBook.discover()
    view = TripView(data)
    specs = build_card_specs(view)
    if len(data.get("days", [])) == 2:
        day_card_count = sum(spec.kind == "day" for spec in specs)
        is_standard_two_day = (
            day_card_count == 2
            and len(_venue_items(view)) <= 5
            and len(_checklist_items(data)) <= 9
        )
        if is_standard_two_day:
            if len(specs) != 5:
                raise RenderError("A non-overflowing two-day trip must render exactly five cards")

    out_dir.mkdir(parents=True, exist_ok=True)
    cards_dir = out_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    card_entries: list[dict[str, Any]] = []
    total = len(specs)
    for page, spec in enumerate(specs, start=1):
        filename = f"{page:02d}-{spec.slug}.png"
        path = cards_dir / filename
        _render_card(view, spec, fonts, page, total, path)
        with Image.open(path) as rendered:
            if rendered.size != (WIDTH, HEIGHT) or rendered.mode != "RGB":
                raise RenderError(f"Rendered PNG failed geometry or color-mode QA: {path}")
        if not _png_has_srgb_chunk(path):
            raise RenderError(f"Rendered PNG is missing its sRGB rendering-intent chunk: {path}")
        card_entries.append(
            {
                "number": page,
                "file": f"cards/{filename}",
                "kind": spec.kind,
                "continuation": spec.continuation,
                "width": WIDTH,
                "height": HEIGHT,
                "mode": "RGB",
                "sha256": _sha256(path),
            }
        )
    summary = _summary_text(view, specs)
    _write_text(out_dir / "summary.txt", summary)
    manifest = {
        "schema_version": "1.0",
        "trip_schema_version": data.get("schema_version"),
        "title": data.get("title"),
        "fixture": bool(data.get("fixture")),
        "source_generated_at": data.get("generated_at"),
        "source_last_verified_at": data.get("last_verified_at"),
        "canvas": {
            "width": WIDTH,
            "height": HEIGHT,
            "aspect_ratio": "3:4",
            "format": "PNG",
            "mode": "RGB",
            "color_space": "sRGB",
        },
        "font": fonts.manifest_value(),
        "summary": "summary.txt",
        "card_count": len(card_entries),
        "cards": card_entries,
    }
    _write_text(
        out_dir / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    return manifest


def _output_is_nonempty(path: Path) -> bool:
    return path.is_dir() and next(path.iterdir(), None) is not None


def render_pack(
    data: dict[str, Any], out_dir: Path, *, force: bool = False
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    if out_dir.is_symlink():
        raise RenderError(f"Output directory must not be a symlink: {out_dir}")
    if out_dir.exists() and not out_dir.is_dir():
        raise RenderError(f"Output path exists and is not a directory: {out_dir}")
    if _output_is_nonempty(out_dir) and not force:
        raise RenderError(
            f"Output directory is not empty: {out_dir}. Use --force to replace it atomically."
        )
    if Image is None:
        raise RenderError(
            "Pillow is required. Install it in the active Python environment "
            "before running render_wechat.py."
        )
    _validate_source(data)
    safe_data = _share_safe_copy(data)

    parent = out_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.tmp-", dir=str(parent)))
    backup: Path | None = None
    try:
        manifest = _render_pack_into(safe_data, temporary)
        if out_dir.exists():
            backup = parent / f".{out_dir.name}.backup-{uuid.uuid4().hex}"
            os.replace(out_dir, backup)
        try:
            os.replace(temporary, out_dir)
        except OSError:
            if backup is not None and backup.exists() and not out_dir.exists():
                os.replace(backup, out_dir)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
            backup = None
        return manifest
    except OSError as exc:
        raise RenderError(f"Could not publish the WeChat pack atomically: {exc}") from exc
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        if backup is not None and backup.exists() and not out_dir.exists():
            os.replace(backup, out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trip_json", type=Path)
    parser.add_argument("--out", required=True, type=Path, dest="out_dir")
    parser.add_argument(
        "--force",
        action="store_true",
        help="atomically replace a non-empty output directory",
    )
    args = parser.parse_args(argv)
    try:
        input_path = args.trip_json.resolve()
        output_path = args.out_dir.resolve()
        if input_path == output_path or output_path in input_path.parents:
            raise RenderError("Output directory must not contain or overwrite trip.json")
        data = _load_trip(args.trip_json)
        try:
            before = args.trip_json.read_bytes()
        except OSError as exc:
            raise RenderError(f"Could not snapshot trip.json before rendering: {exc}") from exc
        manifest = render_pack(data, args.out_dir, force=args.force)
        try:
            after = args.trip_json.read_bytes()
        except OSError as exc:
            raise RenderError(f"Could not verify trip.json after rendering: {exc}") from exc
        if after != before:
            raise RenderError("trip.json changed during rendering; output is not trusted")
    except RenderError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    print(
        f"Rendered {manifest['card_count']} cards, summary.txt, and manifest.json "
        f"to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
