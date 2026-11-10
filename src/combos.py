"""Find and rate 2-3 player combinations in StatsBomb open-data event files.

Usage:  python src/combos.py "data/events/*.json" [--min-minutes 180]
Writes out/units.csv (pairs + trios) and out/dependency.csv, prints top lists.

Definitions
- chain: unbroken run of completed passes inside one possession of one team,
  A -> B -> C -> D gives pairs (A>B, B>C, C>D) and trios (A>B>C, B>C>D).
- shot credit: if the last player of a chain shoots (no penalties), the pair/trio
  that ENDS the chain gets the shot, its xG and the goal.
- minutes together: time all players of a unit were on the pitch at the same time
  (starting XI, substitutions, red cards). All "_p90" values use it.
- progression: how much closer to goal (120, 40) the unit's passes moved the ball
  (StatsBomb pitch units, 120 x 80).
- box entry: a pass of the unit that starts outside and ends inside the penalty box.
- one-two: trio A > B > A.  quick layoff: trio whose middle player passes on
  within 3 s of receiving the pass AND the ball ends in the final third
  (attacking first-time / third-man pattern, not back-line circulation).
- open play only: corners and free kicks into the final third break a chain
  (deliveries are not combinations); penalties are never credited.
"""
import argparse
import glob
import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

GOAL = (120.0, 40.0)
LAYOFF_SECONDS = 3.0
RED_CARDS = ("Red Card", "Second Yellow")


# ---------- small helpers ----------
def ts(e):
    """Seconds since the start of the event's period."""
    h, m, s = e["timestamp"].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def dist_to_goal(loc):
    return math.hypot(GOAL[0] - loc[0], GOAL[1] - loc[1])


def in_box(loc):
    return loc[0] >= 102 and 18 <= loc[1] <= 62


def zone(loc):
    x = loc[0]
    if in_box(loc):
        return "box"
    if x >= 80:
        return "final_third"
    return "middle_third" if x >= 40 else "own_third"


def match_clock(events):
    """Return (offset per period in seconds, total playing time). Shoot-out (period 5) ignored."""
    end = defaultdict(float)
    for e in events:
        if e["period"] <= 4:
            end[e["period"]] = max(end[e["period"]], ts(e))
    offset, total = {}, 0.0
    for p in sorted(end):
        offset[p] = total
        total += end[p]
    return offset, total


# ---------- per match ----------
def on_pitch(events):
    """player -> (team, on_second, off_second) for one match."""
    offset, total = match_clock(events)
    t = lambda e: offset[e["period"]] + ts(e)
    team_of, on, off = {}, {}, {}
    for e in events:
        if e["period"] > 4:
            continue
        kind = e["type"]["name"]
        if kind == "Starting XI":
            for p in e["tactics"]["lineup"]:
                name = p["player"]["name"]
                team_of[name], on[name] = e["team"]["name"], 0.0
        elif kind == "Substitution":
            off[e["player"]["name"]] = t(e)
            new = e["substitution"]["replacement"]["name"]
            team_of[new], on[new] = e["team"]["name"], t(e)
        else:
            card = (e.get("foul_committed") or e.get("bad_behaviour") or {}).get("card", {}).get("name")
            if card in RED_CARDS and "player" in e:
                off[e["player"]["name"]] = t(e)
    return {p: (team_of[p], on[p], off.get(p, total)) for p in on}


def chains(events, match_id=None):
    """Chains of completed passes per possession (see module docstring)."""
    offset, _ = match_clock(events)
    by_possession = defaultdict(list)
    for e in events:
        if e["period"] <= 4:
            by_possession[e["possession"]].append(e)

    out = []
    for evs in by_possession.values():
        evs.sort(key=lambda e: e["index"])
        team = evs[0]["possession_team"]["name"]
        players, passes = [], []

        def flush(shot=None):
            if len(players) >= 2:
                out.append(dict(
                    match_id=match_id, team=team, minute=passes[0]["minute"],
                    players=list(players), passes=list(passes),
                    shot=shot is not None,
                    xg=shot["shot"].get("statsbomb_xg", 0.0) if shot else 0.0,
                    goal=bool(shot) and shot["shot"]["outcome"]["name"] == "Goal",
                ))
            players.clear()
            passes.clear()

        for e in evs:
            if e.get("team", {}).get("name") != team:
                continue  # opponent events inside the possession (pressure, duels ...)
            kind = e["type"]["name"]
            if kind == "Pass":
                passer = e["player"]["name"]
                receiver = e["pass"].get("recipient", {}).get("name")
                completed = "outcome" not in e["pass"] and receiver is not None
                ptype = e["pass"].get("type", {}).get("name")
                if ptype == "Corner" or (ptype == "Free Kick" and e["pass"]["end_location"][0] >= 80):
                    flush()  # set-piece delivery is not an open-play combination
                    continue
                if players and players[-1] != passer:
                    flush()  # ball reached the passer some other way -> new chain
                if not completed:
                    flush()
                    continue
                if not players:
                    players.append(passer)
                players.append(receiver)
                passes.append(dict(start=e["location"], end=e["pass"]["end_location"],
                                   t=offset[e["period"]] + ts(e), minute=e["minute"]))
            elif kind == "Shot":
                open_play = e["shot"].get("type", {}).get("name") != "Penalty"
                if open_play and players and players[-1] == e["player"]["name"]:
                    flush(e)
                else:
                    flush()
        flush()
    return out


# ---------- aggregation ----------
def minutes_together(players, matches):
    """Minutes all `players` were on the pitch together, summed over matches."""
    total = 0.0
    for lineup in matches:
        if all(p in lineup for p in players):
            start = max(lineup[p][1] for p in players)
            end = min(lineup[p][2] for p in players)
            total += max(0.0, end - start)
    return total / 60


def units(all_chains, matches, sizes=(2, 3)):
    """Aggregate chains into pairs/trios. `matches` = list of on_pitch() dicts."""
    rows = defaultdict(lambda: dict(chains=0, prog=0.0, box_entries=0, quick_layoffs=0,
                                    shots=0, xg=0.0, goals=0, examples=[]))
    for c in all_chains:
        p, ps = c["players"], c["passes"]
        for k in sizes:
            for i in range(len(p) - k + 1):
                key = (c["team"], k, tuple(p[i:i + k]))
                r = rows[key]
                own = ps[i:i + k - 1]  # the k-1 passes inside this unit
                r["chains"] += 1
                r["prog"] += sum(dist_to_goal(x["start"]) - dist_to_goal(x["end"]) for x in own)
                r["box_entries"] += sum(in_box(x["end"]) and not in_box(x["start"]) for x in own)
                if k == 3 and own[1]["t"] - own[0]["t"] <= LAYOFF_SECONDS and own[1]["end"][0] >= 80:
                    r["quick_layoffs"] += 1
                if c["shot"] and i + k == len(p):  # this unit ends the chain that led to the shot
                    r["shots"] += 1
                    r["xg"] += c["xg"]
                    r["goals"] += int(c["goal"])
                    if len(r["examples"]) < 5:
                        r["examples"].append(f"{c['match_id']}:{own[0]['minute']}'")

    out = []
    for (team, k, players), r in rows.items():
        mins = minutes_together(set(players), matches)
        per90 = 90 / mins if mins else float("nan")
        out.append(dict(
            team=team, size=k, unit=" > ".join(players),
            one_two=k == 3 and players[0] == players[2],
            minutes_together=round(mins, 1),
            chains=r["chains"], prog=round(r["prog"], 1), box_entries=r["box_entries"],
            quick_layoffs=r["quick_layoffs"], shots=r["shots"], xg=round(r["xg"], 3), goals=r["goals"],
            chains_p90=round(r["chains"] * per90, 2), prog_p90=round(r["prog"] * per90, 1),
            box_entries_p90=round(r["box_entries"] * per90, 2), xg_p90=round(r["xg"] * per90, 3),
            examples=" ".join(r["examples"]),
        ))
    return pd.DataFrame(out).sort_values(["xg_p90", "chains_p90"], ascending=False).reset_index(drop=True)


def dependency(all_chains):
    """Share of each team's chain xG that ran through a player (anywhere in the chain)."""
    team_xg = defaultdict(float)
    player_xg = defaultdict(float)
    for c in all_chains:
        if not c["shot"]:
            continue
        team_xg[c["team"]] += c["xg"]
        for p in set(c["players"]):
            player_xg[(c["team"], p)] += c["xg"]
    df = pd.DataFrame([dict(team=t, player=p, xg_involved=round(x, 3),
                            share_of_team=round(x / team_xg[t], 3) if team_xg[t] else 0.0)
                       for (t, p), x in player_xg.items()])
    return df.sort_values("share_of_team", ascending=False).reset_index(drop=True)


# ---------- CLI ----------
def load(paths):
    all_chains, matches = [], []
    for path in paths:
        events = json.loads(Path(path).read_text(encoding="utf-8"))
        all_chains += chains(events, match_id=Path(path).stem)
        matches.append(on_pitch(events))
    return all_chains, matches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events", nargs="+", help="event json files or glob")
    ap.add_argument("--min-minutes", type=float, default=180, help="min minutes together for the top lists")
    a = ap.parse_args()
    files = [f for g in a.events for f in glob.glob(g)]
    all_chains, matches = load(files)
    df, dep = units(all_chains, matches), dependency(all_chains)
    Path("out").mkdir(exist_ok=True)
    df.to_csv("out/units.csv", index=False)
    dep.to_csv("out/dependency.csv", index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 60)
    cols = ["team", "unit", "minutes_together", "chains_p90", "prog_p90", "box_entries_p90", "xg_p90", "goals"]
    ok = df[df["minutes_together"] >= a.min_minutes]
    print(f"{len(files)} matches, {len(all_chains)} chains, {len(df)} units ({len(ok)} with >= {a.min_minutes:.0f} min together)")
    for k, name in ((2, "pairs"), (3, "trios")):
        print(f"\nTop {name} by xG created per 90 together:")
        print(ok[ok["size"] == k].head(10)[cols].to_string(index=False))
    print("\nTop box-entry pairs per 90:")
    print(ok[ok["size"] == 2].sort_values("box_entries_p90", ascending=False).head(10)[cols].to_string(index=False))
    print("\nMost quick-layoff (third-man) trios:")
    print(ok[ok["size"] == 3].sort_values("quick_layoffs", ascending=False).head(8)[cols[:3] + ["quick_layoffs", "xg"]].to_string(index=False))
    print("\nHighest dependency (share of team chain-xG through one player):")
    print(dep.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
