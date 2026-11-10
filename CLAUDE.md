# combo_scout – notes for Claude

Thomas's side project: football scouting of **2–3 player units** + an LLM layer (tool use, reports, evals, deployment). Purpose: real LLM-app experience for Applied AI / FDE interviews. Not part of the job-search repo rules, except: only what is really built here may later go on a CV.

- Read `README.md` (concept) and `PLAN.md` (phases, checkboxes) first; tick boxes when done.
- KISS: Python 3.12, pandas, plain files. No database/framework until phase 4 (FastAPI).
- Data goes to `data/` (git-ignored). Ask Thomas before downloading datasets. Respect provider licences (StatsBomb: non-commercial, credit StatsBomb).
- Every step must run end to end before the next one. Prefer small, tested functions.
- LLM numbers must come from tools, never from the model. Keep an eval set and re-run it after every prompt/tool change.
- Language: code + docs in English, chat with Thomas in English.
- Coaching mode: Thomas wants to learn – explain choices briefly, let him write parts himself when he asks for practice.
