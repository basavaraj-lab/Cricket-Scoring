import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "matches_data.json")


def _load() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(data: list):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def delete_match(match_id: int) -> bool:
    matches = _load()
    new_list = [m for m in matches if m.get("match_id") != match_id]
    if len(new_list) == len(matches):
        return False
    _save(new_list)
    return True


def save_match(scorecard: dict) -> dict:
    matches = _load()
    scorecard["match_id"] = len(matches) + 1
    scorecard["saved_at"] = datetime.now().isoformat(timespec="seconds")
    matches.append(scorecard)
    _save(matches)
    return {"match_id": scorecard["match_id"], "saved_at": scorecard["saved_at"]}


def get_all_matches() -> list:
    return _load()


def get_overall_stats() -> dict:
    matches = _load()
    batters: dict = {}   # name -> {runs, balls, fours, sixes, matches}
    bowlers: dict = {}   # name -> {wickets, runs, balls, matches}

    for m in matches:
        # collect both innings batter/bowler data
        innings_list = []

        # 1st innings
        if m.get("inn1BattingPlayers"):
            innings_list.append({
                "batters": m.get("inn1BattingPlayers", []),
                "bstats":  m.get("inn1BatterStats", {}),
                "bowlers": m.get("inn1BowlingPlayers", []),
                "bwstats": m.get("inn1BowlerStats", {})
            })
        # 2nd innings (current)
        if m.get("battingPlayers"):
            innings_list.append({
                "batters": m.get("battingPlayers", []),
                "bstats":  m.get("batterStats", {}),
                "bowlers": m.get("bowlingPlayers", []),
                "bwstats": m.get("bowlerStats", {})
            })

        for inn in innings_list:
            for i, name in enumerate(inn["batters"]):
                s = inn["bstats"].get(str(i)) or inn["bstats"].get(i)
                if not s:
                    continue
                if name not in batters:
                    batters[name] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0,
                                     "innings": 0, "fifties": 0, "hundreds": 0}
                b = batters[name]
                b["runs"]    += s.get("runs", 0)
                b["balls"]   += s.get("balls", 0)
                b["fours"]   += s.get("fours", 0)
                b["sixes"]   += s.get("sixes", 0)
                b["innings"] += 1
                if s.get("runs", 0) >= 100:
                    b["hundreds"] += 1
                elif s.get("runs", 0) >= 50:
                    b["fifties"] += 1

            for i, name in enumerate(inn["bowlers"]):
                s = inn["bwstats"].get(str(i)) or inn["bwstats"].get(i)
                if not s or s.get("balls", 0) == 0:
                    continue
                if name not in bowlers:
                    bowlers[name] = {"wickets": 0, "runs": 0, "balls": 0, "innings": 0}
                bw = bowlers[name]
                bw["wickets"] += s.get("wickets", 0)
                bw["runs"]    += s.get("runs", 0)
                bw["balls"]   += s.get("balls", 0)
                bw["innings"] += 1

    # compute derived stats
    batter_list = []
    for name, b in batters.items():
        sr = round((b["runs"] / b["balls"]) * 100, 1) if b["balls"] > 0 else 0.0
        batter_list.append({**b, "name": name, "sr": sr})

    bowler_list = []
    for name, bw in bowlers.items():
        eco = round(bw["runs"] / (bw["balls"] / 6), 2) if bw["balls"] > 0 else 0.0
        overs = f"{bw['balls'] // 6}.{bw['balls'] % 6}"
        bowler_list.append({**bw, "name": name, "eco": eco, "overs": overs})

    return {
        "total_matches": len(matches),
        "batters": sorted(batter_list, key=lambda x: x["runs"], reverse=True),
        "bowlers": sorted(bowler_list, key=lambda x: x["wickets"], reverse=True)
    }
