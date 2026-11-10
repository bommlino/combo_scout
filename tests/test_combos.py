"""Small synthetic tests for src/combos.py.  Run: python -m pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from combos import chains, dependency, on_pitch, units  # noqa: E402

_i = 0


def ev(kind, player, sec, pos=1, team="A", period=1, **kw):
    global _i
    _i += 1
    e = dict(index=_i, period=period, minute=int(sec // 60), timestamp=f"00:{int(sec // 60):02d}:{sec % 60:06.3f}",
             possession=pos, possession_team={"name": team}, team={"name": team},
             type={"name": kind}, player={"name": player})
    e.update(kw)
    return e


def pas(player, to, sec, start=(60, 40), end=(70, 40), pos=1, done=True):
    p = {"recipient": {"name": to}, "end_location": list(end)}
    if not done:
        p["outcome"] = {"name": "Incomplete"}
    return ev("Pass", player, sec, pos=pos, location=list(start), **{"pass": p})


def shot(player, sec, xg, goal, pos=1, penalty=False):
    s = {"statsbomb_xg": xg, "outcome": {"name": "Goal" if goal else "Saved"},
         "type": {"name": "Penalty" if penalty else "Open Play"}}
    return ev("Shot", player, sec, pos=pos, shot=s)


def lineup(team, names):
    return ev("Starting XI", names[0], 0, team=team, tactics={"lineup": [{"player": {"name": n}} for n in names]})


def test_one_two_layoff_shot_credit():
    events = [
        pas("x", "y", 10, start=(80, 40), end=(100, 40)),
        pas("y", "x", 11, start=(100, 40), end=(110, 40)),  # quick layoff, box entry
        shot("x", 13, 0.4, True),
    ]
    c = chains(events, "m1")
    assert len(c) == 1 and c[0]["players"] == ["x", "y", "x"] and c[0]["goal"]
    lu = [{"x": ("A", 0, 5400), "y": ("A", 0, 2700)}]
    df = units(c, lu).set_index("unit")
    trio = df.loc["x > y > x"]
    assert trio.one_two and trio.quick_layoffs == 1 and trio.goals == 1
    assert trio.minutes_together == 45 and abs(trio.xg_p90 - 0.8) < 1e-9
    assert df.loc["y > x"].box_entries == 1 and df.loc["x > y"].shots == 0


def test_penalty_and_incomplete_are_not_credited():
    events = [
        pas("x", "y", 10),
        shot("y", 12, 0.79, True, penalty=True),
        pas("x", "y", 20, pos=2, done=False),
    ]
    c = chains(events)
    assert len(c) == 1 and not c[0]["shot"] and c[0]["xg"] == 0.0  # pass chain kept, penalty not credited


def test_on_pitch_subs_and_red_card():
    events = [
        lineup("A", ["x", "y"]),
        ev("Substitution", "y", 1800, substitution={"replacement": {"name": "z"}}),
        ev("Foul Committed", "x", 2400, foul_committed={"card": {"name": "Red Card"}}),
        ev("Pass", "z", 2700),  # last event -> match length 45 min
    ]
    lu = on_pitch(events)
    assert lu["y"][2] == 1800 and lu["z"][1] == 1800 and lu["x"][2] == 2400 and lu["z"][2] == 2700


def test_dependency_share():
    c = [dict(team="A", players=["x", "y"], shot=True, xg=0.3),
         dict(team="A", players=["y", "z"], shot=True, xg=0.1)]
    dep = dependency(c).set_index("player")
    assert dep.loc["y"].share_of_team == 1.0 and dep.loc["x"].share_of_team == 0.75
