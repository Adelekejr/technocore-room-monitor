#!/usr/bin/env python3
"""Inspect a public Technocore room and produce a useful integrity report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

APP_VERSION = "1.0.0"
DEFAULT_BASE_URL = "https://technocore.chat"
DEFAULT_TIMEOUT = 20.0
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
ROOM_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}")
DID_PATTERN = re.compile(r"^did:key:z6Mk[1-9A-HJ-NP-Za-km-z]+$")


class MonitorError(RuntimeError):
    """A controlled monitor or validation error."""


def validate_room(room: str) -> str:
    if ROOM_PATTERN.fullmatch(room) is None:
        raise MonitorError(
            "room must match ^[a-z0-9][a-z0-9_-]{0,47}$"
        )
    return room


def validate_limit(limit: int) -> int:
    if not 1 <= limit <= 200:
        raise MonitorError("limit must be between 1 and 200")
    return limit


def validate_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    try:
        parsed = urlsplit(normalized)
    except ValueError as error:
        raise MonitorError("base URL is malformed") from error
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise MonitorError("base URL must use HTTPS except for loopback tests")
    if not parsed.netloc or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise MonitorError("base URL is malformed")
    return normalized


def fetch_room(
    room: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    limit: int = 50,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    room = validate_room(room)
    limit = validate_limit(limit)
    base_url = validate_base_url(base_url)
    query = urlencode({"format": "json", "limit": limit})
    request = Request(
        f"{base_url}/r/{room}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": f"technocore-room-monitor/{APP_VERSION}",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        raise MonitorError(f"Technocore returned HTTP {error.code}") from None
    except URLError as error:
        raise MonitorError(f"could not reach Technocore: {error.reason}") from None
    except TimeoutError:
        raise MonitorError("Technocore request timed out") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise MonitorError("Technocore response exceeded the safety limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MonitorError("Technocore returned invalid JSON") from error
    if not isinstance(payload, dict):
        raise MonitorError("Technocore returned a JSON value that is not an object")
    return payload


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_response(payload: dict[str, Any], requested_room: str) -> list[str]:
    warnings: list[str] = []
    if payload.get("room") != requested_room:
        raise MonitorError("response room does not match requested room")
    for field in ("count", "first_seq", "last_seq"):
        if not _is_nonnegative_int(payload.get(field)):
            raise MonitorError(f"response field {field!r} is invalid")
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise MonitorError("response field 'messages' is not a list")
    if payload["count"] != len(messages):
        warnings.append(
            f"count mismatch: response says {payload['count']}, received {len(messages)} messages"
        )
    if messages and payload["first_seq"] != messages[0].get("seq"):
        warnings.append("first_seq does not match the first message sequence")
    if messages and payload["last_seq"] != messages[-1].get("seq"):
        warnings.append("last_seq does not match the last message sequence")
    return warnings


def analyze_room(payload: dict[str, Any], requested_room: str) -> dict[str, Any]:
    warnings = validate_response(payload, requested_room)
    messages = payload["messages"]
    sequences: list[int] = []
    did_count = 0
    anonymous_count = 0
    malformed_count = 0
    malformed_details: list[str] = []
    duplicate_sequences: list[int] = []
    seen_sequences: set[int] = set()
    timestamp_count = 0
    text_lengths: list[int] = []

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            malformed_count += 1
            malformed_details.append(f"message {index}: record is not an object")
            continue
        seq = message.get("seq")
        source = message.get("from")
        text = message.get("text")
        if not _is_nonnegative_int(seq):
            malformed_count += 1
            malformed_details.append(f"message {index}: invalid seq")
        else:
            sequences.append(seq)
            if seq in seen_sequences:
                duplicate_sequences.append(seq)
            seen_sequences.add(seq)
        if not isinstance(source, str):
            malformed_count += 1
            malformed_details.append(f"message {index}: invalid from")
        elif DID_PATTERN.fullmatch(source):
            did_count += 1
        else:
            anonymous_count += 1
        if not isinstance(text, str) or not text.strip():
            malformed_count += 1
            malformed_details.append(f"message {index}: empty or invalid text")
        else:
            text_lengths.append(len(text))
        if isinstance(message.get("ts"), str) and message["ts"].strip():
            timestamp_count += 1

    if sequences != sorted(sequences):
        warnings.append("message sequences are not in ascending order")
    if duplicate_sequences:
        warnings.append(f"duplicate sequences found: {sorted(set(duplicate_sequences))}")
    if malformed_count:
        warnings.append(f"{malformed_count} malformed field or record checks detected")
    if payload["last_seq"] < payload["first_seq"] and payload["count"]:
        warnings.append("last_seq is lower than first_seq")

    total = len(messages)
    return {
        "schema": "technocore-room-monitor-report-v1",
        "monitor_version": APP_VERSION,
        "room": requested_room,
        "server_count": payload["count"],
        "received_messages": total,
        "first_seq": payload["first_seq"],
        "last_seq": payload["last_seq"],
        "sequence_span": (
            payload["last_seq"] - payload["first_seq"] + 1
            if total
            else 0
        ),
        "verified_did_messages": did_count,
        "anonymous_or_unverified_messages": anonymous_count,
        "timestamped_messages": timestamp_count,
        "malformed_messages_or_fields": malformed_count,
        "average_text_length": round(sum(text_lengths) / len(text_lengths), 2)
        if text_lengths
        else 0,
        "duplicate_sequences": sorted(set(duplicate_sequences)),
        "warnings": warnings,
        "malformed_details": malformed_details,
        "source_endpoint": f"/r/{requested_room}?format=json&limit={total or 0}",
        "analyzed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def report_markdown(report: dict[str, Any]) -> str:
    warning_text = (
        "\n".join(f"- {warning}" for warning in report["warnings"])
        if report["warnings"]
        else "- None detected"
    )
    return f"""# Technocore Room Report\n\nGenerated by `technocore-room-monitor` **v{report['monitor_version']}**.\n\n| Metric | Value |\n|---|---:|\n| Room | `{report['room']}` |\n| Server-reported messages | {report['server_count']} |\n| Messages analyzed | {report['received_messages']} |\n| Sequence range | `{report['first_seq']}`–`{report['last_seq']}` |\n| Verified DID messages | {report['verified_did_messages']} |\n| Anonymous or unverified messages | {report['anonymous_or_unverified_messages']} |\n| Timestamped messages | {report['timestamped_messages']} |\n| Malformed messages or fields | {report['malformed_messages_or_fields']} |\n| Average text length | {report['average_text_length']} characters |\n| Analyzed at | `{report['analyzed_at']}` |\n\n## Integrity warnings\n\n{warning_text}\n\n## What this report means\n\nA verified DID count means the `from` field matched the expected Ed25519 `did:key:z6Mk...` shape. It does not independently prove that every message is honest or that a DID belongs to a particular person. Sequence and schema checks describe the response received at analysis time; they are not a guarantee about future room state.\n\nSource endpoint: `{report['source_endpoint']}`\n"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a public Technocore room and create an integrity report."
    )
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--room", default="lobby", help="room name (default: lobby)")
    parser.add_argument(
        "--limit", type=int, default=50, help="messages to request, 1-200 (default: 50)"
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL, help="Technocore base URL"
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the JSON report to this path instead of stdout",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        help="also write a human-readable Markdown report to this path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = fetch_room(
            args.room,
            base_url=args.base_url,
            limit=args.limit,
            timeout=args.timeout,
        )
        report = analyze_room(payload, args.room)
        serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(serialized, encoding="utf-8")
            print(args.output)
        else:
            print(serialized, end="")
        if args.markdown:
            args.markdown.write_text(report_markdown(report), encoding="utf-8")
            print(f"Markdown report: {args.markdown}", file=sys.stderr)
        return 0
    except (MonitorError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
