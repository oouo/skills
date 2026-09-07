#!/usr/bin/env python3

"""Resolve and verify the deterministic top-bar font contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "resources" / "top-bar-font-contract.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(RuntimeError):
    """Raised when the font contract cannot be resolved safely."""


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract() -> dict[str, object]:
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read top-bar font contract: {exc}") from exc

    font = contract.get("font")
    approval = contract.get("approval")
    if not isinstance(font, dict) or not isinstance(approval, dict):
        raise ContractError("Top-bar font contract is missing font or approval data.")
    for key in ("contract_id", "status"):
        if not isinstance(contract.get(key), str) or not contract[key]:
            raise ContractError(f"Top-bar font contract is missing {key}.")
    for key in ("path", "sha256", "license_path"):
        if not isinstance(font.get(key), str) or not font[key]:
            raise ContractError(f"Top-bar font contract is missing font.{key}.")
    if not SHA256_RE.fullmatch(str(font["sha256"])):
        raise ContractError("Bundled top-bar font SHA-256 is invalid.")
    if not isinstance(approval.get("provenance"), str) or not approval["provenance"]:
        raise ContractError("Top-bar font contract is missing approval provenance.")
    rendering = contract.get("rendering")
    if not isinstance(rendering, dict) or type(rendering.get("source_stroke_px")) is not int:
        raise ContractError("Top-bar contract is missing an integer source_stroke_px.")
    if rendering["source_stroke_px"] < 0:
        raise ContractError("Top-bar source_stroke_px must be non-negative.")
    record_path = approval.get("record_path")
    record_sha = approval.get("record_sha256")
    if not isinstance(record_path, str) or not isinstance(record_sha, str):
        raise ContractError("Top-bar contract is missing its approval record and hash.")
    record = ROOT / record_path
    if not record.is_file() or sha256(record) != record_sha:
        raise ContractError("Bundled top-bar approval record is missing or changed.")
    try:
        approved = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read bundled top-bar approval record: {exc}") from exc
    if not isinstance(approved, dict) or any(
        approved.get(key) != expected
        for key, expected in (
            ("status", "approved"),
            ("contract_id", contract["contract_id"]),
            ("font_sha256", font["sha256"]),
            ("rendering", rendering),
        )
    ):
        raise ContractError("Bundled top-bar contract differs from its approval record.")
    return contract


def resolve() -> dict[str, object]:
    contract = load_contract()
    contract_font = contract["font"]
    approval = contract["approval"]
    assert isinstance(contract_font, dict)
    assert isinstance(approval, dict)

    requested_font = os.environ.get("TOP_FONT", "")
    requested_sha = os.environ.get("TOP_FONT_SHA256", "").lower()
    requested_id = os.environ.get("TOP_FONT_CONTRACT_ID", "")
    approval_record = os.environ.get("TOP_FONT_APPROVAL_RECORD", "")

    rendering = contract["rendering"]
    assert isinstance(rendering, dict)
    default_stroke = rendering["source_stroke_px"]
    requested_stroke = os.environ.get("SOURCE_STROKE_W") or str(default_stroke)
    if not re.fullmatch(r"[0-9]+", requested_stroke):
        raise ContractError("SOURCE_STROKE_W must be a non-negative integer.")
    source_stroke = int(requested_stroke)
    if not requested_font and source_stroke != default_stroke:
        raise ContractError(
            f"SOURCE_STROKE_W={source_stroke} conflicts with bundled contract "
            f"{contract['contract_id']} ({default_stroke}px). "
            "Use a distinct explicitly approved override contract for another stroke."
        )
    if requested_font and requested_id == contract["contract_id"]:
        raise ContractError("An override must use a distinct contract ID.")

    if not requested_font:
        stray = [
            name
            for name, value in (
                ("TOP_FONT_SHA256", requested_sha),
                ("TOP_FONT_CONTRACT_ID", requested_id),
                ("TOP_FONT_APPROVAL_RECORD", approval_record),
            )
            if value
        ]
        if stray:
            raise ContractError(
                "TOP_FONT is unset but override fields are present: " + ", ".join(stray)
            )

        font_path = ROOT / str(contract_font["path"])
        license_path = ROOT / str(contract_font["license_path"])
        if not font_path.is_file():
            raise ContractError(f"Bundled top-bar font is missing: {font_path}")
        if not license_path.is_file():
            raise ContractError(f"Bundled font license is missing: {license_path}")
        actual_sha = sha256(font_path)
        expected_sha = str(contract_font["sha256"])
        if actual_sha != expected_sha:
            raise ContractError(
                f"Bundled top-bar font SHA-256 mismatch: {actual_sha}"
            )
        return {
            "contract_id": contract["contract_id"],
            "font_path": str(font_path),
            "font_sha256": actual_sha,
            "font_asset": str(contract_font["path"]),
            "source": "bundled",
            "approval_provenance": approval["provenance"],
            "approval_record_sha256": approval["record_sha256"],
            "source_stroke_px": source_stroke,
        }

    missing = [
        name
        for name, value in (
            ("TOP_FONT_SHA256", requested_sha),
            ("TOP_FONT_CONTRACT_ID", requested_id),
            ("TOP_FONT_APPROVAL_RECORD", approval_record),
        )
        if not value
    ]
    if missing:
        raise ContractError(
            "A top-bar font override needs explicit approval fields: "
            + ", ".join(missing)
        )
    if not SHA256_RE.fullmatch(requested_sha):
        raise ContractError("TOP_FONT_SHA256 must be 64 lowercase hexadecimal digits.")

    font_path = pathlib.Path(requested_font).expanduser().resolve()
    record_path = pathlib.Path(approval_record).expanduser().resolve()
    if not font_path.is_file():
        raise ContractError(f"Approved override font is missing: {font_path}")
    if not record_path.is_file():
        raise ContractError(f"Font approval record is missing: {record_path}")
    actual_sha = sha256(font_path)
    if actual_sha != requested_sha:
        raise ContractError(f"TOP_FONT SHA-256 mismatch: {actual_sha}")

    try:
        approved = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read override approval record as JSON: {exc}") from exc
    if not isinstance(approved, dict) or any(
        approved.get(key) != expected
        for key, expected in (
            ("status", "approved"),
            ("contract_id", requested_id),
            ("font_sha256", requested_sha),
        )
    ):
        raise ContractError(
            "Override approval record must approve the exact contract ID and font SHA-256."
        )
    approved_rendering = approved.get("rendering")
    if (
        not isinstance(approved_rendering, dict)
        or type(approved_rendering.get("source_stroke_px")) is not int
        or approved_rendering["source_stroke_px"] != source_stroke
    ):
        raise ContractError(
            "Override approval record must approve the exact integer rendering.source_stroke_px."
        )

    return {
        "contract_id": requested_id,
        "font_path": str(font_path),
        "font_sha256": actual_sha,
        "font_asset": "external-user-approved-font",
        "source": "explicit-user-approved-override",
        "approval_provenance": str(record_path),
        "approval_record_sha256": sha256(record_path),
        "source_stroke_px": source_stroke,
    }


def manifest_record(resolved: dict[str, object]) -> dict[str, object]:
    return {
        key: resolved[key]
        for key in (
            "contract_id",
            "source",
            "font_sha256",
            "font_asset",
            "approval_provenance",
            "approval_record_sha256",
            "source_stroke_px",
        )
    }


def verify_manifest(path: pathlib.Path, resolved: dict[str, object]) -> None:
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read package top-bar font manifest: {exc}") from exc
    expected = manifest_record(resolved)
    if recorded != expected:
        raise ContractError(
            "Package top-bar font manifest does not match the resolved contract."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format", choices=("tsv", "json", "manifest"), default="tsv"
    )
    parser.add_argument(
        "--verify-manifest", type=pathlib.Path, metavar="TOPBAR-FONT.json"
    )
    args = parser.parse_args()

    try:
        resolved = resolve()
        if args.verify_manifest:
            verify_manifest(args.verify_manifest, resolved)
    except ContractError as exc:
        print(f"HOLD {exc}", file=sys.stderr)
        return 1

    if args.format == "tsv":
        values = (
            resolved["font_path"],
            resolved["font_sha256"],
            resolved["contract_id"],
            resolved["source"],
            resolved["approval_provenance"],
            resolved["approval_record_sha256"] or "none",
            resolved["source_stroke_px"],
        )
        print("\t".join(str(value) for value in values))
    else:
        payload = resolved if args.format == "json" else manifest_record(resolved)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
