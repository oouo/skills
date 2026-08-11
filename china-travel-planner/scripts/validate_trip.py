#!/usr/bin/env python3
"""Validate the china-travel-planner trip.json contract."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


TRIP_STATUSES = {"draft", "ready"}
EVIDENCE_STATUSES = {"verified", "candidate", "unknown"}
SOURCE_TYPES = {
    "official",
    "map",
    "transport",
    "first_party",
    "weather",
    "ugc",
    "local_media",
    "user",
    "other",
}
SOURCE_ACCESS_METHODS = {
    "official_api",
    "authorized_api",
    "official_connector",
    "public_web",
    "user_provided",
    "fixture",
    "unofficial_connector",
    "experimental_connector",
    "reverse_engineered_api",
    "browser_automation",
}
FORBIDDEN_SOURCE_ACCESS_METHODS = {
    "unofficial_connector",
    "experimental_connector",
    "reverse_engineered_api",
    "browser_automation",
}
EVIDENCE_ASPECTS = {
    "identity",
    "location",
    "route",
    "duration",
    "distance",
    "hours",
    "price",
    "reservation",
    "parking",
    "queue",
    "policy",
    "weather",
    "experience",
}
PLACE_KINDS = {
    "origin",
    "destination",
    "attraction",
    "restaurant",
    "stay",
    "service",
    "transport_hub",
    "other",
}
SEGMENT_TYPES = {"travel", "activity", "meal", "rest", "buffer", "checkin"}
PLAN_STATUSES = {"fixed", "planned", "candidate"}
TRAVEL_MODES = {"drive", "rail", "flight", "bus", "metro", "ferry", "taxi", "walk"}
MEAL_KINDS = {"breakfast", "lunch", "dinner", "snack"}
ACTION_STATUSES = {"open", "done", "not_needed"}
CHECKLIST_GROUPS = {"now", "t-48h", "pack"}

SOURCE_OWNERS = {
    "identity": {"official", "map", "first_party", "user"},
    "location": {"official", "map", "first_party", "user"},
    "route": {"map", "transport", "official"},
    "duration": {"map", "transport", "official"},
    "distance": {"map", "transport", "official"},
    "hours": {"official", "first_party", "user"},
    "price": {"first_party", "user"},
    "reservation": {"official", "first_party", "user"},
    "policy": {"official", "user"},
    "weather": {"weather", "official"},
    "parking": {"official", "map", "first_party", "ugc", "user"},
    "queue": {"official", "first_party", "ugc", "local_media", "user"},
    "experience": {"ugc", "local_media", "user"},
}
VERIFIED_SOURCE_OWNERS = {
    aspect: owners - {"ugc"} for aspect, owners in SOURCE_OWNERS.items()
}


@dataclass(frozen=True)
class Issue:
    severity: str
    path: str
    code: str
    message: str


class TripValidator:
    def __init__(self, data: Any) -> None:
        self.data = data
        self.issues: list[Issue] = []
        self.trip_status = "draft"
        self.source_by_id: dict[str, dict[str, Any]] = {}
        self.place_by_id: dict[str, dict[str, Any]] = {}
        self.evidence_by_id: dict[str, dict[str, Any]] = {}
        self.evidence_by_target_aspect: dict[tuple[str, str], dict[str, Any]] = {}
        self.task_by_id: dict[str, dict[str, Any]] = {}
        self.tasks_by_evidence: dict[str, list[dict[str, Any]]] = {}
        self.target_ids: set[str] = set()
        self.used_place_ids: set[str] = set()
        self.used_source_ids: set[str] = set()
        self.used_task_ids: set[str] = set()
        self.used_evidence_ids: set[str] = set()
        self.constraints: dict[str, Any] = {}

    def error(self, path: str, code: str, message: str) -> None:
        self.issues.append(Issue("ERROR", path, code, message))

    def warning(self, path: str, code: str, message: str) -> None:
        self.issues.append(Issue("WARNING", path, code, message))

    def validate(self) -> list[Issue]:
        if not isinstance(self.data, dict):
            self.error("/", "E_ROOT_TYPE", "root must be a JSON object")
            return self._sorted_issues()

        self._validate_root()
        self._validate_brief()
        self._validate_constraints()
        self._validate_sources()
        self._validate_places()
        self._validate_evidence()
        self._validate_overview()
        self._validate_tasks()
        self._validate_days()
        self._validate_checklist()
        self._validate_cross_references()
        return self._sorted_issues()

    def _validate_root(self) -> None:
        required = {
            "schema_version": str,
            "title": str,
            "status": str,
            "timezone": str,
            "generated_at": str,
            "brief": dict,
            "constraints": dict,
            "overview": dict,
            "sources": list,
            "evidence": list,
            "places": list,
            "days": list,
            "verification_tasks": list,
            "checklist": list,
        }
        for key, expected in required.items():
            value = self.data.get(key)
            path = f"/{key}"
            if key not in self.data:
                self.error(path, "E_REQUIRED", "required field is missing")
            elif not isinstance(value, expected):
                self.error(path, "E_TYPE", f"must be {expected.__name__}")

        if self.data.get("schema_version") != "1.0":
            self.error("/schema_version", "E_SCHEMA_VERSION", "must equal '1.0'")
        self.trip_status = self.data.get("status", "draft")
        if not self._enum(self.trip_status, TRIP_STATUSES):
            self.error("/status", "E_ENUM", "must be draft or ready")
        self._nonempty_string(self.data, "title", "")
        self._nonempty_string(self.data, "timezone", "")
        self._parse_datetime(self.data.get("generated_at"), "/generated_at")
        if "last_verified_at" in self.data:
            self._parse_datetime(
                self.data.get("last_verified_at"), "/last_verified_at"
            )

    def _validate_brief(self) -> None:
        brief = self.data.get("brief")
        if not isinstance(brief, dict):
            return
        self._nonempty_string(brief, "origin_place_id", "/brief")
        destinations = brief.get("destination_place_ids")
        if not self._string_list(destinations, allow_empty=False):
            self.error(
                "/brief/destination_place_ids",
                "E_TYPE",
                "must be a non-empty list of place ids",
            )
        start = self._parse_date(brief.get("start_date"), "/brief/start_date")
        end = self._parse_date(brief.get("end_date"), "/brief/end_date")
        if start and end and end < start:
            self.error("/brief/end_date", "E_DATE_ORDER", "must not precede start_date")
        self._nonempty_string(brief, "transport", "/brief")

        party = brief.get("party")
        if not isinstance(party, dict):
            self.error("/brief/party", "E_TYPE", "must be an object")
            return
        adults = party.get("adults")
        seniors = party.get("seniors", 0)
        children = party.get("children", [])
        if not self._nonnegative_int(adults):
            self.error("/brief/party/adults", "E_TYPE", "must be a non-negative integer")
        if not self._nonnegative_int(seniors):
            self.error("/brief/party/seniors", "E_TYPE", "must be a non-negative integer")
        if not isinstance(children, list):
            self.error("/brief/party/children", "E_TYPE", "must be a list")
            children = []
        else:
            for index, child in enumerate(children):
                path = f"/brief/party/children/{index}"
                if not isinstance(child, dict):
                    self.error(path, "E_TYPE", "must be an object")
                    continue
                age = child.get("age_years")
                if age is None:
                    self.warning(path, "W_CHILD_AGE", "child age is unknown")
                elif not isinstance(age, (int, float)) or isinstance(age, bool) or age < 0:
                    self.error(f"{path}/age_years", "E_TYPE", "must be null or non-negative")
        total = (adults if self._nonnegative_int(adults) else 0) + (
            seniors if self._nonnegative_int(seniors) else 0
        ) + len(children)
        if total == 0:
            self.error("/brief/party", "E_PARTY_EMPTY", "must include at least one traveler")

    def _validate_constraints(self) -> None:
        constraints = self.data.get("constraints")
        if not isinstance(constraints, dict):
            return
        self.constraints = constraints
        gap = constraints.get("max_unscheduled_gap_minutes")
        if not self._positive_int(gap, allow_zero=True) or gap > 240:
            self.error(
                "/constraints/max_unscheduled_gap_minutes",
                "E_CONSTRAINT",
                "must be an integer from 0 to 240",
            )

        driving = constraints.get("driving")
        if not isinstance(driving, dict):
            self.error("/constraints/driving", "E_REQUIRED", "must be an object")
        else:
            numeric = (
                "max_continuous_minutes",
                "min_break_minutes",
                "max_daily_minutes",
                "hard_max_daily_minutes",
            )
            for key in numeric:
                if not self._positive_int(driving.get(key)):
                    self.error(f"/constraints/driving/{key}", "E_CONSTRAINT", "must be positive")
            soft = driving.get("max_daily_minutes")
            hard = driving.get("hard_max_daily_minutes")
            if self._positive_int(soft) and self._positive_int(hard) and soft > hard:
                self.error(
                    "/constraints/driving",
                    "E_CONSTRAINT_ORDER",
                    "max_daily_minutes must not exceed hard_max_daily_minutes",
                )
            self._parse_hhmm(driving.get("latest_end"), "/constraints/driving/latest_end")

        child_count = self._child_count()
        child = constraints.get("child")
        if child_count and not isinstance(child, dict):
            self.error(
                "/constraints/child",
                "E_CHILD_CONSTRAINT",
                "is required when children are present",
            )
        elif isinstance(child, dict):
            if not self._positive_int(child.get("max_continuous_vehicle_minutes")):
                self.error(
                    "/constraints/child/max_continuous_vehicle_minutes",
                    "E_CONSTRAINT",
                    "must be positive",
                )
            self._parse_hhmm(
                child.get("latest_day_end"),
                "/constraints/child/latest_day_end",
            )

        windows = constraints.get("meal_windows")
        if not isinstance(windows, dict):
            self.error("/constraints/meal_windows", "E_REQUIRED", "must be an object")
        else:
            for meal, window in windows.items():
                path = f"/constraints/meal_windows/{meal}"
                if meal not in MEAL_KINDS:
                    self.error(path, "E_ENUM", "unknown meal window")
                if not isinstance(window, dict):
                    self.error(path, "E_TYPE", "must be an object")
                    continue
                start = self._parse_hhmm(window.get("start"), f"{path}/start")
                end = self._parse_hhmm(window.get("end"), f"{path}/end")
                if start is not None and end is not None and end <= start:
                    self.error(path, "E_TIME_ORDER", "end must be after start")
                if not isinstance(window.get("required"), bool):
                    self.error(f"{path}/required", "E_TYPE", "must be boolean")

    def _validate_sources(self) -> None:
        sources = self.data.get("sources")
        if not isinstance(sources, list):
            return
        for index, source in enumerate(sources):
            path = f"/sources/{index}"
            if not isinstance(source, dict):
                self.error(path, "E_TYPE", "must be an object")
                continue
            source_id = self._nonempty_string(source, "id", path)
            if source_id:
                if source_id in self.source_by_id:
                    self.error(f"{path}/id", "E_DUPLICATE_ID", f"duplicate id '{source_id}'")
                self.source_by_id[source_id] = source
            source_type = source.get("type")
            if not self._enum(source_type, SOURCE_TYPES):
                self.error(f"{path}/type", "E_ENUM", "unknown source type")
            self._nonempty_string(source, "title", path)
            access_method = source.get("access_method")
            if not self._has_text(access_method):
                self.error(
                    f"{path}/access_method",
                    "E_SOURCE_ACCESS_REQUIRED",
                    "source requires an access method",
                )
            elif access_method not in SOURCE_ACCESS_METHODS:
                self.error(
                    f"{path}/access_method",
                    "E_SOURCE_ACCESS_ENUM",
                    "unknown source access method",
                )
            elif access_method in FORBIDDEN_SOURCE_ACCESS_METHODS:
                self.error(
                    f"{path}/access_method",
                    "E_SOURCE_ACCESS_FORBIDDEN",
                    f"'{access_method}' is not admitted in v1",
                )
            elif access_method == "fixture" and self.data.get("fixture") is not True:
                self.error(
                    f"{path}/access_method",
                    "E_FIXTURE_SOURCE",
                    "fixture access is valid only for fixture trips",
                )
            if (
                source_type == "user"
                and access_method in SOURCE_ACCESS_METHODS
                and access_method not in {"user_provided", "fixture"}
            ):
                self.error(
                    f"{path}/access_method",
                    "E_USER_SOURCE_ACCESS",
                    "user facts require user_provided access",
                )
            url = source.get("url")
            locator = source.get("locator")
            if source_type != "user" and not self._has_text(url) and not self._has_text(locator):
                self.error(path, "E_SOURCE_LOCATOR", "requires url or locator")
            if self._has_text(url):
                parsed = urlparse(url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    self.error(f"{path}/url", "E_URL", "must be an HTTP(S) URL")
            if access_method == "public_web" and not self._has_text(url):
                self.error(
                    f"{path}/url",
                    "E_PUBLIC_SOURCE_URL",
                    "public_web requires a public HTTP(S) URL",
                )
            self._parse_datetime(source.get("accessed_at"), f"{path}/accessed_at")

    def _validate_places(self) -> None:
        places = self.data.get("places")
        if not isinstance(places, list):
            return
        for index, place in enumerate(places):
            path = f"/places/{index}"
            if not isinstance(place, dict):
                self.error(path, "E_TYPE", "must be an object")
                continue
            place_id = self._nonempty_string(place, "id", path)
            if place_id:
                if place_id in self.place_by_id:
                    self.error(f"{path}/id", "E_DUPLICATE_ID", f"duplicate id '{place_id}'")
                self.place_by_id[place_id] = place
                self.target_ids.add(place_id)
            self._nonempty_string(place, "name", path)
            if not self._enum(place.get("kind"), PLACE_KINDS):
                self.error(f"{path}/kind", "E_ENUM", "unknown place kind")
            coordinates = place.get("coordinates")
            if coordinates is not None:
                if not isinstance(coordinates, dict):
                    self.error(f"{path}/coordinates", "E_TYPE", "must be an object")
                else:
                    lat = coordinates.get("lat")
                    lon = coordinates.get("lon")
                    if not self._number(lat) or not -90 <= lat <= 90:
                        self.error(f"{path}/coordinates/lat", "E_COORDINATE", "invalid latitude")
                    if not self._number(lon) or not -180 <= lon <= 180:
                        self.error(f"{path}/coordinates/lon", "E_COORDINATE", "invalid longitude")
            if "details" in place and not isinstance(place.get("details"), dict):
                self.error(f"{path}/details", "E_TYPE", "must be an object")

    def _validate_evidence(self) -> None:
        evidence_items = self.data.get("evidence")
        if not isinstance(evidence_items, list):
            return
        for index, evidence in enumerate(evidence_items):
            path = f"/evidence/{index}"
            if not isinstance(evidence, dict):
                self.error(path, "E_TYPE", "must be an object")
                continue
            evidence_id = self._nonempty_string(evidence, "id", path)
            if evidence_id:
                if evidence_id in self.evidence_by_id:
                    self.error(f"{path}/id", "E_DUPLICATE_ID", f"duplicate id '{evidence_id}'")
                self.evidence_by_id[evidence_id] = evidence
            target_id = self._nonempty_string(evidence, "target_id", path)
            aspect = evidence.get("aspect")
            if not self._enum(aspect, EVIDENCE_ASPECTS):
                self.error(f"{path}/aspect", "E_ENUM", "unknown evidence aspect")
            if target_id and self._enum(aspect, EVIDENCE_ASPECTS):
                key = (target_id, aspect)
                if key in self.evidence_by_target_aspect:
                    self.error(path, "E_DUPLICATE_EVIDENCE", "target and aspect must be unique")
                self.evidence_by_target_aspect[key] = evidence
            status = evidence.get("status")
            if not self._enum(status, EVIDENCE_STATUSES):
                self.error(f"{path}/status", "E_ENUM", "unknown evidence status")
            source_ids = evidence.get("source_ids")
            if not self._string_list(source_ids, allow_empty=True):
                self.error(f"{path}/source_ids", "E_TYPE", "must be a list of source ids")
                source_ids = []
            self.used_source_ids.update(source_ids)
            if (
                isinstance(status, str)
                and status in {"verified", "candidate"}
                and not source_ids
            ):
                self.error(path, "E_EVIDENCE_SOURCE", f"{status} evidence requires a source")
            if status == "unknown" and not self._has_text(evidence.get("note")):
                self.error(path, "E_UNKNOWN_NOTE", "unknown evidence requires a note")
            if status == "candidate":
                self.warning(path, "W_CANDIDATE", "evidence still needs confirmation")
            elif status == "unknown":
                self.warning(path, "W_UNKNOWN", "evidence is explicitly unknown")

    def _validate_overview(self) -> None:
        overview = self.data.get("overview")
        if not isinstance(overview, dict):
            return
        self._nonempty_string(overview, "summary", "/overview")
        decisions = overview.get("decisions", [])
        if not isinstance(decisions, list):
            self.error("/overview/decisions", "E_TYPE", "must be a list")
        else:
            seen: set[str] = set()
            for index, decision in enumerate(decisions):
                path = f"/overview/decisions/{index}"
                if not isinstance(decision, dict):
                    self.error(path, "E_TYPE", "must be an object")
                    continue
                decision_id = self._nonempty_string(decision, "id", path)
                if decision_id:
                    if decision_id in seen:
                        self.error(f"{path}/id", "E_DUPLICATE_ID", "duplicate decision id")
                    seen.add(decision_id)
                    self.target_ids.add(decision_id)
                self._nonempty_string(decision, "question", path)
                if not self._string_list(decision.get("options"), allow_empty=False):
                    self.error(f"{path}/options", "E_TYPE", "must be a non-empty string list")
                status = decision.get("status")
                if not self._enum(status, {"open", "resolved"}):
                    self.error(f"{path}/status", "E_ENUM", "must be open or resolved")
                if status == "resolved" and not self._has_text(decision.get("selected")):
                    self.error(path, "E_DECISION_SELECTED", "resolved decision requires selected")
                if status == "open" and self.trip_status == "ready":
                    self.error(path, "E_READY_DECISION", "ready trip cannot have open decisions")

        risks = overview.get("risks", [])
        if not isinstance(risks, list):
            self.error("/overview/risks", "E_TYPE", "must be a list")
        else:
            seen = set()
            for index, risk in enumerate(risks):
                path = f"/overview/risks/{index}"
                if not isinstance(risk, dict):
                    self.error(path, "E_TYPE", "must be an object")
                    continue
                risk_id = self._nonempty_string(risk, "id", path)
                if risk_id:
                    if risk_id in seen:
                        self.error(f"{path}/id", "E_DUPLICATE_ID", "duplicate risk id")
                    seen.add(risk_id)
                    self.target_ids.add(risk_id)
                self._nonempty_string(risk, "title", path)
                self._nonempty_string(risk, "mitigation", path)
                if not self._enum(risk.get("level"), {"high", "medium", "low"}):
                    self.error(f"{path}/level", "E_ENUM", "must be high, medium, or low")
                if not isinstance(risk.get("critical"), bool):
                    self.error(f"{path}/critical", "E_TYPE", "must be boolean")

    def _validate_tasks(self) -> None:
        tasks = self.data.get("verification_tasks")
        if not isinstance(tasks, list):
            return
        for index, task in enumerate(tasks):
            path = f"/verification_tasks/{index}"
            if not isinstance(task, dict):
                self.error(path, "E_TYPE", "must be an object")
                continue
            task_id = self._nonempty_string(task, "id", path)
            if task_id:
                if task_id in self.task_by_id:
                    self.error(f"{path}/id", "E_DUPLICATE_ID", f"duplicate id '{task_id}'")
                self.task_by_id[task_id] = task
            evidence_id = self._nonempty_string(task, "evidence_id", path)
            if evidence_id:
                self.tasks_by_evidence.setdefault(evidence_id, []).append(task)
                self.used_evidence_ids.add(evidence_id)
            self._nonempty_string(task, "action", path)
            self._nonempty_string(task, "due", path)
            if not isinstance(task.get("blocking"), bool):
                self.error(f"{path}/blocking", "E_TYPE", "must be boolean")
            if not self._enum(task.get("status"), ACTION_STATUSES):
                self.error(f"{path}/status", "E_ENUM", "unknown task status")
            if (
                self.trip_status == "ready"
                and task.get("blocking") is True
                and task.get("status") == "open"
            ):
                self.error(path, "E_READY_BLOCKER", "ready trip cannot have an open blocker")

    def _validate_days(self) -> None:
        days = self.data.get("days")
        brief = self.data.get("brief")
        if not isinstance(days, list) or not isinstance(brief, dict):
            return
        start_date = self._date_or_none(brief.get("start_date"))
        end_date = self._date_or_none(brief.get("end_date"))
        if start_date and end_date and end_date >= start_date:
            expected = (end_date - start_date).days + 1
            if len(days) != expected:
                self.error("/days", "E_DAY_COUNT", f"must contain {expected} day objects")

        seen_segments: set[str] = set()
        for index, day in enumerate(days):
            path = f"/days/{index}"
            if not isinstance(day, dict):
                self.error(path, "E_TYPE", "must be an object")
                continue
            if day.get("day") != index + 1:
                self.error(f"{path}/day", "E_DAY_NUMBER", f"must equal {index + 1}")
            day_date = self._parse_date(day.get("date"), f"{path}/date")
            if start_date and day_date:
                expected_date = start_date + timedelta(days=index)
                if day_date != expected_date:
                    self.error(f"{path}/date", "E_DAY_DATE", f"must equal {expected_date}")
            self._nonempty_string(day, "title", path)
            start_place = self._nonempty_string(day, "start_place_id", path)
            end_place = self._nonempty_string(day, "end_place_id", path)
            if start_place:
                self.used_place_ids.add(start_place)
            if end_place:
                self.used_place_ids.add(end_place)

            segments = day.get("segments")
            if not isinstance(segments, list) or not segments:
                self.error(f"{path}/segments", "E_REQUIRED", "must be a non-empty list")
                continue
            if len(segments) > 8:
                self.warning(
                    f"{path}/segments",
                    "W_CARD_SPLIT",
                    "more than 8 segments will require a continuation card",
                )
            self._validate_day_segments(
                day,
                path,
                day_date,
                start_place,
                end_place,
                seen_segments,
            )

    def _validate_day_segments(
        self,
        day: dict[str, Any],
        path: str,
        day_date: date | None,
        start_place: str | None,
        end_place: str | None,
        seen_segments: set[str],
    ) -> None:
        segments = day["segments"]
        raw_gap = self.constraints.get("max_unscheduled_gap_minutes", 30)
        max_gap = raw_gap if self._positive_int(raw_gap, allow_zero=True) else 30
        raw_driving = self.constraints.get("driving", {})
        driving = raw_driving if isinstance(raw_driving, dict) else {}
        raw_child = self.constraints.get("child", {})
        child = raw_child if isinstance(raw_child, dict) else {}
        raw_min_break = driving.get("min_break_minutes", 20)
        min_break = raw_min_break if self._positive_int(raw_min_break) else 20
        raw_max_continuous = driving.get("max_continuous_minutes", 120)
        max_continuous = (
            raw_max_continuous
            if self._positive_int(raw_max_continuous)
            else 120
        )
        raw_child_max = child.get("max_continuous_vehicle_minutes")
        child_max = raw_child_max if self._positive_int(raw_child_max) else None
        latest_drive = self._hhmm_or_none(driving.get("latest_end"))
        latest_child = self._hhmm_or_none(child.get("latest_day_end"))

        current_place = start_place
        previous_end: datetime | None = None
        continuous_drive = 0
        continuous_vehicle = 0
        daily_drive = 0
        parsed: list[tuple[dict[str, Any], datetime, datetime, str]] = []

        for index, segment in enumerate(segments):
            segment_path = f"{path}/segments/{index}"
            if not isinstance(segment, dict):
                self.error(segment_path, "E_TYPE", "must be an object")
                continue
            segment_id = self._nonempty_string(segment, "id", segment_path)
            if segment_id:
                if segment_id in seen_segments:
                    self.error(f"{segment_path}/id", "E_DUPLICATE_ID", "duplicate segment id")
                seen_segments.add(segment_id)
                self.target_ids.add(segment_id)
            segment_type = segment.get("type")
            if not self._enum(segment_type, SEGMENT_TYPES):
                self.error(f"{segment_path}/type", "E_ENUM", "unknown segment type")
            if not self._enum(segment.get("plan_status"), PLAN_STATUSES):
                self.error(f"{segment_path}/plan_status", "E_ENUM", "unknown plan status")
            self._nonempty_string(segment, "title", segment_path)
            start = self._parse_datetime(segment.get("start_at"), f"{segment_path}/start_at")
            end = self._parse_datetime(segment.get("end_at"), f"{segment_path}/end_at")
            if not start or not end:
                continue
            if end <= start:
                self.error(segment_path, "E_TIME_ORDER", "end_at must be after start_at")
                continue
            if day_date and (start.date() != day_date or end.date() != day_date):
                self.error(segment_path, "E_CROSS_DAY", "segment must stay within its day")
            if start.utcoffset() != end.utcoffset():
                self.error(segment_path, "E_TIMEZONE", "segment offsets must match")
            if previous_end:
                if start < previous_end:
                    self.error(segment_path, "E_OVERLAP", "overlaps the previous segment")
                elif start > previous_end:
                    gap = int((start - previous_end).total_seconds() // 60)
                    if self._positive_int(max_gap, allow_zero=True) and gap > max_gap:
                        self.error(
                            segment_path,
                            "E_GAP",
                            f"unscheduled gap {gap}m exceeds the {max_gap}m constraint",
                        )
                    else:
                        self.warning(
                            segment_path,
                            "W_GAP",
                            f"contains an unscheduled {gap}m gap",
                        )
            previous_end = end
            parsed.append((segment, start, end, segment_path))
            scheduled_minutes = int((end - start).total_seconds() // 60)

            if segment_type == "travel":
                mode = segment.get("mode")
                if not self._enum(mode, TRAVEL_MODES):
                    self.error(f"{segment_path}/mode", "E_ENUM", "unknown travel mode")
                from_place = self._nonempty_string(segment, "from_place_id", segment_path)
                to_place = self._nonempty_string(segment, "to_place_id", segment_path)
                if from_place:
                    self.used_place_ids.add(from_place)
                if to_place:
                    self.used_place_ids.add(to_place)
                if current_place and from_place and from_place != current_place:
                    self.error(
                        segment_path,
                        "E_PLACE_CHAIN",
                        f"starts at '{from_place}' but current place is '{current_place}'",
                    )
                current_place = to_place or current_place
                if segment_id:
                    self._require_evidence(
                        segment_id,
                        "route",
                        segment_path,
                        blocking=segment.get("plan_status") != "candidate",
                    )
                    self._require_evidence(
                        segment_id,
                        "duration",
                        segment_path,
                        blocking=segment.get("plan_status") != "candidate",
                    )
                self._validate_optional_exact_value(
                    segment,
                    "distance_km",
                    "distance",
                    segment_id,
                    segment_path,
                )
                self._validate_optional_exact_value(
                    segment,
                    "route_duration_minutes",
                    "duration",
                    segment_id,
                    segment_path,
                )
                route_duration = segment.get("route_duration_minutes")
                if self._number(route_duration) and route_duration > scheduled_minutes:
                    self.error(
                        f"{segment_path}/route_duration_minutes",
                        "E_SCHEDULE_SHORT",
                        "route duration exceeds the scheduled travel block",
                    )
                if "daylight_required" in segment and not isinstance(
                    segment.get("daylight_required"), bool
                ):
                    self.error(
                        f"{segment_path}/daylight_required",
                        "E_TYPE",
                        "must be boolean",
                    )

                if mode == "drive":
                    daily_drive += scheduled_minutes
                    continuous_drive += scheduled_minutes
                    continuous_vehicle += scheduled_minutes
                    if self._positive_int(max_continuous) and continuous_drive > max_continuous:
                        self.error(
                            segment_path,
                            "E_CONTINUOUS_DRIVE",
                            f"continuous drive {continuous_drive}m exceeds {max_continuous}m",
                        )
                    if latest_drive is not None and self._minute_of_day(end) > latest_drive:
                        self.error(
                            segment_path,
                            "E_LATE_DRIVE",
                            "drive ends after constraints.driving.latest_end",
                        )
                elif mode != "walk":
                    continuous_drive = 0
                    continuous_vehicle += scheduled_minutes
                else:
                    continuous_drive = 0
                    continuous_vehicle = 0
                if (
                    mode != "walk"
                    and self._positive_int(child_max)
                    and continuous_vehicle > child_max
                ):
                    self.error(
                        segment_path,
                        "E_CHILD_VEHICLE",
                        f"continuous vehicle time {continuous_vehicle}m exceeds {child_max}m",
                    )
            else:
                place_id = self._nonempty_string(segment, "place_id", segment_path)
                if place_id:
                    self.used_place_ids.add(place_id)
                if current_place and place_id and place_id != current_place:
                    self.error(
                        segment_path,
                        "E_PLACE_CHAIN",
                        f"occurs at '{place_id}' but current place is '{current_place}'",
                    )
                if segment_type == "meal":
                    meal_kind = segment.get("meal_kind")
                    if not self._enum(meal_kind, MEAL_KINDS):
                        self.error(f"{segment_path}/meal_kind", "E_ENUM", "unknown meal kind")
                    place = self.place_by_id.get(place_id or "")
                    if place and place.get("kind") == "restaurant" and place_id:
                        self._require_evidence(
                            place_id,
                            "hours",
                            segment_path,
                            blocking=segment.get("plan_status") != "candidate",
                        )
                if segment_type == "checkin" and segment.get("plan_status") == "fixed":
                    if place_id:
                        self._require_evidence(
                            place_id,
                            "reservation",
                            segment_path,
                            blocking=True,
                        )
                if scheduled_minutes >= min_break:
                    continuous_drive = 0
                    continuous_vehicle = 0

        if current_place and end_place and current_place != end_place:
            self.error(
                path,
                "E_DAY_END_PLACE",
                f"timeline ends at '{current_place}', expected '{end_place}'",
            )

        end_place_record = self.place_by_id.get(end_place or "")
        if end_place_record and end_place_record.get("kind") == "stay":
            has_checkin = any(
                segment.get("type") == "checkin"
                and segment.get("place_id") == end_place
                for segment, _, _, _ in parsed
            )
            if not has_checkin:
                self.error(
                    path,
                    "E_CHECKIN_MISSING",
                    f"day ending at stay '{end_place}' requires a checkin segment",
                )

        soft = driving.get("max_daily_minutes")
        hard = driving.get("hard_max_daily_minutes")
        if self._positive_int(hard) and daily_drive > hard:
            self.error(path, "E_DAILY_DRIVE", f"daily driving {daily_drive}m exceeds {hard}m")
        elif self._positive_int(soft) and daily_drive > soft:
            self.warning(path, "W_DAILY_DRIVE", f"daily driving {daily_drive}m exceeds {soft}m")

        if self._child_count() and latest_child is not None and parsed:
            if self._minute_of_day(parsed[-1][2]) > latest_child:
                self.error(path, "E_CHILD_DAY_END", "day ends after child latest_day_end")
        self._validate_meal_windows(path, parsed)

    def _validate_meal_windows(
        self,
        path: str,
        parsed: list[tuple[dict[str, Any], datetime, datetime, str]],
    ) -> None:
        if not parsed:
            return
        active_start = self._minute_of_day(parsed[0][1])
        active_end = self._minute_of_day(parsed[-1][2])
        windows = self.constraints.get("meal_windows", {})
        if not isinstance(windows, dict):
            return
        for meal, window in windows.items():
            if not isinstance(window, dict) or window.get("required") is not True:
                continue
            start = self._hhmm_or_none(window.get("start"))
            end = self._hhmm_or_none(window.get("end"))
            if start is None or end is None or active_start >= end or active_end <= start:
                continue
            covered = any(
                segment.get("type") == "meal"
                and segment.get("meal_kind") == meal
                and self._minute_of_day(segment_start) < end
                and self._minute_of_day(segment_end) > start
                for segment, segment_start, segment_end, _ in parsed
            )
            if not covered:
                self.error(path, "E_MEAL_WINDOW", f"active schedule crosses {meal} without a meal")

    def _validate_checklist(self) -> None:
        checklist = self.data.get("checklist")
        if not isinstance(checklist, list):
            return
        for index, item in enumerate(checklist):
            path = f"/checklist/{index}"
            if not isinstance(item, dict):
                self.error(path, "E_TYPE", "must be an object")
                continue
            if not self._enum(item.get("group"), CHECKLIST_GROUPS):
                self.error(f"{path}/group", "E_ENUM", "unknown checklist group")
            self._nonempty_string(item, "item", path)
            if not self._enum(item.get("status"), ACTION_STATUSES):
                self.error(f"{path}/status", "E_ENUM", "unknown checklist status")
            task_ids = item.get("task_ids", [])
            if not self._string_list(task_ids, allow_empty=True):
                self.error(f"{path}/task_ids", "E_TYPE", "must be a list of task ids")
            else:
                self.used_task_ids.update(task_ids)

    def _validate_optional_exact_value(
        self,
        segment: dict[str, Any],
        field: str,
        aspect: str,
        target_id: str | None,
        path: str,
    ) -> None:
        if field not in segment:
            return
        value = segment.get(field)
        if not self._number(value) or value <= 0:
            self.error(f"{path}/{field}", "E_EXACT_VALUE", "must be a positive number")
            return
        evidence = self.evidence_by_target_aspect.get((target_id or "", aspect))
        if not evidence or evidence.get("status") == "unknown":
            self.error(
                f"{path}/{field}",
                "E_FALSE_PRECISION",
                f"exact {field} requires verified or candidate {aspect} evidence",
            )

    def _require_evidence(
        self,
        target_id: str,
        aspect: str,
        path: str,
        blocking: bool,
    ) -> None:
        evidence = self.evidence_by_target_aspect.get((target_id, aspect))
        if not evidence:
            self.error(path, "E_EVIDENCE_MISSING", f"missing {aspect} evidence for '{target_id}'")
            return
        evidence_id = evidence.get("id")
        if isinstance(evidence_id, str):
            self.used_evidence_ids.add(evidence_id)
        if blocking and evidence.get("status") != "verified" and self.trip_status == "ready":
            self.error(
                path,
                "E_READY_EVIDENCE",
                f"ready trip requires verified {aspect} evidence for '{target_id}'",
            )

    def _validate_cross_references(self) -> None:
        brief = self.data.get("brief")
        if isinstance(brief, dict):
            origin = brief.get("origin_place_id")
            if isinstance(origin, str):
                self.used_place_ids.add(origin)
            destinations = brief.get("destination_place_ids", [])
            if isinstance(destinations, list):
                self.used_place_ids.update(value for value in destinations if isinstance(value, str))

        for place_id in sorted(self.used_place_ids):
            if place_id not in self.place_by_id:
                self.error("/places", "E_PLACE_REF", f"referenced place '{place_id}' does not exist")
                continue
            self._require_evidence(place_id, "identity", "/places", blocking=True)
            self._require_evidence(place_id, "location", "/places", blocking=True)

        for evidence_id, evidence in self.evidence_by_id.items():
            target_id = evidence.get("target_id")
            if self._has_text(target_id) and target_id not in self.target_ids:
                self.error(
                    "/evidence",
                    "E_EVIDENCE_TARGET",
                    f"evidence '{evidence_id}' targets unknown id '{target_id}'",
                )
            raw_source_ids = evidence.get("source_ids", [])
            source_ids = (
                raw_source_ids
                if self._string_list(raw_source_ids, allow_empty=True)
                else []
            )
            missing = [source_id for source_id in source_ids if source_id not in self.source_by_id]
            for source_id in missing:
                self.error(
                    "/evidence",
                    "E_SOURCE_REF",
                    f"evidence '{evidence_id}' references unknown source '{source_id}'",
                )
            if evidence.get("status") == "unknown":
                tasks = self.tasks_by_evidence.get(evidence_id, [])
                open_tasks = [task for task in tasks if task.get("status") == "open"]
                if not open_tasks:
                    self.error(
                        "/verification_tasks",
                        "E_UNKNOWN_TASK",
                        f"unknown evidence '{evidence_id}' requires an open verification task",
                    )
            self._validate_source_ownership(evidence_id, evidence)

        for task_id in sorted(self.used_task_ids):
            if task_id not in self.task_by_id:
                self.error("/checklist", "E_TASK_REF", f"unknown task id '{task_id}'")
        for task_id, task in self.task_by_id.items():
            if (
                task.get("blocking") is True
                and task.get("status") == "open"
                and task_id not in self.used_task_ids
            ):
                self.error(
                    "/checklist",
                    "E_CHECKLIST_COVERAGE",
                    f"open blocking task '{task_id}' must be grouped into checklist.task_ids",
                )
            evidence_id = task.get("evidence_id")
            if self._has_text(evidence_id) and evidence_id not in self.evidence_by_id:
                self.error(
                    "/verification_tasks",
                    "E_EVIDENCE_REF",
                    f"task '{task_id}' references unknown evidence '{evidence_id}'",
                )

        for source_id in sorted(set(self.source_by_id) - self.used_source_ids):
            self.warning("/sources", "W_UNUSED_SOURCE", f"source '{source_id}' is unused")
        for place_id in sorted(set(self.place_by_id) - self.used_place_ids):
            self.warning("/places", "W_UNUSED_PLACE", f"place '{place_id}' is unused")

    def _validate_source_ownership(
        self, evidence_id: str, evidence: dict[str, Any]
    ) -> None:
        aspect = evidence.get("aspect")
        if not isinstance(aspect, str):
            return
        status = evidence.get("status")
        if status == "unknown":
            return
        owners = SOURCE_OWNERS.get(aspect)
        verified_owners = VERIFIED_SOURCE_OWNERS.get(aspect)
        if not owners or not verified_owners:
            return
        raw_source_ids = evidence.get("source_ids", [])
        source_ids = (
            raw_source_ids
            if self._string_list(raw_source_ids, allow_empty=True)
            else []
        )
        sources = [
            self.source_by_id[source_id]
            for source_id in source_ids
            if source_id in self.source_by_id
        ]
        types = {
            source.get("type")
            for source in sources
            if isinstance(source.get("type"), str)
        }
        if status == "candidate" and types and not types.intersection(owners):
            self.warning(
                "/evidence",
                "W_SOURCE_OWNERSHIP",
                f"evidence '{evidence_id}' uses {sorted(types)} for {aspect}",
            )
            return
        if status != "verified":
            return

        eligible_types = {
            source.get("type")
            for source in sources
            if self._source_can_verify(source)
            and isinstance(source.get("type"), str)
        }
        if not eligible_types.intersection(verified_owners):
            self.error(
                "/evidence",
                "E_SOURCE_OWNERSHIP",
                f"verified evidence '{evidence_id}' lacks an admitted fact owner for {aspect}",
            )

    def _source_can_verify(self, source: dict[str, Any]) -> bool:
        source_type = source.get("type")
        access_method = source.get("access_method")
        if access_method not in SOURCE_ACCESS_METHODS:
            return False
        if access_method in FORBIDDEN_SOURCE_ACCESS_METHODS:
            return False
        if access_method == "fixture" and self.data.get("fixture") is not True:
            return False
        if access_method == "user_provided" and source_type != "user":
            return False
        return source_type != "ugc"

    def _nonempty_string(
        self, item: dict[str, Any], key: str, parent_path: str
    ) -> str | None:
        value = item.get(key)
        path = f"{parent_path}/{key}" if parent_path else f"/{key}"
        if not self._has_text(value):
            self.error(path, "E_STRING", "must be a non-empty string")
            return None
        return value

    def _parse_date(self, value: Any, path: str) -> date | None:
        parsed = self._date_or_none(value)
        if parsed is None:
            self.error(path, "E_DATE", "must be an ISO date in YYYY-MM-DD format")
        return parsed

    @staticmethod
    def _date_or_none(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _parse_datetime(self, value: Any, path: str) -> datetime | None:
        if not isinstance(value, str):
            self.error(path, "E_DATETIME", "must be an RFC 3339 datetime")
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            self.error(path, "E_DATETIME", "must be an RFC 3339 datetime")
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            self.error(path, "E_TIMEZONE", "datetime must include a UTC offset")
            return None
        return parsed

    def _parse_hhmm(self, value: Any, path: str) -> int | None:
        parsed = self._hhmm_or_none(value)
        if parsed is None:
            self.error(path, "E_TIME", "must use 24-hour HH:MM format")
        return parsed

    @staticmethod
    def _hhmm_or_none(value: Any) -> int | None:
        if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
            return None
        try:
            hour = int(value[:2])
            minute = int(value[3:])
        except ValueError:
            return None
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            return None
        return hour * 60 + minute

    @staticmethod
    def _minute_of_day(value: datetime) -> int:
        return value.hour * 60 + value.minute

    @staticmethod
    def _has_text(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _string_list(value: Any, allow_empty: bool) -> bool:
        return (
            isinstance(value, list)
            and (allow_empty or bool(value))
            and all(isinstance(item, str) and bool(item.strip()) for item in value)
        )

    @staticmethod
    def _number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def _enum(value: Any, allowed: set[str]) -> bool:
        return isinstance(value, str) and value in allowed

    @staticmethod
    def _nonnegative_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    @staticmethod
    def _positive_int(value: Any, allow_zero: bool = False) -> bool:
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        return value >= 0 if allow_zero else value > 0

    def _child_count(self) -> int:
        brief = self.data.get("brief", {})
        party = brief.get("party", {}) if isinstance(brief, dict) else {}
        children = party.get("children", []) if isinstance(party, dict) else []
        return len(children) if isinstance(children, list) else 0

    def _sorted_issues(self) -> list[Issue]:
        return sorted(self.issues, key=lambda issue: (issue.path, issue.code, issue.severity))


def validate_trip(data: Any) -> list[Issue]:
    return TripValidator(data).validate()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def count_issues(issues: Iterable[Issue], severity: str) -> int:
    return sum(issue.severity == severity for issue in issues)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trip_json", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    try:
        data = load_json(args.trip_json)
    except FileNotFoundError:
        print(f"ERROR / E_IO file does not exist: {args.trip_json}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR / E_IO {exc}", file=sys.stderr)
        return 2

    issues = validate_trip(data)
    errors = count_issues(issues, "ERROR")
    warnings = count_issues(issues, "WARNING")

    if args.json_output:
        print(
            json.dumps(
                {
                    "valid": errors == 0,
                    "errors": errors,
                    "warnings": warnings,
                    "issues": [asdict(issue) for issue in issues],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for issue in issues:
            print(f"{issue.severity} {issue.path} {issue.code} {issue.message}")
        print(f"SUMMARY errors={errors} warnings={warnings}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
