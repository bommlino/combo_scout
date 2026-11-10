"""Find 2-3 player combinations in StatsBomb open-data event files.

Usage:  python src/combos.py data/events/*.json  -> out/units.csv + top lists

A "chain" is an unbroken run of completed passes inside one possession of one team:
    A -> B -> C -> D   gives pairs (A>B, B>C, C>D) and trios (A>B>C, B>C>D).
If the last player of a chain shoots, the chain gets that shot (xG, goal), and the
pair/trio that ENDS the chain is credited with it ("combination that created the chance").
"""
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd


def chains(events):
    """Return a list of chains: dict(team, players=[...], shot=bool, xg=float, goal=bool)."""
    by_possession = defaultdict(list)
    for e in events:
        by_possession[e["possession"]].append(e)

    out = []
    for evs in by_possession.values():
        evs.sort(key=lambda e: e["index"])
        team = evs[0]["possession_team"]["name"]
        chain = []

        def flush(shot=False, xg=0.0, goal=False):
            if len(chain) >= 2:
                out.append(dict(team=team, players=list(chain), shot=shot, xg=xg, goal=goal))
            chain.clear()

        for e in evs:
            if e.get("team", {}).get("name") != team:
                continue  # opponent events inside the possession (pressure, duels ...)
            kind = e["type"]["name"]
            if kind == "Pass":
                passer = e["player"]["name"]
                receiver = e["pass"].get("recipient", {}).get("name")
                completed = "outcome" not in e["pass"] and receiver is not None
                if chain and chain[-1] != passer:
                    flush()  # ball came to the passer some other way -> new chain
                if not completed:
                    flush()
                    continue
                if not chain:
                    chain.append(passer)
                chain.append(receiver)
            elif kind == "Shot":
                if chain and chain[-1] == e["player"]["name"]:
                    flush(True, e["shot"].get("statsbomb_xg", 0.0), e["shot"]["outcome"]["name"] == "Goal")
                else:
                    flush()
        flush()
    return out


def units(all_chains, sizes=(2, 3)):
    """Aggregate chains into pairs/trios with counts, shots, xG and goals."""
    rows = defaultdict(lambda: dict(chains=0, shots=0, xg=0.0, goals=0))
    for c in all_chains:
        p = c["players"]
        for k in sizes:
            for i in range(len(p) - k + 1):
                r = rows[(c["team"], k, " > ".join(p[i:i + k]))]
                r["chains"] += 1
                if c["shot"] and i + k == len(p):  # this unit ends the chain that led to the shot
                    r["shots"] += 1
                    r["xg"] += c["xg"]
                    r["goals"] += int(c["goal"])
    df = pd.DataFrame([dict(team=t, size=k, unit=u, **v) for (t, k, u), v in rows.items()])
    return df.sort_values(["xg", "chains"], ascending=False).reset_index(drop=True)


def main(paths):
    all_chains = []
    for path in paths:
        all_chains += chains(json.loads(Path(path).read_text(encoding="utf-8")))
    df = units(all_chains)
    Path("out").mkdir(exist_ok=True)
    df.to_csv("out/units.csv", index=False)
    pd.set_option("display.width", 160)
    for k in (2, 3):
        print(f"\nTop {'pairs' if k == 2 else 'trios'} by xG created:")
        print(df[df["size"] == k].head(15).to_string(index=False))


if __name__ == "__main__":
    files = [f for a in sys.argv[1:] for f in glob.glob(a)]
    if not files:
        sys.exit("usage: python src/combos.py data/events/*.json")
    main(files)
