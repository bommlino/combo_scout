# combo_scout – scouting units of 2–3 players, not single players

**Idea:** classic scouting rates individuals. Football value comes from *combinations*: who passes to whom, which runs open space, which trio creates chances together. `combo_scout` finds, measures and explains **units of 2–3 players** (pass chains, one-twos, third-man runs, overlaps → chances → goals) and answers scout questions in plain language.

Examples of questions it should answer:
- "Which left-side duos at club X create the most xG together?"
- "Which trio produces the most third-man combinations into the box?"
- "If player A leaves, which combinations die with him?" (dependency)
- "Which player on the market fits our striker's best combination pattern?" (complement scouting)

## Core concept
| Level | Unit | Example metrics |
|---|---|---|
| Pair | A → B (and one-twos A → B → A) | completed passes, progressive passes, xG/goals when the chain ends in a shot |
| Trio | A → B → C (third-man) | chains, chains ending in a shot, xG, goals, zone of the final pass |
| Later | + off-ball runs (tracking / 360 frames) | run that receives, space created, defenders bypassed |

MVP = event data only (passes + shots). Runs ("Laufwege") need tracking or 360 freeze-frame data → phase 3.

## Data (free, for non-commercial use – credit the provider)
- **StatsBomb Open Data** – event data incl. xG, many full seasons/tournaments, some with 360 freeze frames. github.com/statsbomb/open-data
- **Metrica Sports sample data** – 3 matches with full tracking (positions 25 Hz) → off-ball runs. github.com/metrica-sports/sample-data
- **SkillCorner Open Data** – broadcast tracking for several matches. github.com/SkillCorner/opendata

## LLM layer (the reason this project exists)
1. **Ask in plain language** → LLM turns the question into calls of small, tested Python tools (`top_units`, `unit_profile`, `dependency`, `similar_units`) – tool use / function calling, no free SQL.
2. **Scouting report** per unit: generated text that cites the underlying sequences (match, minute) – every number comes from the tools, the LLM only writes.
3. **Evals:** a fixed set of ~30 questions with expected answers/numbers; graded automatically (exact numbers) + LLM-as-judge for report quality. Track cost + latency.
4. **Deploy:** small web app (FastAPI + simple UI) in a container; logging of questions, tool calls, answers.

## Quick start
```
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
python tools/get_statsbomb.py 55 282          # UEFA Euro 2024 → data/
python src/combos.py "data/events/*.json"     # → out/units.csv, out/dependency.csv
python -m pytest -q
```

## Status
Phases 1–2 done (pairs/trios with per-90 xG, progression, box entries, one-twos, quick layoffs, dependency). Next: phase 3, the LLM layer. See `PLAN.md`.

Data: StatsBomb Open Data – thanks to StatsBomb (Hudl) for making it available.
