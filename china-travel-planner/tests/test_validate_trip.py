from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "wan-nan-roadtrip.json"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_trip import count_issues, validate_trip  # noqa: E402


def load_fixture() -> dict:
    with FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)


def codes(data: dict, severity: str | None = None) -> set[str]:
    return {
        issue.code
        for issue in validate_trip(data)
        if severity is None or issue.severity == severity
    }


def shift_segments(day: dict, start_index: int, minutes: int) -> None:
    for segment in day["segments"][start_index:]:
        for key in ("start_at", "end_at"):
            value = datetime.fromisoformat(segment[key]) + timedelta(minutes=minutes)
            segment[key] = value.isoformat()


def add_ugc_source(trip: dict, access_method: str) -> str:
    source_id = "src-user-forwarded-ugc"
    trip["sources"].append(
        {
            "id": source_id,
            "type": "ugc",
            "title": "User-forwarded restaurant review",
            "access_method": access_method,
            "url": "https://example.com/restaurant-review",
            "accessed_at": "2026-08-09T09:40:00+08:00",
        }
    )
    return source_id


class TripFixtureTests(unittest.TestCase):
    def test_wan_nan_fixture_is_a_valid_food_first_family_draft(self) -> None:
        trip = load_fixture()

        self.assertIs(trip["fixture"], True)
        self.assertEqual(trip["status"], "draft")
        self.assertEqual(trip["brief"]["party"]["adults"], 4)
        self.assertEqual(len(trip["brief"]["party"]["children"]), 1)
        self.assertEqual(len(trip["days"]), 2)
        self.assertEqual(trip["brief"]["transport"], "self-drive")
        self.assertEqual(trip["brief"]["priorities"][0], "food")

        issues = validate_trip(trip)
        self.assertEqual(count_issues(issues, "ERROR"), 0, issues)
        self.assertIn("W_UNKNOWN", {issue.code for issue in issues})

    def test_overlap_is_an_error(self) -> None:
        trip = load_fixture()
        trip["days"][0]["segments"][1]["start_at"] = (
            "2026-08-15T08:10:00+08:00"
        )

        self.assertIn("E_OVERLAP", codes(trip, "ERROR"))

    def test_large_unscheduled_gap_is_an_error(self) -> None:
        trip = load_fixture()
        shift_segments(trip["days"][0], start_index=1, minutes=40)

        self.assertIn("E_GAP", codes(trip, "ERROR"))

    def test_broken_place_chain_is_an_error(self) -> None:
        trip = load_fixture()
        trip["days"][0]["segments"][2]["from_place_id"] = "shanghai-test-origin"

        self.assertIn("E_PLACE_CHAIN", codes(trip, "ERROR"))

    def test_continuous_drive_limit_is_an_error(self) -> None:
        trip = load_fixture()
        trip["constraints"]["driving"]["max_continuous_minutes"] = 60

        self.assertIn("E_CONTINUOUS_DRIVE", codes(trip, "ERROR"))

    def test_child_latest_day_end_is_an_error(self) -> None:
        trip = load_fixture()
        trip["constraints"]["child"]["latest_day_end"] = "16:00"

        self.assertIn("E_CHILD_DAY_END", codes(trip, "ERROR"))

    def test_missing_required_meal_is_an_error(self) -> None:
        trip = load_fixture()
        lunch = next(
            segment
            for segment in trip["days"][0]["segments"]
            if segment["id"] == "d1-lunch"
        )
        lunch.pop("meal_kind")
        lunch["type"] = "buffer"

        self.assertIn("E_MEAL_WINDOW", codes(trip, "ERROR"))

    def test_dangling_source_reference_is_an_error(self) -> None:
        trip = load_fixture()
        evidence = next(
            item for item in trip["evidence"] if item["id"] == "ev-d1-drive-1-route"
        )
        evidence["source_ids"] = ["missing-map-source"]

        self.assertIn("E_SOURCE_REF", codes(trip, "ERROR"))

    def test_unknown_evidence_without_task_is_an_error(self) -> None:
        trip = load_fixture()
        trip["verification_tasks"] = []
        trip["checklist"][0]["task_ids"] = []

        self.assertIn("E_UNKNOWN_TASK", codes(trip, "ERROR"))

    def test_open_blocking_task_requires_group_ready_checklist_coverage(self) -> None:
        trip = load_fixture()
        for item in trip["checklist"]:
            item["task_ids"] = [
                task_id
                for task_id in item.get("task_ids", [])
                if task_id != "verify-stay-parking"
            ]

        self.assertIn("E_CHECKLIST_COVERAGE", codes(trip, "ERROR"))

    def test_nonblocking_task_may_stay_out_of_group_ready_checklist(self) -> None:
        trip = load_fixture()
        for item in trip["checklist"]:
            item["task_ids"] = [
                task_id
                for task_id in item.get("task_ids", [])
                if task_id != "verify-ningguo-lunch-hours"
            ]

        self.assertNotIn("E_CHECKLIST_COVERAGE", codes(trip, "ERROR"))

    def test_candidate_evidence_emits_warning_without_error(self) -> None:
        trip = load_fixture()
        candidate = next(
            item
            for item in trip["evidence"]
            if item["id"] == "ev-ningguo-lunch-hours"
        )

        self.assertEqual(candidate["status"], "candidate")
        issues = validate_trip(copy.deepcopy(trip))
        self.assertEqual(count_issues(issues, "ERROR"), 0, issues)
        self.assertIn("W_CANDIDATE", {issue.code for issue in issues})

    def test_overnight_stay_requires_checkin_segment(self) -> None:
        trip = load_fixture()
        trip["days"][0]["segments"] = [
            segment
            for segment in trip["days"][0]["segments"]
            if segment["id"] != "d1-checkin"
        ]

        self.assertIn("E_CHECKIN_MISSING", codes(trip, "ERROR"))

    def test_exact_distance_without_distance_evidence_is_an_error(self) -> None:
        trip = load_fixture()
        trip["days"][0]["segments"][0]["distance_km"] = 123

        self.assertIn("E_FALSE_PRECISION", codes(trip, "ERROR"))

    def test_unknown_evidence_requires_an_open_task(self) -> None:
        trip = load_fixture()
        task = next(
            task
            for task in trip["verification_tasks"]
            if task["evidence_id"] == "ev-stay-parking"
        )
        task["status"] = "done"

        self.assertIn("E_UNKNOWN_TASK", codes(trip, "ERROR"))

    def test_source_requires_an_access_method(self) -> None:
        trip = load_fixture()
        trip["sources"][0].pop("access_method")

        self.assertIn("E_SOURCE_ACCESS_REQUIRED", codes(trip, "ERROR"))

    def test_public_web_requires_a_public_url(self) -> None:
        trip = load_fixture()
        source = trip["sources"][1]
        source["access_method"] = "public_web"

        self.assertIn("E_PUBLIC_SOURCE_URL", codes(trip, "ERROR"))

    def test_user_fact_requires_user_provided_access(self) -> None:
        trip = load_fixture()
        source = trip["sources"][0]
        source["access_method"] = "public_web"
        source["url"] = "https://example.com/traveler-brief"

        self.assertIn("E_USER_SOURCE_ACCESS", codes(trip, "ERROR"))

    def test_fixture_source_is_rejected_for_a_real_trip(self) -> None:
        trip = load_fixture()
        trip["fixture"] = False

        self.assertIn("E_FIXTURE_SOURCE", codes(trip, "ERROR"))

    def test_forbidden_ugc_access_methods_are_errors(self) -> None:
        for access_method in [
            "unofficial_connector",
            "experimental_connector",
            "reverse_engineered_api",
            "browser_automation",
        ]:
            with self.subTest(access_method=access_method):
                trip = load_fixture()
                source_id = add_ugc_source(trip, access_method)
                trip["evidence"].append(
                    {
                        "id": "ev-lunch-experience",
                        "target_id": "ningguo-lunch",
                        "aspect": "experience",
                        "status": "candidate",
                        "source_ids": [source_id],
                    }
                )

                self.assertIn("E_SOURCE_ACCESS_FORBIDDEN", codes(trip, "ERROR"))

    def test_user_provided_ugc_candidate_is_allowed(self) -> None:
        trip = load_fixture()
        source_id = add_ugc_source(trip, "user_provided")
        trip["evidence"].append(
            {
                "id": "ev-lunch-experience",
                "target_id": "ningguo-lunch",
                "aspect": "experience",
                "status": "candidate",
                "source_ids": [source_id],
            }
        )

        issues = validate_trip(trip)
        self.assertEqual(count_issues(issues, "ERROR"), 0, issues)
        self.assertIn("W_CANDIDATE", {issue.code for issue in issues})

    def test_user_provided_ugc_cannot_verify_experience(self) -> None:
        trip = load_fixture()
        source_id = add_ugc_source(trip, "user_provided")
        trip["evidence"].append(
            {
                "id": "ev-lunch-experience",
                "target_id": "ningguo-lunch",
                "aspect": "experience",
                "status": "verified",
                "source_ids": [source_id],
            }
        )

        self.assertIn("E_SOURCE_OWNERSHIP", codes(trip, "ERROR"))

    def test_user_forwarded_official_notice_cannot_verify_facts(self) -> None:
        trip = load_fixture()
        source = next(
            item for item in trip["sources"] if item["id"] == "src-official-fixture"
        )
        source["access_method"] = "user_provided"

        self.assertIn("E_SOURCE_OWNERSHIP", codes(trip, "ERROR"))

    def test_verified_hours_require_an_admitted_fact_owner(self) -> None:
        trip = load_fixture()
        source_id = add_ugc_source(trip, "public_web")
        evidence = next(
            item
            for item in trip["evidence"]
            if item["id"] == "ev-ningguo-lunch-hours"
        )
        evidence["status"] = "verified"
        evidence["source_ids"] = [source_id]

        self.assertIn("E_SOURCE_OWNERSHIP", codes(trip, "ERROR"))

    def test_fact_owner_can_verify_hours_with_ugc_corroboration(self) -> None:
        trip = load_fixture()
        source_id = add_ugc_source(trip, "user_provided")
        evidence = next(
            item
            for item in trip["evidence"]
            if item["id"] == "ev-ningguo-lunch-hours"
        )
        evidence["status"] = "verified"
        evidence["source_ids"].append(source_id)

        self.assertNotIn("E_SOURCE_OWNERSHIP", codes(trip, "ERROR"))


if __name__ == "__main__":
    unittest.main()
