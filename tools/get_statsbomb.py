"""Download StatsBomb open data for one competition/season into data/.

Usage:
  python tools/get_statsbomb.py --list                      # show competitions + seasons
  python tools/get_statsbomb.py 55 282                      # competition_id season_id

Source: https://github.com/statsbomb/open-data (non-commercial use, credit StatsBomb).
"""
import json
import sys
import time
from pathlib import Path

import requests

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


def get(path):
    r = requests.get(f"{BASE}/{path}", timeout=60)
    r.raise_for_status()
    return r.json()


def main(args):
    if not args or args[0] == "--list":
        for c in get("competitions.json"):
            print(c["competition_id"], c["season_id"], c["competition_name"], c["season_name"])
        return
    comp, season = args[0], args[1]
    out = Path("data")
    (out / "events").mkdir(parents=True, exist_ok=True)
    matches = get(f"matches/{comp}/{season}.json")
    (out / f"matches_{comp}_{season}.json").write_text(json.dumps(matches), encoding="utf-8")
    for m in matches:
        f = out / "events" / f"{m['match_id']}.json"
        if not f.exists():
            f.write_text(json.dumps(get(f"events/{m['match_id']}.json")), encoding="utf-8")
            time.sleep(0.3)  # be polite
    print(f"{len(matches)} matches -> {out}/events")


if __name__ == "__main__":
    main(sys.argv[1:])
