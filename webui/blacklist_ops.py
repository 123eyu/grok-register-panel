# -*- coding: utf-8 -*-
"""Blacklist read/reset helpers for monitor UI."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "log"
BS = ROOT / "browser_session.py"
BLACKLIST_SNAPSHOT = LOG_DIR / "blacklist_snapshot.json"

BASELINE_ASN = {7922, 5650}
BASELINE_ASN_NOTES = {
    7922: "Comcast Cable",
    5650: "Frontier Communications",
}
BASELINE_ISP = (
    "comcast cable",
    "comcast ip services",
    "frontier communications",
)


def read_blacklist() -> dict:
    errors = []
    items = []
    nums = set()
    isp = []
    try:
        text = BS.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "count": 0,
            "asns": [],
            "items": [],
            "isp_keywords": [],
            "errors": [str(e)],
            "mtime": None,
        }
    try:
        m = re.search(r"_BLOCKED_ASN_NUMS\s*=\s*\{([^}]*)\}", text)
        if m:
            for x in re.findall(r"\d+", m.group(1)):
                nums.add(int(x))
        block = re.search(r"_BLOCKED_ASN_SUBSTR\s*=\s*\((.*?)\)", text, re.S)
        if block:
            for line in block.group(1).splitlines():
                am = re.search(r'"AS(\d+)"\s*,?\s*(?:#\s*(.*))?', line)
                if am:
                    n = int(am.group(1))
                    nums.add(n)
                    note = (am.group(2) or "").strip()
                    items.append({"asn": n, "label": f"AS{n}", "note": note})
        isp_block = re.search(r"_BLOCKED_ISP_SUBSTR\s*=\s*\((.*?)\)", text, re.S)
        if isp_block:
            isp = re.findall(r'"([^"]+)"', isp_block.group(1))
        labeled = {i["asn"] for i in items}
        for n in sorted(nums):
            if n not in labeled:
                items.append({"asn": n, "label": f"AS{n}", "note": ""})
        items.sort(key=lambda x: x["asn"])
    except Exception as e:
        errors.append(f"parse: {e}")
    try:
        mtime = BS.stat().st_mtime
    except Exception:
        mtime = None
    return {
        "ok": len(errors) == 0,
        "error": errors[0] if errors else None,
        "count": len(nums),
        "asns": sorted(nums),
        "items": items,
        "isp_keywords": isp,
        "errors": errors,
        "mtime": mtime,
        "mtime_human": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)) if mtime else None,
        "source": str(BS),
    }


def reset_blacklist(mode: str = "baseline") -> dict:
    """Reset auto-expanded ASN blacklist.

    baseline: keep only Comcast/Frontier fuse
    empty: clear all ASN/ISP rules
    """
    mode = (mode or "baseline").strip().lower()
    if mode not in ("baseline", "empty"):
        return {"ok": False, "error": f"unknown mode {mode}"}

    before = read_blacklist()
    LOG_DIR.mkdir(exist_ok=True)
    try:
        BLACKLIST_SNAPSHOT.write_text(
            json.dumps(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "mode": mode,
                    "before": {
                        "asns": before.get("asns"),
                        "items": before.get("items"),
                        "isp_keywords": before.get("isp_keywords"),
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    try:
        bak = BS.with_name(BS.name + f".bak.reset-{time.strftime('%Y%m%d-%H%M%S')}")
        bak.write_text(BS.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"backup failed: {e}"}

    if mode == "empty":
        nums = set()
        notes = {}
        isps = ()
    else:
        nums = set(BASELINE_ASN)
        notes = dict(BASELINE_ASN_NOTES)
        isps = BASELINE_ISP

    substr_lines = ["_BLOCKED_ASN_SUBSTR = ("]
    for n in sorted(nums):
        note = notes.get(n) or ""
        if note:
            substr_lines.append(f'    "AS{n}",  # {note}')
        else:
            substr_lines.append(f'    "AS{n}",')
    if not nums:
        substr_lines.append("    # empty after reset")
    substr_lines.append(")")
    new_substr = "\n".join(substr_lines)

    isp_lines = ["_BLOCKED_ISP_SUBSTR = ("]
    for k in isps:
        isp_lines.append(f'    "{k}",')
    if not isps:
        isp_lines.append("    # empty after reset")
    isp_lines.append(")")
    new_isp = "\n".join(isp_lines)

    if nums:
        new_nums = "_BLOCKED_ASN_NUMS = {" + ", ".join(str(n) for n in sorted(nums)) + "}"
    else:
        new_nums = "_BLOCKED_ASN_NUMS = set()"

    src = BS.read_text(encoding="utf-8")
    src2, n1 = re.subn(
        r"_BLOCKED_ASN_SUBSTR\s*=\s*\(.*?\)",
        new_substr,
        src,
        count=1,
        flags=re.S,
    )
    src2, n2 = re.subn(
        r"_BLOCKED_ISP_SUBSTR\s*=\s*\(.*?\)",
        new_isp,
        src2,
        count=1,
        flags=re.S,
    )
    src2, n3 = re.subn(
        r"_BLOCKED_ASN_NUMS\s*=\s*\{[^}]*\}|_BLOCKED_ASN_NUMS\s*=\s*set\(\)",
        new_nums,
        src2,
        count=1,
    )
    if n1 < 1 or n2 < 1 or n3 < 1:
        return {
            "ok": False,
            "error": f"replace failed n1={n1} n2={n2} n3={n3}",
            "before_count": before.get("count"),
        }
    BS.write_text(src2, encoding="utf-8")
    after = read_blacklist()
    return {
        "ok": True,
        "mode": mode,
        "before_count": before.get("count"),
        "before_asns": before.get("asns"),
        "after_count": after.get("count"),
        "after_asns": after.get("asns"),
        "items": after.get("items"),
        "isp_keywords": after.get("isp_keywords"),
        "count": after.get("count"),
        "asns": after.get("asns"),
        "snapshot": str(BLACKLIST_SNAPSHOT),
        "message": (
            f"已重置为基线熔断 {sorted(nums)}"
            if mode == "baseline"
            else "已清空全部黑名单"
        ),
    }
