#!/usr/bin/env python3
"""Merge sections_base.json + briefs/<id>.status + briefs/<id>.tokens -> sections.json"""
import json, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
BR = os.path.join(SP, "briefs")
NOW = sys.argv[1] if len(sys.argv) > 1 else ""

base = json.load(open(os.path.join(SP, "sections_base.json")))
out = []
for s in base:
    i = s["id"]
    md_path = os.path.join(BR, i + ".md")
    st_path = os.path.join(BR, i + ".status")
    tk_path = os.path.join(BR, i + ".tokens")
    status, flag = "pending", ""
    if os.path.exists(st_path):
        raw = open(st_path).read()
        for line in raw.split("\n"):
            if line.startswith("status:"):
                status = line.split(":", 1)[1].strip()
            elif line.startswith("flag_reason:"):
                flag = line.split(":", 1)[1].strip()
        # flag_reason may wrap to following lines
        if "flag_reason:" in raw:
            tail = raw.split("flag_reason:", 1)[1].strip()
            if len(tail) > len(flag):
                flag = tail
    if status not in ("ok", "slow", "urgent"):
        status = "pending" if not os.path.exists(md_path) else "ok"
    if status != "urgent":
        flag = ""
    tokens = 0
    if os.path.exists(tk_path):
        try:
            tokens = int(open(tk_path).read().strip())
        except Exception:
            tokens = 0
    s = dict(s)
    s["status"] = status if os.path.exists(md_path) else "pending"
    s["updated"] = NOW if os.path.exists(md_path) else ""
    s["tokens"] = tokens
    s["flag_reason"] = flag
    out.append(s)

json.dump(out, open(os.path.join(SP, "sections.json"), "w"), ensure_ascii=False, indent=1)
built = [s["id"] for s in out if s["status"] != "pending"]
missing = [s["id"] for s in out if s["status"] == "pending"]
flagged = [s["id"] for s in out if s["status"] == "urgent"]
slow = [s["id"] for s in out if s["status"] == "slow"]
tot = sum(s["tokens"] for s in out)
print("built %d/19  flagged=%s  slow=%s  missing=%s  tokens=%d"
      % (len(built), flagged or "-", slow or "-", missing or "-", tot))
