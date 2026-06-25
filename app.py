# -*- coding: utf-8 -*-
"""
Pull MLB pitcher game logs from official MLB StatsAPI for 2026 regular season
through 2026-06-24 and save a projection-ready CSV.

Run:
  python pull_mlb_pitcher_logs_openingday_to_2026_06_24.py

Output:
  mlb_pitcher_logs_2026_openingday_to_2026-06-24.csv
"""

import time
import math
import requests
import pandas as pd
from datetime import datetime

START_SEARCH_DATE = "2026-03-01"   # auto-finds regular season games from here
END_DATE = "2026-06-24"
SEASON = "2026"
OUT_CSV = "mlb_pitcher_logs_2026_openingday_to_2026-06-24.csv"

MLB_BASE = "https://statsapi.mlb.com/api/v1"
MLB_LIVE = "https://statsapi.mlb.com/api/v1.1"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "MLB-K-Projection-Log-Puller/1.0",
    "Accept": "application/json,text/plain,*/*",
})


def safe_float(x, default=None):
    try:
        if x in (None, "", "-"):
            return default
        return float(x)
    except Exception:
        return default


def baseball_ip_to_float(ip):
    if ip in (None, ""):
        return None
    try:
        s = str(ip)
        if "." not in s:
            return float(s)
        whole, frac = s.split(".", 1)
        outs = int(frac[:1]) if frac else 0
        if outs not in (0, 1, 2):
            return float(s)
        return int(whole) + outs / 3.0
    except Exception:
        return None


def fetch_json(url, params=None, retries=3, sleep=0.4):
    last_err = None
    for i in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(sleep * (i + 1))
    raise RuntimeError(f"Failed fetch {url} {params}: {last_err}")


def get_schedule_gamepks():
    data = fetch_json(
        f"{MLB_BASE}/schedule",
        params={
            "sportId": 1,
            "startDate": START_SEARCH_DATE,
            "endDate": END_DATE,
            "gameType": "R",
            "hydrate": "team,probablePitcher,venue",
        },
    )
    games = []
    for d in data.get("dates", []):
        for g in d.get("games", []):
            status = (g.get("status") or {}).get("abstractGameState", "")
            detailed = (g.get("status") or {}).get("detailedState", "")
            # Keep finals/completed only for stable logs.
            if status.lower() not in ("final", "live") and "final" not in detailed.lower():
                continue
            games.append({
                "date": d.get("date") or g.get("officialDate"),
                "game_pk": g.get("gamePk"),
                "away": (((g.get("teams") or {}).get("away") or {}).get("team") or {}).get("abbreviation"),
                "home": (((g.get("teams") or {}).get("home") or {}).get("team") or {}).get("abbreviation"),
                "venue": (g.get("venue") or {}).get("name"),
            })
    return games


def strike_flags(description, code):
    d = str(description or "").lower()
    c = str(code or "").upper()
    called = "called strike" in d or c == "C"
    swinging = "swinging strike" in d or c in {"S", "W"}
    foul = "foul" in d or c in {"F", "L", "T"}
    in_play = "in play" in d or c in {"X"}
    strikeish = called or swinging or foul or in_play
    whiff = swinging
    return called, swinging, foul, in_play, strikeish, whiff


def build_pitch_level_features(feed):
    # keyed by pitcher_id
    feat = {}
    first_pitch_seen = set()
    two_strike_pitch_counts = {}
    putaway_ks = {}

    plays = (((feed.get("liveData") or {}).get("plays") or {}).get("allPlays") or [])
    for play in plays:
        matchup = play.get("matchup") or {}
        pitcher = matchup.get("pitcher") or {}
        pid = pitcher.get("id")
        if not pid:
            continue
        pid = int(pid)
        f = feat.setdefault(pid, {
            "pitch_level_pitches": 0,
            "called_strikes": 0,
            "swinging_strikes": 0,
            "whiffs": 0,
            "fouls": 0,
            "balls_pitch_level": 0,
            "in_play_pitches": 0,
            "csw_pitches": 0,
            "first_pitch_count": 0,
            "first_pitch_strikes": 0,
            "two_strike_pitches": 0,
            "putaway_ks": 0,
        })
        at_bat_index = play.get("atBatIndex")
        result_event = ((play.get("result") or {}).get("event") or "").lower()
        events = play.get("playEvents") or []
        for ev in events:
            if not ev.get("isPitch"):
                continue
            details = ev.get("details") or {}
            desc = details.get("description")
            code = (details.get("code") or "")
            count = ev.get("count") or {}
            balls_before = max(0, int(count.get("balls", 0)) - (1 if "ball" in str(desc).lower() else 0))
            strikes_before = int(count.get("strikes", 0))

            called, swinging, foul, in_play, strikeish, whiff = strike_flags(desc, code)
            f["pitch_level_pitches"] += 1
            if called:
                f["called_strikes"] += 1
            if swinging:
                f["swinging_strikes"] += 1
            if whiff:
                f["whiffs"] += 1
            if foul:
                f["fouls"] += 1
            if in_play:
                f["in_play_pitches"] += 1
            if called or swinging:
                f["csw_pitches"] += 1
            if "ball" in str(desc or "").lower():
                f["balls_pitch_level"] += 1

            if at_bat_index not in first_pitch_seen:
                first_pitch_seen.add(at_bat_index)
                f["first_pitch_count"] += 1
                if strikeish:
                    f["first_pitch_strikes"] += 1

            if strikes_before >= 2:
                f["two_strike_pitches"] += 1
                # If the PA ended in a strikeout and this is the final pitch, count as putaway K.
                # MLB feeds usually include eventType/event in result; final pitch has about.isComplete.
                about = ev.get("about") or {}
                if about.get("isComplete") and "strikeout" in result_event:
                    f["putaway_ks"] += 1

    for pid, f in feat.items():
        p = max(1, f["pitch_level_pitches"])
        f["CSW%"] = round(100.0 * f["csw_pitches"] / p, 1)
        f["SwStr%"] = round(100.0 * f["swinging_strikes"] / p, 1)
        f["Whiff%"] = round(100.0 * f["whiffs"] / p, 1)
        f["Foul%"] = round(100.0 * f["fouls"] / p, 1)
        f["FirstPitchStrike%"] = round(100.0 * f["first_pitch_strikes"] / max(1, f["first_pitch_count"]), 1)
        f["PutawayK_per_2StrikePitch%"] = round(100.0 * f["putaway_ks"] / max(1, f["two_strike_pitches"]), 1)
    return feat


def pitcher_rows_from_game(game):
    game_pk = game["game_pk"]
    feed = fetch_json(f"{MLB_LIVE}/game/{game_pk}/feed/live")
    game_data = feed.get("gameData") or {}
    live_data = feed.get("liveData") or {}
    teams = game_data.get("teams") or {}
    box = (live_data.get("boxscore") or {}).get("teams") or {}
    date = (game_data.get("datetime") or {}).get("officialDate") or game.get("date")
    venue = ((game_data.get("venue") or {}).get("name")) or game.get("venue")
    weather = game_data.get("weather") or {}

    pitch_feats = build_pitch_level_features(feed)
    rows = []

    for side in ["away", "home"]:
        team_obj = teams.get(side) or {}
        opp_side = "home" if side == "away" else "away"
        opp_obj = teams.get(opp_side) or {}
        team_abbr = team_obj.get("abbreviation") or team_obj.get("teamCode") or team_obj.get("name")
        opp_abbr = opp_obj.get("abbreviation") or opp_obj.get("teamCode") or opp_obj.get("name")
        bteam = box.get(side) or {}
        players = bteam.get("players") or {}
        probable_starter_id = None
        try:
            probable_starter_id = int((game_data.get("probablePitchers") or {}).get(side, {}).get("id"))
        except Exception:
            probable_starter_id = None

        for key, p in players.items():
            stats = (p.get("stats") or {}).get("pitching") or {}
            if not stats:
                continue
            pid = (p.get("person") or {}).get("id")
            name = (p.get("person") or {}).get("fullName")
            ip_raw = stats.get("inningsPitched")
            ip = baseball_ip_to_float(ip_raw)
            bf = safe_float(stats.get("battersFaced"), 0) or 0
            if (ip is None or ip == 0) and bf == 0:
                continue
            so = safe_float(stats.get("strikeOuts"), 0) or 0
            bb = safe_float(stats.get("baseOnBalls"), 0) or 0
            h = safe_float(stats.get("hits"), 0) or 0
            r = safe_float(stats.get("runs"), 0) or 0
            er = safe_float(stats.get("earnedRuns"), 0) or 0
            hr = safe_float(stats.get("homeRuns"), 0) or 0
            hbp = safe_float(stats.get("hitBatsmen"), 0) or 0
            pitches = safe_float(stats.get("numberOfPitches"), 0) or 0
            strikes = safe_float(stats.get("strikes"), 0) or 0
            outs = int(round((ip or 0) * 3))
            gs = safe_float(stats.get("gamesStarted"), 0) or 0
            is_starter = bool(gs >= 1 or (probable_starter_id and int(pid) == probable_starter_id))
            pf = pitch_feats.get(int(pid), {}) if pid else {}
            row = {
                "Date": date,
                "Season": SEASON,
                "GamePK": game_pk,
                "PitcherID": pid,
                "Pitcher": name,
                "Team": team_abbr,
                "Opponent": opp_abbr,
                "HomeAway": "AWAY" if side == "away" else "HOME",
                "Venue": venue,
                "Temp": weather.get("temp"),
                "Wind": weather.get("wind"),
                "Condition": weather.get("condition"),
                "IsStarter": int(is_starter),
                "IP_raw": ip_raw,
                "IP": round(ip or 0, 3),
                "Outs": outs,
                "BF": bf,
                "SO": so,
                "BB": bb,
                "H": h,
                "R": r,
                "ER": er,
                "HR": hr,
                "HBP": hbp,
                "Pitches": pitches,
                "Strikes": strikes,
                "Balls_est": max(0, pitches - strikes),
                "Strike%": round(100.0 * strikes / pitches, 1) if pitches else None,
                "K%": round(100.0 * so / bf, 1) if bf else None,
                "BB%": round(100.0 * bb / bf, 1) if bf else None,
                "K-BB%": round(100.0 * (so - bb) / bf, 1) if bf else None,
                "K9": round(so * 9.0 / ip, 2) if ip else None,
                "BB9": round(bb * 9.0 / ip, 2) if ip else None,
                "HR9": round(hr * 9.0 / ip, 2) if ip else None,
                "H9": round(h * 9.0 / ip, 2) if ip else None,
                "WHIP_game": round((h + bb) / ip, 3) if ip else None,
                "Pitches_per_BF": round(pitches / bf, 2) if bf else None,
                "Pitches_per_IP": round(pitches / ip, 1) if ip else None,
                "CSW%": pf.get("CSW%"),
                "SwStr%": pf.get("SwStr%"),
                "Whiff%": pf.get("Whiff%"),
                "FirstPitchStrike%": pf.get("FirstPitchStrike%"),
                "PutawayK_per_2StrikePitch%": pf.get("PutawayK_per_2StrikePitch%"),
                "CalledStrikes": pf.get("called_strikes"),
                "SwingingStrikes": pf.get("swinging_strikes"),
                "Fouls": pf.get("fouls"),
                "InPlayPitches": pf.get("in_play_pitches"),
                "PitchLevelPitches": pf.get("pitch_level_pitches"),
            }
            rows.append(row)
    return rows


def main():
    print(f"Pulling MLB regular-season pitcher logs: {START_SEARCH_DATE} through {END_DATE}")
    games = get_schedule_gamepks()
    print(f"Games found: {len(games)}")
    all_rows = []
    for i, g in enumerate(games, 1):
        try:
            rows = pitcher_rows_from_game(g)
            all_rows.extend(rows)
            if i % 25 == 0 or i == len(games):
                print(f"{i}/{len(games)} games | rows={len(all_rows)}")
        except Exception as e:
            print(f"WARN game {g.get('game_pk')} failed: {e}")
        time.sleep(0.08)

    df = pd.DataFrame(all_rows)
    if not df.empty:
        df = df.sort_values(["Date", "GamePK", "Team", "IsStarter"], ascending=[True, True, True, False])
    df.to_csv(OUT_CSV, index=False)
    print(f"Saved {len(df)} pitcher-game rows -> {OUT_CSV}")


if __name__ == "__main__":
    main()
