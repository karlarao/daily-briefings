#!/usr/bin/env python3
"""Event Horizon generator: render events[] as the 5-column timeline table.

Computes `inside14` FROM THE ROW DATES rather than taking it from prose. That
computation is what caught the edition-097 synthesis lede asserting every dated
cutover fell inside fourteen days ("fifteen of them") when the board held 31
inside 14 days and the briefs carried 95 dated mentions beyond the window. Any
figure quoted in prose must come back out of `facts()`.

Column contract (5 columns, asserted by lens_guard.assert_table_shape):
    Date | Event | Lane | What to do with it | Src
"""
import datetime, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "lens"))
from lens_links import cite                                   # noqa: E402

HEAD = ("<table class='tbl'><thead><tr><th>Date</th><th>Event</th><th>Lane</th>"
        "<th>What to do with it</th><th>Src</th></tr></thead><tbody>")


def _d(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def chip(n):
    """hot <=14d, warm <=30d, else plain; a passed date is 'past'."""
    if n is None:
        return "<span class='chip tbd'>TBD</span>"
    if n < 0:
        return "<span class='chip past'>%dd past</span>" % abs(n)
    if n == 0:
        return "<span class='chip hot'>TODAY</span>"
    if n <= 14:
        return "<span class='chip hot'>%dd</span>" % n
    if n <= 30:
        return "<span class='chip warm'>%dd</span>" % n
    return "<span class='chip'>%dd</span>" % n


def facts(rows, today):
    """Every number the prose is allowed to quote, computed from the rows."""
    t0 = _d(today)
    dated = [r for r in rows if _d(r.get("date"))]
    undated = [r for r in rows if not _d(r.get("date"))]
    outs = [( _d(r["date"]) - t0).days for r in dated]
    return dict(
        total=len(rows), dated=len(dated), undated=len(undated),
        inside14=sum(1 for n in outs if 0 <= n <= 14),
        inside7=sum(1 for n in outs if 0 <= n <= 7),
        today_rows=sum(1 for n in outs if n == 0),
        past=sum(1 for n in outs if n < 0),
        beyond30=sum(1 for n in outs if n > 30),
        distinct_dates_inside14=len({r["date"] for r, n in zip(dated, outs)
                                     if 0 <= n <= 14}),
        max_out=max(outs) if outs else None,
    )


def render(rows, today, *, horizon=60, lane_of=None, act_of=None):
    """Return (html, shown_count). Rows beyond `horizon` days are not shown."""
    t0 = _d(today)
    lane_of = lane_of or {}
    act_of = act_of or {}
    keyed = []
    for r in rows:
        d = _d(r.get("date"))
        n = None if d is None else (d - t0).days
        if n is not None and (n < 0 or n > horizon):
            continue
        keyed.append((n if n is not None else 10 ** 6, r, n))
    keyed.sort(key=lambda x: (x[0], x[1].get("k", "")))
    out = [HEAD]
    for _, r, n in keyed:
        lane = lane_of.get(r["k"], r.get("lane", "&mdash;"))
        act = act_of.get(r["k"], r.get("act", "")) or "&mdash;"
        src = cite(r.get("url"), r.get("last_seen"), r.get("first_seen"), today,
                   today=today)
        date_cell = (r.get("date") or "TBD") + " " + chip(n)
        out.append("<tr><td class='dt'>%s</td><td>%s</td><td class='lane'>%s</td>"
                   "<td class='act'>%s</td><td>%s</td></tr>"
                   % (date_cell, r.get("t", ""), lane, act, src))
    out.append("</tbody></table>")
    return "".join(out), len(keyed)


def _selftest():
    today = "2026-10-20"
    rows = [
        {"k": "a", "date": "2026-10-20", "t": "today", "url": "http://x/a"},
        {"k": "b", "date": "2026-10-27", "t": "in 7"},
        {"k": "c", "date": "2026-11-03", "t": "in 14"},
        {"k": "d", "date": "2026-11-04", "t": "in 15"},
        {"k": "e", "date": "2026-12-20", "t": "in 61"},
        {"k": "f", "date": "2026-10-19", "t": "yesterday"},
        {"k": "g", "t": "undated"},
    ]
    f = facts(rows, today)
    want = dict(total=7, dated=6, undated=1, inside14=3, inside7=2, today_rows=1,
                past=1, beyond30=1, distinct_dates_inside14=3, max_out=61)
    bad = {k: (f[k], v) for k, v in want.items() if f[k] != v}
    html, shown = render(rows, today)
    cols = html.count("<th>")
    cells = [len(re.findall(r"<td", tr)) for tr in re.findall(r"<tr>(?:(?!</tr>).)*</tr>", html)[1:]]
    ok = (not bad) and shown == 5 and cols == 5 and set(cells) == {5}
    if bad:
        print("  facts mismatch:", bad)
    if not ok:
        print("  shown=%s cols=%s cells=%s" % (shown, cols, set(cells)))
    return "PASS" if ok else "FAIL"


if __name__ == "__main__":
    print("events_table self-test:", _selftest())
