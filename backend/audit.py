"""Append-only audit trail of the shop agent loop: output/audit_trail.json

Format: one JSON array that only ever grows. Each run appends events; existing events are
never rewritten or deleted (the closing "]" is moved, nothing else). Safe across server
restarts and runs; a lock + fcntl file lock stop two requests writing at once.

Events per chat turn:
  run_start      time, run_id, who (guest / user:<id>), message (short, secrets redacted), page
  model_response time, finish_reason, tokens, tool calls requested
  tool_call      time, tool, args (short)
  tool_result    time, tool, result (short)
  retry          time, tool, detail (the model's output/tool args were rejected and retried)
  ux_feedback    time, feedback, adjustment (logged by the agent's log_usability_feedback tool)
  run_end        time, stop_reason, duration_ms, requests, tool_calls, tokens, products_shown, reply (short)

Privacy: no emails, no passwords, no password hashes. Text that looks like a password,
email, card number or API key is redacted before writing.
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:  # file lock on macOS/Linux; Windows falls back to the thread lock only
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

AUDIT_PATH = Path(os.getenv("AUDIT_PATH", Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"))
SHORT = 160
_lock = threading.Lock()

_REDACT = [
    (re.compile(r"(?i)\b(pass(word|wd|code)?|pwd)\b\s*(is|:|=)?\s*\S+"), r"\1 [REDACTED]"),
    (re.compile(r"pbkdf2_sha256\$\S+"), "[REDACTED-HASH]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[CARD]"),
    (re.compile(r"\b(sk|pk)-[A-Za-z0-9_-]{12,}\b"), "[API-KEY]"),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def redact(text: str) -> str:
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


def short(value: Any, n: int = SHORT) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, default=lambda o: getattr(o, "model_dump", lambda: str(o))(), ensure_ascii=False)
        except (TypeError, ValueError):
            value = str(value)
    value = redact(re.sub(r"\s+", " ", value)).strip()
    return value if len(value) <= n else value[: n - 1] + "…"


def append_events(events: Iterable[dict[str, Any]], path: Path | None = None) -> None:
    """Append events to the JSON array without touching earlier entries."""
    path = Path(path or AUDIT_PATH)
    events = list(events)
    if not events:
        return
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in events)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock, open(path, "a+b") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                f.write(f"[\n{body}\n]\n".encode())
                return
            # find the closing bracket at the end of the file
            pos, tail = size, b""
            while pos > 0:
                step = min(512, pos)
                pos -= step
                f.seek(pos)
                tail = f.read(step) + tail
                if tail.strip():
                    break
            stripped = tail.rstrip()
            if not stripped.endswith(b"]"):
                # Never wipe a damaged file: keep it and write to a side file instead.
                with open(path.with_suffix(".recovered.jsonl"), "ab") as side:
                    side.write(("\n".join(json.dumps(e) for e in events) + "\n").encode())
                return
            close_at = pos + len(stripped) - 1          # byte offset of the final "]"
            f.seek(close_at)
            f.truncate()                                 # removes only "]" + trailing newline
            sep = b"\n" if stripped[:-1].rstrip().endswith(b"[") else b",\n"
            f.write(sep + body.encode() + b"\n]\n")
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)


def events_from_messages(run_id: str, messages: list[Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Turn PydanticAI messages from this run into audit events (duck-typed for easy testing)."""
    events: list[dict[str, Any]] = []
    counts = {"requests": 0, "tool_calls": 0, "input_tokens": 0, "output_tokens": 0}
    for msg in messages:
        kind = getattr(msg, "kind", "")
        ts = getattr(msg, "timestamp", None)
        t = ts.isoformat(timespec="milliseconds") if hasattr(ts, "isoformat") else now()
        parts = list(getattr(msg, "parts", []) or [])
        if kind == "response":
            counts["requests"] += 1
            usage = getattr(msg, "usage", None)
            inp, out = getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0
            counts["input_tokens"] += inp
            counts["output_tokens"] += out
            calls = [getattr(p, "tool_name", "?") for p in parts if getattr(p, "part_kind", "") == "tool-call"]
            events.append({"time": t, "run_id": run_id, "event": "model_response",
                           "finish_reason": getattr(msg, "finish_reason", None), "tools_requested": calls,
                           "input_tokens": inp, "output_tokens": out})
            for p in parts:
                if getattr(p, "part_kind", "") == "tool-call":
                    counts["tool_calls"] += 1
                    args = p.args_as_dict() if hasattr(p, "args_as_dict") else getattr(p, "args", None)
                    events.append({"time": t, "run_id": run_id, "event": "tool_call",
                                   "tool": p.tool_name, "args": short(args)})
        elif kind == "request":
            for p in parts:
                pk = getattr(p, "part_kind", "")
                pt = getattr(p, "timestamp", None)
                pt = pt.isoformat(timespec="milliseconds") if hasattr(pt, "isoformat") else t
                if pk == "tool-return":
                    events.append({"time": pt, "run_id": run_id, "event": "tool_result",
                                   "tool": p.tool_name, "result": short(getattr(p, "content", ""))})
                elif pk == "retry-prompt":
                    events.append({"time": pt, "run_id": run_id, "event": "retry",
                                   "tool": getattr(p, "tool_name", None), "detail": short(getattr(p, "content", ""))})
    return events, counts
