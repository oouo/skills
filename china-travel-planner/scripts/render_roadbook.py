#!/usr/bin/env python3
"""Render a validated trip.json as a self-contained responsive HTML roadbook."""

from __future__ import annotations

import argparse
import copy
import html
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from validate_trip import validate_trip


EVIDENCE_LABELS = {
    "verified": "已核验",
    "candidate": "待确认",
    "unknown": "待核实",
}
PLAN_LABELS = {
    "fixed": "已固定",
    "planned": "已规划",
    "candidate": "待确认",
}
TRIP_LABELS = {"ready": "当前方案", "draft": "草案"}
ACTION_LABELS = {"open": "待处理", "done": "已完成", "not_needed": "无需处理"}
DECISION_LABELS = {"open": "待确认", "resolved": "已确认"}
SEGMENT_LABELS = {
    "travel": "移动",
    "activity": "游览",
    "meal": "用餐",
    "rest": "休息",
    "buffer": "缓冲",
    "checkin": "入住",
}
MODE_LABELS = {
    "drive": "自驾",
    "self-drive": "自驾",
    "rental-car": "租车自驾",
    "mixed": "多方式联运",
    "rail": "铁路",
    "flight": "航班",
    "bus": "巴士",
    "metro": "地铁",
    "ferry": "轮渡",
    "taxi": "出租车",
    "walk": "步行",
}
MEAL_LABELS = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}
ASPECT_LABELS = {
    "identity": "名称",
    "location": "位置",
    "route": "路线",
    "duration": "用时",
    "distance": "距离",
    "hours": "营业时间",
    "price": "价格",
    "reservation": "预约",
    "parking": "停车",
    "queue": "排队",
    "policy": "政策",
    "weather": "天气",
    "experience": "体验",
}
SOURCE_LABELS = {
    "official": "官方",
    "map": "地图",
    "transport": "交通运营方",
    "first_party": "一手售卖方",
    "weather": "气象机构",
    "ugc": "近期用户经验",
    "local_media": "当地媒体",
    "user": "用户提供",
    "other": "其他",
}
CHECKLIST_LABELS = {"now": "现在确认", "t-48h": "出发前 48 小时", "pack": "随身准备"}
DETAIL_LABELS = {
    "must_order": "建议菜品",
    "price_note": "价格",
    "parking_note": "停车",
    "child_fit": "亲子适配",
    "backup_for": "备选关系",
}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "accesskey",
    "access_key",
    "apikey",
    "api_key",
    "auth",
    "authorization",
    "code",
    "cookie",
    "credential",
    "key",
    "password",
    "secret",
    "sig",
    "sign",
    "session",
    "session_id",
    "signature",
    "token",
    "xsec_token",
}
SENSITIVE_QUERY_SUFFIXES = (
    "auth",
    "cookie",
    "credential",
    "key",
    "password",
    "secret",
    "session",
    "signature",
    "token",
)
SENSITIVE_FIELD_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "booking_code",
    "booking_id",
    "booking_no",
    "booking_number",
    "booking_reference",
    "confirmation_code",
    "confirmation_id",
    "confirmation_no",
    "confirmation_number",
    "cookie",
    "credential",
    "document_number",
    "email",
    "email_address",
    "id_card",
    "id_card_number",
    "identity_document_number",
    "identity_number",
    "id_number",
    "mobile",
    "mobile_number",
    "order_code",
    "order_id",
    "order_no",
    "order_number",
    "passport",
    "passport_number",
    "password",
    "phone",
    "phone_number",
    "reservation_code",
    "reservation_id",
    "reservation_no",
    "reservation_number",
    "reservation_reference",
    "secret",
    "session",
    "session_id",
    "tel",
    "telephone",
    "token",
}
SENSITIVE_FIELD_SUFFIXES = (
    "booking_code",
    "booking_id",
    "booking_no",
    "booking_number",
    "booking_reference",
    "confirmation_code",
    "confirmation_id",
    "confirmation_no",
    "confirmation_number",
    "document_number",
    "email",
    "email_address",
    "id_card",
    "id_card_number",
    "id_number",
    "identity_number",
    "mobile",
    "mobile_number",
    "order_code",
    "order_id",
    "order_no",
    "order_number",
    "passport",
    "passport_number",
    "phone",
    "phone_number",
    "reservation_code",
    "reservation_id",
    "reservation_no",
    "reservation_number",
    "reservation_reference",
    "tel",
    "telephone",
)
SENSITIVE_FIELD_NAMES_ZH = {
    "手机号",
    "电话号码",
    "联系电话",
    "邮箱",
    "电子邮箱",
    "证件号",
    "身份证号",
    "护照号",
    "订单号",
    "预订号",
    "确认号",
}
PRIVATE_PLACE_FIELDS = {
    "address",
    "coordinate",
    "coordinates",
    "detail",
    "description",
    "details",
    "display_name",
    "formatted_address",
    "geo",
    "geometry",
    "lat",
    "latitude",
    "lng",
    "location",
    "longitude",
    "name",
    "notes",
    "position",
    "public_name",
}
SENSITIVE_TEXT_PATTERNS = (
    (re.compile(r"(?<!\d)1[3-9](?:[\s-]?\d){9}(?!\d)"), "[已隐藏手机号]"),
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[已隐藏证件号]"),
    (
        re.compile(
            r"(?i)(订单号|预订号|确认号|booking|reservation|confirmation)"
            r"\s*[:：#]?\s*[^\s,，。;；]+"
        ),
        r"\1：[已隐藏]",
    ),
    (
        re.compile(r"(?i)(证件号|身份证号|护照号)\s*[:：#]?\s*[A-Z0-9-]{4,}"),
        r"\1：[已隐藏]",
    ),
    (
        re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Z]{2,}(?![\w.-])"),
        "[已隐藏邮箱]",
    ),
)
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?P<prefix>(?:^|[?&;\s])(?:access[_-]?token|api[_-]?key|auth(?:orization)?|"
    r"cookie|credential|password|secret|session(?:[_-]?id)?|sig(?:nature)?|token|"
    r"xsec[_-]?token)=)[^&;\s]+"
)


CSS = r"""
:root {
  color-scheme: light;
  --pine-950: #102a26;
  --pine-800: #19483f;
  --mist-50: #f6f7f2;
  --mist-100: #ecefe8;
  --ink: #1b2825;
  --muted: #65716c;
  --road: #e4b33c;
  --clay: #c96743;
  --river: #277a92;
  --line: #d9ded6;
  --surface: rgba(255, 255, 255, .92);
  --shadow: 0 18px 50px rgba(16, 42, 38, .10);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    radial-gradient(circle at 8% 0%, rgba(228, 179, 60, .15), transparent 28rem),
    linear-gradient(180deg, #edf1e9 0, var(--mist-50) 30rem);
  color: var(--ink);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  line-height: 1.62;
}
a { color: var(--river); text-underline-offset: .18em; }
.shell { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 64px; }
.hero {
  position: relative;
  overflow: hidden;
  padding: clamp(28px, 6vw, 70px);
  border-radius: 30px;
  color: white;
  background: linear-gradient(135deg, var(--pine-950), var(--pine-800));
  box-shadow: var(--shadow);
}
.hero::after {
  content: "";
  position: absolute;
  width: 320px;
  height: 320px;
  right: -120px;
  bottom: -180px;
  border: 28px solid rgba(228, 179, 60, .28);
  border-radius: 50%;
}
.eyebrow { margin: 0 0 10px; color: #dce7dd; font-size: .86rem; letter-spacing: .12em; }
h1, h2, h3, p { margin-top: 0; }
h1 { max-width: 780px; margin-bottom: 8px; font-size: clamp(2rem, 7vw, 4.6rem); line-height: 1.08; }
.subtitle { max-width: 720px; margin-bottom: 22px; color: #dfe8e2; font-size: 1.05rem; }
.hero-meta, .route-strip, .badge-row { display: flex; flex-wrap: wrap; gap: 9px; }
.hero-meta span, .route-strip span {
  padding: 7px 11px;
  border: 1px solid rgba(255,255,255,.24);
  border-radius: 999px;
  background: rgba(255,255,255,.08);
}
.fixture-banner, .privacy-note {
  margin: 16px 0 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: #fff4cf;
  color: #654c0c;
  font-weight: 700;
}
main { display: grid; gap: 22px; margin-top: 22px; }
.panel {
  padding: clamp(20px, 4vw, 34px);
  border: 1px solid rgba(16,42,38,.08);
  border-radius: 24px;
  background: var(--surface);
  box-shadow: 0 12px 32px rgba(16,42,38,.055);
}
.section-head { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
.section-head h2 { margin-bottom: 6px; font-size: clamp(1.45rem, 3vw, 2rem); }
.section-kicker { color: var(--muted); font-size: .9rem; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.mini-card {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(246,247,242,.72);
}
.mini-card h3 { margin-bottom: 7px; font-size: 1.04rem; }
.mini-card p:last-child, .mini-card ul:last-child { margin-bottom: 0; }
.muted { color: var(--muted); }
.badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: .78rem;
  font-weight: 750;
  line-height: 1.5;
}
.verified, .ready, .fixed, .done, .resolved { background: #d9edf3; color: #155c72; }
.candidate, .planned, .open { background: #fff0bd; color: #745711; }
.unknown, .draft, .high { background: #f8ddd2; color: #8a3f29; }
.medium { background: #ffedc8; color: #765319; }
.low, .not_needed { background: #e6ebe4; color: #53605a; }
.day { position: relative; }
.timeline { position: relative; display: grid; gap: 13px; margin-top: 18px; padding-left: 22px; }
.timeline::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 99px;
  background: linear-gradient(var(--road), var(--pine-800));
}
.segment {
  position: relative;
  padding: 16px 16px 15px;
  border: 1px solid var(--line);
  border-radius: 17px;
  background: #fff;
}
.segment::before {
  content: "";
  position: absolute;
  left: -22px;
  top: 23px;
  width: 12px;
  height: 12px;
  border: 3px solid white;
  border-radius: 50%;
  background: var(--road);
  box-shadow: 0 0 0 1px var(--road);
}
.segment-top { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 7px; }
.segment-time { font-variant-numeric: tabular-nums; font-weight: 800; color: var(--pine-800); }
.segment h3 { margin-bottom: 6px; }
.facts { display: flex; flex-wrap: wrap; gap: 7px 12px; margin-top: 9px; color: var(--muted); font-size: .9rem; }
.clean-list { margin: 8px 0 0; padding-left: 1.2rem; }
.source-list { display: grid; gap: 9px; }
.source-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 11px 0; border-bottom: 1px solid var(--line); }
.source-row:last-child { border-bottom: 0; }
footer { padding: 24px 6px 0; color: var(--muted); font-size: .86rem; }
.empty { margin-bottom: 0; color: var(--muted); }
@media (max-width: 720px) {
  .shell { width: min(100% - 20px, 1120px); padding-top: 10px; }
  .hero { border-radius: 20px; }
  .panel { border-radius: 18px; }
  .grid { grid-template-columns: 1fr; }
  .section-head { align-items: flex-start; flex-direction: column; gap: 0; }
}
@media print {
  body { background: white; }
  .shell { width: 100%; padding: 0; }
  .hero, .panel { box-shadow: none; break-inside: avoid; }
  .panel { border-color: #bbb; }
  .day { break-before: page; }
  a { color: inherit; text-decoration: none; }
}
"""


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _public_text(value: Any) -> str:
    text = "" if value is None else str(value)
    for pattern, replacement in SENSITIVE_TEXT_PATTERNS:
        text = pattern.sub(replacement, text)
    text = SENSITIVE_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group('prefix')}[已隐藏]",
        text,
    )
    return text


def _escape(value: Any) -> str:
    return html.escape(_public_text(value), quote=True)


def _label(mapping: dict[str, str], value: Any, fallback: str = "待补充") -> str:
    return mapping.get(str(value), fallback)


def _transport_label(value: Any) -> str:
    public_value = _public_text(value).strip()
    if not public_value:
        return "出行方式待定"
    return MODE_LABELS.get(public_value, public_value)


def _badge(value: Any, mapping: dict[str, str]) -> str:
    status = str(value)
    return f'<span class="badge {_escape(status)}">{_escape(_label(mapping, status))}</span>'


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_time(value: Any) -> str:
    parsed = _parse_datetime(value)
    return parsed.strftime("%H:%M") if parsed else _public_text(value)


def _format_date(value: Any) -> str:
    if not isinstance(value, str):
        return "日期待定"
    try:
        parsed = datetime.fromisoformat(value).date()
    except ValueError:
        return _public_text(value)
    return f"{parsed.year}年{parsed.month}月{parsed.day}日"


def _date_range(brief: dict[str, Any]) -> str:
    start = _format_date(brief.get("start_date"))
    end = _format_date(brief.get("end_date"))
    return start if start == end else f"{start}—{end}"


def _party_text(brief: dict[str, Any]) -> str:
    party = _as_dict(brief.get("party"))
    parts: list[str] = []
    adults = party.get("adults")
    seniors = party.get("seniors")
    children = _as_list(party.get("children"))
    if isinstance(adults, int) and adults:
        parts.append(f"{adults}位成人")
    if children:
        parts.append(f"{len(children)}位儿童")
    if isinstance(seniors, int) and seniors:
        parts.append(f"{seniors}位长辈")
    return " · ".join(parts) or "成员待确认"


def _is_private(place: dict[str, Any]) -> bool:
    details = _as_dict(place.get("details"))
    return (
        place.get("private") is True
        or details.get("private") is True
        or bool(details.get("privacy"))
    )


def _place_name(place: dict[str, Any] | None) -> str:
    if not place:
        return "地点待补充"
    if _is_private(place):
        kind = place.get("kind")
        return "私人集合点（已隐藏）" if kind == "origin" else "私人地点（已隐藏）"
    return _public_text(place.get("public_name") or place.get("name") or "地点待补充")


def _normalized_key(value: Any) -> str:
    snake_case = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value))
    return re.sub(r"[^a-z0-9]+", "_", snake_case.lower()).strip("_")


def _is_sensitive_field_key(value: Any) -> bool:
    raw_value = str(value).strip()
    if raw_value in SENSITIVE_FIELD_NAMES_ZH:
        return True
    normalized = _normalized_key(raw_value)
    if normalized in SENSITIVE_FIELD_KEYS:
        return True
    return any(normalized.endswith(f"_{suffix}") for suffix in SENSITIVE_FIELD_SUFFIXES)


def _is_sensitive_query_key(value: Any) -> bool:
    if _is_sensitive_field_key(value):
        return True
    normalized = _normalized_key(value)
    if normalized in SENSITIVE_QUERY_KEYS:
        return True
    return any(normalized.endswith(f"_{suffix}") for suffix in SENSITIVE_QUERY_SUFFIXES)


def _safe_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password:
        return None
    safe_query = [
        (key, _public_text(val))
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_sensitive_query_key(key)
    ]
    return urlunparse(
        parsed._replace(
            path=_public_text(parsed.path),
            query=urlencode(safe_query),
            fragment="",
        )
    )


def _share_safe_string(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        return _safe_url(value) or "[已隐藏链接]"
    return _public_text(value)


def _redact_private_place(place: dict[str, Any]) -> None:
    kind = place.get("kind")
    for key in list(place):
        if _normalized_key(key) in PRIVATE_PLACE_FIELDS:
            del place[key]
    place["name"] = "私人集合点（已隐藏）" if kind == "origin" else "私人地点（已隐藏）"
    place["private"] = True


def _sanitize_share_value(value: Any, *, field_name: str | None = None) -> Any:
    if field_name is not None and _is_sensitive_field_key(field_name):
        return "[已隐藏]"
    if isinstance(value, dict):
        return {
            key: _sanitize_share_value(child, field_name=str(key))
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_share_value(item) for item in value]
    if isinstance(value, str):
        return _share_safe_string(value)
    return value


def make_share_safe_trip(trip: dict[str, Any]) -> dict[str, Any]:
    """Return a share-safe deep copy while preserving the source object."""

    if not isinstance(trip, dict):
        raise TypeError("trip must be a JSON object")
    safe_trip = copy.deepcopy(trip)
    for place in _as_list(safe_trip.get("places")):
        if isinstance(place, dict) and _is_private(place):
            _redact_private_place(place)
    sanitized = _sanitize_share_value(safe_trip)
    if not isinstance(sanitized, dict):  # pragma: no cover - guarded by the input check
        raise TypeError("trip must be a JSON object")
    return sanitized


def _ensure_renderable(trip: dict[str, Any]) -> None:
    issues = validate_trip(copy.deepcopy(trip))
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    if not errors:
        return
    details = "; ".join(
        f"{issue.path} {issue.code} {issue.message}"
        for issue in errors[:5]
    )
    remainder = f"; and {len(errors) - 5} more" if len(errors) > 5 else ""
    raise ValueError(
        f"trip validation failed with {len(errors)} error(s): {details}{remainder}"
    )


def _embedded_json(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    return (
        payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


class RoadbookRenderer:
    def __init__(self, trip: dict[str, Any]) -> None:
        self.trip = trip
        self.brief = _as_dict(trip.get("brief"))
        self.overview = _as_dict(trip.get("overview"))
        self.places = {
            str(place.get("id")): place
            for place in _as_list(trip.get("places"))
            if isinstance(place, dict) and place.get("id")
        }
        self.sources = {
            str(source.get("id")): source
            for source in _as_list(trip.get("sources"))
            if isinstance(source, dict) and source.get("id")
        }
        self.evidence = [
            item for item in _as_list(trip.get("evidence")) if isinstance(item, dict)
        ]
        self.evidence_by_target: dict[str, list[dict[str, Any]]] = {}
        for item in self.evidence:
            target = item.get("target_id")
            if target:
                self.evidence_by_target.setdefault(str(target), []).append(item)
        self.target_names = self._build_target_names()

    def _build_target_names(self) -> dict[str, str]:
        names = {place_id: _place_name(place) for place_id, place in self.places.items()}
        for day in _as_list(self.trip.get("days")):
            if not isinstance(day, dict):
                continue
            for segment in _as_list(day.get("segments")):
                if isinstance(segment, dict) and segment.get("id"):
                    names[str(segment["id"])] = _public_text(segment.get("title") or segment["id"])
        for collection in (self.overview.get("decisions"), self.overview.get("risks")):
            for item in _as_list(collection):
                if isinstance(item, dict) and item.get("id"):
                    names[str(item["id"])] = _public_text(
                        item.get("question") or item.get("title") or item["id"]
                    )
        return names

    def render(self) -> str:
        body = "".join(
            [
                self._render_hero(),
                '<main id="content">',
                self._render_overview(),
                self._render_days(),
                self._render_places(),
                self._render_actions(),
                self._render_evidence(),
                "</main>",
                self._render_footer(),
            ]
        )
        title = _escape(self.trip.get("title") or "旅行路书")
        return (
            "<!doctype html>\n"
            '<html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{title}</title><style>{CSS}</style></head><body>"
            f'<div class="shell">{body}</div>'
            f'<script id="trip-data" type="application/json">'
            f'{_embedded_json(make_share_safe_trip(self.trip))}</script>'
            "</body></html>\n"
        )

    def _route_names(self) -> list[str]:
        result: list[str] = []
        origin_id = self.brief.get("origin_place_id")
        if origin_id:
            result.append(_place_name(self.places.get(str(origin_id))))
        for day in _as_list(self.trip.get("days")):
            if not isinstance(day, dict):
                continue
            for segment in _as_list(day.get("segments")):
                if not isinstance(segment, dict) or segment.get("type") != "travel":
                    continue
                place_id = segment.get("to_place_id")
                name = _place_name(self.places.get(str(place_id)))
                if not result or result[-1] != name:
                    result.append(name)
        if len(result) < 2:
            for place_id in _as_list(self.brief.get("destination_place_ids")):
                name = _place_name(self.places.get(str(place_id)))
                if not result or result[-1] != name:
                    result.append(name)
        return result

    def _render_hero(self) -> str:
        status = str(self.trip.get("status", "draft"))
        subtitle = self.trip.get("subtitle") or self.overview.get("summary") or ""
        route = self._route_names()
        route_html = "".join(f"<span>{_escape(name)}</span>" for name in route)
        fixture = (
            '<p class="fixture-banner">测试数据 · 非真实行程，请勿据此出发或预订</p>'
            if self.trip.get("fixture") is True
            else ""
        )
        return (
            '<header class="hero">'
            '<p class="eyebrow">CONSTRAINT-FIRST ROADBOOK · 风物路书</p>'
            f"<h1>{_escape(self.trip.get('title') or '旅行路书')}</h1>"
            f'<p class="subtitle">{_escape(subtitle)}</p>'
            '<div class="hero-meta">'
            f"{_badge(status, TRIP_LABELS)}"
            f"<span>{_escape(_date_range(self.brief))}</span>"
            f"<span>{_escape(_party_text(self.brief))}</span>"
            f"<span>{_escape(_transport_label(self.brief.get('transport')))}</span>"
            "</div>"
            f'<div class="route-strip" aria-label="路线">{route_html}</div>'
            f"{fixture}"
            '<p class="privacy-note">分享版不展示联系方式、证件号、订单号或私人地址；'
            "出发前请按清单复核动态信息。</p>"
            "</header>"
        )

    def _render_overview(self) -> str:
        decisions = _as_list(self.overview.get("decisions"))
        risks = _as_list(self.overview.get("risks"))
        cards: list[str] = []
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            status = str(decision.get("status", "open"))
            selected = decision.get("selected")
            options = " / ".join(_public_text(option) for option in _as_list(decision.get("options")))
            detail = f"已选：{_public_text(selected)}" if selected else f"选项：{options}"
            cards.append(
                '<article class="mini-card">'
                f"{_badge(status, DECISION_LABELS)}"
                f"<h3>{_escape(decision.get('question') or '待确认事项')}</h3>"
                f'<p class="muted">{_escape(detail)}</p></article>'
            )
        for risk in risks:
            if not isinstance(risk, dict):
                continue
            level = str(risk.get("level", "medium"))
            level_labels = {"high": "高风险", "medium": "需留意", "low": "一般提醒"}
            cards.append(
                '<article class="mini-card">'
                f"{_badge(level, level_labels)}"
                f"<h3>{_escape(risk.get('title') or '行程风险')}</h3>"
                f'<p class="muted">应对：{_escape(risk.get("mitigation") or "待补充")}</p>'
                "</article>"
            )
        content = "".join(cards) if cards else '<p class="empty">当前没有公开决策或重点风险。</p>'
        return (
            '<section class="panel" id="overview"><div class="section-head">'
            '<div><p class="section-kicker">先看这一页</p><h2>行程总览</h2></div>'
            f'<p class="muted">{_escape(self.overview.get("summary") or "概要待补充")}</p>'
            f'</div><div class="grid">{content}</div></section>'
        )

    def _render_days(self) -> str:
        rendered = [self._render_day(day) for day in _as_list(self.trip.get("days")) if isinstance(day, dict)]
        return "".join(rendered) or (
            '<section class="panel"><h2>每日行程</h2><p class="empty">尚未安排每日时间线。</p></section>'
        )

    def _render_day(self, day: dict[str, Any]) -> str:
        segments = "".join(
            self._render_segment(segment)
            for segment in _as_list(day.get("segments"))
            if isinstance(segment, dict)
        )
        return (
            f'<section class="panel day" id="day-{_escape(day.get("day"))}">'
            '<div class="section-head"><div>'
            f'<p class="section-kicker">DAY {_escape(day.get("day"))} · {_escape(_format_date(day.get("date")))}</p>'
            f'<h2>{_escape(day.get("title") or "当日行程")}</h2></div>'
            f'<p class="muted">{len(_as_list(day.get("segments")))} 个时间块</p></div>'
            f'<div class="timeline">{segments}</div></section>'
        )

    def _render_segment(self, segment: dict[str, Any]) -> str:
        segment_type = str(segment.get("type", "activity"))
        plan_status = str(segment.get("plan_status", "planned"))
        facts: list[str] = []
        place: dict[str, Any] | None = None
        if segment_type == "travel":
            start_place = _place_name(self.places.get(str(segment.get("from_place_id"))))
            end_place = _place_name(self.places.get(str(segment.get("to_place_id"))))
            facts.append(f"{start_place} → {end_place}")
            facts.append(_label(MODE_LABELS, segment.get("mode"), "移动"))
            distance = segment.get("distance_km")
            duration = segment.get("route_duration_minutes")
            if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                facts.append(f"{distance:g} km")
            if isinstance(duration, (int, float)) and not isinstance(duration, bool):
                facts.append(f"参考用时 {duration:g} 分钟")
        else:
            place = self.places.get(str(segment.get("place_id")))
            facts.append(_place_name(place))
            if segment_type == "meal":
                facts.append(_label(MEAL_LABELS, segment.get("meal_kind"), "用餐"))

        badges = [_badge(plan_status, PLAN_LABELS)]
        for item in self.evidence_by_target.get(str(segment.get("id")), []):
            badges.append(_badge(item.get("status"), EVIDENCE_LABELS))
        if place:
            for item in self.evidence_by_target.get(str(place.get("id")), []):
                if item.get("aspect") in {"hours", "reservation", "parking"}:
                    badges.append(_badge(item.get("status"), EVIDENCE_LABELS))
        badge_html = "".join(dict.fromkeys(badges))

        notes = [note for note in _as_list(segment.get("notes")) if note]
        notes_html = (
            '<ul class="clean-list">'
            + "".join(f"<li>{_escape(note)}</li>" for note in notes)
            + "</ul>"
            if notes
            else ""
        )
        detail_html = self._render_place_details(place) if segment_type == "meal" else ""
        return (
            '<article class="segment">'
            '<div class="segment-top">'
            f'<span class="segment-time">{_escape(_format_time(segment.get("start_at")))}—'
            f'{_escape(_format_time(segment.get("end_at")))}</span>'
            f'<span class="muted">{_escape(_label(SEGMENT_LABELS, segment_type))}</span>{badge_html}'
            "</div>"
            f"<h3>{_escape(segment.get('title') or '时间块')}</h3>"
            f'<div class="facts">{"".join(f"<span>{_escape(fact)}</span>" for fact in facts)}</div>'
            f"{detail_html}{notes_html}</article>"
        )

    def _render_place_details(self, place: dict[str, Any] | None) -> str:
        if not place or _is_private(place):
            return ""
        details = _as_dict(place.get("details"))
        items: list[str] = []
        for key, label in DETAIL_LABELS.items():
            value = details.get(key)
            if value in (None, "", []):
                continue
            if isinstance(value, list):
                public_value = "、".join(_public_text(item) for item in value)
            elif key == "backup_for" and str(value) in self.places:
                public_value = _place_name(self.places[str(value)])
            else:
                public_value = _public_text(value)
            items.append(f"<span><strong>{_escape(label)}：</strong>{_escape(public_value)}</span>")
        return f'<div class="facts">{"".join(items)}</div>' if items else ""

    def _render_places(self) -> str:
        selected = [
            place
            for place in self.places.values()
            if place.get("kind") in {"restaurant", "stay"}
        ]
        if not selected:
            return ""
        cards = []
        for place in selected:
            kind = "餐饮" if place.get("kind") == "restaurant" else "住宿"
            evidence = self.evidence_by_target.get(str(place.get("id")), [])
            badges = "".join(_badge(item.get("status"), EVIDENCE_LABELS) for item in evidence)
            cards.append(
                '<article class="mini-card">'
                f'<div class="badge-row"><span class="badge low">{kind}</span>{badges}</div>'
                f"<h3>{_escape(_place_name(place))}</h3>"
                f"{self._render_place_details(place)}</article>"
            )
        return (
            '<section class="panel" id="food-stay"><div class="section-head"><div>'
            '<p class="section-kicker">路线节点，不是附录</p><h2>吃住安排</h2></div></div>'
            f'<div class="grid">{"".join(cards)}</div></section>'
        )

    def _render_actions(self) -> str:
        tasks = [task for task in _as_list(self.trip.get("verification_tasks")) if isinstance(task, dict)]
        checklist = [item for item in _as_list(self.trip.get("checklist")) if isinstance(item, dict)]
        cards: list[str] = []
        for group in ("now", "t-48h", "pack"):
            items = [item for item in checklist if item.get("group") == group]
            if not items:
                continue
            lines = "".join(
                f'<li>{_badge(item.get("status"), ACTION_LABELS)} {_escape(item.get("item") or "待办")}</li>'
                for item in items
            )
            cards.append(
                '<article class="mini-card">'
                f"<h3>{_escape(_label(CHECKLIST_LABELS, group, group))}</h3>"
                f'<ul class="clean-list">{lines}</ul></article>'
            )
        if tasks:
            lines = "".join(
                '<li>'
                f'{_badge(task.get("status"), ACTION_LABELS)} '
                f'{_escape(task.get("action") or "复核事项")} · {_escape(task.get("due") or "时间待定")}'
                f'{" · 阻塞出发" if task.get("blocking") is True else ""}</li>'
                for task in tasks
            )
            cards.append(
                '<article class="mini-card"><h3>待核验事实</h3>'
                f'<ul class="clean-list">{lines}</ul></article>'
            )
        content = "".join(cards) if cards else '<p class="empty">当前没有待办事项。</p>'
        return (
            '<section class="panel" id="checklist"><div class="section-head"><div>'
            '<p class="section-kicker">决定能否顺利出发</p><h2>行前清单</h2></div></div>'
            f'<div class="grid">{content}</div></section>'
        )

    def _render_evidence(self) -> str:
        evidence_cards: list[str] = []
        for item in self.evidence:
            source_names = [
                _public_text(self.sources[source_id].get("title") or source_id)
                for source_id in _as_list(item.get("source_ids"))
                if str(source_id) in self.sources
            ]
            source_text = "、".join(source_names) or "暂无来源"
            note = item.get("note")
            evidence_cards.append(
                '<article class="mini-card">'
                f"{_badge(item.get('status'), EVIDENCE_LABELS)}"
                f'<h3>{_escape(self.target_names.get(str(item.get("target_id")), item.get("target_id") or "事实"))}</h3>'
                f'<p><strong>{_escape(_label(ASPECT_LABELS, item.get("aspect"), "事实"))}</strong> · '
                f'{_escape(source_text)}</p>'
                f'{f"<p class=\"muted\">{_escape(note)}</p>" if note else ""}</article>'
            )
        source_rows: list[str] = []
        for source in self.sources.values():
            url = _safe_url(source.get("url"))
            link = (
                f'<a href="{_escape(url)}" target="_blank" rel="noreferrer noopener">查看来源</a>'
                if url
                else "<span class=\"muted\">工具记录</span>"
            )
            accessed = _parse_datetime(source.get("accessed_at"))
            checked = accessed.strftime("%Y-%m-%d %H:%M") if accessed else "时间待补充"
            source_rows.append(
                '<div class="source-row">'
                f'<span class="badge low">{_escape(_label(SOURCE_LABELS, source.get("type"), "来源"))}</span>'
                f'<strong>{_escape(source.get("title") or "未命名来源")}</strong>'
                f'<span class="muted">核查于 {_escape(checked)}</span>{link}</div>'
            )
        evidence_content = "".join(evidence_cards) or '<p class="empty">暂无证据记录。</p>'
        sources_content = "".join(source_rows) or '<p class="empty">暂无来源记录。</p>'
        return (
            '<section class="panel" id="evidence"><div class="section-head"><div>'
            '<p class="section-kicker">结论有出处，未知也可见</p><h2>核验与来源</h2></div></div>'
            f'<div class="grid">{evidence_content}</div><h3>来源新鲜度</h3>'
            f'<div class="source-list">{sources_content}</div></section>'
        )

    def _render_footer(self) -> str:
        generated = _parse_datetime(self.trip.get("generated_at"))
        generated_text = generated.strftime("%Y-%m-%d %H:%M") if generated else "时间待补充"
        return (
            "<footer>"
            f"生成于 {_escape(generated_text)} · schema {_escape(self.trip.get('schema_version') or 'unknown')}。"
            "本路书只呈现 trip.json 中的当前计划，不代替临行前的官方核验。"
            "</footer>"
        )


def render_html(trip: dict[str, Any]) -> str:
    """Return a self-contained HTML document without mutating *trip*."""

    if not isinstance(trip, dict):
        raise TypeError("trip must be a JSON object")
    _ensure_renderable(trip)
    return RoadbookRenderer(trip).render()


def load_trip(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("trip.json root must be an object")
    return data


def write_atomic(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists: {path}; pass --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trip_json", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        input_path = args.trip_json.resolve(strict=True)
    except FileNotFoundError:
        print(f"ERROR: input does not exist: {args.trip_json}", file=sys.stderr)
        return 1
    output_path = args.output.resolve(strict=False)
    if input_path == output_path:
        print("ERROR: output must not overwrite the input trip.json", file=sys.stderr)
        return 1

    try:
        trip = load_trip(input_path)
        document = render_html(trip)
        write_atomic(output_path, document, force=args.force)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
