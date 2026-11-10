# PLAN – combo_scout (started 2026-11-10)

Goal for Thomas: a real, shipped LLM application with evals that he can show in Applied AI / FDE interviews (OpenAI, Anthropic, Mistral, AutoScout24 …) – and a football tool he actually enjoys.
Budget: ~4 weeks, evenings. Keep it small; every step ends with something that runs.

## Phase 1 – combinations from event data (week 1)
- [ ] Get StatsBomb open data for ONE competition (e.g. a recent men's tournament or a league season) → `data/` (not committed). Script: `tools/get_statsbomb.py` (ask before downloading).
- [ ] `src/combos.py`: possession → chains of completed passes → pairs/trios with chains, shots, xG, goals. Sanity-check against matches you know.
- [ ] Output `out/units.csv` + a first look: top duos/trios per team.

## Phase 2 – better metrics (week 2)
- [ ] Progression (distance gained to goal), zone of final pass, one-two and third-man flags.
- [ ] Normalise per 90 minutes the players were on the pitch together (minutes-together from lineups/substitutions).
- [ ] Dependency: share of a team's xG that runs through a player's combinations.

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
