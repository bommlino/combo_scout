# PLAN – combo_scout (started 2026-11-10)

Goal for Thomas: a real, shipped LLM application with evals that he can show in Applied AI / FDE interviews (OpenAI, Anthropic, Mistral, AutoScout24 …) – and a football tool he actually enjoys.
Budget: ~4 weeks, evenings. Keep it small; every step ends with something that runs.

## Phase 1 – combinations from event data (week 1)
- [x] StatsBomb open data: UEFA Euro 2024 (55/282, 51 matches, 120 MB) → `data/` (2026-11-10).
- [x] `src/combos.py`: possession → chains of completed passes → pairs/trios with chains, shots, xG, goals.
- [x] Output `out/units.csv` + first look (8,634 chains, 23,680 units).

## Phase 2 – better metrics (week 2) – done 2026-11-10
- [x] Progression (distance gained to goal), box entries, one-two flag, attacking quick layoffs (≤3 s, ball into final third).
- [x] Minutes together (starting XI, subs, red cards) → per-90 values; top lists only with ≥180 min together.
- [x] Dependency: share of a team's chain-xG that runs through a player (`out/dependency.csv`).
- [x] Open play only: corners / free kicks into the final third break chains; penalties never credited.
- [x] Tests: `python -m pytest -q` (synthetic events).
- [ ] Sanity check with a football eye: does the top list match what you saw at the Euro? (Thomas)
- [ ] Ideas: zone of the final pass per unit, xT instead of distance, 360 freeze frames (defenders bypassed).

## Phase 3 – LLM layer (week 3)
- [ ] 4–5 typed tools over the unit table; LLM with tool use answers questions.
- [ ] Generated scouting report per unit, numbers only from tools, citations to sequences.
- [ ] Eval set (~30 questions) + grader script; log accuracy, cost, latency per change.

## Phase 4 – ship (week 4)
- [ ] FastAPI + minimal UI, Docker, deploy (one cheap host), request logging.
- [ ] README with screenshots + "what I learned" → GitHub (public; Thomas decides).
- [ ] Optional: off-ball runs from Metrica/SkillCorner tracking.

## Open decisions (Thomas)
- LLM provider: OpenAI API (fits the OpenAI applications) or Claude – keep it swappable behind one small client function.
- Which competition first.
- Public GitHub repo yes/no.
