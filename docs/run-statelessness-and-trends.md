# Does the previous routine influence a new run and its trends?

**Short answer: No — each run is stateless and starts cold. The previous day's run has zero influence on today's research or today's "Today's Trends" synthesis.**

Below is the full walkthrough, including the nuances and the one mechanical exception.

---

## Why there's no memory between runs

The pipeline prompt is explicit that the VM is ephemeral:

> "Ephemeral VM — NOTHING persists between runs. This prompt is the ONLY durable thing. Every file below is rebuilt from scratch each run."

So when a run boots, it:

1. Clones the repo fresh and checks out `gh-pages`.
2. Rebuilds all 18 briefs from scratch via **new web searches**.
3. Writes a brand-new `claude.html`.

The only durable artifact is the prompt itself. There is no scratchpad, no database, and no "yesterday's findings" file that feeds forward.

---

## What each research agent actually sees

Each of the 18 research subagents gets **only**:

- Its topic's scope + priorities (from the prompt)
- The shared rules
- A time window ("past 30 days"; AI Daily uses 24–48h)

They do **not** receive yesterday's brief for their topic. Each agent independently searches the web and decides what is in-window. That is deliberate — the design wants a fresh read, not a diff against a prior state it cannot see anyway.

---

## How "Today's Trends" is generated — and what it is NOT

This is the part most likely to mislead, so to be precise: the synthesis step's input is defined as —

> "a cross-topic trends read whose INPUT is the 18 briefs you just wrote — do not search the web again."

So the trends pass is a synthesis **across the 18 briefs from the *same* run**. It looks *sideways* (topic-to-topic, same day), never *backwards* (today vs. yesterday).

When today's trends were written (npm worms, Iceberg-v3 convergence, benchmark-integrity crisis, memory-as-cost), every bullet was derived from the 18 briefs produced that same morning. There was no comparison against the prior day's trends. The `→ seen in:` attributions all point to the current run's briefs, never to a prior day.

---

## The one subtle exception

There *is* an indirect, mechanical form of "considering" the past — but it is not intelligence, it is overwriting:

- The **archive** (`archive/<date>.html` + `archive/index.json`) reads the existing `index.json`, appends today's date, and re-sorts. That is the only place a prior run's file state is read — and only to preserve the calendar list, not to influence content.
- Because the run does a `git pull` on the branch first, if today's `claude.html` were somehow unchanged, git would produce an empty diff. But the content itself is regenerated blind.

So: today's dashboard *replaces* yesterday's `claude.html` at the root; yesterday's is frozen in `archive/`. They coexist for browsing, but today's generation never looked at yesterday's.

---

## What this means in practice

- **No trend continuity / momentum tracking.** If "npm worms" were also flagged yesterday, today's run has no idea — it cannot say "this is the 3rd straight day" or "cooling vs. yesterday." Each day is judged fresh against its own 30-day window.
- **The same story can recur.** A 30-day-window item that appeared yesterday can legitimately appear again today if it is still in-window and still notable. The dedup logic only prevents *topics within a single run* from double-reporting each other (the DEDUP BOUNDARY rules); it does nothing across days.
- **The 30-day window is the only "memory."** It is a rolling lookback baked into each agent's search, not a comparison to prior output.

---

## If you wanted cross-day awareness

Cross-day awareness — e.g., "new since yesterday," trend momentum, or "day N of an ongoing story" — would be a real design change: the run would need to read `archive/<yesterday>.html` (or a structured history file) and feed it to the synthesis step as a second input.

It is very doable (the archive already exists and is git-durable), but it is explicitly *not* how the current pipeline works.
