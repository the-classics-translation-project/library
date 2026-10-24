#!/usr/bin/env python3
"""Read-only, deterministic guide-task discovery. Never submits to a model or relay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _guide_exists(folder: Path) -> bool:
    pointer = _read(folder / "current.json")
    if pointer is None:
        return False
    if not isinstance(pointer, dict) or set(pointer) != {"sha256"}:
        raise ValueError(f"Invalid guide pointer: {folder}")
    fingerprint = pointer["sha256"]
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ValueError(f"Invalid guide hash: {folder}")
    content = (folder / (fingerprint + ".md")).read_bytes()
    if hashlib.sha256(content).hexdigest() != fingerprint or not content.strip():
        raise ValueError(f"Corrupt saved guide: {folder}")
    return True


def plan_entries(works: list[dict], guide_requests: list[dict], has_guide):
    """Pure planner: has_guide(work, target_or_None) checks saved output.

    Legacy combined requests cover BOTH guide types until imported; they must
    not create duplicate independent tasks.
    """
    legacy: dict[tuple[str, str], int] = {}
    for entry in guide_requests:
        request = entry["request"]
        pair = (request["work"], request["target"])
        if pair in legacy and legacy[pair] != entry["issue"]:
            # Multiple accepted historical requests are legal: prefer the oldest.
            continue
        legacy[pair] = entry["issue"]
    result = []
    for work in sorted(works, key=lambda w: w["id"]):
        wid = work["id"]
        targets = sorted(set(work["targets"]))
        if not work["ready"]:
            result.append({"type": "work_analysis", "work": wid,
                           "state": "blocked", "reason": "source not ready"})
            continue
        work_saved = has_guide(wid, None)
        work_legacy = next((legacy[(wid, t)] for t in targets
                            if (wid, t) in legacy), None)
        result.append({"type": "work_analysis", "work": wid,
                       "state": "completed" if work_saved else
                                "covered_by_legacy_issue" if work_legacy else "proposed",
                       **({"issue": work_legacy} if not work_saved and work_legacy else {})})
        for target in targets:
            saved = has_guide(wid, target)
            issue = legacy.get((wid, target))
            state = ("completed" if saved else
                     "covered_by_legacy_issue" if issue else
                     "proposed" if work_saved else "awaiting_work_analysis")
            result.append({"type": "target_guide", "work": wid, "target": target,
                           "state": state,
                           **({"issue": issue} if not saved and issue else {})})
    return result


def discover(root: Path) -> dict:
    """Compute proposals from recorded queue and saved pointers; no writes."""
    from ctp import validate_work, source_fingerprint
    queue = _read(root / "queue.json", {})
    if queue.get("schema_version") != 1 or not isinstance(queue.get("works"), list):
        raise ValueError("Invalid work queue")
    guides = _read(root / "guide-requests.json", {"schema_version": 1, "requests": []})
    if guides.get("schema_version") != 1 or not isinstance(guides.get("requests"), list):
        raise ValueError("Invalid legacy guide queue")
    works = []
    fingerprints = {}
    for row in queue["works"]:
        wid = row["id"]
        wd = root / "books" / wid
        rights = _read(wd / "rights.json", {})
        ready = (rights.get("status") == "acquired" and
                 (wd / "work.json").is_file() and
                 (wd / "structure.json").is_file())
        if ready:
            validate_work(wd)
            fingerprints[wid] = source_fingerprint(wd)
        works.append({"id": wid, "targets": row["targets"], "ready": ready})
    valid_requests = []
    for entry in guides["requests"]:
        req = entry["request"]
        if req["work"] not in fingerprints:
            continue
        # Never let a historical request for an earlier source suppress new work.
        if req["source_fingerprint"] == fingerprints[req["work"]]:
            valid_requests.append(entry)
    def exists(wid, target):
        wd = root / "books" / wid
        folder = (wd / "reference" if target is None else
                  wd / "editions" / target / "reference")
        return _guide_exists(folder)
    rows = plan_entries(works, valid_requests, exists)
    return {"schema_version": 1, "read_only": True, "model_called": False,
            "relay_submitted": False, "tasks": rows,
            "proposed": [r for r in rows if r["state"] == "proposed"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(discover(args.root), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
