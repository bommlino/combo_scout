# combo_scout – notes for Claude

Thomas's side project: football scouting of **2–3 player units** + an LLM layer (tool use, reports, evals, deployment). Purpose: real LLM-app experience for Applied AI / FDE interviews. Not part of the job-search repo rules, except: only what is really built here may later go on a CV.

- Read `README.md` (concept) and `PLAN.md` (phases, checkboxes) first; tick boxes when done.
- KISS: Python 3.12, pandas, plain files. No database/framework until phase 4 (FastAPI).
- Data goes to `data/` (git-ignored). Ask Thomas before downloading datasets. Respect provider licences (StatsBomb: non-commercial, credit StatsBomb).
- Every step must run end to end before the next one. Prefer small, tested functions.
- LLM numbers must come from tools, never from the model. Keep an eval set and re-run it after every prompt/tool change.
- Language: code + docs in English, chat with Thomas in English.
- Coaching mode: Thomas wants to learn – explain choices briefly, let him write parts himself when he asks for practice.
- This repo has its own Claude Code sessions (job search lives in `D:\Dropbox\Jobs\_job_search` – don't mix).

## Setup
- Venv: `.venv` in the repo (Python 3.12; pandas, requests, pytest). Run: `.venv\Scripts\python.exe src\combos.py "data/events/*.json"` · tests: `.venv\Scripts\python.exe -m pytest -q`.
- Data: StatsBomb Euro 2024 already downloaded to `data/` (51 matches). GitHub: public repo github.com/bommlino/combo_scout (gh CLI logged in as bommlino; Thomas OK'd pushing to this repo).

## Handoff (2026-11-10)
- Phases 1–2 done (see `PLAN.md`). Thomas still to sanity-check the Euro top lists with a football eye.
- **Next: phase 3 (LLM layer).** Open decision: LLM provider – suggestion: OpenAI API (fits his OpenAI Applied AI applications), behind one small swappable client function. Thomas puts the API key in `.env` himself (git-ignored); never handle or print keys.
- Goal of phase 3: tool use over the unit table (`top_units`, `unit_profile`, `dependency`, `similar_units`), reports that cite `examples` (match_id:minute), ~30-question eval set + grader, log accuracy/cost/latency.
