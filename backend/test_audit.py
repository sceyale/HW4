"""Audit trail checks (Problem 12). Uses a temporary audit file; no model or key needed.

    python test_audit.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

import audit

results: list[bool] = []


def check(ok, label: str) -> None:
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + label)


path = Path(tempfile.mkdtemp()) / "audit_trail.json"

print("-- append-only JSON --")
audit.append_events([{"event": "run_start", "n": 1}], path)
audit.append_events([{"event": "run_end", "n": 2}], path)
data = json.loads(path.read_text())
check(len(data) == 2 and data[0]["n"] == 1, "file is a valid JSON array after 2 appends")
first_bytes = path.read_bytes()[:40]
audit.append_events([{"event": "run_start", "n": 3}, {"event": "run_end", "n": 4}], path)
data = json.loads(path.read_text())
check([e["n"] for e in data] == [1, 2, 3, 4], "new runs are appended in order; nothing wiped")
check(path.read_bytes()[:40] == first_bytes, "earlier entries are byte-for-byte unchanged")
path.write_text(path.read_text() + "garbage")
audit.append_events([{"event": "x"}], path)
check("garbage" in path.read_text() and path.with_suffix(".recovered.jsonl").exists(),
      "a damaged file is never wiped (events go to a side file)")

print("\n-- redaction (password safety) --")
r = audit.redact("my password is Hunter2!! and email ada@yale.edu card 4111 1111 1111 1111 key sk-abcdefghijklmnop")
check("Hunter2" not in r and "ada@yale.edu" not in r and "4111" not in r and "sk-abc" not in r, f"redacted: {r}")
check("[REDACTED-HASH]" in audit.redact("pbkdf2_sha256$abc$def"), "password hashes are redacted")
check(len(audit.short("x" * 500)) == audit.SHORT, f"long args/results are shortened to {audit.SHORT} chars")

print("\n-- agent loop -> events --")
t = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
msgs = [
    NS(kind="request", parts=[NS(part_kind="user-prompt", content="hoodies in M?")], timestamp=t),
    NS(kind="response", timestamp=t, finish_reason="tool_call", usage=NS(input_tokens=900, output_tokens=40),
       parts=[NS(part_kind="tool-call", tool_name="search_products",
                 args_as_dict=lambda: {"category": "Hoodies", "size": "M"})]),
    NS(kind="request", timestamp=t, parts=[NS(part_kind="tool-return", tool_name="search_products",
                                              content={"total_matches": 19, "products": ["..."]}, timestamp=t)]),
    NS(kind="response", timestamp=t, finish_reason="tool_call", usage=NS(input_tokens=1500, output_tokens=60),
       parts=[NS(part_kind="tool-call", tool_name="final_result", args_as_dict=lambda: {"reply": "We have 19..."})]),
]
ev, counts = audit.events_from_messages("run1", msgs)
kinds = [e["event"] for e in ev]
check(kinds == ["model_response", "tool_call", "tool_result", "model_response", "tool_call"], f"events: {kinds}")
tc = ev[1]
check(tc["tool"] == "search_products" and "Hoodies" in tc["args"] and tc["time"].startswith("2026-10-24"),
      "tool_call has time, tool name and short args")
check("19" in ev[2]["result"], "tool_result has a short result")
check(counts == {"requests": 2, "tool_calls": 2, "input_tokens": 2400, "output_tokens": 100}, f"run totals: {counts}")

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
