
# -*- coding: utf-8 -*-
# ============================================================
# MLB STRIKEOUT PROP ENGINE — ONE FILE — v11.9
# MERGED: TRUE CALIBRATION + MANAGER HOOK + DENSITY ALTITUDE
# Refresh first, then save official before-game snapshot
# Real lines only. No fake prop lines.
# Google Drive persistent logs + grading + learning.
# ============================================================

import os
import json
import math
import html
import difflib
import io
import unicodedata
import requests
import numpy as np
import pandas as pd
import streamlit as st
from math import exp, factorial
from datetime import datetime, timedelta, date

APP_VERSION = "NO_TOP_PLAYS_BUILD |  + TRUE MOBILE UI + TABS FIXED + KPROJ CLARITY + KPROJ SYNCED + TRUE KPROJ SYNC + REBUILT TRUE KPROJ SYNC + ALL TABS KPROJ SYNCED + VISIBLE LOWER TABS + MOBILE CARD FIX + SMART EDGE UPGRADES + CONFIDENCE CLEAN + ACE CEILING PROTECTION + OLD REFRESH + NEW PROJECTIONS + MLB PROJECTED LINEUPS + ENV PITCHCOUNT UMPIRE + ENV UI CARDS + MULTI PROP TABS + VOLUME SAFETY + K + PITCHING OUTS ONLY + CALIBRATION AUDIT ONLY + K ONLY SAVE LINE FIX" +  "v11.17 K PROJ UPSIDE TAB + RECENT FORM TRUE TALENT + LIGHT TRUE LEASH BF + MONEYLINE EDGE + LIGHT BULLPEN TAX + ELITE SAFETY DASH + SAFE/VOLATILE + AUTO RESULTS + PITCHTYPE/UMP/UI + FINAL BOARD + BALANCED FINAL BOARD + ML LOGO UI + ML PRO BOARD UI + ML CONTEXT"

try:
    import pytz
except Exception:
    pytz = None

# =========================
# STORAGE
# =========================
DRIVE_DIR = "/content/drive/MyDrive/mlb_engine"
LOCAL_DIR = "mlb_engine"

try:
    from google.colab import drive
    if not os.path.exists("/content/drive/MyDrive"):
        drive.mount("/content/drive", force_remount=False)
    os.makedirs(DRIVE_DIR, exist_ok=True)
    STORAGE_DIR = DRIVE_DIR
except Exception:
    os.makedirs(LOCAL_DIR, exist_ok=True)
    STORAGE_DIR = LOCAL_DIR

PICK_LOG = os.path.join(STORAGE_DIR, "auto_pick_log.json")
RESULT_LOG = os.path.join(STORAGE_DIR, "auto_result_log.json")
LEARN_FILE = os.path.join(STORAGE_DIR, "pitcher_learning.json")
CLV_FILE = os.path.join(STORAGE_DIR, "clv_tracker.json")
REQUEST_LOG_FILE = os.path.join(STORAGE_DIR, "request_log.json")
SIGNAL_TRACKING_FILE = os.path.join(STORAGE_DIR, "signal_tracking.json")
LONG_BACKTEST_FILE = os.path.join(STORAGE_DIR, "long_backtest_rows.json")
LINEUP_CACHE_FILE = os.path.join(STORAGE_DIR, "locked_lineup_cache.json")
LINE_HISTORY_FILE = os.path.join(STORAGE_DIR, "line_history.json")
CALIBRATION_ENGINE_FILE = os.path.join(STORAGE_DIR, "true_calibration_engine.json")
BULLPEN_LEARNING_FILE = os.path.join(STORAGE_DIR, "bullpen_learning_engine.json")
UMPIRE_LEARNING_FILE = os.path.join(STORAGE_DIR, "umpire_learning_engine.json")
GRADED_FEATURES_FILE = os.path.join(STORAGE_DIR, "graded_feature_bank.json")

MLB_BASE = "https://statsapi.mlb.com/api/v1"
MLB_LIVE = "https://statsapi.mlb.com/api/v1.1"
ODDS_BASE = "https://api.the-odds-api.com/v4"
PRIZEPICKS_URL = "https://api.prizepicks.com/projections"
UNDERDOG_URLS = [
    "https://api.underdogfantasy.com/beta/v6/over_under_lines",
    "https://api.underdogfantasy.com/beta/v5/over_under_lines",
    "https://api.underdogfantasy.com/beta/v4/over_under_lines",
    "https://api.underdogfantasy.com/beta/v3/over_under_lines",
    "https://api.underdogfantasy.com/beta/v2/over_under_lines",
    "https://api.underdogfantasy.com/v1/over_under_lines",
]
SPORTSGAMEODDS_BASE = "https://api.sportsgameodds.com/v2"
OPTICODDS_BASE = "https://api.opticodds.com/api/v3"

SPORTSBOOK_PITCHER_K_MARKETS = [
    "pitcher_strikeouts",
    "player_pitcher_strikeouts",
    "pitcher_strikeouts_alternate",
    "player_pitcher_strikeouts_alternate",
    "pitcher_strikeouts_over_under",
]

LEAGUE_AVG_K = 0.225
DEFAULT_BF = 22.0

# =========================
# v10.8 WEATHER + UMPIRE CAPS
# =========================
# These are deliberately small nudges. They cannot override lines or no-bet gates.
WEATHER_FACTOR_MIN = 0.975
WEATHER_FACTOR_MAX = 1.025
UMPIRE_FACTOR_MIN = 0.975
UMPIRE_FACTOR_MAX = 1.025
# =========================
# v10.3 UNDERDOG DEBUG + PRIMARY BOARD LINE SETTINGS
# =========================
# Goal: fewer plays, fewer coin-flips, higher true hit quality.
# These settings intentionally PASS on borderline props.
MIN_BETTABLE_GAP_KS = 1.00
MIN_ELITE_DATA_SCORE = 92
MIN_ELITE_NO_VIG_EDGE = 8.0
MIN_MATCH_SCORE_STRICT = 0.88

MIN_OFFICIAL_SAVE_SCORE = 82
MIN_BETTABLE_SCORE = 88
MIN_BETTABLE_PROB = 0.64
MIN_BETTABLE_EV = 0.06
MIN_CONFIRMED_LINEUP_SCORE = 90
MAX_RECOMMENDED_KELLY = 0.02

# =========================
# v11.4 RUN-DAMAGE / GAME-SCRIPT RISK SETTINGS
# =========================
OVER_MIN_PROB_STRONG = 0.65
OVER_MIN_EDGE_STRONG = 1.25
RUN_DAMAGE_BF_CUT_MILD = 0.96
RUN_DAMAGE_BF_CUT_HIGH = 0.91
RUN_DAMAGE_BF_CUT_EXTREME = 0.86
HIGH_RUN_DAMAGE_WHIP = 1.35
HIGH_RUN_DAMAGE_RECENT_ER = 4.0
HIGH_OPP_CONTACT_RATE = 0.78
HIGH_OPP_SLG_VS_PITCH = 0.520

# =========================
# v11.12 ADVANCED RUN-DAMAGE RISK SETTINGS
# =========================
# These are capped volume/volatility modifiers. They do not directly lower raw K talent.
RUN_DAMAGE_ADVANCED_ENABLED = True
RUN_DAMAGE_MAX_BF_CUT = 0.88
RUN_DAMAGE_MILD_VOL_PENALTY = 0.03
RUN_DAMAGE_HIGH_VOL_PENALTY = 0.06
RUN_DAMAGE_EXTREME_VOL_PENALTY = 0.09
HIGH_RECENT_BB_AVG = 2.8
HIGH_RECENT_HR_AVG = 1.2
HIGH_RECENT_RUNS_AVG = 4.5
HIGH_SEASON_HR9 = 1.35
HIGH_SEASON_BB9 = 3.8
HIGH_SEASON_H9 = 9.5

# =========================
# v11.6 REPEAT MATCHUP FAMILIARITY SETTINGS
# =========================
REPEAT_MATCHUP_LOOKBACK_DAYS = 21
REPEAT_MATCHUP_FACTOR_MIN = 0.965
REPEAT_MATCHUP_FACTOR_MAX = 1.000
REPEAT_MATCHUP_SAME_7D_FACTOR = 0.970
REPEAT_MATCHUP_SAME_14D_FACTOR = 0.982
REPEAT_MATCHUP_SAME_21D_FACTOR = 0.990
REPEAT_MATCHUP_MULTI_RECENT_FACTOR = 0.965

# =========================
# v11.8 TRUE CALIBRATION ENGINE SETTINGS
# =========================
CALIBRATION_MIN_GLOBAL_SAMPLES = 25
CALIBRATION_MIN_BUCKET_SAMPLES = 8
CALIBRATION_MAX_PROJ_SHIFT_KS = 0.35
CALIBRATION_MAX_PROB_SHIFT = 0.08
CALIBRATION_PRIOR_STRENGTH = 18
CALIBRATION_NOISE_RANGE_SOFT_CAP = 5.0
CALIBRATION_RECENT_LIMIT = 2500

# =========================
# v11.9 STRATEGY UPGRADES
# =========================
# Third-Time-Through-the-Order / manager hook sensitivity.
# Small cap so it improves volume realism without nuking elite starters.
MANAGER_HOOK_STRICTNESS = 0.065
TTTO_THRESHOLD_BATTERS = 18
MANAGER_HOOK_RECENT_BF_CUTOFF = 20
MANAGER_HOOK_RATE_TRIGGER = 0.60

# Density-altitude style weather sensitivity for K props.
# Higher heat/humidity can slightly reduce pitch movement/whiffs.
DA_K_FACTOR_MIN = 0.965
DA_K_FACTOR_MAX = 1.015

# =========================
# v11.10 POWER LEARNING SETTINGS
# =========================
# These learn only from graded official snapshots. They are capped so small samples
# cannot overpower the main projection, Statcast, lineups, or real lines.
BULLPEN_LEARN_MIN_SAMPLES = 10
BULLPEN_LEARN_MAX_BF_ADJ = 0.035
UMPIRE_LEARN_MIN_SAMPLES = 8
UMPIRE_LEARN_MAX_K_ADJ = 0.018
FEATURE_BANK_RECENT_LIMIT = 30000
CONTEXT_PRIOR_STRENGTH = 14

LEARNING_MIN_PRIOR_STARTS = 5
LEARNING_RATE = 0.04
LEARNING_SCALE_MIN = 0.92
LEARNING_SCALE_MAX = 1.08

# =========================
# v10.7 ADVANCED SIM / AI ASSIST SETTINGS
# =========================
# Bayesian + Markov is safe and ON by default.
# XGBoost is experimental and OFF by default until enough graded history exists.
BAYESIAN_MARKOV_SIMS = 14000
BAYESIAN_PROJECTION_STD_MIN = 0.45
BAYESIAN_PROJECTION_STD_MAX = 1.85
XGB_MIN_GRADED_SAMPLES = 100
XGB_MAX_RESIDUAL_ADJ_KS = 0.35
XGB_MAX_PERCENT_ADJ = 0.05
XGB_RECENT_TRAIN_LIMIT = 700


LEAGUE_AVG_WHIFF_BY_PITCH_TYPE = {
    "FF": 0.22, "SI": 0.17, "FC": 0.20, "SL": 0.34, "CU": 0.31,
    "KC": 0.31, "CH": 0.31, "FS": 0.34, "ST": 0.36, "SV": 0.30,
    "KN": 0.25, "EP": 0.15, "UNK": 0.25
}

def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

ODDS_API_KEY = get_secret("ODDS_API_KEY", "")
SPORTSGAMEODDS_API_KEY = get_secret("SPORTSGAMEODDS_API_KEY", "")
OPTICODDS_API_KEY = get_secret("OPTICODDS_API_KEY", "")

# =========================
# PAGE CONFIG + UI
# =========================

# =========================
# TRUE MOBILE K UPSIDE UI PATCH
# UI-only patch.
# Does NOT touch projections, sims, Over/Under decisions, Final Board, Moneyline, or grading.
# Goal: readable phone layout, no skinny stat columns, no sideways squeeze.
# =========================
def inject_true_mobile_k_ui():
    st.markdown("""
    <style>
    /* -------------------------------------------------
       PHONE K UPSIDE CLEANUP
       ------------------------------------------------- */
    @media (max-width: 780px) {

        .block-container {
            padding-left: .55rem !important;
            padding-right: .55rem !important;
            padding-top: .75rem !important;
            max-width: 100% !important;
        }

        h1, h2, h3 {
            line-height: 1.12 !important;
        }

        /* Stop cards from becoming wider than the phone */
        .pick-card,
        .green-card,
        .warn-card,
        .hero-panel {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: hidden !important;
            box-sizing: border-box !important;
            padding: 16px !important;
            border-radius: 20px !important;
        }

        /* Big readable player header */
        .player-name {
            font-size: 30px !important;
            line-height: 1.05 !important;
            word-break: normal !important;
            overflow-wrap: anywhere !important;
        }

        .big-title {
            font-size: 31px !important;
            line-height: 1.05 !important;
        }

        .sub-title,
        .small-muted {
            font-size: 13px !important;
            line-height: 1.25 !important;
        }

        .badge {
            font-size: 13px !important;
            padding: 7px 10px !important;
            white-space: normal !important;
        }

        /* Streamlit columns on phone: make them stack instead of squeezing */
        div[data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: .65rem !important;
        }

        /* KPI grid = readable two-column mobile cards */
        .kpi-strip {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 10px !important;
            width: 100% !important;
            margin: 10px 0 14px 0 !important;
        }

        .kpi-box {
            min-width: 0 !important;
            width: 100% !important;
            padding: 12px 10px !important;
            min-height: 92px !important;
            border-radius: 16px !important;
            text-align: center !important;
            overflow-wrap: anywhere !important;
            word-break: normal !important;
        }

        .kpi-label {
            font-size: 10.5px !important;
            letter-spacing: .035em !important;
            line-height: 1.15 !important;
            white-space: normal !important;
        }

        .kpi-value {
            font-size: 25px !important;
            line-height: 1.05 !important;
            white-space: normal !important;
            margin-top: 6px !important;
        }

        .kpi-sub {
            font-size: 11.5px !important;
            line-height: 1.18 !important;
            white-space: normal !important;
        }

        /* Main numbers remain large but not overflowing */
        .big-number {
            font-size: 38px !important;
            line-height: .98 !important;
            overflow-wrap: normal !important;
        }

        /* Metrics should not create vertical letter wrapping */
        div[data-testid="stMetric"] {
            width: 100% !important;
            min-width: 0 !important;
            padding: 12px !important;
            box-sizing: border-box !important;
            overflow-wrap: normal !important;
            word-break: normal !important;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 12px !important;
            line-height: 1.15 !important;
            white-space: normal !important;
            overflow-wrap: normal !important;
            word-break: normal !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 27px !important;
            line-height: 1.05 !important;
            white-space: normal !important;
            overflow-wrap: normal !important;
            word-break: normal !important;
        }

        div[data-testid="stMetricDelta"] {
            font-size: 12px !important;
            line-height: 1.15 !important;
            white-space: normal !important;
        }

        /* Dataframes scroll instead of crushing columns */
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            overflow-x: auto !important;
            max-width: 100% !important;
        }

        /* Plotly / charts mobile protection */
        .js-plotly-plot,
        .plot-container {
            max-width: 100% !important;
            overflow-x: auto !important;
        }

        /* Last 10 bars stay readable */
        .mini-k-bars {
            gap: 7px !important;
            overflow-x: auto !important;
            padding-bottom: 4px !important;
        }

        .mini-k-bar-wrap {
            min-width: 22px !important;
        }

        .mini-k-bar {
            width: 18px !important;
        }

        /* Tabs are scrollable on phone */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px !important;
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
        }

        .stTabs [data-baseweb="tab"] {
            white-space: nowrap !important;
            font-size: 12px !important;
            padding-left: 8px !important;
            padding-right: 8px !important;
        }
    }

    /* Extra small iPhone width */
    @media (max-width: 430px) {
        .player-name {
            font-size: 28px !important;
        }

        .big-title {
            font-size: 29px !important;
        }

        .big-number {
            font-size: 35px !important;
        }

        .kpi-value {
            font-size: 23px !important;
        }

        .kpi-label {
            font-size: 10px !important;
        }

        .kpi-box {
            padding: 11px 8px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


st.set_page_config(
    page_title="MLB K Prop Engine — Refresh Then Save",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at top,#260000 0%,#090909 42%,#020202 100%); color:#fff;}
.block-container {padding-top:1.1rem; max-width:1550px;}
h1,h2,h3 {color:#fff;}
[data-testid="stMetric"] {
    background:linear-gradient(145deg,#111,#1b0000);
    border:1px solid rgba(255,45,45,.36);
    border-radius:18px;
    padding:16px;
    box-shadow:0 0 18px rgba(255,0,0,.18);
}
.hero-panel {
    background:linear-gradient(135deg,rgba(50,0,0,.92),rgba(8,8,8,.96));
    border:1px solid rgba(255,70,70,.42);
    border-radius:26px;
    padding:22px;
    box-shadow:0 0 34px rgba(255,0,0,.18);
    margin-bottom:18px;
}
.pick-card {
    background:linear-gradient(145deg,#101010,#180000);
    border:1px solid rgba(255,45,45,.36);
    border-radius:22px;
    padding:20px;
    box-shadow:0 0 26px rgba(255,0,0,.17);
    margin-bottom:16px;
}
.green-card {
    background:linear-gradient(145deg,#001b0e,#07110b);
    border:1px solid rgba(0,255,135,.48);
    border-radius:22px;
    padding:22px;
    box-shadow:0 0 28px rgba(0,255,135,.22);
    margin-bottom:16px;
}
.warn-card {
    background:linear-gradient(145deg,#1c1200,#0f0a00);
    border:1px solid rgba(255,190,60,.45);
    border-radius:22px;
    padding:20px;
    box-shadow:0 0 24px rgba(255,190,60,.13);
    margin-bottom:16px;
}
.small-muted {color:#bdbdbd; font-size:13px;}
.big-title {font-size:42px; font-weight:950; color:#fff; letter-spacing:-1px;}
.sub-title {color:#d3d3d3; font-size:15px; margin-top:-6px;}
.player-name {font-size:23px; font-weight:900; color:#fff;}
.big-number {font-size:42px; font-weight:950; line-height:1.05;}
.green {color:#31e84f;}
.orange {color:#ffbe3c;}
.red {color:#ff5f5f;}
.badge {
    display:inline-block;
    padding:6px 12px;
    border-radius:999px;
    background:#2c0000;
    border:1px solid rgba(255,95,95,.48);
    color:#ffc4c4;
    font-weight:800;
    margin:3px 4px 3px 0;
}
.good-badge {background:#002916;border-color:rgba(0,255,135,.55);color:#b5ffd9;}
.yellow-badge {background:#2b1d00;border-color:rgba(255,210,70,.55);color:#ffe2a1;}
.red-badge {background:#2b0000;border-color:rgba(255,75,75,.55);color:#ffc0c0;}
.kpi-strip {display:grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap:12px; margin:12px 0 18px 0;}
.kpi-box {background:linear-gradient(145deg,#101010,#190000);border:1px solid rgba(255,70,70,.30);border-radius:18px;padding:14px;min-height:92px;}
.kpi-label {font-size:12px;color:#aaa;font-weight:800;letter-spacing:.04em;text-transform:uppercase;}
.kpi-value {font-size:26px;font-weight:900;color:#fff;margin-top:6px;}
.kpi-sub {font-size:12px;color:#cfcfcf;margin-top:5px;}
.progress-wrap {width:100%;height:14px;border-radius:99px;background:#050505;overflow:hidden;border:1px solid rgba(255,255,255,.08);}
.progress-green {height:100%;border-radius:99px;background:linear-gradient(90deg,#00d66b,#46ff9a);}
.progress-orange {height:100%;border-radius:99px;background:linear-gradient(90deg,#ff8c00,#ffbf30);}
.progress-red {height:100%;border-radius:99px;background:linear-gradient(90deg,#ff2d2d,#ff7272);}
.mini-k-bars {display:flex;align-items:flex-end;gap:10px;min-height:76px;margin-top:4px;overflow-x:auto;}
.mini-k-bar-wrap {display:inline-flex;flex-direction:column;align-items:center;justify-content:flex-end;min-width:18px;}
.mini-k-bar {display:block;width:17px;background:#31e84f;border-radius:3px;box-shadow:0 0 10px rgba(49,232,79,.18);}
.mini-k-label {font-size:12px;color:#bdbdbd;margin-top:3px;}
.hr-soft {border-top:1px solid rgba(255,255,255,.12); margin:14px 0;}
.section-title-pro {margin-top:22px;margin-bottom:10px;font-size:24px;font-weight:950;color:#fff;border-left:5px solid #ff3b3b;padding-left:12px;}
.stTabs [data-baseweb="tab"] {color:#b8c3cf;font-weight:850;}
.stTabs [aria-selected="true"] {color:#31e84f!important;border-bottom:3px solid #31e84f;}
@media (max-width: 1100px) {.kpi-strip {grid-template-columns: repeat(2, minmax(0, 1fr));}}
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def california_now():
    if pytz:
        return datetime.now(pytz.timezone("America/Los_Angeles"))
    return datetime.utcnow() - timedelta(hours=7)

def safe_float(x, default=None):
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default

def safe_int(x, default=None):
    try:
        if x is None or x == "":
            return default
        return int(float(x))
    except Exception:
        return default

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def log_source_request(source, status, message=""):
    rows = load_json(REQUEST_LOG_FILE, [])
    rows.append({
        "time": now_iso(),
        "source": str(source)[:180],
        "status": str(status)[:80],
        "message": str(message)[:350]
    })
    save_json(REQUEST_LOG_FILE, rows[-500:])

def strip_accents(text):
    """Normalize accents so Underdog names like Sánchez match MLB names like Sanchez."""
    try:
        return "".join(
            ch for ch in unicodedata.normalize("NFKD", str(text or ""))
            if not unicodedata.combining(ch)
        )
    except Exception:
        return str(text or "")

def normalize_name(name):
    s = strip_accents(name).lower().strip()
    for ch in [".", ",", "'", "-", "_", " jr", " sr", " ii", " iii", " iv"]:
        s = s.replace(ch, " ")
    return " ".join(s.split())

def name_score(a, b):
    """Robust player-name match.

    Handles full names, abbreviations, and Underdog initial + last-name display:
    - Cristopher Sanchez vs C. Sánchez
    - Gavin Williams vs G. Williams
    - Jacob deGrom vs J. deGrom
    """
    a_norm, b_norm = normalize_name(a), normalize_name(b)
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    if a_norm in b_norm or b_norm in a_norm:
        return 0.94

    a_parts, b_parts = a_norm.split(), b_norm.split()
    if a_parts and b_parts:
        a_first, b_first = a_parts[0], b_parts[0]
        a_last, b_last = a_parts[-1], b_parts[-1]

        # Exact last-name + first-initial match, e.g. "Cristopher Sanchez" vs "C Sanchez".
        if a_last == b_last and a_first[:1] == b_first[:1]:
            return 0.93

        # Multi-word last names / particles still get strong credit if the last token and initial match.
        if a_last == b_last:
            return max(0.82, difflib.SequenceMatcher(None, a_norm, b_norm).ratio())

    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()

def is_pitcher_k_text(text):
    t = str(text or "").lower()
    return (
        "strikeout" in t
        or "strike out" in t
        or "pitcher k" in t
        or t in ["ks", "k", "pitcher strikeouts"]
    ) and not any(bad in t for bad in ["batter", "hitter"])

def is_bad_sport_text(text):
    """Hard block non-MLB/basketball contamination from prop feeds."""
    t = f" {str(text or '').lower()} "
    bad_terms = [
        " nba", " nba_", "basketball", "wnba", "nfl", "football", "nhl",
        "soccer", "tennis", "golf", "college basketball", "ncaab"
    ]
    return any(x in t for x in bad_terms)

def is_bad_k_market_text(text):
    """Reject non-pitcher-K or alternate/novelty markets that can carry misleading values."""
    t = str(text or "").lower()
    bad_terms = [
        "batter", "hitter", "team strikeouts", "fantasy points", "fantasy score",
        "runs+rbi", "hits+runs+rbi", "total bases", "stolen base", "walks allowed",
        "earned runs", "outs recorded", "pitching outs", "hits allowed", "runs allowed",
        "single", "double", "home run", "rbi", "runs scored", "combo", "rival",
        "special", "discount", "alternative", "alt "
    ]
    return any(x in t for x in bad_terms)

@st.cache_data(ttl=300, show_spinner=False)
def safe_get_json(url, params=None, timeout=14, headers=None):
    try:
        h = {
            "User-Agent": "Mozilla/5.0 MLBKPropEngine/refresh-save-build",
            "Accept": "application/json,text/plain,*/*",
        }
        if headers:
            h.update(headers)
        r = requests.get(url, params=params, timeout=timeout, headers=h)
        if r.status_code != 200:
            log_source_request(url, f"HTTP {r.status_code}", r.text[:250])
            return None
        try:
            return r.json()
        except Exception as e:
            log_source_request(url, "BAD_JSON", str(e))
            return None
    except Exception as e:
        log_source_request(url, "REQUEST_ERROR", str(e))
        return None

def baseball_ip_to_float(ip):
    if ip is None:
        return None
    try:
        s = str(ip)
        if "." not in s:
            return float(s)
        whole, frac = s.split(".", 1)
        outs = int(frac[:1]) if frac else 0
        if outs not in [0, 1, 2]:
            return float(s)
        return int(whole) + outs / 3
    except Exception:
        return None

def get_first_stat_split(data):
    if not isinstance(data, dict):
        return None
    stats = data.get("stats") or []
    if not stats or not isinstance(stats[0], dict):
        return None
    splits = stats[0].get("splits") or []
    if not splits or not isinstance(splits[0], dict):
        return None
    return splits[0]

def flatten_json(obj):
    items = []
    if isinstance(obj, dict):
        items.append(obj)
        for v in obj.values():
            items.extend(flatten_json(v))
    elif isinstance(obj, list):
        for x in obj:
            items.extend(flatten_json(x))
    return items

def first_value(d, keys):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] not in [None, ""]:
            return d[k]
    return None

# =========================
# BETTING MATH
# =========================
def poisson_over_probability(lam, line):
    lam = safe_float(lam, 0)
    line = safe_float(line)
    if line is None or lam <= 0:
        return None
    k = int(math.floor(line))
    prob_under_or_equal = sum((lam ** i) * exp(-lam) / factorial(i) for i in range(k + 1))
    return float(clamp(1 - prob_under_or_equal, 0.001, 0.999))

def american_to_implied(price):
    price = safe_float(price)
    if price is None:
        return None
    if price > 0:
        return 100 / (price + 100)
    return abs(price) / (abs(price) + 100)

def decimal_odds(odds):
    odds = safe_float(odds)
    if odds is None:
        return None
    if odds > 0:
        return 1 + odds / 100
    return 1 + 100 / abs(odds)

def expected_value(prob, odds):
    dec = decimal_odds(odds)
    if prob is None or dec is None:
        return None
    return (prob * (dec - 1)) - (1 - prob)

def kelly_fraction(prob, odds):
    dec = decimal_odds(odds)
    if prob is None or dec is None:
        return 0.0
    b = dec - 1
    q = 1 - prob
    if b <= 0:
        return 0.0
    return float(clamp(((b * prob) - q) / b, 0, 0.25))

def paired_no_vig_probability(rows, target_row):
    price = safe_float(target_row.get("Price"))
    listed = american_to_implied(price)
    if listed is None:
        return None
    provider = str(target_row.get("Provider", target_row.get("Source", ""))).lower()
    line = safe_float(target_row.get("Line"))
    side = str(target_row.get("Side", "")).lower()
    if line is None or not side:
        return listed
    want = "under" if "over" in side else "over" if "under" in side else None
    if not want:
        return listed
    opposite = None
    for r in rows or []:
        if safe_float(r.get("Line")) != line:
            continue
        if str(r.get("Provider", r.get("Source", ""))).lower() != provider:
            continue
        if want in str(r.get("Side", "")).lower():
            opposite = american_to_implied(r.get("Price"))
            break
    if opposite is None:
        return listed
    denom = listed + opposite
    return listed / denom if denom > 0 else listed

# =========================
# LEARNING / CLV / LOGGING
# =========================
def load_learning():
    return load_json(LEARN_FILE, {})

def apply_learning(pid, lam):
    data = load_learning()
    scale = safe_float(data.get(str(pid)), 1.0) or 1.0
    return lam * scale, scale

def pitcher_learning_sample_count(pid):
    """Count previous graded official snapshots for this pitcher before changing learning scale."""
    results = load_json(RESULT_LOG, [])
    return sum(
        1 for r in results
        if str(r.get("pitcher_id")) == str(pid)
        and r.get("actual") is not None
        and r.get("projection") is not None
    )

def update_learning(pid, projected, actual):
    """
    Safer learning:
    - does NOT move from one random outcome
    - waits for prior samples
    - uses a smaller learning rate
    - caps pitcher scale tighter
    """
    data = load_learning()
    projected = safe_float(projected, 0) or 0
    actual = safe_float(actual)
    current = safe_float(data.get(str(pid)), 1.0) or 1.0

    if actual is None or projected <= 0:
        return current

    prior_samples = pitcher_learning_sample_count(pid)
    if prior_samples < LEARNING_MIN_PRIOR_STARTS:
        data[str(pid)] = current
        save_json(LEARN_FILE, data)
        return current

    err = clamp((actual - projected) / max(1.0, projected), -0.35, 0.35)
    new_scale = clamp(current * (1 + LEARNING_RATE * err), LEARNING_SCALE_MIN, LEARNING_SCALE_MAX)
    data[str(pid)] = new_scale
    save_json(LEARN_FILE, data)
    return new_scale

def update_clv_snapshot(player_name, source, line):
    if line is None:
        return None
    data = load_json(CLV_FILE, {})
    today = california_now().strftime("%Y-%m-%d")
    key = f"{today}_{normalize_name(player_name)}_{source}"
    old = data.get(key)
    line = float(line)
    if not old:
        data[key] = {
            "player": player_name,
            "source": source,
            "open_line": line,
            "latest_line": line,
            "last_updated": now_iso()
        }
        save_json(CLV_FILE, data)
        return 0.0
    open_line = safe_float(old.get("open_line"))
    old["latest_line"] = line
    old["last_updated"] = now_iso()
    data[key] = old
    save_json(CLV_FILE, data)
    if open_line is None:
        return 0.0
    return round(line - open_line, 2)

def track_line_delta(player_name, source, line):
    if line is None:
        return None
    hist = load_json(LINE_HISTORY_FILE, {})
    key = f"{normalize_name(player_name)}_{source}"
    rows = hist.get(key, [])
    rows.append({"t": now_iso(), "line": safe_float(line)})
    hist[key] = rows[-30:]
    save_json(LINE_HISTORY_FILE, hist)
    if len(hist[key]) < 2:
        return 0.0
    first = safe_float(hist[key][0].get("line"))
    last = safe_float(hist[key][-1].get("line"))
    if first is None or last is None:
        return None
    return round(last - first, 2)

def log_long_backtest_row(pick):
    rows = load_json(LONG_BACKTEST_FILE, [])
    pid = pick.get("pick_id")
    ids = set(r.get("pick_id") for r in rows)
    if pid not in ids:
        slim = {k: v for k, v in pick.items() if k not in ["prop_rows", "lineup_rows", "pitch_type_rows"]}
        rows.append(slim)
        save_json(LONG_BACKTEST_FILE, rows[-20000:])

def calibration_prop_type(row=None):
    # This one-file app is currently built around MLB pitcher strikeouts.
    return "pitcher_ks"

def calibration_line_source_group(source):
    src = str(source or "").lower()
    if "underdog" in src:
        return "underdog"
    if "prize" in src:
        return "prizepicks"
    if "sportsbook" in src or "draftkings" in src or "fanduel" in src or "betmgm" in src:
        return "sportsbook"
    if "optic" in src:
        return "opticodds"
    if "sportsgameodds" in src or "sgo" in src:
        return "sportsgameodds"
    return "other"

def calibration_bucket(value, cuts, labels):
    v = safe_float(value)
    if v is None:
        return "unknown"
    for cut, label in zip(cuts, labels):
        if v <= cut:
            return label
    return labels[-1] if labels else "unknown"

def calibration_tags_from_row(row):
    side = str(row.get("pick_side") or "UNKNOWN").upper()
    src_group = calibration_line_source_group(row.get("line_source"))
    prob = safe_float(row.get("fair_probability"))
    edge = safe_float(row.get("abs_edge"))
    line = safe_float(row.get("line"))
    score = safe_float(row.get("data_score"))
    risk = str(row.get("risk_label") or "UNKNOWN").upper()
    lineup = "locked" if row.get("lineup_locked") else "fallback"
    price = "real_price" if row.get("price_is_real") else "estimated_price"

    bullpen_status = str(row.get("bullpen_status") or "UNKNOWN").upper()
    umpire_name = normalize_name(row.get("umpire") or "Unknown").replace(" ", "_")
    manager_hook = str(row.get("manager_hook_status") or row.get("manager_hook") or "UNKNOWN").upper()
    weather_factor = safe_float(row.get("weather_factor"))
    ump_factor = safe_float(row.get("ump_factor"))
    bf_factor = safe_float(row.get("bullpen_bf_factor"))

    return [
        f"prop={calibration_prop_type(row)}",
        f"side={side}",
        f"source={src_group}",
        f"side_source={side}_{src_group}",
        f"prob_bucket={calibration_bucket(prob, [0.54,0.58,0.62,0.66,0.70,0.76], ['p<=54','p55-58','p59-62','p63-66','p67-70','p71-76','p77+'])}",
        f"edge_bucket={calibration_bucket(edge, [0.49,0.99,1.49,1.99,2.49], ['e<0.5','e0.5-1.0','e1.0-1.5','e1.5-2.0','e2.0-2.5','e2.5+'])}",
        f"line_bucket={calibration_bucket(line, [3.5,4.5,5.5,6.5], ['l<=3.5','l4.5','l5.5','l6.5','l7+'])}",
        f"score_bucket={calibration_bucket(score, [69,79,87,92,96], ['s<70','s70s','s80-87','s88-92','s93-96','s97+'])}",
        f"risk={risk}",
        f"lineup={lineup}",
        f"price={price}",
        f"bullpen={bullpen_status}",
        f"manager_hook={manager_hook}",
        f"umpire={umpire_name}",
        f"weather_bucket={calibration_bucket(weather_factor, [0.975,0.995,1.005,1.025], ['weather_low','weather_slight_low','weather_neutral','weather_slight_high','weather_high'])}",
        f"ump_factor_bucket={calibration_bucket(ump_factor, [0.985,0.995,1.005,1.015], ['ump_low','ump_slight_low','ump_neutral','ump_slight_high','ump_high'])}",
        f"bullpen_factor_bucket={calibration_bucket(bf_factor, [0.975,0.995,1.005,1.025], ['bp_cut','bp_slight_cut','bp_neutral','bp_slight_boost','bp_boost'])}",
    ]

def build_model_calibration_profile(results):
    finished = [r for r in (results or [])[-CALIBRATION_RECENT_LIMIT:] if r.get("actual") is not None and r.get("projection") is not None]
    finished = [r for r in finished if r.get("graded_result") in ["WIN", "LOSS"] or r.get("win") is not None]
    if not finished:
        return {"samples": 0, "mae": None, "bias": None, "hit_rate": None, "quality_score": 50, "bucket_stats": {}, "note": "No graded samples yet"}

    errors = []
    wins = []
    predicted = []
    bucket_stats = {}

    def ensure_bucket(tag):
        if tag not in bucket_stats:
            bucket_stats[tag] = {"tag": tag, "count": 0, "wins": 0, "pred_sum": 0.0, "err_sum": 0.0, "abs_err_sum": 0.0}
        return bucket_stats[tag]

    for r in finished:
        actual = safe_float(r.get("actual"))
        proj = safe_float(r.get("projection"))
        if actual is None or proj is None:
            continue
        err = actual - proj
        win = 1 if (r.get("graded_result") == "WIN" or r.get("win") is True) else 0
        prob = safe_float(r.get("fair_probability"), 0.5) or 0.5
        errors.append(err)
        wins.append(win)
        predicted.append(prob)
        for tag in calibration_tags_from_row(r):
            b = ensure_bucket(tag)
            b["count"] += 1
            b["wins"] += win
            b["pred_sum"] += prob
            b["err_sum"] += err
            b["abs_err_sum"] += abs(err)

    sample_count = len(errors)
    if not sample_count:
        return {"samples": 0, "mae": None, "bias": None, "hit_rate": None, "quality_score": 50, "bucket_stats": {}, "note": "No usable graded rows"}

    mae = float(np.mean([abs(e) for e in errors]))
    bias = float(np.mean(errors))
    hit_rate = float(np.mean(wins)) if wins else None
    avg_pred = float(np.mean(predicted)) if predicted else 0.5
    brier = float(np.mean([(w - p) ** 2 for w, p in zip(wins, predicted)])) if predicted else None

    compact = {}
    for tag, b in bucket_stats.items():
        c = max(1, b["count"])
        compact[tag] = {
            "tag": tag,
            "count": int(b["count"]),
            "wins": int(b["wins"]),
            "win_rate": round((b["wins"] + CALIBRATION_PRIOR_STRENGTH * 0.5) / (b["count"] + CALIBRATION_PRIOR_STRENGTH), 4),
            "raw_win_rate": round(b["wins"] / c, 4),
            "avg_pred": round(b["pred_sum"] / c, 4),
            "bias": round(b["err_sum"] / c, 4),
            "mae": round(b["abs_err_sum"] / c, 4),
        }

    quality = 48
    quality += min(sample_count, 150) * 0.28
    quality -= min(mae, 3.5) * 7.0
    quality -= min(abs(bias), 2.5) * 5.0
    if brier is not None:
        quality -= max(0, brier - 0.22) * 80
    quality = int(clamp(quality, 0, 100))

    profile = {
        "version": APP_VERSION,
        "updated_at": now_iso(),
        "samples": sample_count,
        "mae": round(mae, 3),
        "bias": round(bias, 3),
        "hit_rate": hit_rate,
        "avg_predicted_prob": round(avg_pred, 4),
        "brier": None if brier is None else round(brier, 4),
        "quality_score": quality,
        "bucket_stats": compact,
        "note": "True calibration active" if sample_count >= CALIBRATION_MIN_GLOBAL_SAMPLES else "Calibration building sample size",
    }
    try:
        save_json(CALIBRATION_ENGINE_FILE, profile)
    except Exception:
        pass
    return profile

def current_calibration_context(row, mean, active_line, active_source, fair_probability=None, price_is_real=False, score=None, risk_label=None, p10=None, p90=None):
    line = safe_float(active_line)
    proj = safe_float(mean)
    side = "NO LINE"
    if line is not None and proj is not None:
        side = "OVER" if proj > line else "UNDER"
    gap = None if line is None or proj is None else abs(proj - line)
    return {
        "prop_type": "pitcher_ks",
        "pick_side": side,
        "line_source": active_source,
        "line": line,
        "projection": proj,
        "abs_edge": gap,
        "fair_probability": fair_probability,
        "price_is_real": price_is_real,
        "data_score": score,
        "risk_label": risk_label,
        "lineup_locked": bool(row.get("lineup_locked")) if isinstance(row, dict) else False,
        "bullpen_status": row.get("bullpen_status") if isinstance(row, dict) else None,
        "bullpen_bf_factor": row.get("bullpen_bf_factor") if isinstance(row, dict) else None,
        "manager_hook_status": row.get("manager_hook_status") or row.get("manager_hook") if isinstance(row, dict) else None,
        "umpire": row.get("umpire") if isinstance(row, dict) else None,
        "ump_factor": row.get("ump_factor") if isinstance(row, dict) else None,
        "weather_factor": row.get("weather_factor") if isinstance(row, dict) else None,
        "p10": p10,
        "p90": p90,
    }

def calibration_weighted_bucket_blend(profile, context, mode="bias"):
    if not profile or profile.get("samples", 0) <= 0:
        return None
    bucket_stats = profile.get("bucket_stats") or {}
    tags = calibration_tags_from_row(context or {})
    vals = []
    for tag in tags:
        b = bucket_stats.get(tag)
        if not b:
            continue
        count = int(b.get("count") or 0)
        if count < CALIBRATION_MIN_BUCKET_SAMPLES:
            continue
        if mode == "prob_delta":
            val = safe_float(b.get("win_rate"), 0.5) - safe_float(b.get("avg_pred"), 0.5)
        elif mode == "mae":
            val = safe_float(b.get("mae"))
        else:
            val = safe_float(b.get("bias"))
        if val is None:
            continue
        weight = math.sqrt(count)
        if tag.startswith("side_source="):
            weight *= 1.35
        if tag.startswith("prob_bucket=") or tag.startswith("edge_bucket="):
            weight *= 1.15
        vals.append((val, weight, tag, count))
    if not vals:
        return None
    total_w = sum(w for _, w, _, _ in vals) or 1.0
    blended = sum(v * w for v, w, _, _ in vals) / total_w
    sample_strength = sum(c for _, _, _, c in vals)
    return {"value": blended, "tags": [t for _, _, t, _ in vals], "sample_strength": sample_strength}

def apply_calibration_adjustment(k_rate, calibration_profile, enabled=True):
    # Backward-compatible pre-simulation K-rate adjustment. Kept deliberately small.
    if not enabled:
        return k_rate, "Calibration adjustment disabled"
    if not calibration_profile or calibration_profile.get("samples", 0) < CALIBRATION_MIN_GLOBAL_SAMPLES:
        return k_rate, "Calibration sample too small; no adjustment"
    bias = safe_float(calibration_profile.get("bias"), 0) or 0
    quality = safe_float(calibration_profile.get("quality_score"), 50) or 50
    confidence = clamp((quality - 45) / 55, 0.15, 0.85)
    factor = clamp(1 + (bias * 0.006 * confidence), 0.975, 1.025)
    return clamp(k_rate * factor, 0.08, 0.50), f"True calibration K-rate n={calibration_profile.get('samples')} x{factor:.3f}"

def apply_true_projection_calibration(mean, sims, context, calibration_profile, enabled=True):
    if not enabled:
        return mean, sims, {"active": False, "shift": 0.0, "note": "True calibration disabled"}
    if not calibration_profile or calibration_profile.get("samples", 0) < CALIBRATION_MIN_GLOBAL_SAMPLES:
        n = 0 if not calibration_profile else calibration_profile.get("samples", 0)
        return mean, sims, {"active": False, "shift": 0.0, "note": f"True calibration warming up ({n}/{CALIBRATION_MIN_GLOBAL_SAMPLES})"}

    global_bias = safe_float(calibration_profile.get("bias"), 0.0) or 0.0
    blend = calibration_weighted_bucket_blend(calibration_profile, context, mode="bias")
    bucket_bias = safe_float(blend.get("value")) if blend else None
    if bucket_bias is None:
        raw_shift = global_bias * 0.45
        used = "global"
        sample_strength = calibration_profile.get("samples", 0)
    else:
        raw_shift = (global_bias * 0.30) + (bucket_bias * 0.70)
        used = "bucket+global"
        sample_strength = blend.get("sample_strength", 0)

    quality = safe_float(calibration_profile.get("quality_score"), 50) or 50
    strength = clamp((quality / 100.0) * (sample_strength / (sample_strength + 80.0)), 0.10, 0.85)
    shift = clamp(raw_shift * strength, -CALIBRATION_MAX_PROJ_SHIFT_KS, CALIBRATION_MAX_PROJ_SHIFT_KS)
    if abs(shift) < 0.01:
        return mean, sims, {"active": False, "shift": 0.0, "note": f"True calibration neutral ({used})"}
    new_sims = np.clip(np.asarray(sims, dtype=float) + shift, 0, None)
    new_mean = float(np.mean(new_sims))
    return new_mean, new_sims, {
        "active": True,
        "shift": round(float(shift), 3),
        "note": f"True calibration projection shift {shift:+.2f} Ks ({used}, q={int(quality)}, n={calibration_profile.get('samples')})"
    }

def apply_true_probability_calibration(fair_prob, context, calibration_profile, enabled=True):
    p = safe_float(fair_prob)
    if p is None:
        return fair_prob, {"active": False, "shift": 0.0, "note": "No probability to calibrate"}
    if not enabled:
        return clamp(p, 0.01, 0.99), {"active": False, "shift": 0.0, "note": "True probability calibration disabled"}
    if not calibration_profile or calibration_profile.get("samples", 0) < CALIBRATION_MIN_GLOBAL_SAMPLES:
        n = 0 if not calibration_profile else calibration_profile.get("samples", 0)
        return clamp(p, 0.01, 0.99), {"active": False, "shift": 0.0, "note": f"Probability calibration warming up ({n}/{CALIBRATION_MIN_GLOBAL_SAMPLES})"}

    blend = calibration_weighted_bucket_blend(calibration_profile, context, mode="prob_delta")
    delta = safe_float(blend.get("value")) if blend else 0.0
    sample_strength = blend.get("sample_strength", 0) if blend else 0
    quality = safe_float(calibration_profile.get("quality_score"), 50) or 50
    reliability = clamp((quality / 100.0) * (sample_strength / (sample_strength + 70.0)), 0.0, 0.75)

    # Noise dampening: wide simulation intervals, weak data, fallback lineups, and estimated odds get pulled toward 50%.
    p10 = safe_float((context or {}).get("p10"))
    p90 = safe_float((context or {}).get("p90"))
    range_width = (p90 - p10) if p10 is not None and p90 is not None else None
    volatility = clamp((range_width or 3.5) / CALIBRATION_NOISE_RANGE_SOFT_CAP, 0.65, 1.35)
    score = safe_float((context or {}).get("data_score"), 80) or 80
    score_shrink = clamp((score - 55) / 45.0, 0.35, 1.0)
    lineup_shrink = 1.0 if (context or {}).get("lineup_locked") else 0.82
    price_shrink = 1.0 if (context or {}).get("price_is_real") else 0.92
    noise_strength = clamp(score_shrink * lineup_shrink * price_shrink / volatility, 0.38, 1.0)

    shifted = p + clamp(delta * reliability, -CALIBRATION_MAX_PROB_SHIFT, CALIBRATION_MAX_PROB_SHIFT)
    damped = 0.50 + ((shifted - 0.50) * noise_strength)
    final = clamp(damped, 0.01, 0.99)
    shift = final - p
    note = f"True probability calibration {shift:+.1%} | reliability {reliability:.2f} | noise {noise_strength:.2f}"
    return final, {"active": abs(shift) >= 0.002, "shift": round(float(shift), 4), "note": note, "reliability": round(reliability, 3), "noise_strength": round(noise_strength, 3)}

def build_true_calibration_dashboard(results):
    profile = build_model_calibration_profile(results or [])
    rows = []
    for tag, b in (profile.get("bucket_stats") or {}).items():
        rows.append({
            "Bucket": tag,
            "Samples": b.get("count"),
            "Wins": b.get("wins"),
            "Smoothed Win Rate": round((b.get("win_rate") or 0) * 100, 1),
            "Raw Win Rate": round((b.get("raw_win_rate") or 0) * 100, 1),
            "Avg Pred %": round((b.get("avg_pred") or 0) * 100, 1),
            "Prob Delta %": round(((b.get("win_rate") or 0.5) - (b.get("avg_pred") or 0.5)) * 100, 1),
            "Bias Ks": b.get("bias"),
            "MAE Ks": b.get("mae"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Samples", "Prob Delta %"], ascending=[False, False])
    return profile, df

# =========================
# MLB DATA
# =========================
def target_dates(day_mode):
    now = california_now()
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    if day_mode == "Today":
        return [today]
    if day_mode == "Tomorrow":
        return [tomorrow]
    return [today, tomorrow]

@st.cache_data(ttl=300, show_spinner=False)
def get_schedule(date_str):
    return safe_get_json(
        f"{MLB_BASE}/schedule",
        params={"sportId": 1, "date": date_str, "hydrate": "probablePitcher,venue,team"}
    ) or {"dates": []}

def extract_probable_pitchers(date_str):
    sched = get_schedule(date_str)
    rows = []
    for d in sched.get("dates", []):
        for g in d.get("games", []):
            game_pk = g.get("gamePk")
            teams = g.get("teams", {})
            away = teams.get("away", {}).get("team", {})
            home = teams.get("home", {}).get("team", {})
            away_pp = teams.get("away", {}).get("probablePitcher")
            home_pp = teams.get("home", {}).get("probablePitcher")
            status = g.get("status", {}).get("abstractGameState", "Preview")
            game_time = g.get("gameDate", "")
            venue = g.get("venue", {}).get("name", "")

            if away_pp:
                rows.append({
                    "date": date_str,
                    "game_pk": game_pk,
                    "game_time": game_time,
                    "status": status,
                    "venue": venue,
                    "pitcher_id": away_pp.get("id"),
                    "pitcher": away_pp.get("fullName"),
                    "hand": away_pp.get("pitchHand", {}).get("code", "R"),
                    "team": away.get("abbreviation", away.get("name")),
                    "team_id": away.get("id"),
                    "opponent": home.get("abbreviation", home.get("name")),
                    "opp_team_id": home.get("id"),
                    "home_team": home.get("name"),
                    "away_team": away.get("name"),
                    "opp_side": "home",
                    "matchup": f"{away.get('abbreviation', away.get('name'))} @ {home.get('abbreviation', home.get('name'))}",
                    "pitcher_confirmed": True
                })
            if home_pp:
                rows.append({
                    "date": date_str,
                    "game_pk": game_pk,
                    "game_time": game_time,
                    "status": status,
                    "venue": venue,
                    "pitcher_id": home_pp.get("id"),
                    "pitcher": home_pp.get("fullName"),
                    "hand": home_pp.get("pitchHand", {}).get("code", "R"),
                    "team": home.get("abbreviation", home.get("name")),
                    "team_id": home.get("id"),
                    "opponent": away.get("abbreviation", away.get("name")),
                    "opp_team_id": away.get("id"),
                    "home_team": home.get("name"),
                    "away_team": away.get("name"),
                    "opp_side": "away",
                    "matchup": f"{away.get('abbreviation', away.get('name'))} @ {home.get('abbreviation', home.get('name'))}",
                    "pitcher_confirmed": True
                })
    for _p in locals().get("board", locals().get("rows", locals().get("out", []))):
        if isinstance(_p, dict) and "prop_rows" in _p:
            _p["prop_rows"] = clean_real_prop_debug_rows(_p.get("prop_rows", []))
    return rows

def get_pitcher_profile(pid):
    data = safe_get_json(
        f"{MLB_BASE}/people/{pid}/stats",
        params={"stats": "season", "group": "pitching"}
    )
    default = {"Pitcher K%": LEAGUE_AVG_K, "BF": 0, "SO": 0, "AVG IP": None, "K/9": None, "source": "Fallback league avg"}
    try:
        split = get_first_stat_split(data)
        if not split:
            return default
        stat = split.get("stat", {})
        ip = baseball_ip_to_float(stat.get("inningsPitched"))
        so = safe_float(stat.get("strikeOuts"), 0) or 0
        bf = safe_float(stat.get("battersFaced"), 0) or 0
        gs = safe_float(stat.get("gamesStarted"), None)
        gp = safe_float(stat.get("gamesPlayed"), 0) or 0
        starts = gs if gs and gs > 0 else gp
        k_pct = so / bf if bf > 0 else LEAGUE_AVG_K
        k9 = so / ip * 9 if ip and ip > 0 else None
        avg_ip = ip / starts if starts and starts > 0 and ip else None
        shrunk = ((k_pct * bf) + (LEAGUE_AVG_K * 150)) / max(bf + 150, 1)
        return {"Pitcher K%": float(clamp(shrunk, 0.08, 0.45)), "BF": bf, "SO": so, "AVG IP": avg_ip, "K/9": k9, "source": "Season K/BF with shrink"}
    except Exception:
        return default

def get_recent_logs(pid, n=12):
    data = safe_get_json(f"{MLB_BASE}/people/{pid}/stats", params={"stats": "gameLog", "group": "pitching"})
    rows = []
    try:
        splits = data["stats"][0]["splits"]
    except Exception:
        return rows
    for g in splits[:n]:
        stat = g.get("stat", {})
        ip_float = baseball_ip_to_float(stat.get("inningsPitched"))
        bf = safe_float(stat.get("battersFaced"))
        so = safe_float(stat.get("strikeOuts"))
        pitches = safe_float(stat.get("numberOfPitches"))
        rows.append({
            "Date": g.get("date"),
            "Opponent": g.get("opponent", {}).get("name"),
            "IP": stat.get("inningsPitched"),
            "IP_float": ip_float,
            "Ks": so,
            "BF": bf,
            "Pitches": pitches,
            "ER": safe_float(stat.get("earnedRuns")),
            "H": safe_float(stat.get("hits")),
            "R": safe_float(stat.get("runs")),
            "BB": safe_float(stat.get("baseOnBalls")),
            "K%": None if not bf else round((so or 0) / bf * 100, 1)
        })
    return rows

def build_leash_model(recent_rows):
    """Projected batters faced with a safer pitcher-leash model."""
    if not recent_rows:
        return {
            "expected_bf": DEFAULT_BF,
            "ppb": 3.9,
            "recent_ip": 5.5,
            "last_10_ks": [],
            "leash_risk": "UNKNOWN",
            "source": "Default fallback"
        }

    df = pd.DataFrame(recent_rows)

    def mean_col(col, rows=None):
        try:
            x = df[col] if rows is None else df.head(rows)[col]
            x = pd.to_numeric(x, errors="coerce").dropna()
            return float(x.mean()) if len(x) else None
        except Exception:
            return None

    avg_bf_l10 = mean_col("BF")
    avg_bf_l5 = mean_col("BF", 5)
    avg_bf_l3 = mean_col("BF", 3)
    avg_ip_l3 = mean_col("IP_float", 3)
    avg_pitches_l3 = mean_col("Pitches", 3)
    avg_pitches_l5 = mean_col("Pitches", 5)

    if avg_bf_l3 and avg_bf_l5 and avg_bf_l10:
        expected_bf = avg_bf_l3 * 0.55 + avg_bf_l5 * 0.30 + avg_bf_l10 * 0.15
        source = "Weighted L3/L5/L10 BF"
    elif avg_bf_l3 and avg_bf_l10:
        expected_bf = avg_bf_l3 * 0.65 + avg_bf_l10 * 0.35
        source = "Weighted L3/L10 BF"
    elif avg_bf_l3:
        expected_bf = avg_bf_l3
        source = "Last 3 BF"
    elif avg_bf_l10:
        expected_bf = avg_bf_l10
        source = "Last 10 BF"
    else:
        expected_bf = DEFAULT_BF
        source = "Default fallback"

    ppb = 3.9
    if avg_pitches_l3 and avg_bf_l3 and avg_bf_l3 > 0:
        ppb = avg_pitches_l3 / avg_bf_l3

    leash_risk = "NORMAL"

    # v9.7 stricter leash: volume is the biggest source of false OVER confidence.
    if ppb >= 4.25:
        expected_bf -= 2.7
        leash_risk = "HIGH_PITCH_COUNT"
    elif ppb >= 4.05:
        expected_bf -= 1.4
        leash_risk = "MILD_PITCH_COUNT"

    # Recent short starts reduce leash confidence more aggressively.
    if avg_ip_l3 is not None and avg_ip_l3 < 5.0:
        expected_bf -= 2.1
        leash_risk = "SHORT_RECENT_STARTS"

    # Recent very high pitch workload: stronger fatigue haircut.
    if avg_pitches_l5 is not None and avg_pitches_l5 > 95:
        expected_bf -= 1.4
        leash_risk = "HIGH_RECENT_WORKLOAD"

    pitch_trend_factor, pitch_trend_note = pitch_count_trend_bf_factor(recent_rows)
    expected_bf = float(clamp(expected_bf * pitch_trend_factor, 14, 31))

    return {
        "expected_bf": expected_bf,
        "ppb": float(ppb),
        "recent_ip": float(avg_ip_l3 or 5.5),
        "last_10_ks": [safe_int(r.get("Ks"), 0) or 0 for r in recent_rows[:10]],
        "leash_risk": leash_risk,
        "pitch_count_trend_factor": round(float(pitch_trend_factor), 3),
        "pitch_count_trend_note": pitch_trend_note,
        "source": f"{source}; {pitch_trend_note}"
    }


# =========================
# LIGHT TRUE LEASH + BATTERS FACED ENGINE
# Hot-run safe version:
# - LIGHT overlay only
# - adjusts expected BF/opportunity, NOT raw K skill
# - keeps v11.17 upside personality intact
# - designed to prevent fake overs without killing true upside
# =========================
LIGHT_TRUE_LEASH_BF_ENABLED = True
LIGHT_TRUE_LEASH_MIN_FACTOR = 0.925
LIGHT_TRUE_LEASH_MAX_FACTOR = 1.035
LIGHT_TRUE_LEASH_BF_MIN = 14.0
LIGHT_TRUE_LEASH_BF_MAX = 31.5

def _ltl_avg(vals):
    vals = [safe_float(v) for v in (vals or []) if safe_float(v) is not None]
    return float(np.mean(vals)) if vals else None

def _ltl_recent_col(recent_rows, key, n=5):
    out = []
    for r in (recent_rows or [])[:n]:
        if isinstance(r, dict):
            v = safe_float(r.get(key))
            if v is not None:
                out.append(v)
    return out

def light_true_leash_bf_engine(base_expected_bf, recent_rows=None, row=None):
    """Light BF overlay for v11.17 Upside.

    This is intentionally softer than the full TRUE LEASH engine:
    - max cut is small
    - max boost is small
    - no projection nerfing
    - only updates expected_bf before simulation/probability
    """
    if not LIGHT_TRUE_LEASH_BF_ENABLED:
        return base_expected_bf, {"factor": 1.0, "label": "OFF", "score": 50, "flags": [], "note": "Light true leash off"}

    bf0 = safe_float(base_expected_bf, DEFAULT_BF) or DEFAULT_BF
    rows = recent_rows or []
    row = row or {}

    avg_bf_l3 = _ltl_avg(_ltl_recent_col(rows, "BF", 3))
    avg_bf_l5 = _ltl_avg(_ltl_recent_col(rows, "BF", 5))
    avg_ip_l3 = _ltl_avg(_ltl_recent_col(rows, "IP_float", 3))
    avg_pitches_l3 = _ltl_avg(_ltl_recent_col(rows, "Pitches", 3))
    avg_bb_l3 = _ltl_avg(_ltl_recent_col(rows, "BB", 3))

    factor = 1.0
    score = 60.0
    flags = []

    # Small anchor toward real recent BF.
    recent_anchor = None
    if avg_bf_l3 and avg_bf_l5:
        recent_anchor = avg_bf_l3 * 0.60 + avg_bf_l5 * 0.40
    elif avg_bf_l3:
        recent_anchor = avg_bf_l3
    elif avg_bf_l5:
        recent_anchor = avg_bf_l5

    if recent_anchor is not None:
        gap = recent_anchor - bf0
        bf0 = bf0 + clamp(gap * 0.22, -1.35, 1.10)
        score += clamp(gap * 1.4, -8, 6)
        flags.append(f"RECENT_BF {recent_anchor:.1f}")

    # Pitch stress: light cuts only.
    ppb_l3 = None
    if avg_pitches_l3 and avg_bf_l3 and avg_bf_l3 > 0:
        ppb_l3 = avg_pitches_l3 / avg_bf_l3
        if ppb_l3 >= 4.40:
            factor *= 0.955
            score -= 10
            flags.append("HIGH_PITCH_STRESS")
        elif ppb_l3 >= 4.18:
            factor *= 0.978
            score -= 5
            flags.append("MILD_PITCH_STRESS")
        elif ppb_l3 <= 3.55 and avg_pitches_l3 >= 86:
            factor *= 1.012
            score += 3
            flags.append("EFFICIENT_VOLUME")

    # IP trend: light.
    if avg_ip_l3 is not None:
        if avg_ip_l3 < 4.5:
            factor *= 0.945
            score -= 11
            flags.append("SHORT_L3_IP")
        elif avg_ip_l3 < 5.0:
            factor *= 0.975
            score -= 5
            flags.append("LOW_L3_IP")
        elif avg_ip_l3 >= 6.2:
            factor *= 1.015
            score += 4
            flags.append("STRONG_L3_IP")

    # Walk stress.
    if avg_bb_l3 is not None:
        if avg_bb_l3 >= 3.0:
            factor *= 0.965
            score -= 7
            flags.append("WALK_STRESS")
        elif avg_bb_l3 >= 2.3:
            factor *= 0.985
            score -= 3
            flags.append("MILD_WALK_STRESS")

    # Existing manager/leash tags.
    manager_hook = str(row.get("manager_hook_status") or row.get("manager_hook") or "").upper()
    leash_risk = str(row.get("leash_risk") or row.get("risk_label") or "").upper()
    if "STRICT" in manager_hook or "STRICT" in leash_risk:
        factor *= 0.955
        score -= 9
        flags.append("STRICT_HOOK")
    elif "SHORT" in manager_hook or "SHORT" in leash_risk:
        factor *= 0.970
        score -= 6
        flags.append("SHORT_LEASH")

    # Existing role safety.
    role_text = str(row.get("pitcher_role") or row.get("role") or "").upper()
    if any(x in role_text for x in ["OPENER", "BULK", "FOLLOWER"]):
        factor *= 0.925
        score -= 18
        flags.append("ROLE_VOLUME_RISK")

    # Bullpen context: small only.
    bullpen_status = str(row.get("bullpen_status") or "").upper()
    if any(x in bullpen_status for x in ["TIRED", "HEAVY", "TAXED", "FATIGUED"]):
        factor *= 1.010
        score += 3
        flags.append("BULLPEN_NEEDS_LENGTH")
    elif any(x in bullpen_status for x in ["FRESH", "RESTED"]):
        factor *= 0.995
        flags.append("FRESH_BULLPEN")

    factor = clamp(factor, LIGHT_TRUE_LEASH_MIN_FACTOR, LIGHT_TRUE_LEASH_MAX_FACTOR)
    new_bf = float(clamp(bf0 * factor, LIGHT_TRUE_LEASH_BF_MIN, LIGHT_TRUE_LEASH_BF_MAX))
    score = int(clamp(round(score), 0, 100))

    if score >= 76:
        label = "STRONG_LEASH"
    elif score >= 60:
        label = "STABLE_LEASH"
    elif score >= 44:
        label = "FRAGILE_LEASH"
    else:
        label = "DANGER_LEASH"

    return new_bf, {
        "factor": round(float(factor), 3),
        "label": label,
        "score": score,
        "flags": flags[:6],
        "note": f"{label}: BF {safe_float(base_expected_bf, DEFAULT_BF):.1f} -> {new_bf:.1f} | light factor {factor:.3f}",
        "avg_bf_l3": None if avg_bf_l3 is None else round(avg_bf_l3, 2),
        "avg_ip_l3": None if avg_ip_l3 is None else round(avg_ip_l3, 2),
        "ppb_l3": None if ppb_l3 is None else round(ppb_l3, 2),
    }


def apply_managerial_hook_v11_9(expected_bf, recent_rows):
    """v11.9: conservative starter-volume haircut for repeated early hooks.

    Uses the pitcher's recent game logs only. If he is getting pulled around or
    before the third-time-through window too often, we trim expected BF slightly.
    The cut is capped and does not remove the existing leash/pitch-count model.
    """
    bf0 = safe_float(expected_bf, DEFAULT_BF) or DEFAULT_BF
    if not recent_rows:
        return bf0, "UNKNOWN", "Manager hook neutral: no recent starts"
    usable = []
    for r in recent_rows[:8]:
        bf = safe_float(r.get("BF"), None)
        if bf is not None and bf > 0:
            usable.append(bf)
    if len(usable) < 3:
        return bf0, "LOW_SAMPLE", f"Manager hook neutral: only {len(usable)} recent BF samples"
    early_hooks = sum(1 for bf in usable if bf <= MANAGER_HOOK_RECENT_BF_CUTOFF)
    hook_rate = early_hooks / max(1, len(usable))
    if hook_rate >= MANAGER_HOOK_RATE_TRIGGER and bf0 >= TTTO_THRESHOLD_BATTERS:
        new_bf = float(clamp(bf0 * (1.0 - MANAGER_HOOK_STRICTNESS), 14, 31))
        return new_bf, "STRICT_HOOK", f"Manager hook cut x{1.0-MANAGER_HOOK_STRICTNESS:.3f}: early-hook rate {hook_rate:.0%} ({early_hooks}/{len(usable)})"
    return bf0, "NORMAL", f"Manager hook normal: early-hook rate {hook_rate:.0%} ({early_hooks}/{len(usable)})"

def blend_pitcher_k_rate(profile_k, recent_rows, pitcher_id):
    profile_k = profile_k if profile_k is not None else LEAGUE_AVG_K
    recent_rates = []
    for r in recent_rows[:5]:
        bf = safe_float(r.get("BF"))
        ks = safe_float(r.get("Ks"))
        if bf and bf > 0 and ks is not None:
            recent_rates.append(ks / bf)
    if recent_rates:
        l5 = float(np.mean(recent_rates))
        base = profile_k * 0.70 + l5 * 0.30
        source = "Season K% + recent-start K% blend"
    else:
        base = profile_k
        source = "Season pitcher K%"
    learned, scale = apply_learning(pitcher_id, base)
    return clamp(learned, 0.08, 0.48), source, scale

def calculate_log5_k_rate(pitcher_k, lineup_k, league_avg_k=LEAGUE_AVG_K):
    pitcher_k = clamp(pitcher_k, 0.01, 0.60)
    lineup_k = clamp(lineup_k, 0.01, 0.60)
    num = (pitcher_k * lineup_k) / league_avg_k
    den = num + ((1 - pitcher_k) * (1 - lineup_k)) / (1 - league_avg_k)
    return float(num / den)

# =========================
# v10.9 TRUE EDGE MERGE HELPERS
# =========================
def elite_pitcher_boost_factor(k_rate):
    """Small K-skill boost for elite strikeout arms.

    Kept conservative because Statcast, recent form, and Log5 already capture a lot
    of pitcher skill. This should never turn a weak edge into an automatic play.
    """
    k_rate = safe_float(k_rate, LEAGUE_AVG_K) or LEAGUE_AVG_K
    if k_rate >= 0.30:
        return 1.035, "Elite pitcher K boost x1.035"
    if k_rate >= 0.27:
        return 1.025, "High-K pitcher boost x1.025"
    if k_rate >= 0.24:
        return 1.015, "Above-average pitcher K boost x1.015"
    return 1.000, "No elite pitcher boost"

def opponent_k_context_factor(lineup_k):
    """Extra lineup strikeout-context nudge after Log5.

    The main opponent-K signal is still the posted-lineup/hitter blend. This small
    factor only recognizes extreme high-K or low-K lineups without double-counting.
    """
    lk = safe_float(lineup_k, LEAGUE_AVG_K) or LEAGUE_AVG_K
    diff = lk - LEAGUE_AVG_K
    if diff >= 0.040:
        return 1.045, "Extreme high-K opponent context x1.045"
    if diff >= 0.030:
        return 1.035, "High-K opponent context x1.035"
    if diff >= 0.020:
        return 1.020, "Above-average opponent K context x1.020"
    if diff <= -0.035:
        return 0.955, "Extreme contact opponent context x0.955"
    if diff <= -0.025:
        return 0.970, "Low-K opponent context x0.970"
    return 1.000, "Neutral opponent K context"

def pitch_count_trend_bf_factor(recent_rows):
    """Recent pitch-count trend factor for starter BF/leash.

    Uses only real recent game-log pitch counts. Missing data remains neutral.
    """
    vals = []
    for r in (recent_rows or [])[:3]:
        p = safe_float(r.get("Pitches"))
        if p is not None and p > 0:
            vals.append(p)
    if not vals:
        return 1.0, "Pitch-count trend unavailable; neutral"
    avg = float(np.mean(vals))
    if avg >= 100:
        return 1.040, f"Recent pitch-count leash boost x1.040 (L3 avg {avg:.0f})"
    if avg >= 92:
        return 1.020, f"Recent pitch-count leash boost x1.020 (L3 avg {avg:.0f})"
    if avg <= 82:
        return 0.940, f"Recent low pitch-count leash cut x0.940 (L3 avg {avg:.0f})"
    return 1.000, f"Neutral pitch-count trend (L3 avg {avg:.0f})"

def tto_decay_factor(pa_index):
    """Third-time-through-order decay for PA-by-PA K probabilities."""
    i = int(pa_index)
    if i < 18:
        return 1.000
    if i < 27:
        return 0.925
    return 0.860

# =========================
# LINEUP / BATTER K
# =========================
@st.cache_data(ttl=600, show_spinner=False)
def get_batter_season_k_rate(player_id):
    data = safe_get_json(f"{MLB_BASE}/people/{player_id}/stats", params={"stats": "season", "group": "hitting"})
    try:
        split = get_first_stat_split(data)
        if not split:
            return None, None, None
        stat = split.get("stat", {})
        so = safe_float(stat.get("strikeOuts"), 0) or 0
        pa = safe_float(stat.get("plateAppearances"), 0) or 0
        ab = safe_float(stat.get("atBats"), 0) or 0
        denom = pa if pa and pa > 0 else ab
        return (so / denom if denom and denom > 0 else None), so, denom
    except Exception:
        return None, None, None

@st.cache_data(ttl=600, show_spinner=False)
def get_batter_k_rate_vs_pitcher_hand(player_id, pitcher_hand):
    if not player_id or pitcher_hand not in ["R", "L"]:
        return None, None, None, "No pitcher hand"
    sit_code = "vrhp" if pitcher_hand == "R" else "vlhp"
    urls = [
        (f"{MLB_BASE}/people/{player_id}/stats", {"stats": "statSplits", "group": "hitting", "sitCodes": sit_code}),
        (f"{MLB_BASE}/people/{player_id}/stats", {"stats": "season", "group": "hitting", "sitCodes": sit_code}),
    ]
    for url, params in urls:
        data = safe_get_json(url, params=params)
        if not isinstance(data, dict):
            continue
        stats = data.get("stats") or []
        for block in stats:
            for split in (block.get("splits") or []):
                stat = split.get("stat") or {}
                so = safe_float(stat.get("strikeOuts"), 0) or 0
                pa = safe_float(stat.get("plateAppearances"), 0) or 0
                ab = safe_float(stat.get("atBats"), 0) or 0
                denom = pa if pa and pa > 0 else ab
                if denom and denom >= 10:
                    return float(so / denom), so, denom, f"Real split vs {'RHP' if pitcher_hand == 'R' else 'LHP'}"
    return None, None, None, "Split unavailable"


@st.cache_data(ttl=21600, show_spinner=False)
def get_batter_rolling_k_rates(player_id, days_list=(14, 30)):
    """Real rolling hitter K rates from MLB game logs.

    Returns only rates supported by real PA/SO game-log rows. Missing data gets no fake weight.
    """
    result = {int(d): None for d in days_list}
    if not player_id:
        return result
    data = safe_get_json(f"{MLB_BASE}/people/{player_id}/stats", params={"stats": "gameLog", "group": "hitting"})
    if not isinstance(data, dict):
        return result
    stats = data.get("stats") or []
    if not stats or not isinstance(stats[0], dict):
        return result
    splits = stats[0].get("splits") or []
    if not splits:
        return result
    today_dt = datetime.utcnow().date()
    for window in days_list:
        so_total, pa_total = 0.0, 0.0
        for g in splits:
            try:
                gdate = datetime.strptime(g.get("date", ""), "%Y-%m-%d").date()
            except Exception:
                continue
            age = (today_dt - gdate).days
            if age < 0 or age > int(window):
                continue
            stat = g.get("stat") or {}
            so = safe_float(stat.get("strikeOuts"), 0) or 0
            pa = safe_float(stat.get("plateAppearances"), 0) or 0
            if pa <= 0:
                pa = safe_float(stat.get("atBats"), 0) or 0
            so_total += so
            pa_total += pa
        if pa_total >= 8:
            result[int(window)] = float(so_total / pa_total)
    return result

def blend_batter_k_inputs(season_k, split_k=None, season_pa=None, split_pa=None, rolling14=None, rolling30=None):
    """Blend only real batter K inputs. Missing parts get zero weight."""
    parts = []
    if split_k is not None:
        # hand split is most matchup-specific, but still sample-sensitive
        split_weight = min(max((split_pa or 25) / 160, 0.20), 0.50)
        parts.append((float(split_k), split_weight, "hand split"))
    if rolling14 is not None:
        parts.append((float(rolling14), 0.25, "rolling 14d"))
    if rolling30 is not None:
        parts.append((float(rolling30), 0.15, "rolling 30d"))
    if season_k is not None:
        season_weight = min(max((season_pa or 50) / 300, 0.25), 0.45)
        parts.append((float(season_k), season_weight, "season"))
    if not parts:
        return None, "No batter K data"
    total_w = sum(w for _, w, _ in parts)
    blended = sum(v * w for v, w, _ in parts) / max(total_w, 1e-9)
    sources = ", ".join(src for _, _, src in parts)
    return clamp(blended, 0.04, 0.55), f"Blended real K inputs: {sources}"


def lineup_cache_key(game_pk, opp_side, pitcher_hand):
    return f"{game_pk}_{opp_side}_{pitcher_hand or 'NA'}"

def get_cached_lineup_rows(game_pk, opp_side, pitcher_hand):
    cache = load_json(LINEUP_CACHE_FILE, {})
    rec = cache.get(lineup_cache_key(game_pk, opp_side, pitcher_hand))
    return rec.get("rows", []) if rec else []

def set_cached_lineup_rows(game_pk, opp_side, pitcher_hand, rows):
    if not rows:
        return
    cache = load_json(LINEUP_CACHE_FILE, {})
    cache[lineup_cache_key(game_pk, opp_side, pitcher_hand)] = {"saved_at": now_iso(), "rows": rows[:9]}
    save_json(LINEUP_CACHE_FILE, cache)

# =========================
# MLB-ONLY PROJECTED LINEUP BUILDER
# Safe pre-lineup batter projection:
# - Does NOT create pitcher rows
# - Does NOT touch refresh flow
# - Does NOT use Rotowire
# - Uses MLB recent lineups / boxscores to estimate expected 1-9 hitters
# =========================
MLB_PROJECTED_LINEUPS_ENABLED = True
MLB_PROJECTED_LINEUP_LOOKBACK_GAMES = 5
MLB_PROJECTED_LINEUP_MIN_VALID_HITTERS = 5

def _proj_lu_team_id_from_game(game_pk, opp_side):
    try:
        live = safe_get_json(f"{MLB_LIVE}/game/{game_pk}/feed/live", timeout=12)
        box_team = (live or {}).get("liveData", {}).get("boxscore", {}).get("teams", {}).get(opp_side, {})
        tid = (box_team.get("team") or {}).get("id")
        if tid:
            return tid
        gd_team = (live or {}).get("gameData", {}).get("teams", {}).get(opp_side, {})
        return gd_team.get("id")
    except Exception:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def _proj_lu_recent_team_games(team_id, before_date=None, n=5):
    """Return recent completed gamePks for a team before target date."""
    if not team_id:
        return []
    try:
        if before_date:
            end_dt = datetime.strptime(str(before_date), "%Y-%m-%d").date() - timedelta(days=1)
        else:
            end_dt = california_now().date() - timedelta(days=1)
        start_dt = end_dt - timedelta(days=14)
        sched = safe_get_json(
            f"{MLB_BASE}/schedule",
            params={
                "sportId": 1,
                "teamId": team_id,
                "startDate": start_dt.strftime("%Y-%m-%d"),
                "endDate": end_dt.strftime("%Y-%m-%d"),
                "hydrate": "team",
            },
            timeout=14,
        ) or {"dates": []}
        games = []
        for d in sched.get("dates", []):
            for g in d.get("games", []):
                state = (g.get("status") or {}).get("abstractGameState")
                if state != "Final":
                    continue
                games.append((g.get("gameDate") or "", g.get("gamePk")))
        games = [pk for _, pk in sorted(games, reverse=True) if pk]
        return games[:int(n or 5)]
    except Exception:
        return []

def _proj_lu_hitter_from_box_player(pid, pdata):
    try:
        stats = (pdata.get("stats") or {}).get("batting") or {}
        bo = pdata.get("battingOrder")
        pos = ((pdata.get("position") or {}).get("abbreviation") or "").upper()
        name = (pdata.get("person") or {}).get("fullName")
        # Exclude pitchers as hitters unless they actually batted. Modern MLB DH means usually no pitchers.
        if pos == "P":
            return None
        ab = safe_float(stats.get("atBats"), 0) or 0
        pa_signal = ab + (safe_float(stats.get("baseOnBalls"), 0) or 0) + (safe_float(stats.get("hitByPitch"), 0) or 0) + (safe_float(stats.get("sacFlies"), 0) or 0)
        if not name or (bo is None and pa_signal <= 0):
            return None
        order = None
        if bo:
            try:
                order = int(str(bo)[:1])
            except Exception:
                order = None
        return {"id": safe_int(pid), "name": name, "order": order, "position": pos}
    except Exception:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def build_mlb_projected_lineup_rows(team_id, pitcher_hand=None, before_date=None):
    """Build projected batter rows from recent MLB starting lineups.

    Score = recent start frequency + batting-order frequency + recency.
    """
    if not MLB_PROJECTED_LINEUPS_ENABLED or not team_id:
        return []
    game_pks = _proj_lu_recent_team_games(team_id, before_date, MLB_PROJECTED_LINEUP_LOOKBACK_GAMES)
    if not game_pks:
        return []

    candidates = {}
    for g_idx, gpk in enumerate(game_pks):
        try:
            live = safe_get_json(f"{MLB_LIVE}/game/{gpk}/feed/live", timeout=14)
            teams = (live or {}).get("liveData", {}).get("boxscore", {}).get("teams", {})
            side = None
            for s in ["away", "home"]:
                if ((teams.get(s) or {}).get("team") or {}).get("id") == team_id:
                    side = s
                    break
            if not side:
                continue
            players = (teams.get(side) or {}).get("players") or {}
            recency_weight = max(0.45, 1.0 - (g_idx * 0.12))
            for k, pdata in players.items():
                pid = str(k).replace("ID", "")
                h = _proj_lu_hitter_from_box_player(pid, pdata)
                if not h:
                    continue
                cid = str(h["id"] or normalize_name(h["name"]))
                d = candidates.setdefault(cid, {
                    "id": h["id"],
                    "name": h["name"],
                    "orders": [],
                    "starts": 0.0,
                    "positions": [],
                    "last_seen_weight": 0.0,
                })
                d["starts"] += recency_weight
                d["last_seen_weight"] = max(d["last_seen_weight"], recency_weight)
                if h.get("order"):
                    d["orders"].append(h["order"])
                if h.get("position"):
                    d["positions"].append(h["position"])
        except Exception:
            continue

    if not candidates:
        return []

    ranked = []
    for cid, d in candidates.items():
        orders = [o for o in d.get("orders", []) if o]
        avg_order = float(np.mean(orders)) if orders else 9.0
        order_score = max(0, 10 - avg_order) * 0.20
        start_score = d.get("starts", 0) * 1.25
        recency_score = d.get("last_seen_weight", 0) * 0.65
        score = start_score + order_score + recency_score
        ranked.append((score, avg_order, d))

    ranked = sorted(ranked, key=lambda x: (-x[0], x[1]))[:9]
    projected = sorted(ranked, key=lambda x: x[1])
    rows = []
    for idx, (_, avg_order, d) in enumerate(projected, start=1):
        player_id = d.get("id")
        name = d.get("name")
        season_k, season_so, season_pa = get_batter_season_k_rate(player_id) if player_id else (None, None, None)
        split_k, split_so, split_pa, split_source = get_batter_k_rate_vs_pitcher_hand(player_id, pitcher_hand) if (player_id and pitcher_hand) else (None, None, None, "No split")
        rolling = get_batter_rolling_k_rates(player_id, days_list=(14, 30)) if player_id else {}
        rolling14 = rolling.get(14)
        rolling30 = rolling.get(30)
        used_k, used_source = blend_batter_k_inputs(
            season_k,
            split_k=split_k,
            season_pa=season_pa,
            split_pa=split_pa,
            rolling14=rolling14,
            rolling30=rolling30,
        )
        if used_k is None:
            used_k = split_k if split_k is not None else season_k
            used_source = split_source if split_k is not None else "Season batter K%"
        rows.append({
            "Order": idx,
            "Batter": name,
            "Player ID": player_id,
            "Projected Order": round(float(avg_order), 2),
            "Start Score": round(float(d.get("starts", 0)), 2),
            "Season K%": None if season_k is None else round(season_k * 100, 1),
            "Split K%": None if split_k is None else round(split_k * 100, 1),
            "Rolling 14d K%": None if rolling14 is None else round(rolling14 * 100, 1),
            "Rolling 30d K%": None if rolling30 is None else round(rolling30 * 100, 1),
            "Split PA/AB": split_pa,
            "Used K%": None if used_k is None else round(used_k * 100, 1),
            "K Source": f"MLB projected lineup + {used_source}",
            "SO": season_so,
            "PA/AB": season_pa,
            "Raw_K_Rate": used_k,
            "Lineup Source": "MLB_PROJECTED_RECENT_LINEUP",
        })
    valid = [r.get("Raw_K_Rate") for r in rows if r.get("Raw_K_Rate") is not None]
    if len(valid) >= MLB_PROJECTED_LINEUP_MIN_VALID_HITTERS:
        return rows[:9]
    return []


@st.cache_data(ttl=300, show_spinner=False)
def calculate_lineup_k_rate(game_pk, opp_side, pitcher_hand=None):
    box = safe_get_json(f"{MLB_BASE}/game/{game_pk}/boxscore")
    if not box:
        team_id = _proj_lu_team_id_from_game(game_pk, opp_side)
        proj_rows = build_mlb_projected_lineup_rows(team_id, pitcher_hand, before_date=None)
        valid_proj = [r.get("Raw_K_Rate") for r in proj_rows[:9] if r.get("Raw_K_Rate") is not None]
        if len(valid_proj) >= MLB_PROJECTED_LINEUP_MIN_VALID_HITTERS:
            return float(np.mean(valid_proj)), proj_rows[:9], "MLB projected recent lineup K%", False
        cached_rows = get_cached_lineup_rows(game_pk, opp_side, pitcher_hand)
        valid_cached = [r.get("Raw_K_Rate") for r in cached_rows[:9] if r.get("Raw_K_Rate") is not None]
        if len(valid_cached) >= 5:
            return float(np.mean(valid_cached)), cached_rows[:9], "Using cached locked lineup", True
        return None, [], "Boxscore not available", False
    players = box.get("teams", {}).get(opp_side, {}).get("players", {})
    rows = []
    for _, pdata in players.items():
        order = pdata.get("battingOrder")
        if not order:
            continue
        person = pdata.get("person", {})
        player_id = person.get("id")
        name = person.get("fullName")
        season_k, season_so, season_pa = get_batter_season_k_rate(player_id)
        split_k, split_so, split_pa, split_source = get_batter_k_rate_vs_pitcher_hand(player_id, pitcher_hand) if pitcher_hand else (None, None, None, "No split")
        rolling = get_batter_rolling_k_rates(player_id, days_list=(14, 30))
        rolling14 = rolling.get(14)
        rolling30 = rolling.get(30)
        used_k, used_source = blend_batter_k_inputs(
            season_k,
            split_k=split_k,
            season_pa=season_pa,
            split_pa=split_pa,
            rolling14=rolling14,
            rolling30=rolling30,
        )
        if used_k is None:
            used_k = split_k if split_k is not None else season_k
            used_source = split_source if split_k is not None else "Season batter K%"
        rows.append({
            "Order": int(str(order)[:3]),
            "Batter": name,
            "Player ID": player_id,
            "Season K%": None if season_k is None else round(season_k * 100, 1),
            "Split K%": None if split_k is None else round(split_k * 100, 1),
            "Rolling 14d K%": None if rolling14 is None else round(rolling14 * 100, 1),
            "Rolling 30d K%": None if rolling30 is None else round(rolling30 * 100, 1),
            "Split PA/AB": split_pa,
            "Used K%": None if used_k is None else round(used_k * 100, 1),
            "K Source": used_source,
            "SO": season_so,
            "PA/AB": season_pa,
            "Raw_K_Rate": used_k
        })
    rows = sorted(rows, key=lambda x: x["Order"])
    valid = [r["Raw_K_Rate"] for r in rows[:9] if r["Raw_K_Rate"] is not None]
    if len(valid) >= 5:
        set_cached_lineup_rows(game_pk, opp_side, pitcher_hand, rows[:9])
        lineup_k = float(np.mean(valid))
        split_count = sum(1 for r in rows[:9] if r.get("Split K%") is not None)
        msg = f"Posted lineup K%; splits for {split_count}/9 hitters"
        return lineup_k, rows[:9], msg, len(rows[:9]) >= 8
    team_id = _proj_lu_team_id_from_game(game_pk, opp_side)
    proj_rows = build_mlb_projected_lineup_rows(team_id, pitcher_hand, before_date=None)
    valid_proj = [r.get("Raw_K_Rate") for r in proj_rows[:9] if r.get("Raw_K_Rate") is not None]
    if len(valid_proj) >= MLB_PROJECTED_LINEUP_MIN_VALID_HITTERS:
        return float(np.mean(valid_proj)), proj_rows[:9], "MLB projected recent lineup K%", False
    cached_rows = get_cached_lineup_rows(game_pk, opp_side, pitcher_hand)
    valid_cached = [r.get("Raw_K_Rate") for r in cached_rows[:9] if r.get("Raw_K_Rate") is not None]
    if len(valid_cached) >= 5:
        return float(np.mean(valid_cached)), cached_rows[:9], "Current lineup thin; using cached locked lineup", True
    return None, rows, "Lineup not posted or not enough hitter K data", False

def team_k_vs_hand(team_id, hand):
    data = safe_get_json(f"{MLB_BASE}/teams/{team_id}/stats", params={"stats": "season", "group": "hitting"})
    try:
        split = get_first_stat_split(data)
        if not split:
            return LEAGUE_AVG_K, "League average fallback"
        stat = split.get("stat", {})
        so = safe_float(stat.get("strikeOuts"), 0) or 0
        pa = safe_float(stat.get("plateAppearances"), 0) or 0
        if pa > 0:
            return float(so / pa), "Team season K/PA fallback"
    except Exception:
        pass
    return LEAGUE_AVG_K, "League average fallback"


def projection_source_label(lineup_msg, lineup_locked, lineup_rows):
    """Clear projection-source label for every board/prop row.

    TRUE LINEUP = current posted 1-9 lineup from MLB boxscore.
    CACHED LINEUP = previously locked lineup used because current boxscore/feed is thin.
    TEAM FALLBACK = no usable lineup, using team K-rate fallback only.
    """
    msg = str(lineup_msg or "").lower()
    row_count = len(lineup_rows or [])
    if "cached" in msg:
        return "CACHED LINEUP"
    if lineup_locked and row_count >= 8 and ("posted lineup" in msg or "posted" in msg):
        return "TRUE LINEUP"
    if lineup_locked and row_count >= 8:
        return "TRUE LINEUP"
    return "TEAM FALLBACK"

def confirmed_lineup_status(source_label, lineup_rows):
    if source_label == "TRUE LINEUP":
        return "CONFIRMED"
    if source_label == "CACHED LINEUP":
        return "CACHED"
    if "PROJECTED RECENT" in str(source_label).upper() or any((r.get("Lineup Source") == "MLB_PROJECTED_RECENT_LINEUP") for r in (lineup_rows or []) if isinstance(r, dict)):
        return "MLB PROJECTED"
    return "FALLBACK"

@st.cache_data(ttl=900, show_spinner=False)
def get_recent_team_bullpen_usage(team_id, as_of_date, lookback_days=3):
    """Real 2-3 day bullpen workload from MLB schedule + boxscores.

    This reads actual team pitcher rows from completed MLB boxscores, excludes the
    starting pitcher, and sums reliever innings + pitch counts. Missing or
    incomplete data returns neutral so projections are not forced by guesses.
    """
    empty = {
        "available": False,
        "games": 0,
        "bullpen_ip": 0.0,
        "bullpen_pitches": 0.0,
        "appearances": 0,
        "back_to_back_relief_appearances": 0,
        "label": "UNKNOWN",
        "message": "Recent bullpen usage unavailable",
    }
    if not team_id:
        return empty

    try:
        end_dt = datetime.strptime(str(as_of_date)[:10], "%Y-%m-%d") - timedelta(days=1)
    except Exception:
        end_dt = california_now().replace(tzinfo=None) - timedelta(days=1)
    start_dt = end_dt - timedelta(days=max(1, int(lookback_days)) - 1)

    sched = safe_get_json(
        f"{MLB_BASE}/schedule",
        params={
            "sportId": 1,
            "teamId": int(team_id),
            "startDate": start_dt.strftime("%Y-%m-%d"),
            "endDate": end_dt.strftime("%Y-%m-%d"),
        },
        timeout=12,
    ) or {}

    games = []
    for d in sched.get("dates", []):
        for g in d.get("games", []):
            status = (g.get("status") or {}).get("abstractGameState", "")
            if status == "Final" and g.get("gamePk"):
                games.append(g)

    total_bullpen_ip = 0.0
    total_bullpen_pitches = 0.0
    total_appearances = 0
    used_games = 0
    reliever_dates = {}

    for g in games[-int(lookback_days):]:
        game_pk = g.get("gamePk")
        game_date = str(g.get("gameDate") or "")[:10] or str(g.get("officialDate") or "")[:10]
        box = safe_get_json(f"{MLB_BASE}/game/{game_pk}/boxscore", timeout=12)
        if not isinstance(box, dict):
            continue

        side = None
        for sname in ["away", "home"]:
            if str((box.get("teams", {}).get(sname, {}).get("team", {}) or {}).get("id")) == str(team_id):
                side = sname
                break
        if not side:
            continue

        team_box = box.get("teams", {}).get(side, {})
        pitcher_ids = team_box.get("pitchers") or []
        players = team_box.get("players") or {}
        if not pitcher_ids:
            continue

        starter_id = str(pitcher_ids[0])
        game_had_reliever = False

        for pid in pitcher_ids:
            pid_str = str(pid)
            if pid_str == starter_id:
                continue
            pdata = players.get(f"ID{pid_str}", {}) or {}
            pitching = ((pdata.get("stats") or {}).get("pitching") or {})
            ip = baseball_ip_to_float(pitching.get("inningsPitched"))
            pitches = safe_float(
                pitching.get("numberOfPitches", pitching.get("pitchesThrown", pitching.get("pitchCount"))),
                0,
            ) or 0

            # Count only real reliever workload rows. If IP is 0 but pitches exist,
            # keep the pitches because a rough/short outing still fatigues the pen.
            if ip is None and pitches <= 0:
                continue

            total_bullpen_ip += float(ip or 0.0)
            total_bullpen_pitches += float(pitches or 0.0)
            total_appearances += 1
            game_had_reliever = True
            reliever_dates.setdefault(pid_str, set()).add(game_date)

        if game_had_reliever:
            used_games += 1

    if used_games <= 0:
        return empty

    back_to_back = sum(1 for dates in reliever_dates.values() if len(dates) >= 2)
    label = "NEUTRAL"
    if total_bullpen_pitches >= 240 or total_bullpen_ip >= 18 or back_to_back >= 4:
        label = "TIRED"
    elif total_bullpen_pitches <= 120 and total_bullpen_ip <= 9 and back_to_back <= 1:
        label = "FRESH"

    return {
        "available": True,
        "games": int(used_games),
        "bullpen_ip": round(total_bullpen_ip, 2),
        "bullpen_pitches": round(total_bullpen_pitches, 1),
        "appearances": int(total_appearances),
        "back_to_back_relief_appearances": int(back_to_back),
        "label": label,
        "message": (
            f"Bullpen {label}: {total_bullpen_pitches:.0f} pitches, "
            f"{total_bullpen_ip:.1f} IP, {total_appearances} relief apps, "
            f"{back_to_back} B2B relievers over {used_games} game(s)"
        ),
    }


def bullpen_fatigue_bf_factor(team_id, as_of_date):
    """Small, capped starter BF adjustment from real recent bullpen fatigue.

    Tired bullpen = slightly longer starter leash. Fresh bullpen = tiny leash cut.
    This cannot override pitcher skill, lineup quality, Statcast, or real prop lines.
    """
    usage = get_recent_team_bullpen_usage(team_id, as_of_date, lookback_days=3)
    if not usage.get("available"):
        return 1.0, usage.get("message", "Recent bullpen usage unavailable"), usage

    label = usage.get("label", "NEUTRAL")
    pitches = safe_float(usage.get("bullpen_pitches"), 0) or 0
    ip = safe_float(usage.get("bullpen_ip"), 0) or 0
    b2b = safe_float(usage.get("back_to_back_relief_appearances"), 0) or 0

    factor = 1.0
    if label == "TIRED":
        factor = 1.04
        note = "Tired bullpen; capped starter-leash boost"
    elif label == "FRESH":
        factor = 0.97
        note = "Fresh bullpen; capped starter-leash haircut"
    else:
        # Small extra nudge for near-heavy usage without calling it tired.
        if pitches >= 190 or ip >= 14 or b2b >= 3:
            factor = 1.02
            note = "Moderate bullpen workload; small starter-leash boost"
        else:
            note = "Neutral recent bullpen workload"

    return float(clamp(factor, 0.96, 1.04)), f"{note} ({usage.get('message')})", usage



# =========================
# v11.10 DEEP BULLPEN / UMPIRE LEARNING
# =========================
def context_learn_bucket(value, cuts, labels):
    return calibration_bucket(value, cuts, labels)

def bullpen_context_key_from_usage(usage):
    usage = usage or {}
    label = str(usage.get("label") or "UNKNOWN").upper()
    pitches = safe_float(usage.get("bullpen_pitches"), 0) or 0
    ip = safe_float(usage.get("bullpen_ip"), 0) or 0
    b2b = safe_float(usage.get("back_to_back_relief_appearances"), 0) or 0
    p_bucket = context_learn_bucket(pitches, [120, 180, 240, 300], ["p<=120", "p121-180", "p181-240", "p241-300", "p300+"])
    ip_bucket = context_learn_bucket(ip, [8, 12, 18], ["ip<=8", "ip9-12", "ip13-18", "ip18+"])
    b2b_bucket = context_learn_bucket(b2b, [0, 1, 3], ["b2b0", "b2b1", "b2b2-3", "b2b4+"])
    return f"{label}|{p_bucket}|{ip_bucket}|{b2b_bucket}"

def umpire_context_key(name):
    nm = normalize_name(name or "Unknown").replace(" ", "_")
    return nm or "unknown"

def _load_context_model(path):
    data = load_json(path, {})
    if not isinstance(data, dict):
        return {}
    return data

def _save_context_model(path, data):
    save_json(path, data)

def _smoothed_error_factor(model, key, metric="bf_error", min_samples=10, max_adj=0.03, denominator=22.0):
    rec = (model or {}).get(str(key), {})
    n = int(rec.get("count") or 0)
    if n < min_samples:
        return 1.0, f"learning warming up ({n}/{min_samples})", n
    avg_err = safe_float(rec.get(metric), 0.0) or 0.0
    # shrink toward 0 so a few outliers do not swing projections.
    reliability = n / (n + CONTEXT_PRIOR_STRENGTH)
    pct = clamp((avg_err / max(denominator, 1.0)) * reliability, -max_adj, max_adj)
    return float(1.0 + pct), f"learned {metric} {avg_err:+.2f}, n={n}, rel={reliability:.2f}", n

def bullpen_learning_bf_factor(usage):
    """Learns whether bullpen states caused BF to be over/under-projected."""
    if not usage or not usage.get("available"):
        return 1.0, "Bullpen learning neutral: usage unavailable", None
    key = bullpen_context_key_from_usage(usage)
    model = _load_context_model(BULLPEN_LEARNING_FILE)
    factor, note, n = _smoothed_error_factor(
        model,
        key,
        metric="bf_error",
        min_samples=BULLPEN_LEARN_MIN_SAMPLES,
        max_adj=BULLPEN_LEARN_MAX_BF_ADJ,
        denominator=22.0,
    )
    factor = float(clamp(factor, 1.0 - BULLPEN_LEARN_MAX_BF_ADJ, 1.0 + BULLPEN_LEARN_MAX_BF_ADJ))
    return factor, f"Bullpen learning x{factor:.3f} [{key}] {note}", key

def umpire_learning_k_factor(name):
    """Learns if a specific umpire has caused K projection bias in graded games."""
    if not name or str(name).lower() == "unknown":
        return 1.0, "Umpire learning neutral: unknown umpire", None
    key = umpire_context_key(name)
    model = _load_context_model(UMPIRE_LEARNING_FILE)
    factor, note, n = _smoothed_error_factor(
        model,
        key,
        metric="k_error",
        min_samples=UMPIRE_LEARN_MIN_SAMPLES,
        max_adj=UMPIRE_LEARN_MAX_K_ADJ,
        denominator=5.0,
    )
    factor = float(clamp(factor, 1.0 - UMPIRE_LEARN_MAX_K_ADJ, 1.0 + UMPIRE_LEARN_MAX_K_ADJ))
    return factor, f"Umpire learning x{factor:.3f} [{key}] {note}", key

def _update_context_avg(model, key, fields):
    if key is None:
        return model
    key = str(key)
    rec = model.get(key, {"count": 0})
    old_n = int(rec.get("count") or 0)
    new_n = old_n + 1
    rec["count"] = new_n
    rec["last_updated"] = now_iso()
    for field, value in fields.items():
        val = safe_float(value)
        if val is None:
            continue
        old_avg = safe_float(rec.get(field), 0.0) or 0.0
        rec[field] = round(old_avg + ((val - old_avg) / new_n), 5)
    model[key] = rec
    return model

def get_actual_pitcher_workload(game_pk, pitcher_id):
    """Return actual K/BF/pitches/IP after game final for deeper learning."""
    box = safe_get_json(f"{MLB_BASE}/game/{game_pk}/boxscore")
    if not box:
        return {}
    for side in ["home", "away"]:
        players = box.get("teams", {}).get(side, {}).get("players", {})
        for p in players.values():
            person = p.get("person", {})
            if str(person.get("id")) == str(pitcher_id):
                pitching = p.get("stats", {}).get("pitching", {}) or {}
                return {
                    "actual": safe_float(pitching.get("strikeOuts")),
                    "actual_bf": safe_float(pitching.get("battersFaced")),
                    "actual_pitches": safe_float(pitching.get("numberOfPitches", pitching.get("pitchesThrown", pitching.get("pitchCount")))),
                    "actual_ip": baseball_ip_to_float(pitching.get("inningsPitched")),
                    "actual_er": safe_float(pitching.get("earnedRuns")),
                    "actual_hits": safe_float(pitching.get("hits")),
                    "actual_bb": safe_float(pitching.get("baseOnBalls")),
                }
    return {}

def update_deep_context_learning_after_grade(pick):
    """Accumulates post-game errors for future bullpen and umpire corrections."""
    if not isinstance(pick, dict):
        return
    actual = safe_float(pick.get("actual"))
    projection = safe_float(pick.get("projection"))
    actual_bf = safe_float(pick.get("actual_bf"))
    expected_bf = safe_float(pick.get("expected_bf"))
    if actual is None or projection is None:
        return

    feature_bank = load_json(GRADED_FEATURES_FILE, [])
    feature_bank.append({
        "pick_id": pick.get("pick_id"),
        "graded_at": pick.get("graded_at") or now_iso(),
        "pitcher": pick.get("pitcher"),
        "pitcher_id": pick.get("pitcher_id"),
        "line": pick.get("line"),
        "pick_side": pick.get("pick_side"),
        "projection": projection,
        "actual": actual,
        "k_error": actual - projection,
        "expected_bf": expected_bf,
        "actual_bf": actual_bf,
        "bf_error": None if actual_bf is None or expected_bf is None else actual_bf - expected_bf,
        "umpire": pick.get("umpire"),
        "ump_factor": pick.get("ump_factor"),
        "bullpen_status": pick.get("bullpen_status"),
        "bullpen_bf_factor": pick.get("bullpen_bf_factor"),
        "bullpen_recent_pitches": pick.get("bullpen_recent_pitches"),
        "bullpen_recent_ip": pick.get("bullpen_recent_ip"),
        "bullpen_back_to_back_relievers": pick.get("bullpen_back_to_back_relievers"),
        "weather_factor": pick.get("weather_factor"),
        "manager_hook_status": pick.get("manager_hook_status") or pick.get("manager_hook"),
        "graded_result": pick.get("graded_result"),
    })
    save_json(GRADED_FEATURES_FILE, feature_bank[-FEATURE_BANK_RECENT_LIMIT:])

    # Umpire learning: actual Ks minus projected Ks for that umpire.
    ump_key = umpire_context_key(pick.get("umpire")) if pick.get("umpire") and str(pick.get("umpire")).lower() != "unknown" else None
    if ump_key:
        model = _load_context_model(UMPIRE_LEARNING_FILE)
        model = _update_context_avg(model, ump_key, {"k_error": actual - projection})
        _save_context_model(UMPIRE_LEARNING_FILE, model)

    # Bullpen learning: actual BF minus projected BF for that bullpen workload bucket.
    bp_label = pick.get("bullpen_status")
    if bp_label and actual_bf is not None and expected_bf is not None:
        usage = {
            "available": True,
            "label": bp_label,
            "bullpen_pitches": pick.get("bullpen_recent_pitches"),
            "bullpen_ip": pick.get("bullpen_recent_ip"),
            "back_to_back_relief_appearances": pick.get("bullpen_back_to_back_relievers"),
        }
        bp_key = bullpen_context_key_from_usage(usage)
        model = _load_context_model(BULLPEN_LEARNING_FILE)
        model = _update_context_avg(model, bp_key, {"bf_error": actual_bf - expected_bf, "k_error": actual - projection})
        _save_context_model(BULLPEN_LEARNING_FILE, model)


# =========================
# v11.2 CONTEXT GUARDRAIL LAYER
# =========================
def opponent_k_rank_label_from_rate(opponent_k_rate):
    """Convert real lineup/team K rate into a coarse rank-style label.

    This is not a fake rank table. It is derived from the same real opponent K%
    already used by the app. Lower rank number = more strikeout-friendly matchup.
    """
    ok = safe_float(opponent_k_rate, LEAGUE_AVG_K) or LEAGUE_AVG_K
    if ok >= LEAGUE_AVG_K + 0.040:
        return 1, "EXTREME_HIGH_K"
    if ok >= LEAGUE_AVG_K + 0.030:
        return 5, "HIGH_K"
    if ok >= LEAGUE_AVG_K + 0.015:
        return 10, "ABOVE_AVG_K"
    if ok <= LEAGUE_AVG_K - 0.035:
        return 30, "EXTREME_CONTACT"
    if ok <= LEAGUE_AVG_K - 0.020:
        return 25, "LOW_K"
    return 15, "NEUTRAL_K"

def vegas_total_leash_ks_adjustment(total):
    """Small Ks projection nudge from run environment.

    Lower totals usually help starters work deeper. Higher totals increase early-hook risk.
    Kept very small so it cannot overpower real lineups, Statcast, or leash model.
    """
    t = safe_float(total)
    if t is None:
        return 0.0, "Vegas total unavailable; neutral"
    if t <= 7.5:
        return 0.18, "Low Vegas total; small Ks leash boost"
    if t >= 9.5:
        return -0.18, "High Vegas total; small Ks leash cut"
    return 0.0, "Neutral Vegas total"

def elite_pitcher_guard_ks_adjustment(k9, k_rate, opponent_k_rate):
    """Protects elite K pitchers from being under-projected in strong K matchups.

    This is capped and only adds a small amount. It does not auto-bet overs.
    """
    k9 = safe_float(k9)
    kr = safe_float(k_rate)
    opp_rank, opp_label = opponent_k_rank_label_from_rate(opponent_k_rate)

    if k9 is None or kr is None:
        return 0.0, "Elite pitcher guard unavailable"

    if k9 >= 10.5 and kr >= 0.29:
        if opp_rank <= 10:
            return 0.35, f"Elite pitcher guard vs {opp_label}; capped boost"
        return 0.22, "Elite pitcher guard; capped boost"
    if k9 >= 9.8 and kr >= 0.27:
        return 0.16, "High-K pitcher guard; capped boost"
    return 0.0, "No elite pitcher guard"

def pitch_mix_handedness_guard_ks_adjustment(pitch_type_rows, lineup_rows):
    """Small boost when slider-heavy pitchers face many opposite/lefty bats.

    Uses real pitch type rows and real lineup rows only. If either is unavailable, neutral.
    """
    try:
        if not pitch_type_rows or not lineup_rows:
            return 0.0, "Pitch-mix handedness guard unavailable"

        slider_usage = 0.0
        for r in pitch_type_rows:
            pt = str(r.get("Pitch Type", "")).lower()
            if pt in ["sl", "slider"]:
                slider_usage = max(slider_usage, (safe_float(r.get("Usage %"), 0) or 0) / 100.0)

        # The current MLB lineup payload in this app may not always include batter handedness.
        # If handedness is absent, this stays neutral instead of guessing.
        lefties = 0
        for r in lineup_rows[:9]:
            hand = str(r.get("Bat Side", r.get("Side", r.get("Bats", "")))).upper()
            if hand.startswith("L"):
                lefties += 1

        if slider_usage > 0.32 and lefties >= 5:
            return 0.16, f"Slider-heavy pitch mix vs {lefties} lefties; capped boost"
        return 0.0, "Neutral pitch-mix handedness guard"
    except Exception as e:
        return 0.0, f"Pitch-mix handedness guard error: {e}"

def apply_context_guardrail_projection(
    projection,
    line=None,
    pitcher_profile=None,
    pitcher_k_rate=None,
    lineup_k=None,
    recent_rows=None,
    pitch_type_rows=None,
    lineup_rows=None,
    vegas_total=None,
    roof_closed=False,
    wind_in=False,
    umpire_boost=0.0,
):
    """Final small, capped projection guardrail layer.

    This layer is intentionally conservative:
    - uses only already-real inputs when available
    - never creates props or lines
    - cannot move projection by more than +/- 0.65 Ks total
    - cannot force a bet; EV/edge/no-bet filters still decide
    """
    base = safe_float(projection)
    if base is None:
        return projection, {
            "Context Guardrail Adj": 0.0,
            "Context Guardrail Notes": "Projection unavailable",
            "Opponent K Rank Label": None,
        }

    notes = []
    adj = 0.0

    lineup_k_val = safe_float(lineup_k, LEAGUE_AVG_K) or LEAGUE_AVG_K
    opp_rank, opp_label = opponent_k_rank_label_from_rate(lineup_k_val)
    notes.append(f"Opponent K rank label: {opp_label}")

    # Pull real K/9 if available
    k9 = None
    if isinstance(pitcher_profile, dict):
        k9 = pitcher_profile.get("K/9")
    kr = safe_float(pitcher_k_rate)

    a, n = elite_pitcher_guard_ks_adjustment(k9, kr, lineup_k_val)
    adj += a
    notes.append(n)

    # Real recent pitch count trend as a projection-level nudge, separate from BF factor
    vals = []
    for r in (recent_rows or [])[:3]:
        p = safe_float(r.get("Pitches"))
        if p is not None and p > 0:
            vals.append(p)
    if len(vals) >= 3:
        avg = sum(vals) / len(vals)
        if avg > 102:
            adj += 0.16
            notes.append(f"High L3 pitch-count trend ({avg:.0f}); small projection boost")
        elif avg < 88:
            adj -= 0.16
            notes.append(f"Low L3 pitch-count trend ({avg:.0f}); small projection cut")
        else:
            notes.append(f"Neutral L3 pitch-count trend ({avg:.0f})")
    else:
        notes.append("Pitch-count trend thin; neutral")

    a, n = vegas_total_leash_ks_adjustment(vegas_total)
    adj += a
    notes.append(n)

    # Weather/roof is intentionally tiny because the app already has weather caps elsewhere
    if bool(roof_closed):
        adj += 0.05
        notes.append("Roof closed; tiny environment stability boost")
    elif bool(wind_in):
        adj += 0.08
        notes.append("Wind in; tiny Ks environment boost")

    # Umpire boost must already be produced by a real umpire model. Manual boost defaults to 0.
    ub = clamp(safe_float(umpire_boost, 0.0) or 0.0, -0.15, 0.15)
    if abs(ub) > 0:
        adj += ub
        notes.append(f"Umpire guardrail adj {ub:+.2f}")

    a, n = pitch_mix_handedness_guard_ks_adjustment(pitch_type_rows, lineup_rows)
    adj += a
    notes.append(n)

    adj = float(clamp(adj, -0.65, 0.65))
    final_projection = float(clamp(base + adj, 1.0, 14.0))

    return final_projection, {
        "Context Guardrail Adj": round(adj, 2),
        "Context Guardrail Notes": " | ".join(notes),
        "Opponent K Rank": opp_rank,
        "Opponent K Rank Label": opp_label,
    }


# =========================
# v11.4 RUN-DAMAGE / SHORT-OUTING RISK LAYER
# =========================
def pitcher_run_damage_profile(pitcher_id, recent_rows=None, statcast_profile=None):
    """Advanced run-damage / short-outing risk profile.

    v11.12 upgrade:
    Uses H, R, ER, BB and HR as volume-risk signals. This does not directly
    downgrade a pitcher\'s raw K skill. It only helps estimate whether the
    starter is more likely to lose batters faced because of traffic, damage,
    pitch-count stress, or an early hook.
    """
    profile = {
        "available": False,
        "whip": None,
        "era": None,
        "h9": None,
        "bb9": None,
        "hr9": None,
        "season_hits": None,
        "season_runs": None,
        "season_er": None,
        "season_bb": None,
        "season_hr": None,
        "recent_er_avg": None,
        "recent_runs_avg": None,
        "recent_hits_avg": None,
        "recent_bb_avg": None,
        "recent_hr_avg": None,
        "recent_ip_avg": None,
        "recent_traffic_index": None,
        "risk_score": 0,
        "risk_level": "UNKNOWN",
        "bf_factor": 1.0,
        "volatility_penalty": 0.0,
        "notes": []
    }

    def add_score(points, note):
        profile["risk_score"] += int(points)
        if note:
            profile["notes"].append(str(note))

    try:
        data = safe_get_json(
            f"{MLB_BASE}/people/{pitcher_id}/stats",
            params={"stats": "season", "group": "pitching"},
            timeout=12,
        )
        split = get_first_stat_split(data)
        stat = (split or {}).get("stat", {}) if split else {}

        ip = baseball_ip_to_float(stat.get("inningsPitched"))
        h = safe_float(stat.get("hits"), 0) or 0
        r = safe_float(stat.get("runs"), 0) or 0
        er = safe_float(stat.get("earnedRuns"), 0) or 0
        bb = safe_float(stat.get("baseOnBalls"), 0) or 0
        hr = safe_float(stat.get("homeRuns"), 0) or 0

        profile["whip"] = safe_float(stat.get("whip"))
        profile["era"] = safe_float(stat.get("era"))
        profile["season_hits"] = h
        profile["season_runs"] = r
        profile["season_er"] = er
        profile["season_bb"] = bb
        profile["season_hr"] = hr

        if ip and ip > 0:
            profile["available"] = True
            profile["h9"] = h / ip * 9
            profile["bb9"] = bb / ip * 9
            profile["hr9"] = hr / ip * 9

        if profile["whip"] is not None:
            profile["available"] = True
            if profile["whip"] >= 1.55:
                add_score(4, f"Extreme WHIP {profile['whip']:.2f}")
            elif profile["whip"] >= 1.45:
                add_score(3, f"High WHIP {profile['whip']:.2f}")
            elif profile["whip"] >= HIGH_RUN_DAMAGE_WHIP:
                add_score(2, f"Elevated WHIP {profile['whip']:.2f}")

        if profile["era"] is not None:
            if profile["era"] >= 5.40:
                add_score(3, f"Extreme ERA {profile['era']:.2f}")
            elif profile["era"] >= 5.00:
                add_score(2, f"High ERA {profile['era']:.2f}")
            elif profile["era"] >= 4.25:
                add_score(1, f"Elevated ERA {profile['era']:.2f}")

        if profile["h9"] is not None:
            if profile["h9"] >= 10.5:
                add_score(3, f"Extreme H/9 {profile['h9']:.1f}")
            elif profile["h9"] >= HIGH_SEASON_H9:
                add_score(2, f"High H/9 {profile['h9']:.1f}")

        if profile["bb9"] is not None:
            if profile["bb9"] >= 4.5:
                add_score(3, f"Extreme BB/9 {profile['bb9']:.1f}")
            elif profile["bb9"] >= HIGH_SEASON_BB9:
                add_score(2, f"High BB/9 {profile['bb9']:.1f}")
            elif profile["bb9"] >= 3.2:
                add_score(1, f"Elevated BB/9 {profile['bb9']:.1f}")

        if profile["hr9"] is not None:
            if profile["hr9"] >= 1.70:
                add_score(3, f"Extreme HR/9 {profile['hr9']:.2f}")
            elif profile["hr9"] >= HIGH_SEASON_HR9:
                add_score(2, f"High HR/9 {profile['hr9']:.2f}")
            elif profile["hr9"] >= 1.10:
                add_score(1, f"Elevated HR/9 {profile['hr9']:.2f}")
    except Exception as e:
        profile["notes"].append(f"Season run-damage unavailable: {e}")

    try:
        ers, runs, hits, walks, homers, ips = [], [], [], [], [], []
        for r in (recent_rows or [])[:5]:
            er = safe_float(r.get("ER", r.get("Earned Runs")))
            rr = safe_float(r.get("R", r.get("Runs")))
            h = safe_float(r.get("H", r.get("Hits")))
            bb = safe_float(r.get("BB", r.get("Walks", r.get("BaseOnBalls"))))
            hr = safe_float(r.get("HR", r.get("Home Runs", r.get("homeRuns"))))
            ip = safe_float(r.get("IP_float"))
            if er is not None: ers.append(er)
            if rr is not None: runs.append(rr)
            if h is not None: hits.append(h)
            if bb is not None: walks.append(bb)
            if hr is not None: homers.append(hr)
            if ip is not None: ips.append(ip)

        if ers:
            profile["recent_er_avg"] = float(np.mean(ers))
            profile["available"] = True
            if profile["recent_er_avg"] >= HIGH_RUN_DAMAGE_RECENT_ER:
                add_score(3, f"High recent ER avg {profile['recent_er_avg']:.1f}")
            elif profile["recent_er_avg"] >= 3.0:
                add_score(2, f"Elevated recent ER avg {profile['recent_er_avg']:.1f}")

        if runs:
            profile["recent_runs_avg"] = float(np.mean(runs))
            profile["available"] = True
            if profile["recent_runs_avg"] >= HIGH_RECENT_RUNS_AVG:
                add_score(3, f"High recent R avg {profile['recent_runs_avg']:.1f}")
            elif profile["recent_runs_avg"] >= 3.5:
                add_score(2, f"Elevated recent R avg {profile['recent_runs_avg']:.1f}")

        if hits:
            profile["recent_hits_avg"] = float(np.mean(hits))
            profile["available"] = True
            if profile["recent_hits_avg"] >= 7.0:
                add_score(3, f"Extreme recent H avg {profile['recent_hits_avg']:.1f}")
            elif profile["recent_hits_avg"] >= 6.0:
                add_score(2, f"High recent H avg {profile['recent_hits_avg']:.1f}")
            elif profile["recent_hits_avg"] >= 5.0:
                add_score(1, f"Elevated recent H avg {profile['recent_hits_avg']:.1f}")

        if walks:
            profile["recent_bb_avg"] = float(np.mean(walks))
            profile["available"] = True
            if profile["recent_bb_avg"] >= 3.5:
                add_score(3, f"Extreme recent BB avg {profile['recent_bb_avg']:.1f}")
            elif profile["recent_bb_avg"] >= HIGH_RECENT_BB_AVG:
                add_score(2, f"High recent BB avg {profile['recent_bb_avg']:.1f}")
            elif profile["recent_bb_avg"] >= 2.2:
                add_score(1, f"Elevated recent BB avg {profile['recent_bb_avg']:.1f}")

        if homers:
            profile["recent_hr_avg"] = float(np.mean(homers))
            profile["available"] = True
            if profile["recent_hr_avg"] >= 1.8:
                add_score(3, f"Extreme recent HR avg {profile['recent_hr_avg']:.1f}")
            elif profile["recent_hr_avg"] >= HIGH_RECENT_HR_AVG:
                add_score(2, f"High recent HR avg {profile['recent_hr_avg']:.1f}")

        if ips:
            profile["recent_ip_avg"] = float(np.mean(ips))
            profile["available"] = True
            if profile["recent_ip_avg"] < 4.5:
                add_score(3, f"Very short recent IP {profile['recent_ip_avg']:.1f}")
            elif profile["recent_ip_avg"] < 5.0:
                add_score(2, f"Recent IP short {profile['recent_ip_avg']:.1f}")

        if hits or walks or homers:
            traffic = (profile.get("recent_hits_avg") or 0) + (profile.get("recent_bb_avg") or 0) + (profile.get("recent_hr_avg") or 0) * 1.6
            profile["recent_traffic_index"] = round(float(traffic), 2)
            if traffic >= 9.0:
                add_score(3, f"Extreme recent traffic index {traffic:.1f}")
            elif traffic >= 7.2:
                add_score(2, f"High recent traffic index {traffic:.1f}")
            elif traffic >= 6.2:
                add_score(1, f"Elevated recent traffic index {traffic:.1f}")
    except Exception as e:
        profile["notes"].append(f"Recent run-damage unavailable: {e}")

    score = int(profile.get("risk_score", 0) or 0)
    if not profile["available"]:
        profile["risk_level"] = "UNKNOWN"
        profile["bf_factor"] = 1.0
        profile["volatility_penalty"] = 0.0
        if not profile["notes"]:
            profile["notes"].append("Run-damage inputs unavailable")
    elif score >= 11:
        profile["risk_level"] = "EXTREME"
        profile["bf_factor"] = RUN_DAMAGE_MAX_BF_CUT
        profile["volatility_penalty"] = RUN_DAMAGE_EXTREME_VOL_PENALTY
    elif score >= 8:
        profile["risk_level"] = "HIGH"
        profile["bf_factor"] = RUN_DAMAGE_BF_CUT_HIGH
        profile["volatility_penalty"] = RUN_DAMAGE_HIGH_VOL_PENALTY
    elif score >= 4:
        profile["risk_level"] = "MILD"
        profile["bf_factor"] = RUN_DAMAGE_BF_CUT_MILD
        profile["volatility_penalty"] = RUN_DAMAGE_MILD_VOL_PENALTY
    else:
        profile["risk_level"] = "LOW"
        profile["bf_factor"] = 1.0
        profile["volatility_penalty"] = 0.0

    # Keep notes compact and readable in Streamlit/debug rows.
    profile["notes"] = profile["notes"][:10]
    return profile



def opponent_contact_damage_profile(batter_pitch_rows=None):
    out = {
        "available": False,
        "avg_contact": None,
        "avg_slg_vs_pitch": None,
        "risk_score": 0,
        "risk_level": "UNKNOWN",
        "notes": []
    }
    contacts, slgs = [], []
    for r in (batter_pitch_rows or []):
        c = safe_float(r.get("Per-Batter Contact%"))
        s = safe_float(r.get("Per-Batter SLG vs Pitch"))
        if c is not None:
            contacts.append(c / 100.0 if c > 1 else c)
        if s is not None:
            slgs.append(s)

    if contacts:
        out["available"] = True
        out["avg_contact"] = float(np.mean(contacts))
        if out["avg_contact"] >= 0.79:
            out["risk_score"] += 3
            out["notes"].append(f"High opponent contact vs pitch mix {out['avg_contact']:.1%}")
        elif out["avg_contact"] >= 0.75:
            out["risk_score"] += 2
            out["notes"].append(f"Elevated opponent contact vs pitch mix {out['avg_contact']:.1%}")
    if slgs:
        out["available"] = True
        out["avg_slg_vs_pitch"] = float(np.mean(slgs))
        if out["avg_slg_vs_pitch"] >= 0.560:
            out["risk_score"] += 3
            out["notes"].append(f"High opponent SLG vs pitch mix {out['avg_slg_vs_pitch']:.3f}")
        elif out["avg_slg_vs_pitch"] >= HIGH_OPP_SLG_VS_PITCH:
            out["risk_score"] += 2
            out["notes"].append(f"Elevated opponent SLG vs pitch mix {out['avg_slg_vs_pitch']:.3f}")

    score = int(out.get("risk_score", 0) or 0)
    if not out["available"]:
        out["risk_level"] = "UNKNOWN"
        out["notes"].append("Opponent contact/SLG profile unavailable")
    elif score >= 5:
        out["risk_level"] = "HIGH"
    elif score >= 3:
        out["risk_level"] = "MILD"
    else:
        out["risk_level"] = "LOW"
    return out

def combined_game_script_risk(pitcher_damage, opponent_damage, line=None, side=None):
    p_score = safe_int((pitcher_damage or {}).get("risk_score"), 0) or 0
    o_score = safe_int((opponent_damage or {}).get("risk_score"), 0) or 0
    total = p_score + o_score
    ln = safe_float(line)
    side_text = str(side or "").upper()

    notes = []
    notes.extend((pitcher_damage or {}).get("notes", [])[:3])
    notes.extend((opponent_damage or {}).get("notes", [])[:3])

    # v11.12: let the advanced H/R/ER/BB/HR profile supply a capped BF factor,
    # then combine with opponent contact damage. This remains a volume-risk layer only.
    pitcher_bf_factor = safe_float((pitcher_damage or {}).get("bf_factor"), 1.0) or 1.0
    if total >= 9 or (pitcher_damage or {}).get("risk_level") == "EXTREME":
        label, factor = "EXTREME", min(RUN_DAMAGE_BF_CUT_EXTREME, pitcher_bf_factor)
    elif total >= 6 or (pitcher_damage or {}).get("risk_level") == "HIGH" or (opponent_damage or {}).get("risk_level") == "HIGH":
        label, factor = "HIGH", min(RUN_DAMAGE_BF_CUT_HIGH, pitcher_bf_factor)
    elif total >= 3 or (pitcher_damage or {}).get("risk_level") == "MILD" or (opponent_damage or {}).get("risk_level") == "MILD":
        label, factor = "MILD", min(RUN_DAMAGE_BF_CUT_MILD, pitcher_bf_factor)
    else:
        label, factor = "LOW", min(1.0, pitcher_bf_factor)

    vol_penalty = safe_float((pitcher_damage or {}).get("volatility_penalty"), 0.0) or 0.0
    if vol_penalty > 0:
        notes.append(f"Run-damage volatility penalty {vol_penalty:.0%}")

    if "OVER" in side_text and ln is not None and ln >= 5.5 and label in ["MILD", "HIGH", "EXTREME"]:
        factor = min(factor, 0.94 if label == "MILD" else 0.88 if label == "HIGH" else 0.82)
        notes.append("Over line needs 6+ Ks; early-hook risk amplified")

    return {
        "label": label,
        "factor": float(clamp(factor, RUN_DAMAGE_MAX_BF_CUT, 1.0)),
        "score": int(total),
        "volatility_penalty": round(float(vol_penalty), 3),
        "notes": " | ".join(notes[:10]) if notes else "No major run-damage risk detected"
    }

def apply_game_script_bf_cut(expected_bf, game_script_risk):
    bf = safe_float(expected_bf)
    if bf is None:
        return expected_bf
    factor = safe_float((game_script_risk or {}).get("factor"), 1.0) or 1.0
    return float(clamp(bf * factor, 12, 31))

def stronger_over_gate(side, prob, edge, source_label, game_script_risk, market_source_count=None):
    if "OVER" not in str(side or "").upper():
        return None
    notes = []
    p = safe_float(prob)
    e = safe_float(edge)
    label = (game_script_risk or {}).get("label", "UNKNOWN")

    if p is not None and p < OVER_MIN_PROB_STRONG:
        notes.append(f"stronger over gate: probability below {int(OVER_MIN_PROB_STRONG*100)}%")
    if e is not None and e < OVER_MIN_EDGE_STRONG:
        notes.append(f"stronger over gate: edge below {OVER_MIN_EDGE_STRONG:.2f} K")
    if source_label != "TRUE LINEUP":
        notes.append("stronger over gate: lineup not true/confirmed")
    if label in ["HIGH", "EXTREME"]:
        notes.append(f"stronger over gate: game-script risk {label}")
    if market_source_count is not None and safe_int(market_source_count, 0) <= 1:
        notes.append("market confirmation rule: only one market source")
    return "; ".join(notes) if notes else None


# =========================
# v11.6 REPEAT MATCHUP / FAMILIARITY LAYER
# =========================
@st.cache_data(ttl=900, show_spinner=False)
def pitcher_recent_opponent_familiarity(pitcher_id, opponent_team_name=None, opponent_abbrev=None, lookback_days=21):
    """Small repeat-opponent familiarity factor.

    If a pitcher faced this same opponent recently, hitters may have a small timing/recognition edge.
    This is intentionally capped and only cuts Ks slightly. Missing data stays neutral.
    """
    result = {
        "available": False,
        "factor": 1.0,
        "recent_matchups": 0,
        "last_days_ago": None,
        "label": "NEUTRAL",
        "note": "No recent same-opponent matchup found"
    }
    if not pitcher_id:
        return result

    data = safe_get_json(
        f"{MLB_BASE}/people/{pitcher_id}/stats",
        params={"stats": "gameLog", "group": "pitching"},
        timeout=12,
    )
    if not isinstance(data, dict):
        result["note"] = "Pitcher game log unavailable for repeat-matchup check"
        return result

    try:
        splits = data["stats"][0]["splits"]
    except Exception:
        result["note"] = "Pitcher game log missing splits for repeat-matchup check"
        return result

    opp_norms = set()
    for v in [opponent_team_name, opponent_abbrev]:
        if v:
            opp_norms.add(normalize_name(v))
    if not opp_norms:
        result["note"] = "Opponent name unavailable for repeat-matchup check"
        return result

    today = california_now().date()
    matches = []

    for g in splits:
        try:
            gdate = datetime.strptime(g.get("date", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        days_ago = (today - gdate).days
        if days_ago < 0 or days_ago > int(lookback_days):
            continue

        opp_obj = g.get("opponent", {}) or {}
        opp_values = [
            opp_obj.get("name"),
            opp_obj.get("abbreviation"),
            opp_obj.get("teamName"),
            opp_obj.get("clubName"),
        ]
        opp_game_norms = {normalize_name(x) for x in opp_values if x}
        if opp_norms & opp_game_norms:
            matches.append(days_ago)

    if not matches:
        return result

    matches = sorted(matches)
    n = len(matches)
    last_days = matches[0]
    factor = 1.0
    label = "LOW"

    if n >= 2 and last_days <= 21:
        factor = REPEAT_MATCHUP_MULTI_RECENT_FACTOR
        label = "HIGH"
    elif last_days <= 7:
        factor = REPEAT_MATCHUP_SAME_7D_FACTOR
        label = "HIGH"
    elif last_days <= 14:
        factor = REPEAT_MATCHUP_SAME_14D_FACTOR
        label = "MILD"
    elif last_days <= 21:
        factor = REPEAT_MATCHUP_SAME_21D_FACTOR
        label = "LOW"

    factor = float(clamp(factor, REPEAT_MATCHUP_FACTOR_MIN, REPEAT_MATCHUP_FACTOR_MAX))
    return {
        "available": True,
        "factor": factor,
        "recent_matchups": int(n),
        "last_days_ago": int(last_days),
        "label": label,
        "note": f"Repeat opponent familiarity {label}: faced opponent {n} time(s) in last {lookback_days} days; most recent {last_days} day(s) ago; K factor x{factor:.3f}"
    }

def apply_repeat_matchup_factor(k_rate, repeat_profile):
    kr = safe_float(k_rate)
    if kr is None:
        return k_rate, "Repeat matchup factor skipped; missing K rate"
    factor = safe_float((repeat_profile or {}).get("factor"), 1.0) or 1.0
    return float(clamp(kr * factor, 0.08, 0.50)), (repeat_profile or {}).get("note", "Repeat matchup neutral")

# =========================
# STATCAST
# =========================
@st.cache_data(ttl=21600, show_spinner=False)
def get_statcast_pitch_profile(pitcher_id, days=365):
    empty = {"available": False, "message": "No pitcher id", "rows": 0, "csw": None, "whiff": None, "pitch_mix": [], "pitch_type_profile": [], "putaway": None}
    if not pitcher_id:
        return empty
    end = datetime.now()
    start = end - timedelta(days=int(days))
    url = "https://baseballsavant.mlb.com/statcast_search/csv"
    params = {
        "all": "true",
        "player_type": "pitcher",
        "pitchers_lookup[]": str(pitcher_id),
        "game_date_gt": start.strftime("%Y-%m-%d"),
        "game_date_lt": end.strftime("%Y-%m-%d"),
        "type": "details",
    }
    try:
        r = requests.get(url, params=params, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.text.strip():
            empty["message"] = f"Statcast HTTP {r.status_code}"
            return empty
        df = pd.read_csv(io.StringIO(r.text), low_memory=False)
        if df.empty or "description" not in df.columns:
            empty["message"] = "Statcast returned no pitch rows"
            return empty
        desc = df["description"].astype(str).str.lower()
        pitch_count = int(len(df))
        called_mask = desc.eq("called_strike")
        whiff_mask = desc.isin(["swinging_strike", "swinging_strike_blocked", "foul_tip"])
        swing_mask = desc.isin(["swinging_strike", "swinging_strike_blocked", "foul_tip", "foul", "foul_bunt", "missed_bunt", "hit_into_play", "hit_into_play_no_out", "hit_into_play_score"])
        called = int(called_mask.sum())
        whiffs_n = int(whiff_mask.sum())
        swings = int(swing_mask.sum())
        csw = (called + whiffs_n) / pitch_count if pitch_count else None
        whiff = whiffs_n / swings if swings else None
        pitch_mix = []
        pitch_type_profile = []
        if "pitch_type" in df.columns:
            df2 = df.copy()
            df2["pitch_type"] = df2["pitch_type"].fillna("UNK").astype(str)
            df2["_called"] = called_mask.astype(int)
            df2["_whiff"] = whiff_mask.astype(int)
            df2["_swing"] = swing_mask.astype(int)
            total = max(len(df2), 1)
            grouped = df2.groupby("pitch_type").agg(Pitches=("pitch_type", "size"), Called=("_called", "sum"), Whiffs=("_whiff", "sum"), Swings=("_swing", "sum")).reset_index()
            grouped["Usage"] = grouped["Pitches"] / total
            grouped["CSW"] = (grouped["Called"] + grouped["Whiffs"]) / grouped["Pitches"].replace(0, np.nan)
            grouped["WhiffRate"] = grouped["Whiffs"] / grouped["Swings"].replace(0, np.nan)
            grouped = grouped.sort_values("Usage", ascending=False).head(8)
            for _, row in grouped.iterrows():
                pt = str(row["pitch_type"])
                usage = safe_float(row["Usage"], 0) or 0
                wr = safe_float(row["WhiffRate"])
                csw_rate = safe_float(row["CSW"])
                pitch_mix.append({"Pitch Type": pt, "Usage %": round(usage * 100, 1)})
                pitch_type_profile.append({
                    "Pitch Type": pt,
                    "Usage %": round(usage * 100, 1),
                    "Pitcher Whiff%": None if wr is None or pd.isna(wr) else round(wr * 100, 1),
                    "Pitcher CSW%": None if csw_rate is None or pd.isna(csw_rate) else round(csw_rate * 100, 1),
                    "Pitches": int(row["Pitches"]),
                    "Swings": int(row["Swings"]),
                })
        return {"available": True, "message": "Real Statcast pitch-level data loaded", "rows": pitch_count, "csw": None if csw is None else float(csw), "whiff": None if whiff is None else float(whiff), "pitch_mix": pitch_mix, "pitch_type_profile": pitch_type_profile}
    except Exception as e:
        empty["message"] = f"Statcast unavailable: {e}"
        return empty

def apply_statcast_csw_adjustment(pitcher_k, statcast_profile, enabled=True):
    if not enabled or not statcast_profile or not statcast_profile.get("available"):
        return pitcher_k, "No Statcast adjustment"
    csw = statcast_profile.get("csw")
    if csw is None:
        return pitcher_k, "No Statcast CSW available"
    factor = clamp(1 + ((float(csw) - 0.275) * 0.45), 0.93, 1.07)
    return clamp(pitcher_k * factor, 0.08, 0.50), f"Real Statcast CSW adjustment x{factor:.3f}"

def apply_pitch_type_matchup_adjustment(pitcher_k, pitcher_statcast, enabled=True):
    if not enabled or not pitcher_statcast or not pitcher_statcast.get("available"):
        return pitcher_k, "No pitch-type matchup adjustment", False, [], 1.0
    # Conservative simplified pitch-type factor from pitcher whiff vs league ref.
    rows = []
    weighted = 0
    total_w = 0
    for r in pitcher_statcast.get("pitch_type_profile", []):
        pt = r.get("Pitch Type")
        usage = (safe_float(r.get("Usage %"), 0) or 0) / 100
        wr = safe_float(r.get("Pitcher Whiff%"))
        ref = LEAGUE_AVG_WHIFF_BY_PITCH_TYPE.get(pt, 0.25)
        if usage >= 0.03 and wr is not None:
            idx = clamp((wr / 100) / max(ref, 0.01), 0.85, 1.18)
            weighted += usage * idx
            total_w += usage
            rows.append({"Pitch Type": pt, "Usage %": round(usage * 100, 1), "Pitcher Whiff%": wr, "League Ref Whiff%": round(ref * 100, 1), "Index": round(idx, 3)})
    if total_w <= 0:
        return pitcher_k, "Pitch-type rows unavailable", False, rows, 1.0
    combined = weighted / total_w
    factor = clamp(1 + ((combined - 1) * 0.08), 0.97, 1.03)
    return clamp(pitcher_k * factor, 0.08, 0.50), f"Pitch-type whiff mix adjustment x{factor:.3f}", True, rows, factor



@st.cache_data(ttl=21600, show_spinner=False)
def get_batter_statcast_pitch_type_profile(batter_id, days=365, pitcher_hand=None):
    """Real per-batter Statcast profile by pitch type.

    Adds:
    - per-batter whiff% by pitch type
    - per-batter contact% by pitch type
    - per-batter SLG vs pitch type from real batted-ball outcomes
    - overall batter whiff/contact profile

    Missing or thin data stays neutral. Nothing is guessed.
    """
    empty = {
        "available": False,
        "message": "No batter id",
        "rows": 0,
        "overall_whiff": None,
        "overall_contact": None,
        "pitch_type_profile": []
    }
    if not batter_id:
        return empty

    end = datetime.now()
    start = end - timedelta(days=int(days))
    url = "https://baseballsavant.mlb.com/statcast_search/csv"
    params = {
        "all": "true",
        "player_type": "batter",
        "batters_lookup[]": str(batter_id),
        "game_date_gt": start.strftime("%Y-%m-%d"),
        "game_date_lt": end.strftime("%Y-%m-%d"),
        "type": "details",
    }

    def _event_total_bases(ev):
        ev = str(ev or "").lower()
        if ev == "single":
            return 1
        if ev == "double":
            return 2
        if ev == "triple":
            return 3
        if ev == "home_run":
            return 4
        return 0

    def _is_ab_event(ev):
        ev = str(ev or "").lower()
        if not ev or ev in ["nan", "none"]:
            return False
        non_ab = {
            "walk", "intent_walk", "hit_by_pitch", "sac_bunt", "sac_fly",
            "catcher_interf", "sac_fly_double_play", "sac_bunt_double_play"
        }
        return ev not in non_ab

    try:
        r = requests.get(url, params=params, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.text.strip():
            empty["message"] = f"Batter Statcast HTTP {r.status_code}"
            return empty

        df = pd.read_csv(io.StringIO(r.text), low_memory=False)
        if df.empty or "description" not in df.columns or "pitch_type" not in df.columns:
            empty["message"] = "Batter Statcast returned no pitch-type rows"
            return empty

        # Use pitcher-hand split only if enough real rows exist; otherwise keep full batter sample.
        if pitcher_hand in ["R", "L"] and "p_throws" in df.columns:
            hand_df = df[df["p_throws"].astype(str).str.upper() == pitcher_hand].copy()
            if len(hand_df) >= 25:
                df = hand_df

        desc = df["description"].astype(str).str.lower()
        whiff_mask = desc.isin(["swinging_strike", "swinging_strike_blocked", "foul_tip"])
        swing_mask = desc.isin([
            "swinging_strike", "swinging_strike_blocked", "foul_tip", "foul", "foul_bunt",
            "missed_bunt", "hit_into_play", "hit_into_play_no_out", "hit_into_play_score"
        ])
        contact_mask = swing_mask & (~whiff_mask)

        df2 = df.copy()
        df2["pitch_type"] = df2["pitch_type"].fillna("UNK").astype(str)
        df2["_whiff"] = whiff_mask.astype(int)
        df2["_swing"] = swing_mask.astype(int)
        df2["_contact"] = contact_mask.astype(int)

        if "events" in df2.columns:
            df2["_ab_event"] = df2["events"].apply(_is_ab_event).astype(int)
            df2["_total_bases"] = df2["events"].apply(_event_total_bases).astype(float)
        else:
            df2["_ab_event"] = 0
            df2["_total_bases"] = 0.0

        overall_swings = int(df2["_swing"].sum())
        overall_whiffs = int(df2["_whiff"].sum())
        overall_contacts = int(df2["_contact"].sum())
        overall_whiff = overall_whiffs / overall_swings if overall_swings > 0 else None
        overall_contact = overall_contacts / overall_swings if overall_swings > 0 else None

        grouped = df2.groupby("pitch_type").agg(
            Pitches=("pitch_type", "size"),
            Whiffs=("_whiff", "sum"),
            Swings=("_swing", "sum"),
            Contacts=("_contact", "sum"),
            ABEvents=("_ab_event", "sum"),
            TotalBases=("_total_bases", "sum"),
        ).reset_index()

        grouped = grouped[grouped["Swings"] >= 5]
        if grouped.empty:
            empty["message"] = "Batter Statcast has too few swings by pitch type"
            return empty

        grouped["WhiffRate"] = grouped["Whiffs"] / grouped["Swings"].replace(0, np.nan)
        grouped["ContactRate"] = grouped["Contacts"] / grouped["Swings"].replace(0, np.nan)
        grouped["SLG"] = grouped["TotalBases"] / grouped["ABEvents"].replace(0, np.nan)

        profile = []
        for _, row in grouped.iterrows():
            wr = safe_float(row["WhiffRate"])
            cr = safe_float(row["ContactRate"])
            slg = safe_float(row["SLG"])
            if wr is None or pd.isna(wr):
                continue
            profile.append({
                "Pitch Type": str(row["pitch_type"]),
                "Batter Whiff%": round(wr * 100, 1),
                "Batter Contact%": None if cr is None or pd.isna(cr) else round(cr * 100, 1),
                "Batter SLG vs Pitch": None if slg is None or pd.isna(slg) else round(slg, 3),
                "Swings": int(row["Swings"]),
                "Contacts": int(row["Contacts"]),
                "Pitches Seen": int(row["Pitches"]),
                "AB Events": int(row["ABEvents"]),
                "Total Bases": int(row["TotalBases"]),
            })

        if not profile:
            empty["message"] = "No batter pitch-type rows passed sample filter"
            return empty

        return {
            "available": True,
            "message": "Real batter Statcast pitch-type whiff/contact/SLG loaded",
            "rows": int(len(df)),
            "overall_whiff": None if overall_whiff is None else float(overall_whiff),
            "overall_contact": None if overall_contact is None else float(overall_contact),
            "pitch_type_profile": profile
        }
    except Exception as e:
        empty["message"] = f"Batter Statcast unavailable: {e}"
        return empty


def build_pitch_type_matchup_profile(pitcher_statcast, lineup_rows, enabled=True, min_batters=5, pitcher_hand=None):
    """Compare real pitcher pitch mix to real batter pitch-type profiles.

    v11.3 adds per-batter:
    - K% already supplied from lineup_rows
    - SLG vs pitch type
    - contact% / whiff% by pitch type

    Missing pitch types are ignored, never guessed.
    """
    result = {
        "available": False,
        "factor": 1.0,
        "message": "Pitch-type matchup disabled or unavailable",
        "rows": [],
        "batter_rows": [],
        "batters_loaded": 0
    }
    if not enabled:
        result["message"] = "Pitch-type matchup disabled"
        return result
    if not pitcher_statcast or not pitcher_statcast.get("available"):
        result["message"] = "Pitcher Statcast pitch mix unavailable"
        return result
    pitch_profile = pitcher_statcast.get("pitch_type_profile") or []
    if not pitch_profile:
        result["message"] = "Pitcher pitch-type profile unavailable"
        return result
    if not lineup_rows:
        result["message"] = "No posted lineup for batter pitch-type matching"
        return result

    pitcher_usage = {r.get("Pitch Type"): (safe_float(r.get("Usage %"), 0) or 0) / 100.0 for r in pitch_profile}
    pitcher_whiff = {
        r.get("Pitch Type"): (safe_float(r.get("Pitcher Whiff%")) / 100.0 if safe_float(r.get("Pitcher Whiff%")) is not None else None)
        for r in pitch_profile
    }
    pitch_types = [pt for pt, use in pitcher_usage.items() if pt and use >= 0.03]

    batter_profiles = []
    batter_detail_rows = []

    for r in lineup_rows[:9]:
        bid = r.get("Player ID")
        batter_name = r.get("Batter")
        prof = get_batter_statcast_pitch_type_profile(bid, days=365, pitcher_hand=pitcher_hand)
        if prof.get("available"):
            by_pt = {x.get("Pitch Type"): x for x in prof.get("pitch_type_profile", [])}
            batter_profiles.append({
                "Batter": batter_name,
                "Order": r.get("Order"),
                "Used K%": r.get("Used K%"),
                "Raw_K_Rate": r.get("Raw_K_Rate"),
                "Overall Contact%": None if prof.get("overall_contact") is None else round(prof.get("overall_contact") * 100, 1),
                "Overall Whiff%": None if prof.get("overall_whiff") is None else round(prof.get("overall_whiff") * 100, 1),
                "by_pt": by_pt
            })

            for pt, prow in by_pt.items():
                if pt not in pitch_types:
                    continue
                batter_detail_rows.append({
                    "Order": r.get("Order"),
                    "Batter": batter_name,
                    "Player ID": bid,
                    "Pitch Type": pt,
                    "Pitcher Usage %": round((pitcher_usage.get(pt, 0) or 0) * 100, 1),
                    "Per-Batter K%": r.get("Used K%"),
                    "Per-Batter Contact%": prow.get("Batter Contact%"),
                    "Per-Batter Whiff%": prow.get("Batter Whiff%"),
                    "Per-Batter SLG vs Pitch": prow.get("Batter SLG vs Pitch"),
                    "Swings": prow.get("Swings"),
                    "Pitches Seen": prow.get("Pitches Seen"),
                    "AB Events": prow.get("AB Events"),
                })

    result["batters_loaded"] = len(batter_profiles)
    result["batter_rows"] = batter_detail_rows

    if len(batter_profiles) < min_batters:
        result["message"] = f"Only {len(batter_profiles)}/9 batter pitch-type profiles loaded; no adjustment applied"
        return result

    rows = []
    weighted_index = 0.0
    used_weight = 0.0

    for pt in pitch_types:
        use = pitcher_usage.get(pt, 0) or 0
        batter_whiff_rates = []
        batter_contact_rates = []
        batter_slg_rates = []
        batter_swings = 0
        slg_ab_events = 0

        for bp in batter_profiles:
            row = bp["by_pt"].get(pt)
            if not row:
                continue

            wr = safe_float(row.get("Batter Whiff%"))
            cr = safe_float(row.get("Batter Contact%"))
            slg = safe_float(row.get("Batter SLG vs Pitch"))
            swings = safe_int(row.get("Swings"), 0) or 0
            ab_events = safe_int(row.get("AB Events"), 0) or 0

            if wr is not None and swings >= 5:
                batter_whiff_rates.append(wr / 100.0)
                batter_swings += swings
            if cr is not None and swings >= 5:
                batter_contact_rates.append(cr / 100.0)
            if slg is not None and ab_events >= 2:
                batter_slg_rates.append(slg)
                slg_ab_events += ab_events

        if len(batter_whiff_rates) < 3:
            continue

        avg_batter_whiff = float(np.mean(batter_whiff_rates))
        avg_batter_contact = float(np.mean(batter_contact_rates)) if batter_contact_rates else None
        avg_batter_slg = float(np.mean(batter_slg_rates)) if batter_slg_rates else None

        league_ref = LEAGUE_AVG_WHIFF_BY_PITCH_TYPE.get(pt, 0.25)
        pitcher_wr = pitcher_whiff.get(pt)

        pitcher_bonus = 1.0
        if pitcher_wr is not None:
            pitcher_bonus = clamp(pitcher_wr / max(league_ref, 0.01), 0.85, 1.18)

        batter_whiff_index = avg_batter_whiff / max(league_ref, 0.01)

        # Contact and SLG protect against fake K boosts when hitters see a pitch well.
        contact_guard = 1.0
        if avg_batter_contact is not None:
            if avg_batter_contact >= 0.78:
                contact_guard = 0.96
            elif avg_batter_contact <= 0.64:
                contact_guard = 1.04

        slg_guard = 1.0
        if avg_batter_slg is not None:
            if avg_batter_slg >= 0.520:
                slg_guard = 0.97
            elif avg_batter_slg <= 0.300:
                slg_guard = 1.03

        combined_index = (batter_whiff_index * 0.60) + (pitcher_bonus * 0.25) + (contact_guard * 0.10) + (slg_guard * 0.05)
        combined_index = clamp(combined_index, 0.82, 1.22)

        weighted_index += use * combined_index
        used_weight += use

        rows.append({
            "Pitch Type": pt,
            "Pitcher Usage %": round(use * 100, 1),
            "Avg Batter Whiff%": round(avg_batter_whiff * 100, 1),
            "Avg Batter Contact%": None if avg_batter_contact is None else round(avg_batter_contact * 100, 1),
            "Avg Batter SLG vs Pitch": None if avg_batter_slg is None else round(avg_batter_slg, 3),
            "League Ref Whiff%": round(league_ref * 100, 1),
            "Pitcher Whiff%": None if pitcher_wr is None else round(pitcher_wr * 100, 1),
            "Contact Guard": round(contact_guard, 3),
            "SLG Guard": round(slg_guard, 3),
            "Index": round(combined_index, 3),
            "Batter Profiles Used": len(batter_whiff_rates),
            "Batter Swings": batter_swings,
            "SLG AB Events": slg_ab_events,
        })

    if used_weight <= 0 or not rows:
        result["message"] = "No overlapping pitcher/batter pitch-type rows passed sample filter"
        return result

    avg_index = weighted_index / used_weight
    factor = clamp(1 + ((avg_index - 1) * 0.10), 0.965, 1.035)
    result.update({
        "available": True,
        "factor": factor,
        "message": f"Real per-batter K/contact/whiff/SLG pitch-type matchup x{factor:.3f} ({len(batter_profiles)}/9 batters loaded)",
        "rows": rows,
        "batter_rows": batter_detail_rows,
    })
    return result


def apply_advanced_pitch_type_matchup_adjustment(pitcher_k, matchup_profile, enabled=True):
    if not enabled or not matchup_profile or not matchup_profile.get("available"):
        msg = matchup_profile.get("message", "No batter-vs-pitch-type matchup adjustment") if matchup_profile else "No batter-vs-pitch-type matchup adjustment"
        return pitcher_k, msg
    factor = safe_float(matchup_profile.get("factor"), 1.0) or 1.0
    return clamp(pitcher_k * factor, 0.08, 0.50), matchup_profile.get("message", f"Pitch-type matchup x{factor:.3f}")

# =========================
# SIMULATION
# =========================
def park_k_factor(venue_name):
    """Small, conservative park adjustment. Missing venue stays neutral."""
    v = normalize_name(venue_name)
    park_map = {
        "tropicana field": 1.025,
        "loan depot park": 1.015,
        "oracle park": 1.010,
        "petco park": 1.010,
        "t mobile park": 1.010,
        "coors field": 0.965,
        "great american ball park": 0.985,
        "fenway park": 0.990,
        "citizens bank park": 0.990,
        "globe life field": 1.005,
    }
    for name, factor in park_map.items():
        if name in v:
            return factor
    return 1.00

# MLB venue coordinates for live weather. Indoor/retractable parks default neutral.
VENUE_WEATHER_META = {
    "angel stadium": (33.8003, -117.8827, False),
    "busch stadium": (38.6226, -90.1928, False),
    "camden yards": (39.2839, -76.6217, False),
    "citizens bank park": (39.9061, -75.1665, False),
    "coors field": (39.7559, -104.9942, False),
    "dodger stadium": (34.0739, -118.2400, False),
    "fenway park": (42.3467, -71.0972, False),
    "great american ball park": (39.0979, -84.5066, False),
    "guaranteed rate field": (41.8300, -87.6339, False),
    "kauffman stadium": (39.0517, -94.4803, False),
    "loan depot park": (25.7781, -80.2197, True),
    "minute maid park": (29.7572, -95.3555, True),
    "nationals park": (38.8730, -77.0074, False),
    "oracle park": (37.7786, -122.3893, False),
    "petco park": (32.7073, -117.1573, False),
    "pnc park": (40.4469, -80.0057, False),
    "progressive field": (41.4962, -81.6852, False),
    "rogers centre": (43.6414, -79.3894, True),
    "sutter health park": (38.5803, -121.5139, False),
    "target field": (44.9817, -93.2776, False),
    "t mobile park": (47.5914, -122.3325, True),
    "tropicana field": (27.7682, -82.6534, True),
    "truist park": (33.8908, -84.4678, False),
    "wrigley field": (41.9484, -87.6553, False),
    "yankee stadium": (40.8296, -73.9262, False),
    "american family field": (43.0280, -87.9712, True),
    "chase field": (33.4455, -112.0667, True),
    "citi field": (40.7571, -73.8458, False),
    "comerica park": (42.3390, -83.0485, False),
    "globe life field": (32.7473, -97.0842, True),
}

def venue_weather_meta(venue_name):
    v = normalize_name(venue_name)
    for name, meta in VENUE_WEATHER_META.items():
        if name in v:
            return meta
    return None

def parse_game_hour_pt(game_time):
    try:
        s = str(game_time or "").replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if pytz and dt.tzinfo is not None:
            dt = dt.astimezone(pytz.timezone("America/Los_Angeles"))
        return dt.strftime("%Y-%m-%dT%H:00")
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_open_meteo_hourly(lat, lon, date_str):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "America/Los_Angeles",
            "start_date": date_str,
            "end_date": date_str,
        }
        return safe_get_json("https://api.open-meteo.com/v1/forecast", params=params, timeout=12) or {}
    except Exception as e:
        log_source_request("OpenMeteo", "ERROR", str(e))
        return {}

def weather_k_factor(venue_name, game_time, enabled=True):
    """Conservative live weather K factor.

    Weather only nudges K probability slightly and defaults neutral when unavailable.
    Indoor/retractable parks are neutral because roof status is often unknown.
    """
    if not enabled:
        return 1.0, "Weather adjustment off", {}
    meta = venue_weather_meta(venue_name)
    if not meta:
        return 1.0, "Weather unavailable for venue; neutral", {}
    lat, lon, indoor = meta
    if indoor:
        return 1.0, "Indoor/retractable venue; weather neutral", {"indoor": True}
    try:
        date_str = str(game_time or "")[:10]
        hour_key = parse_game_hour_pt(game_time)
        data = get_open_meteo_hourly(lat, lon, date_str)
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            return 1.0, "Weather feed empty; neutral", {}
        idx = 0
        if hour_key in times:
            idx = times.index(hour_key)
        else:
            # nearest available hour by string distance fallback
            idx = min(range(len(times)), key=lambda i: abs(i - len(times)//2))
        temp = safe_float((hourly.get("temperature_2m") or [None])[idx])
        wind = safe_float((hourly.get("wind_speed_10m") or [None])[idx])
        humidity = safe_float((hourly.get("relative_humidity_2m") or [None])[idx])
        precip = safe_float((hourly.get("precipitation_probability") or [None])[idx])

        factor = 1.0
        # Cold air can help pitchers slightly; extreme heat can reduce stamina/command slightly.
        if temp is not None:
            if temp <= 55:
                factor += 0.006
            elif temp >= 88:
                factor -= 0.008
        # Strong wind can increase run environment/long innings; tiny K haircut.
        if wind is not None and wind >= 15:
            factor -= 0.006
        # Very high humidity/precip risk can affect grip/command; tiny K haircut.
        if humidity is not None and humidity >= 80:
            factor -= 0.004
        if precip is not None and precip >= 35:
            factor -= 0.006

        # v11.9 Density Altitude style adjustment. This is intentionally small:
        # heat + humidity can reduce pitch movement/whiffs, while cool/dry air can
        # slightly help. We multiply it into the existing weather factor and cap it.
        da_factor = 1.0
        da_note = "DA neutral"
        if temp is not None and humidity is not None:
            temp_effect = (temp - 70.0) * 0.0012
            humidity_effect = (humidity - 50.0) * 0.0005
            da_impact = temp_effect + humidity_effect
            da_factor = float(clamp(1.0 - (da_impact * 0.15), DA_K_FACTOR_MIN, DA_K_FACTOR_MAX))
            da_note = f"DA x{da_factor:.3f}"

        factor = float(clamp(factor * da_factor, min(WEATHER_FACTOR_MIN, DA_K_FACTOR_MIN), max(WEATHER_FACTOR_MAX, DA_K_FACTOR_MAX)))
        details = {"temp_f": temp, "wind_mph": wind, "humidity": humidity, "precip_prob": precip, "indoor": False, "density_altitude_factor": round(da_factor, 3)}
        note = f"Weather x{factor:.3f} ({da_note}): {temp if temp is not None else 'NA'}F, wind {wind if wind is not None else 'NA'} mph, humidity {humidity if humidity is not None else 'NA'}%, precip {precip if precip is not None else 'NA'}%"
        return factor, note, details
    except Exception as e:
        return 1.0, f"Weather error; neutral: {e}", {}

# Conservative umpire K tendency table. Missing/unknown umps stay neutral.
UMPIRE_K_TENDENCY = {
    "Lance Barrett": 1.020,
    "Mark Wegner": 1.018,
    "Pat Hoberg": 1.015,
    "Adam Hamari": 1.012,
    "Ryan Blakney": 1.010,
    "Bill Miller": 0.982,
    "Chris Segal": 0.985,
    "Angel Hernandez": 0.990,
    "Laz Diaz": 0.990,
    "CB Bucknor": 0.992,
}

def umpire_factor(game_pk, enabled=True):
    if not enabled:
        return 1.00, "Umpire adjustment off", "Umpire adjustment off"
    data = safe_get_json(f"{MLB_LIVE}/game/{game_pk}/feed/live")
    try:
        officials = data["liveData"]["boxscore"].get("officials", [])
        name = officials[0]["official"]["fullName"] if officials else "Unknown"
        raw = safe_float(UMPIRE_K_TENDENCY.get(name), 1.0) or 1.0
        factor = float(clamp(raw, UMPIRE_FACTOR_MIN, UMPIRE_FACTOR_MAX))
        if name == "Unknown":
            return 1.00, name, "Umpire unknown; neutral"
        return factor, name, f"Umpire K tendency x{factor:.3f} ({name})"
    except Exception:
        return 1.00, "Unknown", "Umpire unavailable; neutral"

def build_pa_sequence(lineup_rows, bf, fallback_k):
    bf = int(round(bf))
    if lineup_rows:
        rates = [r.get("Raw_K_Rate") for r in lineup_rows[:9] if r.get("Raw_K_Rate") is not None]
        if len(rates) >= 5:
            return [rates[i % len(rates)] for i in range(max(1, bf))], "Batter-by-batter posted lineup"
    return [fallback_k for _ in range(max(1, bf))], "Team/fallback K sequence"

def simulate_matchup(pitcher_k, batter_rates, park=1.0, ump=1.0, sims=12000):
    rates = []
    for idx, br in enumerate(batter_rates):
        k = calculate_log5_k_rate(pitcher_k, br)
        k *= park * ump * tto_decay_factor(idx)
        rates.append(clamp(k, 0.03, 0.60))
    out = np.random.binomial(1, np.array(rates), size=(sims, len(rates))).sum(axis=1)
    return out, rates


def bayesian_projection_std(data_score, lineup_locked, pitcher_confirmed, leash):
    """Dynamic uncertainty for K simulations.

    Higher data quality = tighter distribution. Missing lineup, unconfirmed pitcher,
    or leash risk = wider uncertainty. This does not create edge; it usually shrinks
    extreme confidence back toward reality.
    """
    score = safe_float(data_score, 50) or 50
    std = 1.25 - (score / 100.0) * 0.55
    if not lineup_locked:
        std += 0.28
    if not pitcher_confirmed:
        std += 0.32
    if leash and leash.get("leash_risk") in ["HIGH_PITCH_COUNT", "SHORT_RECENT_STARTS", "HIGH_RECENT_WORKLOAD"]:
        std += 0.25
    ppb = safe_float((leash or {}).get("ppb"), 4.0) or 4.0
    if ppb >= 4.15:
        std += 0.15
    return float(clamp(std, BAYESIAN_PROJECTION_STD_MIN, BAYESIAN_PROJECTION_STD_MAX))


def simulate_bayesian_markov_matchup(pitcher_k, batter_rates, expected_bf, park=1.0, ump=1.0, data_score=50, lineup_locked=False, pitcher_confirmed=True, leash=None, sims=BAYESIAN_MARKOV_SIMS):
    """MLB-specific Bayesian + Markov Monte Carlo.

    This keeps our current batter-by-batter K probabilities, but adds realistic uncertainty:
    - starter volume uncertainty around expected BF
    - pitcher K-rate uncertainty based on data quality/leash
    - PA-by-PA Markov flow instead of fixed 27 outs
    """
    base_rates = []
    for idx, br in enumerate(batter_rates):
        k = calculate_log5_k_rate(pitcher_k, br)
        base_rates.append(clamp(k * park * ump * tto_decay_factor(idx), 0.03, 0.60))

    if not base_rates:
        base_rates = [clamp(pitcher_k * park * ump, 0.03, 0.60)] * int(max(1, round(expected_bf or DEFAULT_BF)))

    data_score = safe_float(data_score, 50) or 50
    proj_std = bayesian_projection_std(data_score, lineup_locked, pitcher_confirmed, leash)
    expected_bf = safe_float(expected_bf, DEFAULT_BF) or DEFAULT_BF

    # Better score -> tighter BF range. Risky leash -> wider BF range.
    bf_sd = 1.25 + (1 - data_score / 100.0) * 2.0
    if leash and leash.get("leash_risk") in ["HIGH_PITCH_COUNT", "SHORT_RECENT_STARTS", "HIGH_RECENT_WORKLOAD"]:
        bf_sd += 1.2

    # Convert projection-level uncertainty into a conservative multiplier on PA K probabilities.
    baseline_projection = max(sum(base_rates[:int(round(expected_bf))]), 0.25)
    mult_sd = clamp(proj_std / max(baseline_projection, 1.0), 0.04, 0.22)

    results = np.zeros(int(sims), dtype=float)
    rates_arr = np.array(base_rates, dtype=float)
    n_rates = len(rates_arr)

    for i in range(int(sims)):
        sampled_bf = int(round(np.random.normal(expected_bf, bf_sd)))
        sampled_bf = int(clamp(sampled_bf, 12, 34))
        k_mult = float(np.random.normal(1.0, mult_sd))
        k_mult = clamp(k_mult, 0.72, 1.28)
        idx = np.arange(sampled_bf) % n_rates
        probs = np.clip(rates_arr[idx] * k_mult, 0.02, 0.68)
        results[i] = np.random.binomial(1, probs).sum()

    note = f"Bayesian Markov MC: sims={int(sims)}, BF μ={expected_bf:.1f}, BF σ={bf_sd:.2f}, K σ={proj_std:.2f}"
    return results, base_rates, note


XGB_FEATURES = [
    "projection", "pitcher_k", "opp_k", "expected_bf", "ppb", "recent_ip",
    "data_score", "lineup_locked", "pitcher_confirmed", "statcast_available",
    "statcast_csw", "statcast_whiff", "pitch_type_matchup_available", "pitch_type_factor",
    "consensus_count", "consensus_spread"
]


def xgb_feature_row_from_picklike(d):
    def b(v):
        return 1.0 if bool(v) else 0.0
    return {
        "projection": safe_float(d.get("projection"), 0) or 0,
        "pitcher_k": safe_float(d.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K,
        "opp_k": safe_float(d.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K,
        "expected_bf": safe_float(d.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF,
        "ppb": safe_float(d.get("ppb"), 4.0) or 4.0,
        "recent_ip": safe_float(d.get("recent_ip"), 5.5) or 5.5,
        "data_score": safe_float(d.get("data_score"), 50) or 50,
        "lineup_locked": b(d.get("lineup_locked")),
        "pitcher_confirmed": b(d.get("pitcher_confirmed")),
        "statcast_available": b(d.get("statcast_available")),
        "statcast_csw": safe_float(d.get("statcast_csw"), 0) or 0,
        "statcast_whiff": safe_float(d.get("statcast_whiff"), 0) or 0,
        "pitch_type_matchup_available": b(d.get("pitch_type_matchup_available")),
        "pitch_type_factor": safe_float(d.get("pitch_type_factor"), 1.0) or 1.0,
        "consensus_count": safe_float(d.get("consensus_count"), 0) or 0,
        "consensus_spread": safe_float(d.get("consensus_spread"), 0) or 0,
    }


def build_xgb_training_frame():
    """Train on our own graded official snapshots only.

    Target is residual actual Ks - existing projection, so XGBoost can only act
    as a correction layer. It does not replace the core model.
    """
    results = load_json(RESULT_LOG, [])
    rows = []
    for r in results[-XGB_RECENT_TRAIN_LIMIT:]:
        actual = safe_float(r.get("actual"))
        proj = safe_float(r.get("projection"))
        if actual is None or proj is None:
            continue
        if r.get("graded_result") not in ["WIN", "LOSS"]:
            continue
        feat = xgb_feature_row_from_picklike(r)
        feat["target_residual"] = float(clamp(actual - proj, -4.0, 4.0))
        rows.append(feat)
    return pd.DataFrame(rows)


def apply_xgboost_assist(current_features, current_projection, enabled=False):
    """Optional capped XGBoost correction.

    OFF by default. Activates only after enough graded picks and only changes
    the projection by a small capped amount. It cannot affect line source,
    Underdog lock, or strict no-bet gates.
    """
    info = {
        "enabled": bool(enabled),
        "active": False,
        "samples": 0,
        "adjustment": 0.0,
        "message": "XGBoost assist off",
    }
    base = safe_float(current_projection, 0) or 0
    if not enabled:
        return base, info

    df = build_xgb_training_frame()
    info["samples"] = int(len(df))
    if len(df) < XGB_MIN_GRADED_SAMPLES:
        info["message"] = f"Need {XGB_MIN_GRADED_SAMPLES}+ graded picks; found {len(df)}"
        return base, info

    try:
        from xgboost import XGBRegressor
    except Exception as e:
        info["message"] = f"xgboost not installed: {e}"
        return base, info

    try:
        train_df = df.copy()
        X = train_df[XGB_FEATURES].fillna(0.0)
        y = train_df["target_residual"].astype(float)
        model = XGBRegressor(
            n_estimators=160,
            max_depth=2,
            learning_rate=0.035,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="reg:squarederror",
            random_state=42,
        )
        model.fit(X, y)
        cur = pd.DataFrame([current_features])[XGB_FEATURES].fillna(0.0)
        raw_adj = float(model.predict(cur)[0])
        cap = min(XGB_MAX_RESIDUAL_ADJ_KS, abs(base) * XGB_MAX_PERCENT_ADJ)
        adj = float(clamp(raw_adj, -cap, cap))
        info.update({
            "active": True,
            "adjustment": round(adj, 3),
            "message": f"XGBoost residual assist active: raw {raw_adj:+.2f}, capped {adj:+.2f} K from {len(df)} samples",
        })
        return float(clamp(base + adj, 0.0, 15.0)), info
    except Exception as e:
        info["message"] = f"XGBoost assist error: {e}"
        return base, info

# =========================
# v11.14 FINAL DECISION / BET ACTION ENGINE
# =========================
# These helpers prevent the app from treating 5.64 as an automatic 6.
# They use the actual strikeout threshold: over 5.5 needs 6+, over 6.5 needs 7+.
def required_ks_for_over(line):
    line = safe_float(line)
    if line is None:
        return None
    return int(math.floor(line)) + 1

def max_ks_for_under(line):
    line = safe_float(line)
    if line is None:
        return None
    return int(math.floor(line))

def discrete_side_probability(sims, line):
    if line is None:
        return None, None, None
    needed = required_ks_for_over(line)
    arr = np.asarray(sims, dtype=float)
    # If sims are continuous, this still correctly asks: how often does the
    # simulated outcome clear the whole-number strikeout threshold?
    over_prob = float(np.mean(arr >= needed))
    under_prob = float(1.0 - over_prob)
    return over_prob, under_prob, needed

def calculate_pick_metrics(sims, line):
    if line is None:
        return {"over_prob": None, "under_prob": None, "fair_prob": None, "pick_side": "NO LINE", "edge": None, "grade": "NO LINE", "ev": None, "over_needed": None}
    over_prob, under_prob, over_needed = discrete_side_probability(sims, line)
    if over_prob >= under_prob:
        side = "OVER"
        fair = over_prob
    else:
        side = "UNDER"
        fair = under_prob
    edge = (fair - 0.50) * 100
    grade = "S" if fair >= 0.68 else "A" if fair >= 0.60 else "B" if fair >= 0.55 else "C"
    return {"over_prob": over_prob, "under_prob": under_prob, "fair_prob": fair, "pick_side": side, "edge": edge, "grade": grade, "ev": (fair * 100) - ((1 - fair) * 100), "over_needed": over_needed}

def is_key_k_line(line):
    line = safe_float(line)
    if line is None:
        return False
    return abs((line % 1) - 0.5) < 1e-9 and int(math.floor(line)) in [3, 4, 5, 6, 7]

def elite_k_upside_score(pitcher_k, lineup_k, expected_bf=None, p90=None, recent_ks=None, ppb=None, run_damage_level=None):
    """Ceiling protection for pitchers who can realistically spike 7-10 Ks.

    This does not force an OVER. It mainly blocks weak UNDER bets on high-upside arms.
    """
    score = 0.0
    pk = safe_float(pitcher_k, LEAGUE_AVG_K) or LEAGUE_AVG_K
    lk = safe_float(lineup_k, LEAGUE_AVG_K) or LEAGUE_AVG_K
    bf = safe_float(expected_bf, DEFAULT_BF) or DEFAULT_BF
    ppb_val = safe_float(ppb, 3.9) or 3.9
    p90v = safe_float(p90)

    if pk >= 0.315:
        score += 32
    elif pk >= 0.290:
        score += 25
    elif pk >= 0.265:
        score += 16
    elif pk >= 0.245:
        score += 8

    if lk >= 0.260:
        score += 24
    elif lk >= 0.245:
        score += 18
    elif lk >= 0.235:
        score += 10

    if bf >= 25.0:
        score += 18
    elif bf >= 23.0:
        score += 11
    elif bf >= 21.0:
        score += 5

    if p90v is not None:
        if p90v >= 8.0:
            score += 14
        elif p90v >= 7.0:
            score += 9
        elif p90v >= 6.5:
            score += 5

    if recent_ks:
        try:
            vals = [safe_float(x, 0) or 0 for x in recent_ks[:5]]
            if vals:
                avg = float(np.mean(vals))
                mx = max(vals)
                if avg >= 6.0:
                    score += 10
                elif avg >= 5.0:
                    score += 5
                if mx >= 8:
                    score += 8
                elif mx >= 7:
                    score += 5
        except Exception:
            pass

    if ppb_val <= 3.75:
        score += 5
    elif ppb_val >= 4.15:
        score -= 8

    rd = str(run_damage_level or '').upper()
    if rd == 'EXTREME':
        score -= 18
    elif rd == 'HIGH':
        score -= 10
    elif rd == 'MILD':
        score -= 4

    return int(clamp(score, 0, 100))

def final_pick_decision(projection, line, over_prob, under_prob, edge_abs, data_score=0, ev=None,
                        pitcher_k=None, lineup_k=None, expected_bf=None, ppb=None, p90=None,
                        recent_ks=None, run_damage_level=None, leash_risk=None,
                        lineup_locked=False, pitcher_confirmed=False):
    """Single source of truth for OVER / UNDER / LEAN / PASS.

    Output meanings:
    - 🔥 BET OVER / 🔥 BET UNDER = playable recommendation
    - ⚠️ LEAN OVER / ⚠️ LEAN UNDER = informational lean only, not a full bet
    - 🚫 PASS = do not bet
    """
    if line is None or projection is None:
        return {"model_side": "NO LINE", "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": None, "decision_note": "No real line", "elite_upside_score": 0, "over_needed": None}

    over_needed = required_ks_for_over(line)
    over_prob = safe_float(over_prob)
    under_prob = safe_float(under_prob)
    if over_prob is None or under_prob is None:
        return {"model_side": "NO PROB", "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": None, "decision_note": "No usable probability", "elite_upside_score": 0, "over_needed": over_needed}

    # Choose side by probability, not by decimal projection alone.
    if over_prob >= under_prob:
        side = "OVER"
        fair = over_prob
    else:
        side = "UNDER"
        fair = under_prob

    edge_abs = safe_float(edge_abs, 0.0) or 0.0
    score = safe_float(data_score, 0.0) or 0.0
    evv = safe_float(ev, 0.0) or 0.0
    ppb_val = safe_float(ppb, 3.9) or 3.9
    key_line = is_key_k_line(line)
    upside = elite_k_upside_score(pitcher_k, lineup_k, expected_bf, p90, recent_ks, ppb, run_damage_level)
    rd = str(run_damage_level or '').upper()
    leash = str(leash_risk or '').upper()

    notes = []
    if key_line:
        notes.append(f"key line: over needs {over_needed}+")
    if upside >= 70:
        notes.append(f"elite upside {upside}/100")
    elif upside >= 55:
        notes.append(f"upside {upside}/100")
    if rd in ['HIGH', 'EXTREME']:
        notes.append(f"run-damage risk {rd}")
    if leash in ['HIGH_PITCH_COUNT', 'SHORT_RECENT_STARTS', 'HIGH_RECENT_WORKLOAD', 'STRICT_HOOK']:
        notes.append(f"leash risk {leash}")

    # Thin edges around half-number K lines are traps.
    if key_line and edge_abs < 0.55:
        return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "Thin key-line edge; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}

    # Never make a confident UNDER on a high-upside arm unless the under edge is very large.
    if side == "UNDER" and upside >= 60 and edge_abs < 1.35:
        return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "Blocked weak UNDER vs high-K upside; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}

    # Asymmetric thresholds: unders need stronger proof than overs.
    if side == "UNDER":
        min_bet_prob = 0.67 if key_line else 0.65
        min_bet_edge = 1.10 if key_line else 0.95
        min_lean_prob = 0.62 if key_line else 0.60
        min_lean_edge = 0.90 if key_line else 0.75

        if fair >= min_bet_prob and edge_abs >= min_bet_edge and score >= 88 and evv >= 0.04:
            return {"model_side": side, "bet_action": "🔥 BET UNDER", "action_tier": "BET", "fair_probability": fair, "decision_note": "Clears strict UNDER gate; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}
        if fair >= min_lean_prob and edge_abs >= min_lean_edge:
            return {"model_side": side, "bet_action": "⚠️ LEAN UNDER", "action_tier": "LEAN", "fair_probability": fair, "decision_note": "Lean only, not full bet; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}
        return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "UNDER edge/probability too thin; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}

    if side == "OVER":
        min_bet_prob = 0.62 if not key_line else 0.63
        min_bet_edge = 1.00 if not key_line else 1.05
        min_lean_prob = 0.57
        min_lean_edge = 0.70 if not key_line else 0.80

        # Run damage should block fragile overs, but not automatically kill elite-upside profiles.
        if rd == 'EXTREME' and edge_abs < 1.35:
            return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "Extreme run-damage blocks borderline OVER; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}
        if rd == 'HIGH' and edge_abs < 1.15 and upside < 70:
            return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "High run-damage blocks weak OVER; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}

        if fair >= min_bet_prob and edge_abs >= min_bet_edge and score >= 86 and (evv >= 0.03 or upside >= 70):
            return {"model_side": side, "bet_action": "🔥 BET OVER", "action_tier": "BET", "fair_probability": fair, "decision_note": "Clears OVER gate; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}
        if fair >= min_lean_prob and edge_abs >= min_lean_edge:
            return {"model_side": side, "bet_action": "⚠️ LEAN OVER", "action_tier": "LEAN", "fair_probability": fair, "decision_note": "Lean only, not full bet; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}
        return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "OVER edge/probability too thin; " + "; ".join(notes), "elite_upside_score": upside, "over_needed": over_needed}

    return {"model_side": side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": fair, "decision_note": "No final gate cleared", "elite_upside_score": upside, "over_needed": over_needed}

# =========================
# REAL PROP SOURCES
# =========================
def source_result(source, status, line=None, rows=None, message=""):
    return {"source": source, "status": status, "line": safe_float(line), "rows": rows or [], "message": message}


def clean_real_prop_debug_rows(rows):
    """Display/storage filter: only valid MLB pitcher strikeout prop rows.

    Wrong-sport Underdog rows like LeBron/Shai NBA props are dropped here even
    if they made it through another source's raw/debug output.
    """
    cleaned = []
    nba_name_block = {
        "lebron james", "shai gilgeous alexander", "james harden", "donovan mitchell",
        "anthony edwards", "nikola jokic", "luka doncic", "jayson tatum",
        "stephen curry", "kevin durant", "giannis antetokounmpo", "victor wembanyama"
    }

    for r in rows or []:
        if not isinstance(r, dict):
            continue

        matched = str(r.get("Matched Name", r.get("matched_name", r.get("Player", ""))) or "")
        matched_norm = normalize_name(matched)
        if matched_norm in nba_name_block:
            continue
        if any(n in matched_norm for n in nba_name_block):
            continue

        line = safe_float(
            r.get("Line", r.get("line", r.get("Prop Line", r.get("line_display"))))
        )
        market = str(r.get("Market", r.get("market", "")) or "")
        blob = " ".join(str(v) for v in r.values())[:4000]

        if is_bad_sport_text(blob):
            continue
        if is_valid_k_line(line, allow_integer=False) is None:
            continue
        if is_bad_k_market_text(blob):
            continue

        # Accepted rows usually have Market = Pitcher Strikeouts. For raw rows,
        # require strikeout text in the blob.
        if market:
            if not is_pitcher_k_text(market) and not is_pitcher_k_text(blob):
                continue
        elif not is_pitcher_k_text(blob):
            continue

        cleaned.append(r)

    return cleaned

def is_half_point_line(line):
    """True for normal no-push prop lines like 4.5, 5.5, 6.5."""
    val = safe_float(line)
    if val is None:
        return False
    return 1.5 <= val <= 12.5 and abs(val % 1 - 0.5) < 1e-9


def is_valid_k_line(line, allow_integer=False):
    """Validate MLB pitcher strikeout prop line.

    Underdog pick'em lines should normally be half-point lines. Integers are accepted only
    for priced sportsbook/alternate markets where pushes can exist.
    """
    val = safe_float(line)
    if val is None:
        return None
    if not (1.5 <= val <= 12.5):
        return None
    if abs(val * 2 - round(val * 2)) > 1e-9:
        return None
    if not allow_integer and not is_half_point_line(val):
        return None
    return float(val)


def extract_half_lines_from_text(text):
    """Pull likely half-point K lines from title/display text, preferring values near strikeout words."""
    import re
    if not text:
        return []
    t = str(text)
    low = t.lower()
    if not any(k in low for k in ["strikeout", "strikeouts", "pitcher k", "pitcher_k"]):
        return []
    vals = []
    # Prefer half numbers because Underdog uses half-lines to avoid pushes.
    for m in re.finditer(r"(?<!\d)(\d{1,2}\.5)(?!\d)", t):
        val = safe_float(m.group(1))
        if is_valid_k_line(val, allow_integer=False) is not None:
            vals.append(float(val))
    return vals

@st.cache_data(ttl=600, show_spinner=False)
def get_odds_events():
    if not ODDS_API_KEY:
        return []
    data = safe_get_json(f"{ODDS_BASE}/sports/baseball_mlb/events", params={"apiKey": ODDS_API_KEY}, timeout=16)
    return data if isinstance(data, list) else []

@st.cache_data(ttl=600, show_spinner=False)
def get_sportsbook_event_pitcher_k_lines(event_id, player_name):
    if not event_id:
        return source_result("Sportsbook", "NO EVENT", rows=[], message="No matching Odds API event id")
    data = safe_get_json(
        f"{ODDS_BASE}/sports/baseball_mlb/events/{event_id}/odds",
        params={"apiKey": ODDS_API_KEY, "regions": "us,us2,uk,eu,au", "markets": ",".join(SPORTSBOOK_PITCHER_K_MARKETS), "oddsFormat": "american"},
        timeout=16
    )
    if not data or (isinstance(data, dict) and data.get("message")):
        return source_result("Sportsbook", "FAILED", rows=[], message="Event odds call failed or plan has no player props")
    rows = []
    for book in data.get("bookmakers", []):
        book_name = book.get("title") or book.get("key") or "Sportsbook"
        for market in book.get("markets", []):
            if market.get("key") not in SPORTSBOOK_PITCHER_K_MARKETS:
                continue
            for outcome in market.get("outcomes", []):
                desc = outcome.get("description") or outcome.get("player") or outcome.get("participant") or outcome.get("name") or ""
                score = name_score(player_name, desc)
                if score < 0.80:
                    continue
                point = safe_float(outcome.get("point"))
                if point is None:
                    continue
                rows.append({"Source": "OddsAPI", "Provider": book_name, "Player": player_name, "Matched Name": desc, "Match Score": round(score, 3), "Market": market.get("key"), "Line": point, "Side": str(outcome.get("name", "")).upper(), "Price": outcome.get("price"), "Last Update": market.get("last_update") or book.get("last_update")})
    if not rows:
        return source_result("Sportsbook", "NO MATCH", rows=[], message="No sportsbook K prop matched this pitcher")
    line_vals = [safe_float(r["Line"]) for r in rows if safe_float(r.get("Line")) is not None]
    consensus = float(np.median(line_vals)) if line_vals else rows[0]["Line"]
    return source_result("Sportsbook", "FOUND", line=consensus, rows=rows, message=f"Found {len(rows)} sportsbook outcomes")

def get_sportsbook_k_data(game_home, game_away, player_name):
    events = get_odds_events()
    event_id = None
    target_teams = {normalize_name(game_home), normalize_name(game_away)}
    for ev in events:
        home = normalize_name(ev.get("home_team"))
        away = normalize_name(ev.get("away_team"))
        if {home, away} == target_teams or (home in target_teams and away in target_teams):
            event_id = ev.get("id")
            break
    return get_sportsbook_event_pitcher_k_lines(event_id, player_name)

@st.cache_data(ttl=600, show_spinner=False)
def get_prizepicks_k_data(player_name):
    data = safe_get_json(PRIZEPICKS_URL, timeout=16)
    if not data:
        return source_result("PrizePicks", "FAILED", message="API failed or returned no JSON")
    players = {}
    for inc in data.get("included", []):
        inc_type = inc.get("type", "")
        attrs = inc.get("attributes", {}) or {}
        if inc_type in ["new_player", "player"]:
            pid = str(inc.get("id"))
            name = attrs.get("name") or attrs.get("display_name") or attrs.get("full_name")
            league = attrs.get("league") or attrs.get("league_name") or attrs.get("sport") or ""
            team = attrs.get("team") or attrs.get("team_name") or ""
            if pid and name:
                players[pid] = {"name": name, "league": league, "team": team}
    rows = []
    for item in data.get("data", []):
        attrs = item.get("attributes", {}) or {}
        stat_type = attrs.get("stat_type") or attrs.get("stat_display_name") or attrs.get("name") or ""
        if not is_pitcher_k_text(stat_type):
            continue
        line_score = safe_float(attrs.get("line_score") or attrs.get("line") or attrs.get("projection"))
        if line_score is None:
            continue
        rel = item.get("relationships", {}) or {}
        pdata = (rel.get("new_player", {}) or {}).get("data") or (rel.get("player", {}) or {}).get("data") or {}
        pid = str(pdata.get("id", ""))
        info = players.get(pid, {})
        pp_name = info.get("name") or attrs.get("player_name") or attrs.get("description") or ""
        league_blob = f"{info.get('league','')} {attrs.get('league','')} {attrs.get('league_name','')} {attrs.get('sport','')}".lower()
        if league_blob.strip() and not any(x in league_blob for x in ["mlb", "baseball"]):
            continue
        score = name_score(player_name, pp_name)
        if score >= 0.80:
            rows.append({"Source": "PrizePicks", "Provider": "PrizePicks", "Player": player_name, "Matched Name": pp_name, "Team": info.get("team", ""), "League": info.get("league", ""), "Market": stat_type, "Line": line_score, "Side": "OVER/UNDER", "Price": None, "Match Score": round(score, 3), "Start Time": attrs.get("start_time"), "Projection ID": item.get("id")})
    if not rows:
        return source_result("PrizePicks", "NO MATCH", message="No fuzzy pitcher strikeout prop match found")
    rows = sorted(rows, key=lambda r: -r.get("Match Score", 0))
    return source_result("PrizePicks", "FOUND", line=rows[0]["Line"], rows=rows, message=f"Found {len(rows)} PrizePicks matches")

def extract_prop_rows_from_any_json(data, player_name, source_name):
    rows = []
    if not data:
        return rows
    objects = flatten_json(data)
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        blob = json.dumps(obj, default=str).lower()
        if is_bad_sport_text(blob) or is_bad_k_market_text(blob):
            continue
        if not ("pitcher strikeout" in blob or "pitcher strikeouts" in blob or "pitcher k" in blob or "pitcher_k" in blob or "strikeouts" in blob):
            continue
        candidate_bits = []
        for key in ["player", "player_name", "participant", "participant_name", "name", "description", "display_name", "market_name", "selection", "title"]:
            val = obj.get(key)
            if isinstance(val, dict):
                val = val.get("name") or val.get("full_name") or val.get("display_name")
            if val:
                candidate_bits.append(str(val))
        candidate = " ".join(candidate_bits) or blob[:160]
        score = name_score(player_name, candidate)
        if score < 0.80 and normalize_name(player_name) in normalize_name(blob):
            score = 0.82
        if score < 0.80:
            continue
        line = safe_float(first_value(obj, ["stat_value", "target_value", "over_under_line", "line_score", "line", "point", "handicap"]))
        line = is_valid_k_line(line, allow_integer=True)
        if line is None:
            continue
        side = first_value(obj, ["side", "label", "name", "selection", "outcome", "bet_type"]) or "Over/Under"
        price = safe_float(first_value(obj, ["price", "odds", "american_odds", "american", "over_price", "under_price"]))
        book = first_value(obj, ["sportsbook", "book", "bookmaker", "operator", "source"]) or source_name
        if isinstance(book, dict):
            book = book.get("name") or source_name
        rows.append({"Source": source_name, "Provider": str(book), "Player": player_name, "Matched Name": candidate[:120], "Match Score": round(score, 3), "Market": first_value(obj, ["market", "market_name", "stat", "stat_type", "prop", "category"]) or "Pitcher Strikeouts", "Side": str(side).upper(), "Line": line, "Price": price})
    dedup = {}
    for r in rows:
        key = (r.get("Provider"), r.get("Source"), str(r.get("Side")).lower(), r.get("Line"), r.get("Price"))
        dedup[key] = r
    return list(dedup.values())

def get_underdog_k_data(player_name):
    """Live Underdog parser for MLB pitcher strikeout props.

    v10 upgrade:
    - Still tries the safe relationship path first: line -> over_under -> appearance -> player.
    - If Underdog changes nesting or omits type labels, falls back to a recursive parser.
    - Accepts active Underdog K lines when the player name and strikeout market are clearly present.
    - Keeps NBA/WNBA/fantasy/team props blocked.
    """
    accepted_rows = []
    rejected_rows = []
    last_msg = ""
    target_norm = normalize_name(player_name)

    LINE_TYPES = {"over_under_line", "over_under_lines"}
    OU_TYPES = {"over_under", "over_unders"}
    APP_TYPES = {"appearance", "appearances"}
    PLAYER_TYPES = {"player", "players"}

    def attrs(obj):
        if not isinstance(obj, dict):
            return {}
        out = {}
        a = obj.get("attributes")
        if isinstance(a, dict):
            out.update(a)
        for k, v in obj.items():
            if k not in ["attributes", "relationships", "included", "data"] and k not in out:
                out[k] = v
        return out

    def obj_type(obj, fallback=""):
        return str(obj.get("type") or fallback or "").lower().replace("-", "_") if isinstance(obj, dict) else ""

    def obj_id(obj):
        if not isinstance(obj, dict):
            return None
        val = obj.get("id") or attrs(obj).get("id")
        return str(val) if val not in [None, ""] else None

    def rel_id(obj, rel_names):
        if not isinstance(obj, dict):
            return None
        rels = obj.get("relationships") or {}
        for name in rel_names:
            candidates = [name, name.replace("_", "-"), name.replace("_", "")]
            for cname in candidates:
                if cname not in rels:
                    continue
                node = rels.get(cname)
                data = node.get("data") if isinstance(node, dict) else node
                if isinstance(data, dict):
                    rid = data.get("id")
                    if rid not in [None, ""]:
                        return str(rid)
                if isinstance(data, list) and data:
                    for item in data:
                        if isinstance(item, dict) and item.get("id") not in [None, ""]:
                            return str(item.get("id"))
        return None

    def collect_objects(data):
        objects = []
        def walk(x, parent_key=""):
            if isinstance(x, dict):
                y = dict(x)
                if parent_key and "_parent_key" not in y:
                    y["_parent_key"] = parent_key
                objects.append(y)
                for k, v in x.items():
                    walk(v, k)
            elif isinstance(x, list):
                for item in x:
                    walk(item, parent_key)
        walk(data)
        return objects

    def text_from(*objs):
        parts = []
        wanted = [
            "title", "display_title", "name", "player_name", "full_name", "first_name", "last_name",
            "display_name", "stat", "stat_type", "appearance_stat", "display_stat", "label", "market",
            "market_name", "sport", "league", "sport_name", "league_name", "position", "description",
            "over_under", "over_under_title", "scoring_type", "projection_type"
        ]
        for obj in objs:
            if not isinstance(obj, dict):
                continue
            a = attrs(obj)
            for k in wanted:
                v = a.get(k)
                if isinstance(v, dict):
                    for kk in wanted:
                        if v.get(kk) not in [None, ""]:
                            parts.append(str(v.get(kk)))
                elif v not in [None, ""]:
                    parts.append(str(v))
        return " | ".join(parts)

    def player_name_from(player_obj, appearance_obj=None, line_obj=None, ou_obj=None):
        p = attrs(player_obj) if isinstance(player_obj, dict) else {}
        a = attrs(appearance_obj) if isinstance(appearance_obj, dict) else {}
        l = attrs(line_obj) if isinstance(line_obj, dict) else {}
        o = attrs(ou_obj) if isinstance(ou_obj, dict) else {}
        candidates = [
            p.get("display_name"), p.get("full_name"), p.get("name"), p.get("player_name"),
            p.get("short_name"), p.get("abbreviation"), p.get("abbr_name"),
            (str(p.get("first_name", "")).strip() + " " + str(p.get("last_name", "")).strip()).strip(),
            a.get("player_name"), a.get("full_name"), a.get("display_name"), a.get("title"), a.get("name"),
            a.get("short_name"), a.get("abbreviation"), a.get("abbr_name"),
            l.get("player_name"), l.get("full_name"), l.get("display_name"), l.get("title"), l.get("name"),
            l.get("short_name"), l.get("abbreviation"), l.get("abbr_name"),
            o.get("player_name"), o.get("full_name"), o.get("display_name"), o.get("title"), o.get("name"),
            o.get("short_name"), o.get("abbreviation"), o.get("abbr_name"),
        ]
        for c in candidates:
            if c and normalize_name(c):
                return str(c)
        return ""

    def line_from_obj(*objs):
        # Underdog displayed K lines should come from real line fields only.
        # Do NOT use generic points/point/value/total fields; those caused wrong lines.
        safe_keys = ["stat_value", "line_score", "over_under_line", "target_value"]
        for obj in objs:
            a = attrs(obj)
            for k in safe_keys:
                val = safe_float(a.get(k))
                if is_valid_k_line(val, allow_integer=False) is not None:
                    return float(val), f"{k} half-line from Underdog object"
        text_lines = extract_half_lines_from_text(" | ".join(text_from(o) for o in objs))
        if text_lines:
            return float(text_lines[0]), "half-line from Underdog text"
        return None, "no valid Underdog half-line"

    def blob_from(*objs):
        return " | ".join([text_from(o) for o in objs if isinstance(o, dict)]).lower()

    def is_bad_sport(blob):
        return is_bad_sport_text(blob)

    def is_pitcher_k_blob(blob):
        blob = blob.lower()
        if not any(x in blob for x in ["pitcher strikeout", "pitcher strikeouts", "pitcher_k", "pitcher k", "strikeouts", "strike outs"]):
            return False
        return not is_bad_k_market_text(blob)

    def active_status_ok(*objs):
        status_blob = " ".join(
            str(attrs(o).get(k, ""))
            for o in objs if isinstance(o, dict)
            for k in ["status", "state", "display_status", "over_status", "under_status", "hidden", "active"]
        ).lower()
        if any(x in status_blob for x in ["suspended", "removed", "hidden", "inactive", "closed", "disabled"]):
            return False
        return True

    def underdog_player_score(actual_player, evidence):
        score = max(name_score(player_name, actual_player), name_score(player_name, evidence))
        # Strong fallback for Underdog display names that use first initial + last name.
        # Example: MLB probable pitcher = "Cristopher Sanchez"; Underdog row = "C. Sánchez".
        t_parts = target_norm.split()
        if len(t_parts) >= 2:
            target_initial = t_parts[0][:1]
            target_last = t_parts[-1]
            evidence_norm = normalize_name(evidence)
            # Look for "c sanchez", "c. sanchez", or any blob containing the last name with matching initial.
            if target_last in evidence_norm:
                tokens = evidence_norm.split()
                for i, tok in enumerate(tokens):
                    if tok == target_last and i > 0 and tokens[i - 1][:1] == target_initial:
                        score = max(score, 0.93)
                    if tok == target_last and target_initial in evidence_norm:
                        score = max(score, 0.88)
        if target_norm and target_norm in normalize_name(evidence):
            score = max(score, 0.94)
        return score

    def add_row(line, score, matched, evidence, line_note, path, source_mode):
        accepted_rows.append({
            "Source": "Underdog",
            "Provider": "Underdog",
            "Player": player_name,
            "Matched Name": (matched or evidence[:120]),
            "Match Score": round(float(score), 3),
            "Market": "Pitcher Strikeouts",
            "Side": "OVER/UNDER",
            "Line": float(line),
            "Price": None,
            "Line Evidence": line_note,
            "Parser Mode": source_mode,
            "Underdog Path": path,
        })

    for url in UNDERDOG_URLS:
        data = safe_get_json(url, timeout=18)
        if not data:
            last_msg = f"No JSON from {url}"
            continue

        objects = collect_objects(data)
        by_id_any = {}
        over_unders, appearances, players, line_candidates = {}, {}, {}, []

        for obj in objects:
            typ = obj_type(obj, obj.get("_parent_key", ""))
            oid = obj_id(obj)
            if oid:
                by_id_any[oid] = obj
            if typ in LINE_TYPES or "over_under_line" in typ:
                line_candidates.append(obj)
            elif typ in OU_TYPES or typ == "over_under":
                if oid:
                    over_unders[oid] = obj
            elif typ in APP_TYPES or "appearance" in typ:
                if oid:
                    appearances[oid] = obj
            elif typ in PLAYER_TYPES or typ == "player":
                if oid:
                    players[oid] = obj

        def get_by_id(oid):
            return by_id_any.get(str(oid)) if oid not in [None, ""] else None

        # Relationship parser first.
        if not line_candidates:
            for obj in objects:
                a = attrs(obj)
                if any(a.get(k) not in [None, ""] for k in ["stat_value", "line_score", "over_under_line", "target_value", "line", "points"]):
                    if isinstance(obj.get("relationships"), dict) or is_pitcher_k_blob(json.dumps(obj, default=str).lower()):
                        line_candidates.append(obj)

        for line_obj in line_candidates:
            ou_id = rel_id(line_obj, ["over_under", "overUnders", "over_under_id", "over"])
            ou_obj = over_unders.get(ou_id) or get_by_id(ou_id)

            app_id = rel_id(line_obj, ["appearance", "appearances", "appearance_id"])
            if not app_id and isinstance(ou_obj, dict):
                app_id = rel_id(ou_obj, ["appearance", "appearances", "appearance_id"])
            app_obj = appearances.get(app_id) or get_by_id(app_id)

            player_id = rel_id(line_obj, ["player", "players", "player_id"])
            if not player_id and isinstance(ou_obj, dict):
                player_id = rel_id(ou_obj, ["player", "players", "player_id"])
            if not player_id and isinstance(app_obj, dict):
                player_id = rel_id(app_obj, ["player", "players", "player_id"])
            if not player_id and isinstance(app_obj, dict):
                player_id = attrs(app_obj).get("player_id") or attrs(app_obj).get("playerId")
            player_obj = players.get(str(player_id)) or get_by_id(player_id)

            evidence = text_from(line_obj, ou_obj, app_obj, player_obj)
            blob = evidence.lower()
            if is_bad_sport(blob):
                continue
            if not is_pitcher_k_blob(blob):
                # rejected row hidden intentionally
                continue

            actual_player = player_name_from(player_obj, app_obj, line_obj, ou_obj)
            score = underdog_player_score(actual_player, evidence)
            if score < 0.82:
                # rejected row hidden intentionally
                continue

            chosen_line, line_note = line_from_obj(line_obj, ou_obj)
            if chosen_line is None:
                # rejected row hidden intentionally
                continue
            if not active_status_ok(line_obj, ou_obj):
                continue
            add_row(chosen_line, score, actual_player, evidence, line_note, f"line:{obj_id(line_obj)} -> over_under:{ou_id} -> appearance:{app_id} -> player:{player_id}", "relationship")

        # Recursive fallback parser for new/changed Underdog JSON.
        # This is intentionally looser than relationship mode, but still requires:
        # target player name + strikeout market + sane K line + no bad sport/market words.
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            blob_json = json.dumps(obj, default=str)
            blob_low = blob_json.lower()
            if is_bad_sport(blob_low):
                continue
            if not is_pitcher_k_blob(blob_low):
                continue
            # Try candidate fields and the full object blob so abbreviated Underdog names match daily.
            cand = []
            for k in ["player", "player_name", "participant", "participant_name", "name", "description", "display_name", "title", "short_name", "abbreviation", "abbr_name"]:
                v = attrs(obj).get(k)
                if isinstance(v, dict):
                    v = v.get("name") or v.get("full_name") or v.get("display_name") or v.get("title") or v.get("short_name")
                if v:
                    cand.append(str(v))
            matched = " ".join(cand) or player_name
            score = max(underdog_player_score(matched, blob_json), name_score(player_name, matched))
            if score < 0.82:
                continue
            line, line_note = line_from_obj(obj)
            if line is None:
                continue
            if not active_status_ok(obj):
                continue
            add_row(line, score, matched, blob_json[:200], line_note, f"fallback:{obj_id(obj) or attrs(obj).get('id') or len(accepted_rows)}", "recursive fallback")

        if accepted_rows:
            break

    if not accepted_rows:
        return source_result("Underdog", "NO MATCH", rows=[], message=last_msg or "No active Underdog pitcher-K line matched. Rejected wrong-sport rows are hidden.")

    dedup = {}
    for r in accepted_rows:
        key = (r.get("Underdog Path"), r.get("Line"), r.get("Parser Mode"))
        if key not in dedup or safe_float(r.get("Match Score"), 0) > safe_float(dedup[key].get("Match Score"), 0):
            dedup[key] = r
    accepted_rows = list(dedup.values())

    # Pick the live Underdog board line.
    # Important: alternate/fallback nested rows can produce lower lines.
    # So we prefer relationship rows, then half-point rows, then highest line among similarly matched rows.
    primary_rows = [r for r in accepted_rows if r.get("Parser Mode") == "relationship"] or accepted_rows
    half_rows = [r for r in primary_rows if is_half_point_line(r.get("Line"))] or primary_rows

    def row_rank(r):
        rel_bonus = 1 if r.get("Parser Mode") == "relationship" else 0
        half_bonus = 1 if is_half_point_line(r.get("Line")) else 0
        score = safe_float(r.get("Match Score"), 0) or 0
        line = safe_float(r.get("Line"), -999) or -999
        return (rel_bonus, half_bonus, round(score, 2), line)

    best_row = sorted(half_rows, key=row_rank, reverse=True)[0]
    active = safe_float(best_row.get("Line"))

    return source_result(
        "Underdog",
        "FOUND",
        line=float(active),
        rows=sorted(accepted_rows, key=lambda r: (-safe_float(r.get("Match Score"), 0), safe_float(r.get("Line"), 99))),
        message=f"Live Underdog line matched: {float(active):.1f} via {best_row.get('Matched Name')} ({best_row.get('Parser Mode')}); rejected debug rows hidden to prevent wrong-sport noise"
    )

@st.cache_data(ttl=600, show_spinner=False)
def get_sportsgameodds_k_data(player_name):
    if not SPORTSGAMEODDS_API_KEY:
        return source_result("SportsGameOdds", "DISABLED", message="Add SPORTSGAMEODDS_API_KEY to enable")
    endpoints = [f"{SPORTSGAMEODDS_BASE}/events", f"{SPORTSGAMEODDS_BASE}/odds", f"{SPORTSGAMEODDS_BASE}/props"]
    headers = {"X-Api-Key": SPORTSGAMEODDS_API_KEY, "Authorization": f"Bearer {SPORTSGAMEODDS_API_KEY}"}
    all_rows = []
    last_msg = ""
    for url in endpoints:
        data = safe_get_json(url, params={"sport": "baseball", "league": "mlb", "market": "player_pitcher_strikeouts"}, headers=headers, timeout=16)
        if not data:
            last_msg = f"No JSON from {url}"
            continue
        all_rows.extend(extract_prop_rows_from_any_json(data, player_name, "SportsGameOdds"))
    if not all_rows:
        return source_result("SportsGameOdds", "NO MATCH", message=last_msg or "No SportsGameOdds row matched")
    lines = [safe_float(r.get("Line")) for r in all_rows if safe_float(r.get("Line")) is not None]
    return source_result("SportsGameOdds", "FOUND", line=float(np.median(lines)), rows=all_rows, message=f"Found {len(all_rows)} SportsGameOdds rows")

@st.cache_data(ttl=600, show_spinner=False)
def get_opticodds_k_data(player_name):
    if not OPTICODDS_API_KEY:
        return source_result("OpticOdds", "DISABLED", message="Add OPTICODDS_API_KEY to enable")
    endpoints = [f"{OPTICODDS_BASE}/fixtures/odds", f"{OPTICODDS_BASE}/odds", f"{OPTICODDS_BASE}/player-props"]
    headers = {"X-Api-Key": OPTICODDS_API_KEY, "Authorization": f"Bearer {OPTICODDS_API_KEY}"}
    all_rows = []
    last_msg = ""
    for url in endpoints:
        data = safe_get_json(url, params={"sport": "baseball", "league": "mlb", "market": "player_pitcher_strikeouts"}, headers=headers, timeout=16)
        if not data:
            last_msg = f"No JSON from {url}"
            continue
        all_rows.extend(extract_prop_rows_from_any_json(data, player_name, "OpticOdds"))
    if not all_rows:
        return source_result("OpticOdds", "NO MATCH", message=last_msg or "No OpticOdds row matched")
    lines = [safe_float(r.get("Line")) for r in all_rows if safe_float(r.get("Line")) is not None]
    return source_result("OpticOdds", "FOUND", line=float(np.median(lines)), rows=all_rows, message=f"Found {len(all_rows)} OpticOdds rows")

def choose_active_line(sportsbook_data, pp_data, ud_data, sgo_data, optic_data):
    """Choose a safe active line.

    For this app, Underdog is treated as the live source of truth when it has an exact
    half-point pitcher-K match. That prevents the app from showing 5 when Underdog is
    actually showing 4.5. Other sources remain available as backup/consensus.
    """
    candidates = []

    def add(source, line, weight, allow_integer=False):
        val = is_valid_k_line(line, allow_integer=allow_integer)
        if val is not None:
            candidates.append({"Source": source, "Line": val, "Weight": float(weight)})

    # Underdog first: user is comparing the app to live Underdog props.
    ud_line = is_valid_k_line(ud_data.get("line"), allow_integer=False)
    if ud_data.get("status") == "FOUND" and ud_line is not None:
        # Still collect other rows for diagnostics, but do not let consensus round/shift Underdog.
        add("Sportsbook", sportsbook_data.get("line"), 3.0, allow_integer=True)
        add("SportsGameOdds", sgo_data.get("line"), 2.5, allow_integer=True)
        add("OpticOdds", optic_data.get("line"), 2.5, allow_integer=True)
        add("PrizePicks", pp_data.get("line"), 1.5, allow_integer=False)
        add("Underdog", ud_line, 3.5, allow_integer=False)
        raw = [c["Line"] for c in candidates] or [ud_line]
        spread = float(max(raw) - min(raw)) if len(raw) > 1 else 0.0
        return float(ud_line), "Underdog Live Exact", {
            "count": len(candidates),
            "quality": "UNDERDOG_EXACT",
            "spread": round(spread, 2),
            "rows": candidates,
        }

    # Backup mode when Underdog has no exact match.
    add("Sportsbook", sportsbook_data.get("line"), 3.0, allow_integer=True)
    add("SportsGameOdds", sgo_data.get("line"), 2.5, allow_integer=True)
    add("OpticOdds", optic_data.get("line"), 2.5, allow_integer=True)
    add("PrizePicks", pp_data.get("line"), 1.5, allow_integer=False)

    if not candidates:
        return None, "No Valid Real Pitcher-K Line", {"count": 0, "quality": "NO LINE", "spread": None, "rows": []}

    raw_lines = [c["Line"] for c in candidates]
    spread = float(max(raw_lines) - min(raw_lines)) if len(candidates) > 1 else 0.0

    if len(candidates) >= 2 and spread > 1.0:
        priority = {"Sportsbook": 1, "SportsGameOdds": 2, "OpticOdds": 3, "PrizePicks": 4}
        best = sorted(candidates, key=lambda c: priority.get(c["Source"], 99))[0]
        return best["Line"], f"{best['Source']} Only (source disagreement blocked)", {
            "count": len(candidates), "quality": "DISAGREE", "spread": round(spread, 2), "rows": candidates
        }

    expanded = []
    for c in candidates:
        expanded.extend([c["Line"]] * max(1, int(round(c["Weight"] * 2))))
    consensus = float(np.median(expanded))

    # Do not create fake .0 lines from consensus if half-line sources dominate.
    half_candidates = [c["Line"] for c in candidates if is_half_point_line(c["Line"])]
    if half_candidates and not is_half_point_line(consensus):
        counts = {}
        for v in half_candidates:
            counts[v] = counts.get(v, 0) + 1
        consensus = sorted(counts.items(), key=lambda kv: (-kv[1], abs(kv[0] - consensus)))[0][0]

    quality = "STRONG" if len(candidates) >= 3 and spread <= 0.5 else "OK" if len(candidates) >= 2 and spread <= 1.0 else "THIN"
    source = "Cross-Source Consensus" if len(candidates) >= 2 else candidates[0]["Source"]
    return consensus, f"{source} ({quality})", {"count": len(candidates), "quality": quality, "spread": round(spread, 2), "rows": candidates}

# =========================
# CONFIDENCE / SIGNAL
# =========================
# CONFIDENCE / SIGNAL
# =========================
def data_lock_score(lineup_locked, pitcher_confirmed, active_line, consensus_info, ppb, statcast_available, pitch_type_available):
    score = 38
    if pitcher_confirmed:
        score += 15
    if lineup_locked:
        score += 20
    if active_line is not None:
        score += 15
    if consensus_info.get("count", 0) >= 3 and (consensus_info.get("spread") is None or consensus_info.get("spread") <= 0.5):
        score += 9
    elif consensus_info.get("count", 0) >= 2:
        score += 6
    if ppb and ppb < 4.05:
        score += 3
    elif ppb and ppb >= 4.25:
        score -= 5
    if statcast_available:
        score += 5
    if pitch_type_available:
        score += 3
    return int(clamp(score, 0, 100))

def shrink_probability_to_market(model_prob, score=50, lineup_locked=False, pitcher_confirmed=False):
    p = safe_float(model_prob)
    if p is None:
        return None

    # v9.7 market shrink: do not let simulations print fake 70%+ confidence.
    strength = 0.18 + (float(score or 50) / 100.0) * 0.48
    strength += 0.06 if lineup_locked else -0.12
    strength += 0.05 if pitcher_confirmed else -0.10
    strength = clamp(strength, 0.16, 0.82)

    capped = clamp(0.50 + ((p - 0.50) * strength), 0.01, 0.99)

    if not lineup_locked or not pitcher_confirmed:
        capped = min(capped, 0.68)
    elif score < MIN_CONFIRMED_LINEUP_SCORE:
        capped = min(capped, 0.76)

    return clamp(capped, 0.01, 0.99)

def no_bet_gate(active_line, pick_side, fair_prob, ev, gap, score, lineup_locked, pitcher_confirmed, line_source, consensus_info, leash):
    """Final hard filter. If any reason appears, the app must PASS.

    v9.7 is built to win by selectivity: fewer recommendations, stronger edge.
    """
    reasons = []
    consensus_info = consensus_info or {}
    leash = leash or {}
    ppb = safe_float(leash.get("ppb"), 4.0) or 4.0
    recent_ip = safe_float(leash.get("recent_ip"), 5.5) or 5.5

    if active_line is None:
        reasons.append("no real prop line")
    if pick_side not in ["OVER", "UNDER"]:
        reasons.append("no valid side")
    if fair_prob is None or fair_prob < MIN_BETTABLE_PROB:
        reasons.append(f"probability below {int(MIN_BETTABLE_PROB*100)}%")
    if ev is None or ev < MIN_BETTABLE_EV:
        reasons.append(f"EV below {round(MIN_BETTABLE_EV*100,1)}%")
    if gap is None or gap < MIN_BETTABLE_GAP_KS:
        reasons.append(f"edge below {MIN_BETTABLE_GAP_KS} K")
    if score < MIN_BETTABLE_SCORE:
        reasons.append(f"data score below {MIN_BETTABLE_SCORE}")
    if not pitcher_confirmed:
        reasons.append("pitcher not confirmed")

    # No confirmed lineup = never trust an OVER. Unders can survive only with all other gates.
    if not lineup_locked and pick_side == "OVER":
        reasons.append("no confirmed lineup for over")
    elif not lineup_locked:
        reasons.append("lineup not locked")

    if consensus_info.get("quality") in ["NO LINE", "REJECTED"]:
        reasons.append("no validated market consensus")
    if consensus_info.get("rejected"):
        reasons.append("one or more source lines rejected as outliers")
    underdog_exact = ("underdog" in str(line_source).lower()) and consensus_info.get("quality") == "UNDERDOG_EXACT"
    if consensus_info.get("count", 0) < 2 and not underdog_exact:
        reasons.append("not enough market sources")

    # Pitcher volume/leash is the main K-prop trap.
    if ppb >= 4.15:
        reasons.append("pitcher uses too many pitches per batter")
    if recent_ip < 4.8:
        reasons.append("recent innings too low")
    if leash.get("leash_risk") in ["HIGH_PITCH_COUNT", "SHORT_RECENT_STARTS", "HIGH_RECENT_WORKLOAD"]:
        reasons.append(f"leash risk: {leash.get('leash_risk')}")

    # v11.12: H/R/ER/BB/HR run-damage risk blocks fragile overs.
    rd_level = str(leash.get("run_damage_risk_level") or "").upper()
    rd_factor = safe_float(leash.get("run_damage_factor"), 1.0) or 1.0
    if pick_side == "OVER" and rd_level in ["HIGH", "EXTREME"]:
        reasons.append(f"run-damage short-outing risk: {rd_level}")
    elif pick_side == "OVER" and rd_factor <= 0.92 and gap is not None and gap < 1.35:
        reasons.append("run-damage BF cut too large for a borderline over")

    return len(reasons) == 0, reasons

def classify_risk(prob, score, priced, edge_pct, gap, line_source):
    p = safe_float(prob)
    if p is None:
        return "NO MODEL %", "No usable probability"

    pct = p * 100
    # v9.7: stop labeling weak props as playable. Only elite/strong survive visually.
    if pct >= 70 and score >= MIN_ELITE_DATA_SCORE and priced and edge_pct >= MIN_ELITE_NO_VIG_EDGE and gap >= 1.15:
        return "🔥 ELITE WATCH — VERIFY", "All strict real-data, price, gap, and market gates passed"
    if pct >= 64 and score >= MIN_BETTABLE_SCORE and priced and edge_pct >= MIN_BETTABLE_EV * 100 and gap >= MIN_BETTABLE_GAP_KS:
        return "✅ STRONG WATCH", "Playable only after final manual check: lineup, weather, pitcher status"

    notes = []
    if pct < MIN_BETTABLE_PROB * 100:
        notes.append(f"probability under {int(MIN_BETTABLE_PROB*100)}%")
    if score < MIN_BETTABLE_SCORE:
        notes.append(f"data score under {MIN_BETTABLE_SCORE}")
    if not priced:
        notes.append("no real sportsbook price")
    if edge_pct is not None and edge_pct < MIN_ELITE_NO_VIG_EDGE:
        notes.append("no-vig edge not elite")
    if "No Real Line" in str(line_source):
        notes.append("no real prop line")
    if gap is None or gap < MIN_BETTABLE_GAP_KS:
        notes.append(f"gap under {MIN_BETTABLE_GAP_KS} K")
    return "PASS / NO BET", "; ".join(notes) if notes else "Does not clear strict win filter"

def build_signal(proj, line, fair_prob, ev, ppb, score):
    if line is None:
        return "PASS — NO REAL LINE", "pass"
    gap = abs(proj - line)
    side = "OVER" if proj > line else "UNDER"
    ppb = safe_float(ppb, 4.0) or 4.0

    if (
        fair_prob is not None and fair_prob >= 0.68
        and gap >= 1.15
        and ev is not None and ev >= 0.08
        and score >= 92
        and ppb < 4.05
    ):
        return f"🔥 ELITE WATCH {side}", "good"

    if (
        fair_prob is not None and fair_prob >= 0.64
        and gap >= 1.00
        and ev is not None and ev >= 0.06
        and score >= 88
        and ppb < 4.10
    ):
        return f"✅ STRONG WATCH {side}", "good"

    return f"PASS — {side}", "pass"



def bullpen_workload_bf_factor(team_id, as_of_date=None):
    """Backward-compatible wrapper for the newer real recent bullpen fatigue model."""
    return bullpen_fatigue_bf_factor(team_id, as_of_date or california_now().strftime("%Y-%m-%d"))[:2]

# =========================
# PROJECTION ENGINE
# =========================
def make_projection(row, bankroll, default_odds, use_statcast, use_pitch_type, use_calibration, use_bayesian_markov=True, use_weather=True, use_umpire=True, use_xgboost_assist=False, use_sgo=False, use_optic=False):
    pid = row["pitcher_id"]
    pitcher_name = row["pitcher"]
    hand = row["hand"]

    profile = get_pitcher_profile(pid)
    recent_rows = get_recent_logs(pid)
    leash = build_leash_model(recent_rows)

    lineup_k, lineup_rows, lineup_msg, lineup_locked = calculate_lineup_k_rate(row["game_pk"], row["opp_side"], hand)
    if lineup_k is None:
        lineup_k, fallback_msg = team_k_vs_hand(row["opp_team_id"], hand)
        lineup_rows = []
        lineup_msg = fallback_msg
        lineup_locked = False

    proj_source_label = projection_source_label(lineup_msg, lineup_locked, lineup_rows)
    lineup_status_label = confirmed_lineup_status(proj_source_label, lineup_rows)

    pitcher_k, pitcher_k_source, learn_scale = blend_pitcher_k_rate(profile["Pitcher K%"], recent_rows, pid)
    elite_factor, elite_note = elite_pitcher_boost_factor(pitcher_k)
    pitcher_k = clamp(pitcher_k * elite_factor, 0.08, 0.50)

    statcast_profile = get_statcast_pitch_profile(pid, days=365)
    pitcher_k, statcast_note = apply_statcast_csw_adjustment(pitcher_k, statcast_profile, enabled=use_statcast)

    # v9.6 upgrade: prefer true batter-vs-pitch-type matchup when lineup is available.
    matchup_profile = build_pitch_type_matchup_profile(
        statcast_profile,
        lineup_rows if lineup_locked else [],
        enabled=use_pitch_type,
        min_batters=5,
        pitcher_hand=hand,
    )
    if matchup_profile.get("available"):
        pitcher_k, pitch_type_note = apply_advanced_pitch_type_matchup_adjustment(pitcher_k, matchup_profile, enabled=use_pitch_type)
        pitch_type_available = True
        pitch_type_rows = matchup_profile.get("rows", [])
        pitch_type_factor = safe_float(matchup_profile.get("factor"), 1.0) or 1.0
    else:
        # fallback to pitcher-only whiff mix when batter Statcast profiles are thin or lineup is not posted
        pitcher_k, pitch_type_note, pitch_type_available, pitch_type_rows, pitch_type_factor = apply_pitch_type_matchup_adjustment(pitcher_k, statcast_profile, enabled=use_pitch_type)
        if not pitch_type_available:
            pitch_type_note = matchup_profile.get("message", pitch_type_note)

    batter_pitch_profile_rows = matchup_profile.get("batter_rows", []) if isinstance(matchup_profile, dict) else []

    # v11.4 run-damage / game-script risk
    try:
        pitcher_damage_profile = pitcher_run_damage_profile(pid, recent_rows=recent_rows, statcast_profile=statcast_profile)
        opponent_damage_profile = opponent_contact_damage_profile(batter_pitch_profile_rows if "batter_pitch_profile_rows" in locals() else [])
        game_script_risk = combined_game_script_risk(pitcher_damage_profile, opponent_damage_profile)
        leash["expected_bf"] = apply_game_script_bf_cut(leash.get("expected_bf"), game_script_risk)
        leash["run_damage_risk_level"] = game_script_risk.get("label", "UNKNOWN")
        leash["run_damage_factor"] = game_script_risk.get("factor", 1.0)
        leash["run_damage_volatility_penalty"] = game_script_risk.get("volatility_penalty", 0.0)
        game_script_note = f"{game_script_risk.get('label')} | factor {game_script_risk.get('factor'):.2f} | vol {game_script_risk.get('volatility_penalty',0):.0%} | {game_script_risk.get('notes')}"
    except Exception as _gs_e:
        pitcher_damage_profile = {"risk_level": "UNKNOWN", "risk_score": 0, "notes": [str(_gs_e)]}
        opponent_damage_profile = {"risk_level": "UNKNOWN", "risk_score": 0, "notes": []}
        game_script_risk = {"label": "UNKNOWN", "factor": 1.0, "score": 0, "notes": f"Game-script risk skipped: {_gs_e}"}
        game_script_note = game_script_risk.get("notes")

    # v11.9 manager hook / TTTO volume upgrade. Applied after base leash and
    # game-script risk, before bullpen factor, so final BF still respects bullpen context.
    try:
        hooked_bf, manager_hook_status, manager_hook_note = apply_managerial_hook_v11_9(leash.get("expected_bf"), recent_rows)
        # LIGHT TRUE LEASH + BF: opportunity-volume overlay only, keeps K skill untouched.
        expected_bf, light_true_leash_info = light_true_leash_bf_engine(expected_bf, recent_rows, row if "row" in locals() else locals().get("p", {}))
        # LIGHT BULLPEN TAX: final leash/BF-only nudge; K skill remains untouched.
        expected_bf, light_bullpen_tax_info = apply_light_bullpen_tax_to_bf(expected_bf, row if "row" in locals() else locals().get("p", {}))
        if isinstance(locals().get("row", None), dict):
            row["light_true_leash_bf"] = round(float(expected_bf), 2)
            row["light_true_leash_label"] = light_true_leash_info.get("label")
            row["light_true_leash_score"] = light_true_leash_info.get("score")
            row["light_true_leash_factor"] = light_true_leash_info.get("factor")
            row["light_true_leash_note"] = light_true_leash_info.get("note")
            row["light_true_leash_flags"] = " | ".join(light_true_leash_info.get("flags") or [])
        leash["expected_bf"] = hooked_bf
        leash["manager_hook_status"] = manager_hook_status
        leash["manager_hook_note"] = manager_hook_note
    except Exception as _hook_e:
        manager_hook_status = "UNKNOWN"
        manager_hook_note = f"Manager hook skipped: {_hook_e}"
        leash["manager_hook_status"] = manager_hook_status
        leash["manager_hook_note"] = manager_hook_note

    # v11.6 repeat opponent familiarity
    try:
        repeat_matchup_profile = pitcher_recent_opponent_familiarity(
            pid,
            opponent_team_name=row.get("opponent", row.get("opp_team", "")) if isinstance(row, dict) else "",
            opponent_abbrev=row.get("opponent", "") if isinstance(row, dict) else "",
            lookback_days=REPEAT_MATCHUP_LOOKBACK_DAYS,
        )
    except Exception as _rep_e:
        repeat_matchup_profile = {"available": False, "factor": 1.0, "label": "UNKNOWN", "note": f"Repeat matchup skipped: {_rep_e}"}
    repeat_matchup_note = repeat_matchup_profile.get("note", "Repeat matchup neutral")

    calibration_profile = build_model_calibration_profile(load_json(RESULT_LOG, []))
    pitcher_k, calibration_note = apply_calibration_adjustment(pitcher_k, calibration_profile, enabled=use_calibration)

    matchup_k = calculate_log5_k_rate(pitcher_k, lineup_k)
    opp_context_factor, opp_context_note = opponent_k_context_factor(lineup_k)
    matchup_k = clamp(matchup_k * opp_context_factor, 0.03, 0.60)
    ump_mult, ump_name, umpire_note = umpire_factor(row["game_pk"], enabled=use_umpire)
    try:
        ump_learn_mult, ump_learn_note, ump_learn_key = umpire_learning_k_factor(ump_name) if use_umpire else (1.0, "Umpire learning off", None)
        ump_mult = float(clamp(ump_mult * ump_learn_mult, UMPIRE_FACTOR_MIN - UMPIRE_LEARN_MAX_K_ADJ, UMPIRE_FACTOR_MAX + UMPIRE_LEARN_MAX_K_ADJ))
        umpire_note = f"{umpire_note}; {ump_learn_note}"
    except Exception as _ump_learn_e:
        ump_learn_mult, ump_learn_key = 1.0, None
        umpire_note = f"{umpire_note}; umpire learning skipped: {_ump_learn_e}"
    park = park_k_factor(row.get("venue"))
    weather_mult, weather_note, weather_details = weather_k_factor(row.get("venue"), row.get("game_time"), enabled=use_weather)
    env_mult = float(clamp(park * ump_mult * weather_mult, 0.94, 1.06))

    bf = leash["expected_bf"]
    bullpen_factor, bullpen_note, bullpen_usage = bullpen_fatigue_bf_factor(row.get("team_id"), row.get("date"))
    try:
        bullpen_learn_factor, bullpen_learn_note, bullpen_learn_key = bullpen_learning_bf_factor(bullpen_usage)
        bullpen_factor = float(clamp(bullpen_factor * bullpen_learn_factor, 0.94, 1.06))
        bullpen_note = f"{bullpen_note}; {bullpen_learn_note}"
    except Exception as _bp_learn_e:
        bullpen_learn_factor, bullpen_learn_key = 1.0, None
        bullpen_note = f"{bullpen_note}; bullpen learning skipped: {_bp_learn_e}"
    bf = float(clamp(bf * bullpen_factor, 14, 31))
    batter_rates, simulation_source = build_pa_sequence(lineup_rows if lineup_locked else [], bf, lineup_k)

    # v10.7: safer Bayesian + Markov Monte Carlo built around expected BF, not generic 27 outs.
    preliminary_score = data_lock_score(
        lineup_locked=lineup_locked,
        pitcher_confirmed=row.get("pitcher_confirmed"),
        active_line=None,
        consensus_info={"count": 0, "spread": None},
        ppb=leash["ppb"],
        statcast_available=statcast_profile.get("available"),
        pitch_type_available=pitch_type_available,
    )
    if use_bayesian_markov:
        sims, pa_probs, bayesian_markov_note = simulate_bayesian_markov_matchup(
            matchup_k,
            batter_rates,
            expected_bf=bf,
            park=env_mult,
            ump=1.0,
            data_score=preliminary_score,
            lineup_locked=lineup_locked,
            pitcher_confirmed=row.get("pitcher_confirmed"),
            leash=leash,
            sims=BAYESIAN_MARKOV_SIMS,
        )
        simulation_source = simulation_source + " + Bayesian Markov MC"
    else:
        sims, pa_probs = simulate_matchup(matchup_k, batter_rates, park=env_mult, ump=1.0, sims=12000)
        bayesian_markov_note = "Standard Monte Carlo"

    mean = float(np.mean(sims))

    # v10.7 optional XGBoost residual assist. Capped and OFF by default.
    xgb_current_features = xgb_feature_row_from_picklike({
        "projection": mean,
        "pitcher_k": pitcher_k,
        "opp_k": lineup_k,
        "expected_bf": bf,
        "ppb": leash["ppb"],
        "recent_ip": leash["recent_ip"],
        "data_score": preliminary_score,
        "lineup_locked": lineup_locked,
        "pitcher_confirmed": row.get("pitcher_confirmed"),
        "statcast_available": statcast_profile.get("available"),
        "statcast_csw": None if statcast_profile.get("csw") is None else statcast_profile.get("csw") * 100,
        "statcast_whiff": None if statcast_profile.get("whiff") is None else statcast_profile.get("whiff") * 100,
        "pitch_type_matchup_available": pitch_type_available,
        "pitch_type_factor": pitch_type_factor,
        "consensus_count": 0,
        "consensus_spread": 0,
    })
    adjusted_mean, xgb_info = apply_xgboost_assist(xgb_current_features, mean, enabled=use_xgboost_assist)
    if xgb_info.get("active"):
        delta = adjusted_mean - mean
        sims = np.clip(sims + delta, 0, None)
        mean = float(np.mean(sims))

    median = float(np.median(sims))
    p10 = float(np.percentile(sims, 10))
    p90 = float(np.percentile(sims, 90))

    sportsbook_data = get_sportsbook_k_data(row["home_team"], row["away_team"], pitcher_name)
    pp_data = get_prizepicks_k_data(pitcher_name)
    ud_data = get_underdog_k_data(pitcher_name)
    sgo_data = get_sportsgameodds_k_data(pitcher_name) if use_sgo else source_result("SportsGameOdds", "OFF", message="Optional source turned off")
    optic_data = get_opticodds_k_data(pitcher_name) if use_optic else source_result("OpticOdds", "OFF", message="Optional source turned off")

    active_line, active_source, consensus = choose_active_line(sportsbook_data, pp_data, ud_data, sgo_data, optic_data)

    # v11.8 TRUE CALIBRATION ENGINE:
    # Uses only graded official snapshots. It shifts projection slightly by proven bias buckets,
    # then probability calibration later corrects overconfidence/noise.
    pre_calibration_mean = float(mean)
    pre_calibration_p10 = float(p10)
    pre_calibration_p90 = float(p90)
    calibration_context_pre = current_calibration_context(
        row, mean, active_line, active_source, fair_probability=None,
        price_is_real=False, score=preliminary_score, risk_label=None, p10=p10, p90=p90
    )
    mean, sims, true_projection_calibration = apply_true_projection_calibration(
        mean, sims, calibration_context_pre, calibration_profile, enabled=use_calibration
    )
    if true_projection_calibration.get("active"):
        median = float(np.median(sims))
        p10 = float(np.percentile(sims, 10))
        p90 = float(np.percentile(sims, 90))

    # NOTE: CLV/line tracking updates on refresh because it tracks market movement.
    # Official pick history is only saved when you press "SAVE OFFICIAL BEFORE-GAME SNAPSHOT".
    line_delta = update_clv_snapshot(pitcher_name, active_source, active_line) if active_line is not None else None
    true_line_delta = track_line_delta(pitcher_name, active_source, active_line) if active_line is not None else None

    metrics = calculate_pick_metrics(sims, active_line)

    score = data_lock_score(
        lineup_locked=lineup_locked,
        pitcher_confirmed=row.get("pitcher_confirmed"),
        active_line=active_line,
        consensus_info=consensus,
        ppb=leash["ppb"],
        statcast_available=statcast_profile.get("available"),
        pitch_type_available=pitch_type_available
    )

    over_prob_raw = metrics.get("over_prob")
    over_prob = shrink_probability_to_market(over_prob_raw, score, lineup_locked, row.get("pitcher_confirmed")) if over_prob_raw is not None else None
    under_prob = 1 - over_prob if over_prob is not None else None

    if active_line is None:
        pick_side = "NO LINE"
        fair_prob = None
        fair_prob_raw_after_market = None
        true_probability_calibration = {"active": False, "shift": 0.0, "note": "No line/probability to calibrate"}
        price = None
        price_is_real = False
        price_source = "NO LINE"
        no_vig = None
        ev = None
        kelly = 0.0
        edge_pct = None
        gap = None
        final_decision = {"model_side": pick_side, "bet_action": "🚫 PASS", "action_tier": "PASS", "fair_probability": None, "decision_note": "No real line", "elite_upside_score": 0, "over_needed": None}
    else:
        # v11.15 audit fix: choose the priced/model side from discrete probability,
        # not from decimal mean alone. This keeps side, price lookup, EV, and final
        # decision aligned around 4.5/5.5/6.5 key lines.
        if over_prob is not None and under_prob is not None:
            pick_side = "OVER" if over_prob >= under_prob else "UNDER"
        else:
            pick_side = "OVER" if mean > active_line else "UNDER"
        fair_prob = over_prob if pick_side == "OVER" else under_prob

        # Price handling fix:
        # - If a real sportsbook/odds source has a matching side+line, use it.
        # - If not, keep a clearly labeled estimated EV using the sidebar default odds.
        #   This avoids silently presenting default -110 as a real market price.
        price = None
        price_is_real = False
        price_source = "NO REAL PRICE"
        priced_rows = []
        for src in [sportsbook_data, sgo_data, optic_data]:
            priced_rows.extend(src.get("rows", []))
        matching_priced = []
        for r in priced_rows:
            if safe_float(r.get("Line")) == safe_float(active_line) and pick_side in str(r.get("Side", "")).upper():
                if safe_float(r.get("Price")) is not None:
                    matching_priced.append(r)
        if matching_priced:
            best = sorted(matching_priced, key=lambda x: expected_value(fair_prob, x.get("Price")) or -999)[-1]
            price = safe_float(best.get("Price"))
            price_is_real = True
            price_source = str(best.get("Source") or best.get("Provider") or "Real sportsbook price")
            no_vig = paired_no_vig_probability(priced_rows, best)
        else:
            # Underdog/PrizePicks style entries often have a real line but no American odds.
            # Use this only as an estimate for sorting/visibility, not as a real price.
            price = safe_float(default_odds, -110.0) or -110.0
            price_source = "ESTIMATED FROM DEFAULT ODDS"
            no_vig = american_to_implied(price)

        true_prob_context = current_calibration_context(
            row, mean, active_line, active_source, fair_probability=fair_prob,
            price_is_real=price_is_real, score=score, risk_label=None, p10=p10, p90=p90
        )
        fair_prob_raw_after_market = fair_prob
        fair_prob, true_probability_calibration = apply_true_probability_calibration(
            fair_prob, true_prob_context, calibration_profile, enabled=use_calibration
        )
        if pick_side == "OVER":
            over_prob = fair_prob
            under_prob = 1 - fair_prob if fair_prob is not None else None
        elif pick_side == "UNDER":
            under_prob = fair_prob
            over_prob = 1 - fair_prob if fair_prob is not None else None

        gap = abs(mean - active_line)
        # v11.14: centralized final decision layer. This may change the model side
        # by probability, and it separates BET / LEAN / PASS.
        provisional_ev = expected_value(fair_prob, price)
        final_decision = final_pick_decision(
            projection=mean,
            line=active_line,
            over_prob=over_prob,
            under_prob=under_prob,
            edge_abs=gap,
            data_score=score,
            ev=provisional_ev,
            pitcher_k=pitcher_k,
            lineup_k=lineup_k,
            expected_bf=bf,
            ppb=leash.get("ppb"),
            p90=p90,
            recent_ks=leash.get("last_10_ks"),
            run_damage_level=leash.get("run_damage_risk_level") or (pitcher_damage_profile.get("risk_level") if isinstance(pitcher_damage_profile, dict) else None),
            leash_risk=leash.get("leash_risk"),
            lineup_locked=lineup_locked,
            pitcher_confirmed=row.get("pitcher_confirmed"),
        )
        pick_side = final_decision.get("model_side") or pick_side
        fair_prob = final_decision.get("fair_probability") if final_decision.get("fair_probability") is not None else fair_prob
        if pick_side == "OVER":
            over_prob = fair_prob
            under_prob = 1 - fair_prob if fair_prob is not None else under_prob
        elif pick_side == "UNDER":
            under_prob = fair_prob
            over_prob = 1 - fair_prob if fair_prob is not None else over_prob

        ev = expected_value(fair_prob, price)
        raw_kelly = kelly_fraction(fair_prob, price)
        kelly = min(raw_kelly, MAX_RECOMMENDED_KELLY) if raw_kelly is not None else 0.0
        edge_pct = ((fair_prob - no_vig) * 100) if no_vig is not None and fair_prob is not None else None

    risk_label, risk_notes = classify_risk(
        fair_prob,
        score,
        priced=bool(price_is_real or ("underdog" in str(active_source).lower())),
        edge_pct=edge_pct if edge_pct is not None else -999,
        gap=gap if gap is not None else 0,
        line_source=active_source
    )

    signal, signal_type = build_signal(mean, active_line, fair_prob or 0, ev, leash["ppb"], score)

    bettable, no_bet_reasons = no_bet_gate(
        active_line=active_line,
        pick_side=pick_side,
        fair_prob=fair_prob,
        ev=ev,
        gap=gap,
        score=score,
        lineup_locked=lineup_locked,
        pitcher_confirmed=row.get("pitcher_confirmed"),
        line_source=active_source,
        consensus_info=consensus,
        leash=leash,
    )

    if not bettable:
        signal_type = "pass"
        if pick_side in ["OVER", "UNDER"]:
            signal = f"PASS — {pick_side}"
        else:
            signal = "PASS"

        # v11.16 audit fix:
        # A failed hard no-bet gate must always become PASS, even if the
        # softer decision layer originally said LEAN or BET. LEAN is not a bet,
        # but showing LEAN next to hard-fail reasons can confuse the UI.
        if isinstance(final_decision, dict):
            final_decision["bet_action"] = "🚫 PASS"
            final_decision["action_tier"] = "PASS"
            final_decision["decision_note"] = (
                final_decision.get("decision_note", "") + "; blocked by hard no-bet gate"
            ).strip("; ")

        risk_notes = (risk_notes + "; " if risk_notes else "") + "No-bet gate: " + "; ".join(no_bet_reasons)

    # v11.14 visible action label. Only 🔥 BET means official playable.
    if isinstance(final_decision, dict):
        bet_action = final_decision.get("bet_action", "🚫 PASS")
        action_tier = final_decision.get("action_tier", "PASS")
        final_decision_note = final_decision.get("decision_note", "")
        if action_tier == "BET":
            signal_type = "good"
            signal = bet_action
        elif action_tier == "LEAN":
            signal_type = "lean"
            signal = bet_action
        else:
            signal_type = "pass"
            signal = bet_action
    else:
        bet_action = "🚫 PASS"
        action_tier = "PASS"
        final_decision_note = "Final decision unavailable"

    if active_line is not None and not price_is_real:
        risk_notes = (risk_notes + "; " if risk_notes else "") + "EV/odds are estimated from sidebar default odds, not a real sportsbook price"

    # Add transparent calibration notes to the card/debug output.
    if true_projection_calibration.get("note"):
        risk_notes = (risk_notes + "; " if risk_notes else "") + true_projection_calibration.get("note")
    if true_probability_calibration.get("note"):
        risk_notes = (risk_notes + "; " if risk_notes else "") + true_probability_calibration.get("note")
    if isinstance(game_script_risk, dict) and game_script_risk.get("label") in ["MILD", "HIGH", "EXTREME"]:
        risk_notes = (risk_notes + "; " if risk_notes else "") + "Run Damage Engine: " + str(game_script_note)
    if final_decision_note:
        risk_notes = (risk_notes + "; " if risk_notes else "") + "Final Decision: " + str(final_decision_note)

    prop_rows = []
    for src in [sportsbook_data, pp_data, ud_data, sgo_data, optic_data]:
        for r in src.get("rows", []):
            rr = dict(r)
            rr["Model Projection"] = round(mean, 2)
            line = safe_float(rr.get("Line"))
            if line is not None:
                raw_p = poisson_over_probability(mean, line)
                cal_p = shrink_probability_to_market(raw_p, score, lineup_locked, row.get("pitcher_confirmed"))
                lean = "OVER" if mean > line else "UNDER"
                lean_prob = cal_p if lean == "OVER" else 1 - cal_p
                rr["Model Lean"] = lean
                rr["Model Action"] = bet_action if 'bet_action' in locals() else "🚫 PASS"
                rr["Final Action Tier"] = action_tier if 'action_tier' in locals() else "PASS"
                rr["Raw Model Prob %"] = round((raw_p if lean == "OVER" else 1 - raw_p) * 100, 1)
                rr["Model Prob %"] = round(lean_prob * 100, 1)
                rr["Hit Risk"], rr["Risk Notes"] = classify_risk(
                    lean_prob,
                    score,
                    priced=safe_float(rr.get("Price")) is not None,
                    edge_pct=0,
                    gap=abs(mean - line),
                    line_source=rr.get("Source")
                )
            rr["All Real"] = "YES"
            rr["Projection Source"] = proj_source_label
            rr["Lineup Status"] = lineup_status_label
            rr["Bullpen Status"] = bullpen_usage.get("label") if isinstance(bullpen_usage, dict) else None
            rr["Bullpen Pitches"] = bullpen_usage.get("bullpen_pitches") if isinstance(bullpen_usage, dict) else None
            rr["Bullpen IP"] = bullpen_usage.get("bullpen_ip") if isinstance(bullpen_usage, dict) else None
            rr["Bullpen Fatigue Factor"] = round(safe_float(bullpen_factor, 1.0), 3)
            rr["Bullpen Fatigue Note"] = bullpen_note
            rr["Game Script Risk"] = game_script_risk.get("label", "UNKNOWN") if "game_script_risk" in locals() else "UNKNOWN"
            rr["Game Script Note"] = game_script_note if "game_script_note" in locals() else ""
            rr["Manager Hook"] = leash.get("manager_hook_status")
            rr["Manager Hook Note"] = leash.get("manager_hook_note")
            rr["Repeat Matchup"] = repeat_matchup_profile.get("label", "NEUTRAL") if "repeat_matchup_profile" in locals() else "NEUTRAL"
            rr["Repeat Matchup Note"] = repeat_matchup_note if "repeat_matchup_note" in locals() else (repeat_matchup_profile.get("note", "") if "repeat_matchup_profile" in locals() else "")
            rr["Run Damage Risk"] = pitcher_damage_profile.get("risk_level", "UNKNOWN") if "pitcher_damage_profile" in locals() else "UNKNOWN"
            rr["Run Damage Score"] = pitcher_damage_profile.get("risk_score") if "pitcher_damage_profile" in locals() else None
            rr["Run Damage BF Factor"] = pitcher_damage_profile.get("bf_factor") if "pitcher_damage_profile" in locals() else None
            rr["Run Damage Vol Penalty"] = pitcher_damage_profile.get("volatility_penalty") if "pitcher_damage_profile" in locals() else None
            rr["Run Damage H9"] = pitcher_damage_profile.get("h9") if "pitcher_damage_profile" in locals() else None
            rr["Run Damage BB9"] = pitcher_damage_profile.get("bb9") if "pitcher_damage_profile" in locals() else None
            rr["Run Damage HR9"] = pitcher_damage_profile.get("hr9") if "pitcher_damage_profile" in locals() else None
            rr["Recent H/R/ER/BB/HR"] = (f"H {pitcher_damage_profile.get('recent_hits_avg')} | R {pitcher_damage_profile.get('recent_runs_avg')} | ER {pitcher_damage_profile.get('recent_er_avg')} | BB {pitcher_damage_profile.get('recent_bb_avg')} | HR {pitcher_damage_profile.get('recent_hr_avg')}") if "pitcher_damage_profile" in locals() else ""
            rr["Opponent Damage Risk"] = opponent_damage_profile.get("risk_level", "UNKNOWN") if "opponent_damage_profile" in locals() else "UNKNOWN"
            rr["Pitch-Type Batter Detail Rows"] = len(batter_pitch_profile_rows) if "batter_pitch_profile_rows" in locals() else 0
            prop_rows.append(rr)

    pick_id = f"{row['date']}_{row['game_pk']}_{pid}_{active_line}_{active_source}"

    return {
        "pick_id": pick_id,
        "created_at": now_iso(),
        "date": row["date"],
        "game_pk": row["game_pk"],
        "game_time": row["game_time"],
        "status": row["status"],
        "venue": row.get("venue"),
        "pitcher_id": str(pid),
        "pitcher": pitcher_name,
        "hand": hand,
        "team": row["team"],
        "opponent": row["opponent"],
        "matchup": row["matchup"],
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "pitcher_confirmed": bool(row.get("pitcher_confirmed")),
        "lineup_locked": bool(lineup_locked),
        "lineup_note": lineup_msg,
        "projection_source": proj_source_label,
        "lineup_status": lineup_status_label,
        "pitcher_k": round(pitcher_k, 3),
        "pitcher_k_source": pitcher_k_source,
        "opp_k": round(lineup_k, 3),
        "simulation_source": simulation_source,
        "bayesian_markov_enabled": bool(use_bayesian_markov),
        "bayesian_markov_note": bayesian_markov_note,
        "xgboost_enabled": bool(use_xgboost_assist),
        "xgboost_active": bool(xgb_info.get("active")),
        "xgboost_samples": int(xgb_info.get("samples", 0)),
        "xgboost_adjustment": safe_float(xgb_info.get("adjustment"), 0.0),
        "xgboost_note": xgb_info.get("message"),
        "umpire": ump_name,
        "ump_factor": round(ump_mult, 3),
        "umpire_learning_factor": round(safe_float(locals().get("ump_learn_mult", 1.0), 1.0), 3),
        "umpire_learning_key": locals().get("ump_learn_key"),
        "umpire_note": umpire_note,
        "weather_enabled": bool(use_weather),
        "weather_factor": round(weather_mult, 3),
        "weather_note": weather_note,
        "weather_temp_f": weather_details.get("temp_f") if isinstance(weather_details, dict) else None,
        "weather_wind_mph": weather_details.get("wind_mph") if isinstance(weather_details, dict) else None,
        "weather_humidity": weather_details.get("humidity") if isinstance(weather_details, dict) else None,
        "weather_precip_prob": weather_details.get("precip_prob") if isinstance(weather_details, dict) else None,
        "environment_factor": round(env_mult, 3),
        "expected_bf": round(bf, 1),
        "ppb": round(leash["ppb"], 2),
        "leash_risk": leash.get("leash_risk"),
        "bullpen_status": bullpen_usage.get("label") if isinstance(bullpen_usage, dict) else None,
        "bullpen_bf_factor": round(safe_float(bullpen_factor, 1.0), 3),
        "bullpen_learning_factor": round(safe_float(locals().get("bullpen_learn_factor", 1.0), 1.0), 3),
        "bullpen_learning_key": locals().get("bullpen_learn_key"),
        "bullpen_note": bullpen_note,
        "game_script_risk": game_script_risk,
        "game_script_note": game_script_note,
        "run_damage_risk_level": pitcher_damage_profile.get("risk_level", "UNKNOWN") if isinstance(pitcher_damage_profile, dict) else "UNKNOWN",
        "run_damage_score": pitcher_damage_profile.get("risk_score") if isinstance(pitcher_damage_profile, dict) else None,
        "run_damage_bf_factor": pitcher_damage_profile.get("bf_factor") if isinstance(pitcher_damage_profile, dict) else None,
        "run_damage_volatility_penalty": pitcher_damage_profile.get("volatility_penalty") if isinstance(pitcher_damage_profile, dict) else None,
        "run_damage_h9": pitcher_damage_profile.get("h9") if isinstance(pitcher_damage_profile, dict) else None,
        "run_damage_bb9": pitcher_damage_profile.get("bb9") if isinstance(pitcher_damage_profile, dict) else None,
        "run_damage_hr9": pitcher_damage_profile.get("hr9") if isinstance(pitcher_damage_profile, dict) else None,
        "recent_hits_avg": pitcher_damage_profile.get("recent_hits_avg") if isinstance(pitcher_damage_profile, dict) else None,
        "recent_runs_avg": pitcher_damage_profile.get("recent_runs_avg") if isinstance(pitcher_damage_profile, dict) else None,
        "recent_er_avg": pitcher_damage_profile.get("recent_er_avg") if isinstance(pitcher_damage_profile, dict) else None,
        "recent_bb_avg": pitcher_damage_profile.get("recent_bb_avg") if isinstance(pitcher_damage_profile, dict) else None,
        "recent_hr_avg": pitcher_damage_profile.get("recent_hr_avg") if isinstance(pitcher_damage_profile, dict) else None,
        "repeat_matchup_profile": repeat_matchup_profile,
        "repeat_matchup_note": repeat_matchup_note if "repeat_matchup_note" in locals() else repeat_matchup_profile.get("note", ""),
        "pitcher_damage_profile": pitcher_damage_profile,
        "opponent_damage_profile": opponent_damage_profile,
        "bullpen_recent_games": bullpen_usage.get("games") if isinstance(bullpen_usage, dict) else None,
        "bullpen_recent_ip": bullpen_usage.get("bullpen_ip") if isinstance(bullpen_usage, dict) else None,
        "bullpen_recent_pitches": bullpen_usage.get("bullpen_pitches") if isinstance(bullpen_usage, dict) else None,
        "bullpen_recent_appearances": bullpen_usage.get("appearances") if isinstance(bullpen_usage, dict) else None,
        "bullpen_back_to_back_relievers": bullpen_usage.get("back_to_back_relief_appearances") if isinstance(bullpen_usage, dict) else None,
        "recent_ip": round(leash["recent_ip"], 2),
        "last_10_ks": leash["last_10_ks"],
        "projection": round(mean, 2),
        "pre_calibration_projection": round(pre_calibration_mean, 2),
        "calibration_projection_shift": round(mean - pre_calibration_mean, 3),
        "median": round(median, 2),
        "p10": round(p10, 2),
        "p90": round(p90, 2),
        "pre_calibration_p10": round(pre_calibration_p10, 2),
        "pre_calibration_p90": round(pre_calibration_p90, 2),
        "learning_scale": round(learn_scale, 3),
        "line": active_line,
        "line_source": active_source,
        "underdog_status": ud_data.get("status"),
        "underdog_line": ud_data.get("line"),
        "underdog_message": ud_data.get("message"),
        "line_delta": line_delta,
        "true_line_delta": true_line_delta,
        "consensus_count": consensus.get("count"),
        "consensus_quality": consensus.get("quality"),
        "consensus_spread": consensus.get("spread"),
        "leash_risk": leash.get("leash_risk"),
        "bettable": bettable,
        "no_bet_reasons": no_bet_reasons,
        "odds": price,
        "price_is_real": bool(price_is_real),
        "price_source": price_source,
        "bet_action": bet_action if 'bet_action' in locals() else "🚫 PASS",
        "action_tier": action_tier if 'action_tier' in locals() else "PASS",
        "final_decision_note": final_decision_note if 'final_decision_note' in locals() else "",
        "elite_upside_score": final_decision.get("elite_upside_score") if isinstance(final_decision, dict) else None,
        "over_needed": final_decision.get("over_needed") if isinstance(final_decision, dict) else None,
        "pick_side": pick_side,
        "over_probability": None if over_prob is None else round(over_prob, 4),
        "under_probability": None if under_prob is None else round(under_prob, 4),
        "fair_probability": None if fair_prob is None else round(fair_prob, 4),
        "pre_calibration_fair_probability": None if fair_prob_raw_after_market is None else round(fair_prob_raw_after_market, 4),
        "calibration_probability_shift": None if fair_prob_raw_after_market is None or fair_prob is None else round(fair_prob - fair_prob_raw_after_market, 4),
        "edge_ks": None if active_line is None else round(mean - active_line, 2),
        "abs_edge": None if active_line is None else round(abs(mean - active_line), 2),
        "edge_pct": None if edge_pct is None else round(edge_pct, 2),
        "ev": None if ev is None else round(ev, 4),
        "kelly": round(kelly, 4),
        # v11.15 audit fix: only official BET actions receive a stake.
        # LEAN and PASS are informational only and must display $0.
        "bet_size": round(bankroll * kelly, 2) if (locals().get("action_tier") == "BET" and locals().get("bettable", False)) else 0.0,
        "data_score": score,
        "risk_label": risk_label,
        "risk_notes": risk_notes,
        "signal": signal,
        "signal_type": signal_type,
        "graded": False,
        "actual": None,
        "win": None,
        "statcast_available": statcast_profile.get("available"),
        "statcast_rows": statcast_profile.get("rows"),
        "statcast_csw": None if statcast_profile.get("csw") is None else round(statcast_profile.get("csw") * 100, 1),
        "statcast_whiff": None if statcast_profile.get("whiff") is None else round(statcast_profile.get("whiff") * 100, 1),
        "statcast_note": statcast_note,
        "pitch_type_matchup_available": pitch_type_available,
        "pitch_type_factor": round(safe_float(pitch_type_factor, 1.0), 3),
        "pitch_type_note": pitch_type_note,
        "calibration_note": calibration_note,
        "true_projection_calibration_note": true_projection_calibration.get("note"),
        "true_projection_calibration_active": bool(true_projection_calibration.get("active")),
        "true_projection_calibration_shift": true_projection_calibration.get("shift"),
        "true_probability_calibration_note": true_probability_calibration.get("note"),
        "true_probability_calibration_active": bool(true_probability_calibration.get("active")),
        "true_probability_calibration_shift": true_probability_calibration.get("shift"),
        "calibration_quality": calibration_profile.get("quality_score"),
        "calibration_samples": calibration_profile.get("samples"),
        "calibration_brier": calibration_profile.get("brier"),
        "prop_rows": prop_rows,
        "lineup_rows": lineup_rows,
        "pitch_type_rows": pitch_type_rows,
        "batter_pitch_profile_rows": batter_pitch_profile_rows,
        "source_status": {
            "sportsbook": sportsbook_data.get("status"),
            "prizepicks": pp_data.get("status"),
            "underdog": ud_data.get("status"),
            "sportsgameodds": sgo_data.get("status"),
            "opticodds": optic_data.get("status"),
        }
    }

def save_many_once(new_picks):
    picks = load_saved_pick_log_normalized()
    ids = set([p.get("pick_id") for p in picks])
    added = 0
    for p in new_picks:
        if p.get("pick_id") not in ids:
            official = dict(p)
            official["official_snapshot_saved_at"] = now_iso()
            official["snapshot_type"] = "OFFICIAL_BEFORE_GAME"
            official["official_quality_gate"] = "PASS" if official.get("data_score", 0) >= MIN_OFFICIAL_SAVE_SCORE else "LOW_DATA_REVIEW"
            picks.append(official)
            log_long_backtest_row(official)
            ids.add(p.get("pick_id"))
            added += 1
    save_json(PICK_LOG, picks[-10000:])
    return added

# =========================
# GRADING
# =========================
def is_game_final(game_pk):
    sched = safe_get_json(f"{MLB_BASE}/schedule", params={"sportId": 1, "gamePk": game_pk})
    try:
        games = (sched.get("dates") or [{}])[0].get("games") or []
        return bool(games and games[0].get("status", {}).get("abstractGameState") == "Final")
    except Exception:
        return False

def get_actual_pitcher_ks(game_pk, pitcher_id):
    box = safe_get_json(f"{MLB_BASE}/game/{game_pk}/boxscore")
    if not box:
        return None
    for side in ["home", "away"]:
        players = box.get("teams", {}).get(side, {}).get("players", {})
        for p in players.values():
            person = p.get("person", {})
            if str(person.get("id")) == str(pitcher_id):
                return p.get("stats", {}).get("pitching", {}).get("strikeOuts", None)
    return None

def grade_finished_games():
    picks = load_saved_pick_log_normalized()
    results = load_json(RESULT_LOG, [])
    result_ids = set([r.get("pick_id") for r in results])
    graded = 0
    for p in picks:
        if p.get("graded"):
            continue
        if not p.get("game_pk") or not p.get("pitcher_id"):
            continue
        if not is_game_final(p["game_pk"]):
            continue
        workload = get_actual_pitcher_workload(p["game_pk"], p["pitcher_id"])
        actual = workload.get("actual") if workload else get_actual_pitcher_ks(p["game_pk"], p["pitcher_id"])
        if actual is None:
            continue
        p["actual"] = actual
        if workload:
            for _wk, _wv in workload.items():
                if _wv is not None:
                    p[_wk] = _wv
        p["graded"] = True
        p["graded_at"] = now_iso()
        line = safe_float(p.get("line"))
        side = p.get("pick_side")
        if line is not None and side in ["OVER", "UNDER"]:
            win = (actual > line) if side == "OVER" else (actual < line)
            p["win"] = bool(win)
            p["graded_result"] = "WIN" if win else "LOSS"
        else:
            p["win"] = None
            p["graded_result"] = "NO LINE"
        p["new_learning_scale"] = round(update_learning(p["pitcher_id"], p.get("projection"), actual), 3)
        update_deep_context_learning_after_grade(p)
        if p.get("pick_id") not in result_ids:
            results.append(dict(p))
            result_ids.add(p.get("pick_id"))
        graded += 1
    save_json(PICK_LOG, picks[-10000:])
    save_json(RESULT_LOG, results[-10000:])
    return graded

def build_signal_tracking():
    results = load_json(RESULT_LOG, [])
    finished = [r for r in results if r.get("graded_result") in ["WIN", "LOSS"]]
    buckets = {}
    def add_bucket(key, row):
        if key not in buckets:
            buckets[key] = {"tag": key, "count": 0, "wins": 0}
        buckets[key]["count"] += 1
        buckets[key]["wins"] += 1 if row.get("graded_result") == "WIN" else 0
    for r in finished:
        tags = [
            f"side={r.get('pick_side')}",
            f"risk={r.get('risk_label')}",
            f"line_source={r.get('line_source')}",
            f"consensus={r.get('consensus_quality')}",
            f"lineup_locked={r.get('lineup_locked')}",
            f"statcast={r.get('statcast_available')}",
            f"pitch_type={r.get('pitch_type_matchup_available')}",
            f"data_score={int((r.get('data_score') or 0)//10)*10}s",
        ]
        for tag in tags:
            add_bucket(tag, r)
    rows = []
    for v in buckets.values():
        count = v["count"]
        wins = v["wins"]
        rows.append({"Signal Tag": v["tag"], "Samples": count, "Wins": wins, "Win Rate": round(wins / count * 100, 1) if count else 0})
    df = pd.DataFrame(rows).sort_values(["Samples", "Win Rate"], ascending=[False, False]) if rows else pd.DataFrame()
    save_json(SIGNAL_TRACKING_FILE, rows)
    return df

# =========================
# RENDERING
# =========================
def render_kpis(picks, bankroll):
    valid = [p for p in picks if p.get("ev") is not None]
    best = sorted(valid, key=lambda x: x.get("ev", -999), reverse=True)[0] if valid else None
    real_line_count = len([p for p in picks if p.get("line") is not None])
    strong_count = len([p for p in picks if p.get("signal_type") == "good"])
    no_line_count = len([p for p in picks if p.get("line") is None])
    statcast_count = len([p for p in picks if p.get("statcast_available")])
    pitch_type_count = len([p for p in picks if p.get("pitch_type_matchup_available")])
    st.markdown(f"""
    <div class="kpi-strip">
      <div class="kpi-box"><div class="kpi-label">Board Rows</div><div class="kpi-value">{len(picks)}</div><div class="kpi-sub">Current screen</div></div>
      <div class="kpi-box"><div class="kpi-label">Real Lines</div><div class="kpi-value green">{real_line_count}</div><div class="kpi-sub">No fake prop lines</div></div>
      <div class="kpi-box"><div class="kpi-label">No Line</div><div class="kpi-value orange">{no_line_count}</div><div class="kpi-sub">Projection only</div></div>
      <div class="kpi-box"><div class="kpi-label">Strong Signals</div><div class="kpi-value green">{strong_count}</div><div class="kpi-sub">Strict gates</div></div>
      <div class="kpi-box"><div class="kpi-label">Statcast</div><div class="kpi-value">{statcast_count}/{len(picks)}</div><div class="kpi-sub">Pitch-type {pitch_type_count}</div></div>
      <div class="kpi-box"><div class="kpi-label">Bankroll</div><div class="kpi-value green">${bankroll:,.0f}</div><div class="kpi-sub">{california_now().strftime('%I:%M %p PT')}</div></div>
    </div>
    """, unsafe_allow_html=True)
    if best:
        st.markdown(f"""
        <div class="green-card">
          <div class="small-muted">Best EV Play On Current Board</div>
          <div class="big-number green">{best.get('signal')}</div>
          <div>{best.get('pitcher')} — {best.get('pick_side')} {best.get('line')} Ks | EV {round((best.get('ev') or 0)*100,2)}% | Data {best.get('data_score')}/100</div>
        </div>
        """, unsafe_allow_html=True)

def render_pick_card(p):
    prob = p.get("fair_probability")
    prob_pct = int(round(prob * 100)) if prob is not None else 0
    progress_width = max(3, min(100, prob_pct))
    risk = p.get("risk_label", "")
    signal_type = p.get("signal_type", "pass")
    if "85" in risk or signal_type == "good":
        color_class, progress_class, badge = "green", "progress-green", "good-badge"
    elif "PASS" in risk or "NO" in risk:
        color_class, progress_class, badge = "red", "progress-red", "red-badge"
    else:
        color_class, progress_class, badge = "orange", "progress-orange", "yellow-badge"
    line_display = f"{safe_float(p.get('line')):.1f}" if p.get('line') is not None else "NO REAL LINE"
    edge_display = p.get("edge_ks") if p.get("edge_ks") is not None else "—"
    ev_display = f"{(p.get('ev') or 0)*100:.2f}%" if p.get("ev") is not None else "—"
    prob_display = f"{prob_pct}%" if prob is not None else "—"
    # Render-safe Last 10 K bars.
    # NOTE: this avoids standalone raw HTML ever being printed by Streamlit/tunnel caching.
    # The full card below is still rendered with unsafe_allow_html=True.
    bars = "<span class='small-muted'>No recent K log</span>"
    last_ks = p.get("last_10_ks", []) or []
    if last_ks:
        max_k = max(max([safe_int(x, 0) or 0 for x in last_ks]), 1)
        bar_parts = []
        for k_raw in last_ks[:10]:
            k = safe_int(k_raw, 0) or 0
            h = int(20 + (k / max_k) * 42)
            bar_parts.append(
                f"<span class='mini-k-bar-wrap'>"
                f"<span class='mini-k-bar' style='height:{h}px;'></span>"
                f"<span class='mini-k-label'>{k}</span>"
                f"</span>"
            )
        bars = "<div class='mini-k-bars'>" + "".join(bar_parts) + "</div>"
    statcast_txt = "YES" if p.get("statcast_available") else "NO"
    pitch_type_txt = "YES" if p.get("pitch_type_matchup_available") else "NO"
    st.markdown(f"""
    <div class="pick-card">
      <div style="display:grid;grid-template-columns:1.3fr .8fr .9fr 1fr 1fr;gap:18px;align-items:center;">
        <div>
          <div class="player-name">{p.get('pitcher')}</div>
          <div class="small-muted">{p.get('matchup')} | {p.get('hand')}HP</div>
          <div class="small-muted">{p.get('team')} vs {p.get('opponent')}</div>
          <span class="badge {badge}">{p.get('risk_label')}</span>
          <span class="badge">{p.get('line_source')}</span>
          <span class="badge good-badge">{p.get('projection_source')}</span>
          <span class="badge">Lineup: {p.get('lineup_status')}</span>
        </div>
        <div><div class="small-muted">Projection</div><div class="big-number {color_class}">{p.get('projection')}</div><div class="small-muted">BF {p.get('expected_bf')} | PPB {p.get('ppb')}</div></div>
        <div><div class="small-muted">Line</div><div class="big-number">{line_display}</div><div class="small-muted">Edge: {edge_display} K</div></div>
        <div>
          <div class="small-muted">Model Side</div><div class="big-number {color_class}">{p.get('pick_side')}</div>
          <div class="small-muted">Final Action</div><div class="{color_class}" style="font-size:22px;font-weight:950;">{p.get('bet_action', '🚫 PASS')}</div>
          <div class="small-muted">Fair Prob</div><div class="{color_class}" style="font-size:26px;font-weight:900;">{prob_display}</div>
          <div class="progress-wrap"><div class="{progress_class}" style="width:{progress_width}%;"></div></div>
        </div>
        <div>
          <div class="small-muted">Signal</div><div class="{color_class}" style="font-size:20px;font-weight:950;">{p.get('signal')}</div>
          <div class="small-muted" style="margin-top:8px;">EV</div><div style="font-size:22px;font-weight:900;">{ev_display}</div>
          <div class="small-muted">Price Source</div><div style="font-size:12px;font-weight:800;">{p.get('price_source')}</div>
          <div class="small-muted">Bet Size</div><div style="font-size:22px;font-weight:900;">${p.get('bet_size')}</div>
        </div>
      </div>
      <div class="hr-soft"></div>
      <div style="display:grid;grid-template-columns:.7fr .7fr .7fr .7fr .7fr .7fr 2.2fr;gap:14px;align-items:end;">
        <div><div class="small-muted">Data Score</div><div style="font-size:22px;font-weight:900;">{p.get('data_score')}/100</div></div>
        <div><div class="small-muted">Pitcher K%</div><div style="font-size:22px;font-weight:900;">{p.get('pitcher_k')}</div></div>
        <div><div class="small-muted">Opp K%</div><div style="font-size:22px;font-weight:900;">{p.get('opp_k')}</div></div>
        <div><div class="small-muted">Statcast</div><div style="font-size:22px;font-weight:900;">{statcast_txt}</div></div>
        <div><div class="small-muted">Pitch-Type</div><div style="font-size:22px;font-weight:900;">{pitch_type_txt}</div></div>
        <div><div class="small-muted">CLV Δ</div><div style="font-size:22px;font-weight:900;">{p.get('line_delta')}</div></div>
        <div><div class="small-muted">Last 10 Ks</div>{bars}</div>
      </div>
      <div class="small-muted" style="margin-top:12px;">Final Decision: {p.get('final_decision_note', '')} | Elite Upside: {p.get('elite_upside_score')} | Over Needs: {p.get('over_needed')}+</div>
      <div class="small-muted" style="margin-top:12px;">Risk Notes: {p.get('risk_notes')}</div>
      <div class="small-muted">Statcast: {p.get('statcast_note')} | Pitch Type: {p.get('pitch_type_note')} | Calibration: {p.get('calibration_note')}</div>
      <div class="small-muted">Projection Source: {p.get('projection_source')} | Lineup Status: {p.get('lineup_status')} | Lineup Note: {p.get('lineup_note')}</div>
      <div class="small-muted">Repeat Matchup: {p.get("repeat_matchup_note", "Neutral")}\nBullpen Fatigue: {p.get('bullpen_status')} | factor {p.get('bullpen_bf_factor')} | {p.get('bullpen_recent_pitches')} pitches / {p.get('bullpen_recent_ip')} IP | {p.get('bullpen_note')}</div>
      <div class="small-muted">Weather: {p.get('weather_note')} | Umpire: {p.get('umpire_note')}</div>
      <div class="small-muted">Advanced Sim: {p.get('bayesian_markov_note')} | XGBoost: {p.get('xgboost_note')}</div>
    </div>
    """, unsafe_allow_html=True)




# =========================
# MULTI-PROP PITCHER TABS
# UI/projection extension only. Does NOT change strikeout math.
# =========================
MULTI_PROP_TABS_ENABLED = True

def _mp_avg(rows, key, n=5, default=None):
    vals=[]
    for r in (rows or [])[:n]:
        if isinstance(r, dict):
            v=safe_float(r.get(key))
            if v is not None:
                vals.append(v)
    return float(np.mean(vals)) if vals else default

def _mp_expected_bf(row):
    for k in ["Exp BF","expected_bf","Expected BF","BF Projection"]:
        v=safe_float((row or {}).get(k))
        if v is not None:
            return float(clamp(v, 10, 34))
    rr=(row or {}).get("recent_rows") or (row or {}).get("Recent Rows") or []
    return float(clamp(_mp_avg(rr,"BF",5,DEFAULT_BF) or DEFAULT_BF, 10, 34))

def _mp_pitcher_rates(pid):
    out={"bb":0.085,"hits":0.230,"er":0.105,"outs_bf":0.72,"source":"fallback"}
    if not pid:
        return out
    data=safe_get_json(f"{MLB_BASE}/people/{pid}/stats", params={"stats":"season","group":"pitching"}, timeout=14)
    try:
        split=get_first_stat_split(data)
        stt=(split or {}).get("stat",{})
        bf=safe_float(stt.get("battersFaced"),0) or 0
        ip=baseball_ip_to_float(stt.get("inningsPitched"))
        if bf>0:
            out["bb"]=clamp((safe_float(stt.get("baseOnBalls"),0) or 0)/bf,0.025,0.180)
            out["hits"]=clamp((safe_float(stt.get("hits"),0) or 0)/bf,0.120,0.360)
            out["er"]=clamp((safe_float(stt.get("earnedRuns"),0) or 0)/bf,0.030,0.210)
        if bf>0 and ip:
            out["outs_bf"]=clamp((ip*3.0)/bf,0.52,0.86)
        out["source"]="season"
    except Exception:
        pass
    return out

def _mp_line(row, keys):
    for k in keys:
        v=safe_float((row or {}).get(k))
        if v is not None:
            return v
    return None

def multi_prop_project_pitcher(row, prop_type):
    row=row or {}
    pid=row.get("pitcher_id") or row.get("Pitcher ID")
    rr=row.get("recent_rows") or row.get("Recent Rows") or []
    ebf=_mp_expected_bf(row)
    try:
        dummy, ebf, _ = apply_pitch_count_trend_overlay(row, 0.0, ebf, rr)
        dummy, ebf, _ = apply_weather_engine_upgrade_overlay(row, 0.0, ebf)
    except Exception:
        pass
    rates=_mp_pitcher_rates(pid)

    if prop_type=="Pitching Outs":
        base=ebf*rates["outs_bf"]
        recent=_mp_avg(rr,"IP_float",5,None)
        recent=recent*3.0 if recent is not None else None
        proj=base*0.62+recent*0.38 if recent is not None else base
        proj=clamp(proj,3,27)
        line=_mp_line(row,["Pitching Outs Line","Outs Line","outs_line","line_outs"])
        note="Best secondary prop. Uses expected BF, outs/BF, recent IP, pitch trend, weather BF."
    elif prop_type=="Walks Allowed":
        base=ebf*rates["bb"]
        recent=_mp_avg(rr,"BB",5,None)
        proj=base*0.70+recent*0.30 if recent is not None else base
        proj=clamp(proj,0.1,6.5)
        line=_mp_line(row,["Walks Line","BB Line","walks_line","line_walks"])
        note="Good secondary prop. Uses BB/BF, expected BF, and recent BB."
    elif prop_type=="Earned Runs":
        base=ebf*rates["er"]
        recent=_mp_avg(rr,"ER",5,None)
        proj=base*0.68+recent*0.32 if recent is not None else base
        proj=clamp(proj,0.1,8)
        line=_mp_line(row,["Earned Runs Line","ER Line","earned_runs_line","line_er"])
        note="More volatile: sequencing, BABIP, defense and bullpen matter."
    else:
        base=ebf*rates["hits"]
        recent=_mp_avg(rr,"H",5,None)
        proj=base*0.68+recent*0.32 if recent is not None else base
        proj=clamp(proj,0.5,12)
        line=_mp_line(row,["Hits Allowed Line","Hits Line","hits_allowed_line","line_hits_allowed"])
        note="More volatile than Ks/outs because BABIP and defense matter."

    if line is None:
        direction="NO LINE"; edge=None; decision="NO LINE"; tier="NO LINE"
    else:
        edge=round(proj-line,2)
        direction="OVER" if edge>0 else "UNDER"
        ae=abs(edge)
        if prop_type in ["Pitching Outs","Walks Allowed"]:
            if ae>=1.2: tier="A"; decision=f"🔥 {direction}"
            elif ae>=0.75: tier="B"; decision=f"✅ {direction}"
            elif ae>=0.35: tier="C"; decision=f"⚠️ {direction}"
            else: tier="PASS"; decision=f"🚫 P{direction[0]}"
        else:
            if ae>=1.4: tier="B"; decision=f"✅ {direction}"
            elif ae>=0.85: tier="C"; decision=f"⚠️ {direction}"
            else: tier="PASS"; decision=f"🚫 P{direction[0]}"

    return {"Pitcher":row.get("pitcher") or row.get("Pitcher"),"Matchup":row.get("matchup") or row.get("Matchup"),"Prop":prop_type,
            "Projection":round(float(proj),2),"Line":line,"Edge":edge,"Pick":decision,"Tier":tier,
            "Expected BF":round(float(ebf),2),"Pitch Trend":row.get("Pitch Trend Label"),
            "Team Hook":row.get("Team Hook Label"),"Weather":row.get("Weather Upgrade Label"),"Note":note}

def build_multi_prop_table(rows, prop_type):
    data=[multi_prop_project_pitcher(r,prop_type) for r in (rows or []) if isinstance(r,dict)]
    df=pd.DataFrame(data)
    if not df.empty:
        df["_line_sort"]=df["Line"].apply(lambda x:0 if pd.notna(x) else 1)
        df["_edge_sort"]=df["Edge"].apply(lambda x:abs(safe_float(x,0) or 0))
        df=df.sort_values(["_line_sort","_edge_sort"], ascending=[True,False]).drop(columns=["_line_sort","_edge_sort"])
    return df

def render_multi_prop_tab(rows, prop_type):
    st.markdown(f"### {prop_type}")
    st.caption("Uses the same refreshed pitchers/workload context. Lines show if that prop line is available or mapped into the row.")
    df=build_multi_prop_table(rows, prop_type)
    if df.empty:
        st.info("Refresh the live board first.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)





# =========================
# CALIBRATION AUDIT ONLY
# Safe version:
# - Dashboard only
# - Does NOT alter projections
# - Does NOT touch refresh
# - Does NOT touch player loading
# =========================
CALIBRATION_AUDIT_ONLY_ENABLED = True

def _audit_actual_projection(row):
    actual = safe_float(row.get("actual") or row.get("Actual") or row.get("Actual Ks") or row.get("actual_ks"))
    proj = safe_float(row.get("projection") or row.get("K PROJ") or row.get("Projection") or row.get("proj"))
    return actual, proj

def _audit_side(row):
    raw = str(row.get("pick_side") or row.get("Pick") or row.get("Decision") or row.get("Model Lean") or "").upper()
    if "OVER" in raw or " O" in raw or raw.startswith("O"):
        return "OVER"
    if "UNDER" in raw or " U" in raw or raw.startswith("U"):
        return "UNDER"
    proj = safe_float(row.get("projection") or row.get("K PROJ") or row.get("Projection"))
    line = safe_float(row.get("line") or row.get("UD/Line") or row.get("Line"))
    if proj is not None and line is not None:
        return "OVER" if proj > line else "UNDER"
    return "UNKNOWN"

def _audit_line(row):
    return safe_float(row.get("line") or row.get("UD/Line") or row.get("Line"))

def _audit_tier(row):
    return str(row.get("Tier") or row.get("tier") or row.get("Base Tier") or "UNKNOWN").upper()

def _audit_edge(row):
    edge = safe_float(row.get("Edge") or row.get("Edge Gap") or row.get("Lean Gap") or row.get("abs_edge"))
    if edge is not None:
        return abs(edge)
    proj = safe_float(row.get("projection") or row.get("K PROJ") or row.get("Projection"))
    line = _audit_line(row)
    if proj is not None and line is not None:
        return abs(proj - line)
    return None

def _audit_win(row):
    raw = str(row.get("graded_result") or row.get("Result") or row.get("result") or "").upper()
    if raw == "WIN" or row.get("win") is True:
        return 1
    if raw == "LOSS" or row.get("win") is False:
        return 0
    actual, proj = _audit_actual_projection(row)
    line = _audit_line(row)
    side = _audit_side(row)
    if actual is None or line is None:
        return None
    if side == "OVER":
        return 1 if actual > line else 0
    if side == "UNDER":
        return 1 if actual < line else 0
    return None

def _audit_bucket_line(line):
    line = safe_float(line)
    if line is None:
        return "NO LINE"
    if line <= 3.5:
        return "Line <= 3.5"
    if line <= 4.5:
        return "Line 4.5"
    if line <= 5.5:
        return "Line 5.5"
    if line <= 6.5:
        return "Line 6.5"
    return "Line 7+"

def _audit_bucket_edge(edge):
    edge = safe_float(edge)
    if edge is None:
        return "No Edge"
    if edge < 0.5:
        return "Edge < 0.5"
    if edge < 1.0:
        return "Edge 0.5-1.0"
    if edge < 1.5:
        return "Edge 1.0-1.5"
    if edge < 2.0:
        return "Edge 1.5-2.0"
    return "Edge 2.0+"

def build_calibration_audit_rows(results=None):
    results = results if results is not None else load_json(RESULT_LOG, [])
    groups = {}

    def add_group(name, row, err, win):
        g = groups.setdefault(name, {"Bucket": name, "Samples": 0, "Wins": 0, "Err Sum": 0.0, "Abs Err Sum": 0.0})
        g["Samples"] += 1
        g["Wins"] += int(win)
        g["Err Sum"] += float(err)
        g["Abs Err Sum"] += abs(float(err))

    for r in results or []:
        if not isinstance(r, dict):
            continue
        actual, proj = _audit_actual_projection(r)
        win = _audit_win(r)
        if actual is None or proj is None or win is None:
            continue
        err = actual - proj
        side = _audit_side(r)
        tier = _audit_tier(r)
        line_bucket = _audit_bucket_line(_audit_line(r))
        edge_bucket = _audit_bucket_edge(_audit_edge(r))

        add_group("ALL", r, err, win)
        add_group(f"Side: {side}", r, err, win)
        add_group(f"Tier: {tier}", r, err, win)
        add_group(line_bucket, r, err, win)
        add_group(edge_bucket, r, err, win)
        add_group(f"{side} | {line_bucket}", r, err, win)
        add_group(f"{side} | {edge_bucket}", r, err, win)

    rows = []
    for g in groups.values():
        n = max(1, g["Samples"])
        rows.append({
            "Bucket": g["Bucket"],
            "Samples": g["Samples"],
            "Wins": g["Wins"],
            "Win Rate %": round((g["Wins"] / n) * 100, 1),
            "Bias Ks": round(g["Err Sum"] / n, 2),
            "MAE Ks": round(g["Abs Err Sum"] / n, 2),
        })
    return pd.DataFrame(rows)

def render_calibration_audit_tab():
    st.markdown("### 🧠 Calibration Audit Only")
    st.caption("Safe audit dashboard only. It does not change projections, player loading, lines, or decisions.")
    df = build_calibration_audit_rows(load_json(RESULT_LOG, []))
    if df.empty:
        st.info("No graded results found yet. Save/grade results first.")
        return
    all_row = df[df["Bucket"] == "ALL"]
    if not all_row.empty:
        r = all_row.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Samples", int(r["Samples"]))
        c2.metric("Win Rate", f"{r['Win Rate %']}%")
        c3.metric("Bias Ks", r["Bias Ks"])
        c4.metric("MAE Ks", r["MAE Ks"])

    st.dataframe(df.sort_values(["Samples", "Bucket"], ascending=[False, True]), use_container_width=True, hide_index=True)

    with st.expander("How to use this", expanded=False):
        st.write("Bias Ks > 0 means actual Ks are coming in higher than projection.")
        st.write("Bias Ks < 0 means projections are too high in that bucket.")
        st.write("Look for buckets with at least 25+ samples before making real tuning decisions.")





# =========================
# SAVE / LOAD REAL LINE NORMALIZATION FIX
# K-only. Keeps real saved line/source fields available after reload.
# =========================
def normalize_saved_real_line_fields(row):
    row = dict(row or {})
    line = first_value(row, ["UD/Line", "line", "Line", "active_line", "Active Line", "Prop Line"])
    line = safe_float(line)
    if line is not None:
        row["UD/Line"] = line
        row["line"] = line
        row["Line"] = line

    source = first_value(row, ["Line Source", "line_source", "Source", "active_source", "Active Source"])
    if source:
        row["Line Source"] = source
        row["line_source"] = source
    elif line is not None:
        row["Line Source"] = row.get("Line Source") or "Saved Real Line"
        row["line_source"] = row.get("line_source") or row["Line Source"]

    proj = first_value(row, ["K PROJ", "projection", "Projection", "proj"])
    proj = safe_float(proj)
    if proj is not None:
        row["K PROJ"] = proj
        row["projection"] = proj
        row["Projection"] = proj

    pitcher = first_value(row, ["Pitcher", "pitcher", "Player", "player"])
    if pitcher:
        row["Pitcher"] = pitcher
        row["pitcher"] = pitcher

    return row

def normalize_saved_snapshot_rows(rows):
    return [normalize_saved_real_line_fields(r) for r in (rows or []) if isinstance(r, dict)]

def load_saved_pick_log_normalized():
    return normalize_saved_snapshot_rows(load_json(PICK_LOG, []))

def save_pick_log_normalized(rows):
    save_json(PICK_LOG, normalize_saved_snapshot_rows(rows or []))


# =========================
# APP
# =========================
st.markdown("""
<div class="hero-panel">
  <div class="big-title">🔥 MLB STRIKEOUT PROP ENGINE v11.17 SAFETY GATES + PASS DIRECTION</div>
  <div class="sub-title">Strict Win Filter + MLB-only Underdog line lock → Refresh → Save → Grade</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Controls")
    day_mode = st.radio("Game Feed", ["Today + Tomorrow", "Today", "Tomorrow"], index=0)
    bankroll = st.number_input("Bankroll", min_value=1.0, value=1000.0, step=50.0)
    default_odds = st.number_input("Default Odds if sportsbook price missing", value=-110.0, step=5.0)
    hide_no_line = st.checkbox("Hide No Real Line picks", value=False)
    only_strong = st.checkbox("Show only strong signals", value=True)
    st.divider()
    st.header("Model Upgrades")
    use_statcast = st.checkbox("Use Statcast pitcher CSW/whiff", value=True)
    use_pitch_type = st.checkbox("Use pitch-type whiff mix", value=True)
    use_calibration = st.checkbox("Use historical calibration", value=True)
    use_bayesian_markov = st.checkbox("Use Bayesian Markov Monte Carlo", value=True)
    use_weather = st.checkbox("Use live weather adjustment", value=True)
    use_umpire = st.checkbox("Use capped umpire tendency", value=True)
    use_xgboost_assist = st.checkbox("Experimental: capped XGBoost assist", value=False)
    use_sgo = st.checkbox("Optional: SportsGameOdds API", value=False)
    use_optic = st.checkbox("Optional: OpticOdds API", value=False)
    if st.button("🧹 Clear Streamlit Cache + Reload Live Lines", use_container_width=True):
        st.cache_data.clear()
        st.session_state.loaded_picks = []
        st.session_state.last_refresh_time = None
        st.success("Cache cleared. Now click REFRESH LIVE BOARD again.")
    st.caption("Refresh does not save official picks. Save only when the board looks right. Optional paid APIs stay OFF unless you have keys.")

dates = target_dates(day_mode)

if "loaded_picks" not in st.session_state:
    st.session_state.loaded_picks = []
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = None
if "last_saved_count" not in st.session_state:
    st.session_state.last_saved_count = 0

col_refresh, col_save = st.columns(2)

with col_refresh:
    refresh_btn = st.button("🔄 REFRESH LIVE BOARD — Do Not Save Yet", use_container_width=True)

with col_save:
    save_btn = st.button("💾 SAVE OFFICIAL BEFORE-GAME SNAPSHOT", use_container_width=True)

if refresh_btn:
    all_rows = []
    for d in dates:
        all_rows.extend(extract_probable_pitchers(d))

    projections = []
    progress = st.progress(0)

    for i, row in enumerate(all_rows):
        try:
            projections.append(
                make_projection(
                    row,
                    bankroll=bankroll,
                    default_odds=default_odds,
                    use_statcast=use_statcast,
                    use_pitch_type=use_pitch_type,
                    use_calibration=use_calibration,
                    use_bayesian_markov=use_bayesian_markov,
                    use_weather=use_weather,
                    use_umpire=use_umpire,
                    use_xgboost_assist=use_xgboost_assist,
                    use_sgo=use_sgo,
                    use_optic=use_optic
                )
            )
        except Exception as e:
            log_source_request("make_projection", "ERROR", f"{row.get('pitcher')}: {e}")
        progress.progress((i + 1) / max(1, len(all_rows)))

    st.session_state.loaded_picks = projections
    st.session_state.last_refresh_time = now_iso()
    st.success(f"Refreshed {len(projections)} pitchers. Nothing officially saved yet.")

if save_btn:
    if not st.session_state.get("loaded_picks"):
        st.warning("Refresh the live board first, inspect the lines, then save the official before-game snapshot.")
    else:
        added = save_many_once(st.session_state.loaded_picks)
        st.session_state.last_saved_count = added
        st.success(f"Saved official before-game snapshot. Added {added} new rows.")

saved = load_saved_pick_log_normalized()

# IMPORTANT:
# - If you have refreshed this session, the screen shows refreshed live board.
# - If not, it shows saved official snapshots for the selected dates.
if st.session_state.get("loaded_picks"):
    board = st.session_state.loaded_picks
    board_status = "LIVE REFRESHED BOARD — NOT OFFICIAL UNLESS SAVED"
else:
    board = [p for p in saved if p.get("date") in dates]
    board_status = "SAVED OFFICIAL SNAPSHOTS"

if hide_no_line:
    board = [p for p in board if p.get("line") is not None]
if only_strong:
    board = [p for p in board if p.get("signal_type") == "good"]

st.info(f"{APP_VERSION} | {board_status} | Last refresh: {st.session_state.get('last_refresh_time') or 'Not refreshed this session'} | Last save added: {st.session_state.get('last_saved_count', 0)}")

render_kpis(board, bankroll)

def display_clean_real_prop_rows(rows, **kwargs):
    cleaned = clean_real_prop_debug_rows(rows)
    if cleaned:
        st.dataframe(pd.DataFrame(cleaned), use_container_width=True, hide_index=True)
    else:
        st.info("No rejected/NBA debug rows shown. Only valid MLB pitcher strikeout lines will appear here.")


# =========================
# =========================
def _best4_num(x, default=0.0):
    v = safe_float(x, default)
    return default if v is None else v

def best4_pick_direction(p):
    side = str(p.get("pick_side") or "").upper().strip()
    if side in ["OVER", "UNDER"]:
        return side
    proj = safe_float(p.get("projection"))
    line = safe_float(p.get("line"))
    if proj is None or line is None:
        return "PASS"
    return "OVER" if proj > line else "UNDER"

def best4_abs_edge(p):
    # Prefer the app's own edge fields, but fall back to projection - line.
    for key in ["abs_edge", "edge_ks", "edge", "projection_gap"]:
        v = safe_float(p.get(key))
        if v is not None:
            return abs(v)
    proj = safe_float(p.get("projection"))
    line = safe_float(p.get("line"))
    if proj is None or line is None:
        return 0.0
    return abs(proj - line)

def best4_is_risky_text(*vals):
    t = " ".join(str(v or "") for v in vals).upper()
    bad = ["EXTREME", "HIGH RISK", "VOLATILE", "NO BET", "BAD", "MISSING", "LOW SAMPLE"]
    return any(x in t for x in bad)

def best4_rejection_reasons(p):
    reasons = []
    prob = _best4_num(p.get("fair_probability"), 0.0)
    edge = best4_abs_edge(p)
    data_score = _best4_num(p.get("data_score"), 0.0)
    ev = _best4_num(p.get("ev"), 0.0)
    line = safe_float(p.get("line"))
    proj = safe_float(p.get("projection"))

    if line is None:
        reasons.append("No real line")
    if proj is None:
        reasons.append("No projection")
    if prob < MIN_BETTABLE_PROB:
        reasons.append(f"Prob below {MIN_BETTABLE_PROB:.0%}")
    if edge < MIN_BETTABLE_GAP_KS:
        reasons.append(f"Gap under {MIN_BETTABLE_GAP_KS:.1f} Ks")
    if data_score < MIN_BETTABLE_SCORE:
        reasons.append(f"Data score below {MIN_BETTABLE_SCORE}")
    if ev < MIN_BETTABLE_EV:
        reasons.append(f"EV below {MIN_BETTABLE_EV:.0%}")
    if not p.get("lineup_locked"):
        reasons.append("Lineup not confirmed")
    if not p.get("price_is_real"):
        reasons.append("Price/EV estimated")

    risk_text = " ".join(str(p.get(k, "")) for k in [
        "risk_label", "leash_risk", "manager_hook_status", "manager_hook", "bullpen_status",
        "weather_note", "umpire_note", "calibration_note", "signal"
    ])
    if best4_is_risky_text(risk_text):
        reasons.append("Risk flag present")
    return reasons

def best4_hit_rate_score(p):
    """Display-only hit-rate score. Does not change projections/signals."""
    prob = _best4_num(p.get("fair_probability"), 0.50)
    edge = best4_abs_edge(p)
    data_score = _best4_num(p.get("data_score"), 70.0)
    ev = _best4_num(p.get("ev"), 0.0)
    p10 = safe_float(p.get("p10"))
    p90 = safe_float(p.get("p90"))
    sim_range = (p90 - p10) if p10 is not None and p90 is not None else 3.5

    score = 0.0
    score += prob * 48.0
    score += min(edge, 3.25) * 9.0
    score += data_score * 0.20
    score += max(ev, 0.0) * 75.0

    # Stability bonuses/penalties are small and capped.
    if p.get("lineup_locked"):
        score += 4.0
    else:
        score -= 5.0
    if p.get("price_is_real"):
        score += 3.0
    else:
        score -= 3.0
    if str(p.get("signal_type", "")).lower() == "good":
        score += 3.0
    if str(p.get("bettable", "")).lower() in ["true", "yes", "1"] or p.get("bettable") is True:
        score += 2.0
    if sim_range > 4.5:
        score -= min((sim_range - 4.5) * 2.5, 8.0)

    # Do not allow dangerous flags to rank at the top.
    score -= len(best4_rejection_reasons(p)) * 4.0
    return round(float(clamp(score, 0, 100)), 2)

def build_best4_table(board):
    rows = []
    for p in board or []:
        line = safe_float(p.get("line"))
        proj = safe_float(p.get("projection"))
        if line is None or proj is None:
            continue
        direction = best4_pick_direction(p)
        edge_signed = proj - line
        reasons = best4_rejection_reasons(p)
        top_score = best4_hit_rate_score(p)
        qualified = (
            not reasons
            and top_score >= 88
            and _best4_num(p.get("fair_probability"), 0) >= MIN_BETTABLE_PROB
            and best4_abs_edge(p) >= MIN_BETTABLE_GAP_KS
            and str(p.get("action_tier", "PASS")).upper() == "BET"
        )
        rows.append({
            "Player": p.get("pitcher") or p.get("player") or "",
            "Matchup": p.get("matchup", ""),
            "Pick": direction,
            "Final Action": p.get("bet_action", "🚫 PASS"),
            "Action Tier": p.get("action_tier", "PASS"),
            "Line": line,
            "Projection": round(proj, 2),
            "Edge": round(edge_signed, 2),
            "Abs Edge": round(abs(edge_signed), 2),
            "Fair Prob %": round(_best4_num(p.get("fair_probability"), 0) * 100, 1),
            "EV %": round(_best4_num(p.get("ev"), 0) * 100, 1),
            "Data Score": round(_best4_num(p.get("data_score"), 0), 1),
            "Hit-Rate Score": top_score,
            "Lineup": "Confirmed" if p.get("lineup_locked") else "Fallback",
            "Price": "Real" if p.get("price_is_real") else "Estimated",
            "Risk": p.get("risk_label", ""),
            "Hook": p.get("manager_hook_status") or p.get("manager_hook") or "",
            "Weather": p.get("weather_note", ""),
            "Calibration": p.get("calibration_note", p.get("true_calibration_note", "")),
            "Status": "TOP QUALIFIED" if qualified else "PASS",
            "Why": "Qualified" if qualified else "; ".join(reasons),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df, df, df
    df = df.sort_values(["Status", "Hit-Rate Score", "Fair Prob %", "Abs Edge"], ascending=[True, False, False, False])
    qualified = df[df["Status"] == "TOP QUALIFIED"].sort_values("Hit-Rate Score", ascending=False)
    safe_top4 = qualified.head(4)
    aggressive = df[
        (df["Fair Prob %"] >= 60)
        & (df["Abs Edge"] >= 0.75)
        & (df["Data Score"] >= 82)
    ].sort_values("Hit-Rate Score", ascending=False).head(4)
    return safe_top4, aggressive, df

def render_best4_builder(board):
    st.caption("Display-only ranker. It does not change projections, EV, calibration, or saved official snapshots.")
    top4_safe, aggressive_top4, ranked_all = build_best4_table(board)

    c1, c2, c3 = st.columns(3)
    c1.metric("Ultra-Safe Qualified", len(top4_safe))
    c2.metric("Aggressive Candidates", len(aggressive_top4))
    c3.metric("Ranked Board", len(ranked_all))

    st.subheader("🔥 Top 4 Safest")
    if top4_safe.empty:
        st.warning("No ultra-safe Top 4 right now. That is a good sign: the app is not forcing weak plays.")
    else:
        st.dataframe(top4_safe, use_container_width=True, hide_index=True)

    st.subheader("⚡ Aggressive Top 4")
    if aggressive_top4.empty:
        st.info("No aggressive candidates right now.")
    else:
        st.dataframe(aggressive_top4, use_container_width=True, hide_index=True)

    st.subheader("✅ All Ranked / 🚫 Pass Reasons")
    if ranked_all.empty:
        st.info("No lined picks available to rank.")
    else:
        st.dataframe(ranked_all, use_container_width=True, hide_index=True)



# =========================
# v11.17 K PROJ / UPSIDE TAB
# =========================
def kproj_line_for_display(p):
    """Use Underdog line first, then the active real line. Never creates fake lines."""
    ud = safe_float(p.get("underdog_line"))
    if ud is not None:
        return ud, "Underdog"
    active = safe_float(p.get("line"))
    if active is not None:
        return active, str(p.get("line_source") or "Active Line")
    return None, "NO LINE"

def kproj_putaway_value(p):
    # Best available strikeout-stuff proxy already inside this app.
    whiff = safe_float(p.get("statcast_whiff"))
    csw = safe_float(p.get("statcast_csw"))
    if whiff is not None:
        return whiff, "Whiff%"
    if csw is not None:
        return csw, "CSW%"
    pk = safe_float(p.get("pitcher_k"))
    if pk is not None:
        return pk * 100, "Pitcher K%"
    return None, "Unavailable"

def kproj_true_talent_baseline(p):
    """True-talent strikeout baseline used to stop fake-low projections.

    This uses pitcher K skill + opponent K opportunity + expected BF, then applies
    only capped/lite modifiers. It is not an automatic over boost; it is a sanity
    baseline so arms like Rodón/Strider/Cavalli do not get crushed to 1-3 Ks.
    """
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    ok = safe_float(p.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    pitch_factor = safe_float(p.get("pitch_type_factor"), 1.0) or 1.0
    stat_whiff = safe_float(p.get("statcast_whiff"))
    stat_csw = safe_float(p.get("statcast_csw"))
    recent_max, recent_avg, recent_n = kproj_recent_ceiling_stats(p) if "kproj_recent_ceiling_stats" in globals() else (0,0,0)

    # Pitcher talent is the anchor. Opponent K helps, but cannot erase pitcher skill.
    matchup_rate = (pk * 0.72) + (ok * 0.28)
    baseline = bf * matchup_rate

    # Lite stuff/context nudges.
    if pitch_factor >= 1.035:
        baseline += 0.30
    elif pitch_factor >= 1.015:
        baseline += 0.15
    elif pitch_factor <= 0.965 and pk < 0.255:
        baseline -= 0.12

    if stat_whiff is not None:
        if stat_whiff >= 31:
            baseline += 0.35
        elif stat_whiff >= 28:
            baseline += 0.20
    elif stat_csw is not None:
        if stat_csw >= 31:
            baseline += 0.25
        elif stat_csw >= 29:
            baseline += 0.12

    # Recent ceiling matters more for preventing bad UNDERS than for forcing OVERS.
    if recent_max >= 9:
        baseline += 0.55
    elif recent_max >= 7:
        baseline += 0.35
    elif recent_max >= 6:
        baseline += 0.18
    if recent_avg >= 6.0:
        baseline += 0.35
    elif recent_avg >= 5.0:
        baseline += 0.18

    # For confirmed starters, cap negative suppression. If not stable starter, stay conservative.
    if kproj_is_confirmed_starter_like(p):
        baseline = max(baseline, bf * pk * KPROJ_MAX_NEGATIVE_SUPPRESSION_STARTER)
    else:
        baseline *= 0.88

    # Prevent nonsense floors, but do not make everyone elite.
    cap = 8.25 if pk >= 0.285 else 7.35 if pk >= 0.260 else 6.55 if pk >= 0.240 else 5.65
    return round(float(clamp(baseline, 0.0, cap)), 2)


def apply_elite_pitcher_floor(raw_projection, historical_k9, expected_bf):
    """
    K UPSIDE TAB ONLY: circuit breaker that stops established high-strikeout
    arms from being under-projected because of short-term rolling bias,
    tight pitch-cap assumptions, or stacked matchup penalties.
    """
    raw_projection = safe_float(raw_projection, 0.0) or 0.0
    historical_k9 = safe_float(historical_k9, 0.0) or 0.0
    expected_bf = safe_float(expected_bf, DEFAULT_BF) or DEFAULT_BF
    if historical_k9 >= 10.0:
        implied_floor = expected_bf * (historical_k9 / 38.0)
        return max(raw_projection, implied_floor)
    if historical_k9 >= 9.0:
        implied_floor = expected_bf * (historical_k9 / 41.0)
        return max(raw_projection, implied_floor)
    return raw_projection


def project_volume_and_efficiency(p_avg_bf, p_pitches_per_bf, opp_ppa, league_ppa=3.90):
    """
    K UPSIDE TAB ONLY: dynamic BF scaler. It slightly rewards efficient pitchers
    facing low-patience/high-vulnerability lineups, but caps the move so it
    cannot create unrealistic volume.
    """
    p_avg_bf = safe_float(p_avg_bf, DEFAULT_BF) or DEFAULT_BF
    p_pitches_per_bf = safe_float(p_pitches_per_bf, 3.85) or 3.85
    opp_ppa = safe_float(opp_ppa, league_ppa) or league_ppa
    if opp_ppa <= 0 or p_pitches_per_bf <= 0:
        return p_avg_bf
    ppa_scalar = league_ppa / opp_ppa
    # Cap this because team PPA feeds can be noisy/missing.
    ppa_scalar = clamp(ppa_scalar, 0.94, 1.08)
    # Efficient pitchers get a small extra volume bump; inefficient arms get a small cut.
    efficiency_scalar = clamp(3.90 / p_pitches_per_bf, 0.94, 1.06)
    return round(float(clamp(p_avg_bf * ppa_scalar * efficiency_scalar, 14.0, 30.0)), 1)


def kproj_historical_k9(p):
    """Best K/9 proxy available inside the app data."""
    for key in ["k9", "K/9", "pitcher_k9", "season_k9"]:
        v = safe_float(p.get(key))
        if v is not None and v > 0:
            return v
    pk = safe_float(p.get("pitcher_k"), None)
    if pk is not None and pk > 0:
        # K% to rough K/9 proxy, using starter BF/IP around 4.25.
        return pk * 4.25 * 9.0
    return 0.0


def kproj_recent_form_projection(p, expected_bf=None):
    """
    K UPSIDE TAB ONLY: projection style inspired by the card example.
    Weighted blend:
      - matchup/BF projection
      - last-10 K average
      - K/9 baseline
      - BF + opponent K opportunity boost
    This does not touch the main engine or other tabs.
    """
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    ok = safe_float(p.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    bf = safe_float(expected_bf, safe_float(p.get("expected_bf"), DEFAULT_BF)) or DEFAULT_BF
    k9 = kproj_historical_k9(p)
    recent_vals = [safe_float(x, None) for x in (p.get("last_10_ks") or [])[:10]]
    recent_vals = [float(x) for x in recent_vals if x is not None]

    # Pitcher skill remains the anchor, opponent K is opportunity.
    combined_rate = clamp((pk * 0.68) + (ok * 0.32), 0.08, 0.42)
    matchup_projection = bf * combined_rate

    if recent_vals:
        last10_avg = sum(recent_vals) / len(recent_vals)
        last5_avg = sum(recent_vals[:5]) / max(1, len(recent_vals[:5]))
        recent_avg = (last10_avg * 0.60) + (last5_avg * 0.40)
        recent_max = max(recent_vals)
    else:
        recent_avg = matchup_projection
        recent_max = 0.0

    k9_projection = (k9 / 9.0) * (bf / 4.25) if k9 > 0 else matchup_projection

    # Opportunity boost mirrors the card logic: high BF + high opponent K = over-friendly.
    opportunity = 0.0
    if bf >= 26:
        opportunity += 0.45
    elif bf >= 24:
        opportunity += 0.25
    elif bf <= 19:
        opportunity -= 0.25

    if ok >= 0.245:
        opportunity += 0.35
    elif ok >= 0.230:
        opportunity += 0.18
    elif ok <= 0.205 and pk < 0.260:
        opportunity -= 0.22

    if recent_max >= 9:
        opportunity += 0.35
    elif recent_max >= 7:
        opportunity += 0.18

    # If recent history is real, use it. If not, rely more on matchup.
    if recent_vals:
        blended = (matchup_projection * 0.45) + (recent_avg * 0.30) + (k9_projection * 0.15) + ((matchup_projection + opportunity) * 0.10)
    else:
        blended = (matchup_projection * 0.70) + (k9_projection * 0.20) + ((matchup_projection + opportunity) * 0.10)

    # Do not let this layer create absurd projections on low-skill arms.
    cap = 10.25 if pk >= 0.300 or k9 >= 10.0 else 9.25 if pk >= 0.270 or k9 >= 9.0 else 8.25 if pk >= 0.245 else 7.15
    return round(float(clamp(blended, 0.0, cap)), 2)


# =========================
# LIGHT DYNAMIC LEASH / BF BOOST
# Small workload-based BF adjustment only.
# This is NOT a blanket +0.5 K boost.
# It helps pitchers with strong recent workload / long leash profiles.
# =========================
DYNAMIC_LEASH_BF_ENABLED = True
DYNAMIC_LEASH_BF_MAX_BOOST = 1.15
DYNAMIC_LEASH_BF_MAX_CUT = -0.55

def dynamic_leash_bf_adjustment(row=None):
    if not DYNAMIC_LEASH_BF_ENABLED:
        return 0.0, "OFF", "Dynamic leash disabled"

    row = row or {}
    adj = 0.0
    notes = []

    exp_bf = safe_float(row.get("expected_bf"), None)
    ip_floor = safe_float(row.get("ip_floor") or row.get("IP Floor"), None)
    recent_ip = safe_float(row.get("recent_ip") or row.get("avg_ip_l3") or row.get("avg_ip_l5"), None)
    avg_pitches = safe_float(row.get("avg_pitches_l3") or row.get("avg_pitches_l5") or row.get("recent_pitches"), None)
    role_score = safe_float(row.get("role_score") or row.get("Role Score"), None)
    starter_score = safe_float(row.get("starter_score") or row.get("Starter Score"), None)

    leash_text = str(row.get("leash_risk") or row.get("Pitch Alert") or row.get("pitch_alert") or "").upper()
    bullpen_text = " ".join(str(row.get(k, "")) for k in [
        "bullpen_status", "bullpen_note", "bullpen_risk", "bp_status",
        "pen_status", "bullpen_fatigue", "bullpen_usage_note",
        "light_bullpen_tax_label"
    ]).upper()

    if exp_bf is not None and exp_bf >= 24.0:
        adj += 0.25
        notes.append("strong BF path")
    if exp_bf is not None and exp_bf >= 26.0:
        adj += 0.20
        notes.append("elite BF path")
    if ip_floor is not None and ip_floor >= 5.3:
        adj += 0.20
        notes.append("solid IP floor")
    if recent_ip is not None and recent_ip >= 5.8:
        adj += 0.20
        notes.append("recent length")
    if avg_pitches is not None and avg_pitches >= 92:
        adj += 0.25
        notes.append("pitch-count leash")
    if avg_pitches is not None and avg_pitches >= 98:
        adj += 0.15
        notes.append("deep pitch-count leash")
    if role_score is not None and role_score >= 78:
        adj += 0.15
        notes.append("stable role")
    if starter_score is not None and starter_score >= 78:
        adj += 0.10
        notes.append("starter confirmed")
    if any(x in bullpen_text for x in ["TAXED", "TIRED", "FATIGUED", "HEAVY", "OVERUSED"]):
        adj += 0.20
        notes.append("bullpen supports length")

    if exp_bf is not None and exp_bf <= 17.0:
        adj -= 0.35
        notes.append("low BF path")
    if exp_bf is not None and exp_bf <= 14.5:
        adj -= 0.25
        notes.append("very low BF path")
    if any(x in leash_text for x in ["SHORT", "STRICT", "LIMIT", "LOW_ALERT", "MEDIUM_ALERT", "LOW BF"]):
        adj -= 0.25
        notes.append("leash warning")
    if avg_pitches is not None and avg_pitches <= 72:
        adj -= 0.20
        notes.append("low pitch-count trend")

    adj = clamp(adj, DYNAMIC_LEASH_BF_MAX_CUT, DYNAMIC_LEASH_BF_MAX_BOOST)

    if abs(adj) < 0.05:
        return 0.0, "NEUTRAL", "No meaningful leash adjustment"

    label = "LEASH_BOOST" if adj > 0 else "LEASH_CUT"
    return round(float(adj), 2), label, " | ".join(notes[:4])

def apply_dynamic_leash_to_expected_bf(expected_bf, row=None):
    bf = safe_float(expected_bf, DEFAULT_BF) or DEFAULT_BF
    adj, label, note = dynamic_leash_bf_adjustment(row)
    smart_bf = smart_edge_bf_nudge(row)
    new_bf = float(clamp(bf + adj + smart_bf, 14.0, 31.5))
    if isinstance(row, dict):
        row["dynamic_leash_bf_adj"] = adj
        row["smart_bf_nudge"] = smart_bf
        row["dynamic_leash_label"] = label
        row["dynamic_leash_note"] = note
        row["dynamic_leash_bf"] = round(new_bf, 2)
    return new_bf



# =========================
# SMART EDGE UPGRADES PACK
# Light additive modules:
# 1) Miss-by-1 analytics fields
# 2) Lineup strikeout pressure score
# 3) Pitch count trend score
# 4) True leash score
# 5) Bullpen incentive score
# 6) Umpire K environment score
#
# These are small confidence/BF/projection nudges only.
# They do NOT replace the K engine and do NOT blanket boost overs.
# =========================
SMART_EDGE_UPGRADES_ENABLED = True
SMART_EDGE_MAX_PROJ_NUDGE = 0.35
SMART_EDGE_MAX_BF_NUDGE = 0.75

def _num_list_from_any(x):
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        out = []
        for v in x:
            fv = safe_float(v, None)
            if fv is not None:
                out.append(fv)
        return out
    txt = str(x)
    vals = []
    for m in re.findall(r"-?\d+(?:\.\d+)?", txt):
        fv = safe_float(m, None)
        if fv is not None:
            vals.append(fv)
    return vals

def smart_pitch_count_trend_score(row=None):
    row = row or {}
    vals = []
    for key in ["recent_pitches_list", "last_pitches", "pitches_l3", "pitches_l5", "recent_pitches"]:
        vals += _num_list_from_any(row.get(key))
    vals = [v for v in vals if 20 <= v <= 125]
    if not vals:
        avg = safe_float(row.get("avg_pitches_l3") or row.get("avg_pitches_l5"), None)
        vals = [avg] if avg is not None else []
    if not vals:
        return 50, "UNKNOWN_PITCH_COUNT", "No pitch-count trend"

    use = vals[:5]
    avg = sum(use) / len(use)
    if avg >= 98:
        return 88, "DEEP_PITCH_COUNT", f"Recent pitch count avg {avg:.1f}"
    if avg >= 92:
        return 76, "GOOD_PITCH_COUNT", f"Recent pitch count avg {avg:.1f}"
    if avg >= 84:
        return 60, "NORMAL_PITCH_COUNT", f"Recent pitch count avg {avg:.1f}"
    if avg >= 74:
        return 42, "LIGHT_PITCH_COUNT", f"Recent pitch count avg {avg:.1f}"
    return 25, "LOW_PITCH_COUNT", f"Recent pitch count avg {avg:.1f}"

def smart_lineup_k_pressure_score(row=None):
    row = row or {}
    # Use real lineup rows if available; otherwise fall back to opponent K%.
    hitters = row.get("lineup_rows") or row.get("confirmed_lineup_rows") or row.get("projected_lineup_rows") or []
    k_rates = []
    if isinstance(hitters, list):
        for h in hitters:
            if isinstance(h, dict):
                k = safe_float(h.get("k_rate") or h.get("K%") or h.get("k_pct") or h.get("strikeout_rate"), None)
                if k is not None:
                    if k > 1:
                        k /= 100.0
                    if 0.05 <= k <= 0.45:
                        k_rates.append(k)
    if k_rates:
        high24 = sum(1 for k in k_rates if k >= 0.24)
        high28 = sum(1 for k in k_rates if k >= 0.28)
        low18 = sum(1 for k in k_rates if k <= 0.18)
        avg = sum(k_rates) / len(k_rates)
        score = 50 + (high24 * 4) + (high28 * 5) - (low18 * 4) + ((avg - 0.22) * 100)
        score = int(clamp(score, 5, 95))
        label = "HIGH_K_LINEUP" if score >= 70 else "LOW_K_LINEUP" if score <= 38 else "NEUTRAL_LINEUP_K"
        return score, label, f"{high24} hitters 24%+ K, {high28} hitters 28%+ K, {low18} hitters <=18% K"

    ok = safe_float(row.get("opp_k"), None)
    if ok is not None:
        if ok > 1:
            ok /= 100.0
        score = int(clamp(50 + ((ok - 0.22) * 160), 20, 85))
        label = "HIGH_K_TEAM" if ok >= 0.245 else "LOW_K_TEAM" if ok <= 0.205 else "NEUTRAL_K_TEAM"
        return score, label, f"Opponent K% fallback {ok*100:.1f}%"
    return 50, "UNKNOWN_LINEUP_K", "No lineup K profile"

def smart_true_leash_score(row=None):
    row = row or {}
    exp_bf = safe_float(row.get("expected_bf"), None)
    ip_floor = safe_float(row.get("ip_floor") or row.get("IP Floor"), None)
    role = safe_float(row.get("role_score") or row.get("Role Score"), 50) or 50
    starter = safe_float(row.get("starter_score") or row.get("Starter Score"), 50) or 50
    pitch_score, pitch_label, _ = smart_pitch_count_trend_score(row)

    score = 45
    if exp_bf is not None:
        score += (exp_bf - 20.0) * 4.2
    if ip_floor is not None:
        score += (ip_floor - 4.5) * 7.0
    score += (role - 50) * 0.12
    score += (starter - 50) * 0.10
    score += (pitch_score - 50) * 0.18

    txt = str(row.get("leash_risk") or row.get("Pitch Alert") or row.get("pitch_alert") or "").upper()
    if any(x in txt for x in ["STRICT", "SHORT", "LIMIT", "LOW BF", "MEDIUM_ALERT"]):
        score -= 14
    elif any(x in txt for x in ["CLEAR", "NO OBVIOUS"]):
        score += 5

    score = int(clamp(score, 5, 95))
    label = "LONG_LEASH" if score >= 72 else "SHORT_LEASH" if score <= 38 else "NORMAL_LEASH"
    return score, label, f"{label}; pitch trend {pitch_label}"

def smart_bullpen_incentive_score(row=None):
    row = row or {}
    txt = " ".join(str(row.get(k, "")) for k in [
        "bullpen_status", "bullpen_note", "bullpen_risk", "bp_status",
        "pen_status", "bullpen_fatigue", "bullpen_usage_note",
        "light_bullpen_tax_label"
    ]).upper()
    score = 50
    label = "NEUTRAL_BP"
    if any(x in txt for x in ["TAXED", "EXHAUSTED", "OVERUSED", "HEAVY"]):
        score, label = 78, "BP_LENGTH_SUPPORT"
    elif any(x in txt for x in ["TIRED", "FATIGUED", "BACK-TO-BACK", "B2B"]):
        score, label = 65, "SLIGHT_BP_SUPPORT"
    elif any(x in txt for x in ["FRESH", "RESTED"]):
        score, label = 38, "QUICK_HOOK_RISK"
    return score, label, label.replace("_", " ").title()

def smart_umpire_k_environment_score(row=None):
    row = row or {}
    fac = safe_float(row.get("Advanced Umpire Factor") or row.get("umpire_factor") or row.get("ump_factor"), None)
    label0 = str(row.get("Advanced Umpire Label") or row.get("umpire_label") or "").upper()
    if fac is not None:
        if fac >= 1.025:
            return 68, "K_UMP_BOOST", f"Ump factor {fac:.3f}"
        if fac <= 0.975:
            return 32, "K_UMP_SUPPRESS", f"Ump factor {fac:.3f}"
        return 50, "UMP_NEUTRAL", f"Ump factor {fac:.3f}"
    if "BOOST" in label0 or "K_PLUS" in label0:
        return 65, "K_UMP_BOOST", label0
    if "SUPPRESS" in label0 or "K_MINUS" in label0:
        return 35, "K_UMP_SUPPRESS", label0
    return 50, "UMP_UNKNOWN_NEUTRAL", "No umpire K environment"

def smart_edge_projection_nudge(row=None):
    """Small projection nudge from lineup/leash/ump. Capped at +/-0.35 K."""
    if not SMART_EDGE_UPGRADES_ENABLED:
        return 0.0, "OFF", "Smart edge upgrades off"
    row = row or {}

    lineup_score, lineup_label, lineup_note = smart_lineup_k_pressure_score(row)
    leash_score, leash_label, leash_note = smart_true_leash_score(row)
    bp_score, bp_label, bp_note = smart_bullpen_incentive_score(row)
    ump_score, ump_label, ump_note = smart_umpire_k_environment_score(row)
    pitch_score, pitch_label, pitch_note = smart_pitch_count_trend_score(row)

    nudge = 0.0
    nudge += (lineup_score - 50) * 0.006
    nudge += (leash_score - 50) * 0.005
    nudge += (bp_score - 50) * 0.003
    nudge += (ump_score - 50) * 0.003
    nudge += (pitch_score - 50) * 0.003

    # Do not over-boost pitchers already under low-BF warning.
    exp_bf = safe_float(row.get("expected_bf"), None)
    if exp_bf is not None and exp_bf <= 17 and nudge > 0:
        nudge *= 0.35

    nudge = float(clamp(nudge, -SMART_EDGE_MAX_PROJ_NUDGE, SMART_EDGE_MAX_PROJ_NUDGE))
    label = "SMART_BOOST" if nudge >= 0.12 else "SMART_CUT" if nudge <= -0.12 else "SMART_NEUTRAL"

    if isinstance(row, dict):
        row["smart_lineup_k_score"] = lineup_score
        row["smart_lineup_k_label"] = lineup_label
        row["smart_leash_score"] = leash_score
        row["smart_leash_label"] = leash_label
        row["smart_bullpen_score"] = bp_score
        row["smart_bullpen_label"] = bp_label
        row["smart_umpire_score"] = ump_score
        row["smart_umpire_label"] = ump_label
        row["smart_pitch_count_score"] = pitch_score
        row["smart_pitch_count_label"] = pitch_label
        row["smart_edge_nudge"] = round(nudge, 2)
        row["smart_edge_label"] = label
        row["smart_edge_note"] = " | ".join([lineup_label, leash_label, bp_label, ump_label, pitch_label])

    return round(nudge, 2), label, " | ".join([lineup_note, leash_note, bp_note, ump_note, pitch_note][:5])

def smart_edge_bf_nudge(row=None):
    """Small BF nudge from true leash/pitch-count/bullpen. Capped at +/-0.75 BF."""
    if not SMART_EDGE_UPGRADES_ENABLED:
        return 0.0
    leash_score, _, _ = smart_true_leash_score(row)
    bp_score, _, _ = smart_bullpen_incentive_score(row)
    pitch_score, _, _ = smart_pitch_count_trend_score(row)
    bf_nudge = (leash_score - 50) * 0.012 + (bp_score - 50) * 0.006 + (pitch_score - 50) * 0.008
    return round(float(clamp(bf_nudge, -0.45, SMART_EDGE_MAX_BF_NUDGE)), 2)

def miss_by_one_bucket(proj, line, actual=None, side=None):
    proj = safe_float(proj, None)
    line = safe_float(line, None)
    actual = safe_float(actual, None)
    if proj is None or line is None:
        return "NO_LINE"
    projected_edge = abs(proj - line)
    if actual is None:
        return "PENDING_CLOSE_EDGE" if projected_edge <= 1.0 else "PENDING_BIG_EDGE"
    if side is None:
        side = "OVER" if proj > line else "UNDER"
    if side == "OVER":
        diff = actual - line
    else:
        diff = line - actual
    if diff >= 2:
        return "WON_BY_2_PLUS"
    if diff >= 1:
        return "WON_BY_1_PLUS"
    if diff >= 0:
        return "WON_CLOSE"
    if diff >= -1:
        return "LOST_BY_1"
    return "LOST_BY_2_PLUS"


def kproj_upside_projection(p):
    """K UPSIDE TAB projection with recent-form weighted true-talent guard.

    This changes ONLY the K PROJ / Upside tab. The main engine remains separate.

    Philosophy:
    1) Respect pitcher strikeout talent and recent K history first.
    2) Use expected BF/opponent K opportunity like the reference card.
    3) Cap negative suppression so high-K arms do not become fake UNDERS.
    4) Keep role/leash/weather risk, but only as controlled nudges.
    """
    base = safe_float(p.get("pre_calibration_projection"), safe_float(p.get("projection"), 0.0)) or 0.0
    main_proj = safe_float(p.get("projection"), base) or base
    p90 = safe_float(p.get("p90"))
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    ok = safe_float(p.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    raw_bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    ppb = safe_float(p.get("ppb"), safe_float(p.get("pitches_per_bf"), 3.9)) or 3.9
    opp_ppa = safe_float(p.get("opp_team_ppa"), safe_float(p.get("opp_ppa"), 3.90)) or 3.90
    upside = safe_float(p.get("elite_upside_score"), 0.0) or 0.0
    pitch_factor = safe_float(p.get("pitch_type_factor"), 1.0) or 1.0
    stat_whiff = safe_float(p.get("statcast_whiff"))
    stat_csw = safe_float(p.get("statcast_csw"))
    historical_k9 = kproj_historical_k9(p)

    expected_bf = project_volume_and_efficiency(raw_bf, ppb, opp_ppa)
    # Light dynamic leash/BF adjustment: workload only, capped, not a blanket K boost.
    expected_bf = apply_dynamic_leash_to_expected_bf(expected_bf, p)
    talent_base = kproj_true_talent_baseline(p)
    recent_form_proj = kproj_recent_form_projection(p, expected_bf=expected_bf)

    # Start from the strongest reasonable baseline, then blend.
    original_proj = max(base, main_proj)
    if kproj_is_confirmed_starter_like(p):
        proj = (original_proj * 0.22) + (talent_base * 0.34) + (recent_form_proj * 0.44)
    else:
        proj = (original_proj * 0.45) + (talent_base * 0.30) + (recent_form_proj * 0.25)

    # Elite pitcher floor circuit breaker from K/9 + BF.
    proj = apply_elite_pitcher_floor(proj, historical_k9, expected_bf)

    # Partial ceiling pull. Keeps distributions alive without blindly forcing overs.
    if p90 is not None and p90 > proj:
        ceiling_weight = 0.12 + min(upside, 100) / 100.0 * 0.16
        proj += (p90 - proj) * ceiling_weight

    # Skill/opportunity nudges.
    if pk >= 0.30 or historical_k9 >= 10.0:
        proj += 0.30
    elif pk >= 0.27 or historical_k9 >= 9.0:
        proj += 0.18
    elif pk >= 0.245:
        proj += 0.08
    elif pk <= 0.205:
        proj -= 0.08

    if ok >= 0.255:
        proj += 0.22
    elif ok >= 0.240:
        proj += 0.12
    elif ok <= 0.205 and pk < 0.255:
        proj -= 0.12

    if expected_bf >= 26:
        proj += 0.28
    elif expected_bf >= 24:
        proj += 0.14
    elif expected_bf <= 18:
        proj -= 0.22

    if pitch_factor >= 1.025:
        proj += 0.10
    elif pitch_factor <= 0.975 and pk < 0.255:
        proj -= 0.05

    if stat_whiff is not None:
        if stat_whiff >= 31:
            proj += 0.18
        elif stat_whiff >= 27:
            proj += 0.08
    elif stat_csw is not None:
        if stat_csw >= 31:
            proj += 0.12
        elif stat_csw >= 29:
            proj += 0.06

    recent_max, recent_avg, recent_n = kproj_recent_ceiling_stats(p)
    if recent_n:
        if recent_avg >= 6.0:
            proj += 0.25
        elif recent_avg >= 5.0:
            proj += 0.12
        if recent_max >= 9:
            proj += 0.24
        elif recent_max >= 7:
            proj += 0.12

    # Smart edge upgrades: small capped projection confidence nudge.
    smart_nudge, smart_label, smart_note = smart_edge_projection_nudge(p)
    proj += smart_nudge

    # Risk stays, but it cannot erase true K skill unless ceiling risk is low.
    rd = str(p.get("run_damage_risk_level") or "").upper()
    leash = str(p.get("leash_risk") or "").upper()
    ceiling_risk, _ = kproj_ceiling_risk_score(p)
    if rd == "EXTREME" and ceiling_risk < 45 and upside < 55:
        proj -= 0.18
    elif rd == "HIGH" and ceiling_risk < 35 and upside < 50:
        proj -= 0.08
    if leash in ["SHORT_RECENT_STARTS", "HIGH_PITCH_COUNT", "HIGH_RECENT_WORKLOAD"] and ceiling_risk < 45 and upside < 55:
        proj -= 0.10

    true_floor, _floor_note = kproj_true_projection_floor(p)
    if true_floor is not None and proj < true_floor:
        proj += min(true_floor - proj, KPROJ_MAX_PROJECTION_LIFT)

    # Hard suppression cap: confirmed starters with ceiling cannot be smashed below true talent/recent form.
    if kproj_is_confirmed_starter_like(p):
        if ceiling_risk >= KPROJ_CEILING_RISK_WARN_UNDER or historical_k9 >= 9.0 or recent_max >= 7:
            proj = max(proj, talent_base * KPROJ_TOTAL_SUPPRESSION_CAP, recent_form_proj * 0.88)

    recent_rows_wl2 = p.get("recent_rows") or p.get("Recent Rows") or []
    proj, expected_bf, wl2_prof = apply_workload_leash_2_to_projection(p, proj, expected_bf, recent_rows_wl2)
    if "apply_team_manager_hook_profile" in globals():
        proj, expected_bf, team_hook_prof = apply_team_manager_hook_profile(p, proj, expected_bf)
    recent_rows_micro = p.get("recent_rows") or p.get("Recent Rows") or []
    proj, expected_bf, pitch_trend_prof = apply_pitch_count_trend_overlay(p, proj, expected_bf, recent_rows_micro)
    proj, umpire_micro_prof = apply_umpire_micro_overlay(p, proj)
    proj, expected_bf, weather_upgrade_prof = apply_weather_engine_upgrade_overlay(p, proj, expected_bf)
    active_line_for_volume = safe_float(p.get("line") or p.get("Line") or p.get("UD/Line") or p.get("active_line"))
    proj, volume_safety_prof = apply_high_projection_volume_safety(p, proj, active_line_for_volume, expected_bf)
    return round(float(clamp(proj, 0.0, 15.0)), 2)

# =========================
# v11.17+ SAFETY GATES — decision/risk only
# Keeps K projection math untouched. Tightens official picks.
# =========================
KPROJ_MIN_OFFICIAL_GAP_OVER = 1.00
KPROJ_MIN_OFFICIAL_GAP_UNDER = 1.75
KPROJ_MIN_LEAN_GAP_OVER = 0.55
KPROJ_MIN_LEAN_GAP_UNDER = 1.15
KPROJ_MIN_OFFICIAL_HIT_RATE = 0.62
KPROJ_MIN_LEAN_HIT_RATE = 0.56


# =========================
# TRUE PROJECTION GUARD SETTINGS
# =========================
# These protect against fake-low K PROJ outcomes like:
# - starter with real K ceiling getting pushed to 2-3 Ks
# - official UNDER caused by stacked small penalties
# They DO NOT blindly boost every pitcher. They only activate when starter role,
# BF floor, recent ceiling, or K-stuff signals show spike risk.
KPROJ_TRUE_GUARD_ENABLED = True
KPROJ_CEILING_RISK_BLOCK_UNDER = 46
KPROJ_CEILING_RISK_WARN_UNDER = 34
KPROJ_MAX_PROJECTION_LIFT = 3.25
KPROJ_MIN_STARTER_BF_FOR_FLOOR = 17.0
KPROJ_TOTAL_SUPPRESSION_CAP = 0.92  # K PROJ should not fall far below true-talent baseline when K ceiling is real
KPROJ_TRUE_TALENT_BLEND_WEIGHT = 0.72
KPROJ_MAX_NEGATIVE_SUPPRESSION_STARTER = 0.88
KPROJ_MIN_UNDER_EDGE_NO_CEILING = 2.00


def kproj_recent_ceiling_stats(p):
    vals = [safe_float(x, None) for x in (p.get("last_10_ks") or [])[:10]]
    vals = [float(x) for x in vals if x is not None]
    if not vals:
        return 0.0, 0.0, 0
    return float(max(vals)), float(sum(vals[:5]) / max(1, len(vals[:5]))), len(vals)


def kproj_is_confirmed_starter_like(p):
    role = str(p.get("role") or p.get("pitcher_role") or p.get("probable_role") or "").lower()
    return bool(
        p.get("is_starter") is True
        or p.get("pitcher_confirmed") is True
        or p.get("starter_confirmed") is True
        or p.get("probable_pitcher") is True
        or p.get("probable") is True
        or "starter" in role
    )


def kproj_ceiling_risk_score(p):
    """0-100 risk that an UNDER can get nuked by a K spike."""
    score = 0.0
    notes = []
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    ok = safe_float(p.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    p90 = safe_float(p.get("p90"))
    upside = safe_float(p.get("elite_upside_score"), 0) or 0
    pitch_factor = safe_float(p.get("pitch_type_factor"), 1.0) or 1.0
    whiff = safe_float(p.get("statcast_whiff"))
    csw = safe_float(p.get("statcast_csw"))
    recent_max, recent_avg, recent_n = kproj_recent_ceiling_stats(p)

    if kproj_is_confirmed_starter_like(p):
        score += 10; notes.append("starter")
    if bf >= 22:
        score += 18; notes.append("strong BF")
    elif bf >= 19:
        score += 12; notes.append("playable BF")
    if pk >= 0.285:
        score += 28; notes.append("elite K%")
    elif pk >= 0.260:
        score += 22; notes.append("high K%")
    elif pk >= 0.240:
        score += 14; notes.append("above avg K%")
    if ok >= 0.250:
        score += 18; notes.append("high opp K")
    elif ok >= 0.235:
        score += 12; notes.append("opp K help")
    if recent_max >= 8:
        score += 22; notes.append("8+ recent ceiling")
    elif recent_max >= 6:
        score += 15; notes.append("6+ recent ceiling")
    if recent_avg >= 5.5:
        score += 12; notes.append("hot recent K avg")
    elif recent_avg >= 4.8:
        score += 7; notes.append("decent recent K avg")
    if p90 is not None and p90 >= 7:
        score += 18; notes.append("high p90")
    elif p90 is not None and p90 >= 6:
        score += 12; notes.append("solid p90")
    if upside >= 70:
        score += 18; notes.append("elite upside")
    elif upside >= 55:
        score += 12; notes.append("upside")
    if pitch_factor >= 1.035:
        score += 12; notes.append("pitch mix plus")
    elif pitch_factor >= 1.015:
        score += 7; notes.append("pitch mix slight plus")
    if whiff is not None and whiff >= 29:
        score += 14; notes.append("whiff plus")
    elif csw is not None and csw >= 30:
        score += 10; notes.append("CSW plus")

    return int(clamp(score, 0, 100)), "; ".join(notes)


def kproj_true_projection_floor(p):
    """Projection floor so stacked penalties cannot create fake-low K PROJ."""
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    p90 = safe_float(p.get("p90"))
    upside = safe_float(p.get("elite_upside_score"), 0) or 0
    recent_max, recent_avg, recent_n = kproj_recent_ceiling_stats(p)
    ceiling_risk, _ = kproj_ceiling_risk_score(p)

    if not KPROJ_TRUE_GUARD_ENABLED:
        return None, "true guard off"
    if not kproj_is_confirmed_starter_like(p) or bf < KPROJ_MIN_STARTER_BF_FOR_FLOOR:
        return None, "no starter/BF floor"
    if ceiling_risk < KPROJ_CEILING_RISK_WARN_UNDER:
        return None, f"ceiling risk low {ceiling_risk}/100"

    talent_base = kproj_true_talent_baseline(p)

    # Stronger floors for true K arms. These are still below ceiling, but prevent 1-3 K nonsense.
    if pk >= 0.300:
        min_floor = 5.35
    elif pk >= 0.275:
        min_floor = 4.95
    elif pk >= 0.255:
        min_floor = 4.55
    elif pk >= 0.235:
        min_floor = 4.10
    else:
        min_floor = 3.45

    if bf < 20:
        min_floor -= 0.45
    elif bf >= 24:
        min_floor += 0.25

    if recent_max >= 8:
        min_floor += 0.45
    elif recent_max >= 6:
        min_floor += 0.25
    if recent_avg >= 5.5:
        min_floor += 0.25
    if p90 is not None and p90 >= 7:
        min_floor += 0.25
    if upside >= 70:
        min_floor += 0.25

    floor = max(talent_base * 0.88, min_floor)

    # Cap still prevents automatic overs on average arms.
    cap = 7.35 if pk >= 0.285 or upside >= 75 else 6.65 if pk >= 0.255 else 5.75
    floor = round(float(clamp(floor, 0.0, cap)), 2)
    return floor, f"true floor {floor} | talent base {talent_base} | ceiling risk {ceiling_risk}/100"


def kproj_role_stability_score(p):
    """0-100 role stability score. Used only for decision gating, not K projection."""
    score = 72.0
    notes = []

    role = str(p.get("role") or p.get("pitcher_role") or p.get("probable_role") or "").lower()
    starter_flag = (
        p.get("is_starter") is True
        or p.get("pitcher_confirmed") is True
        or p.get("starter_confirmed") is True
        or p.get("probable_pitcher") is True
        or p.get("probable") is True
    )
    expected_bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    exp_ip = expected_bf / 4.25

    if starter_flag is True or "starter" in role:
        score += 12
        notes.append("starter role")
    elif "opener" in role or "bulk" in role or "reliever" in role:
        score -= 22
        notes.append("opener/bulk/relief risk")
    else:
        score -= 6
        notes.append("role not fully confirmed")

    lineup_status = str(p.get("lineup_status") or "").upper()
    if "CONFIRMED" in lineup_status or "TRUE" in lineup_status:
        score += 8
        notes.append("true lineup")
    elif "FALLBACK" in lineup_status:
        score -= 8
        notes.append("fallback lineup")

    leash = str(p.get("leash_risk") or "").upper()
    if leash in ["SHORT_RECENT_STARTS", "HIGH_PITCH_COUNT", "HIGH_RECENT_WORKLOAD"]:
        score -= 14
        notes.append(f"leash {leash}")

    rd = str(p.get("run_damage_risk_level") or "").upper()
    if rd == "EXTREME":
        score -= 12
        notes.append("extreme run damage")
    elif rd == "HIGH":
        score -= 8
        notes.append("high run damage")

    if expected_bf < 16:
        score -= 18
        notes.append("low BF floor")
    elif expected_bf < 19:
        score -= 9
        notes.append("medium BF floor")
    elif expected_bf >= 22:
        score += 5
        notes.append("strong BF floor")

    return int(clamp(score, 0, 100)), "; ".join(notes), round(exp_ip, 2)


def kproj_starter_confirmation_score(p):
    """0-100 confidence that pitcher role/start context is stable."""
    score = 70.0
    notes = []

    probable = (
        p.get("probable_pitcher")
        or p.get("probable")
        or p.get("starter_confirmed")
        or p.get("pitcher_confirmed")
        or p.get("is_starter")
    )
    role = str(p.get("role") or p.get("pitcher_role") or "").lower()
    lineup_status = str(p.get("lineup_status") or "").upper()

    if probable is True or "starter" in role:
        score += 18
        notes.append("starter/probable confirmed")
    else:
        score -= 10
        notes.append("starter not fully confirmed")

    if "CONFIRMED" in lineup_status or "TRUE" in lineup_status:
        score += 8
    elif "FALLBACK" in lineup_status:
        score -= 8

    return int(clamp(score, 0, 100)), "; ".join(notes)


def kproj_probable_innings_floor(p):
    """Conservative innings floor proxy from expected BF and optional recent IP fields."""
    expected_bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    recent_ip = safe_float(p.get("recent_ip_avg"), None)
    if recent_ip is None:
        recent_ip = safe_float(p.get("recent_ip"), None)
    last_ip = safe_float(p.get("last_start_ip"), None)

    bf_ip = expected_bf / 4.25
    vals = [bf_ip]
    if recent_ip is not None:
        vals.append(recent_ip)
    if last_ip is not None:
        vals.append(last_ip)

    floor_ip = min(vals) if vals else bf_ip
    return round(float(clamp(floor_ip, 0.0, 8.0)), 2)


def kproj_distribution_profile(proj, line, p):
    """K UPSIDE TAB ONLY: true distribution layer.

    Returns floor / median / ceiling plus OVER and UNDER probabilities.
    This is not a forced over boost. It widens outcomes for volatile strikeout
    arms and makes UNDER confidence softer when the pitcher has real ceiling.
    """
    mean = safe_float(proj, 0.0) or 0.0
    line = safe_float(line)
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    ok = safe_float(p.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    bf = safe_float(p.get("expected_bf"), DEFAULT_BF) or DEFAULT_BF
    p90 = safe_float(p.get("p90"))
    upside = safe_float(p.get("elite_upside_score"), 0.0) or 0.0
    role_score, _, _ = kproj_role_stability_score(p)
    starter_score, _ = kproj_starter_confirmation_score(p)
    ip_floor = kproj_probable_innings_floor(p)
    ceiling_risk, _ = kproj_ceiling_risk_score(p)

    recent_vals = [safe_float(x, None) for x in (p.get("last_10_ks") or [])[:10]]
    recent_vals = [float(x) for x in recent_vals if x is not None]
    recent_sd = 0.0
    recent_max = 0.0
    recent_avg = 0.0
    if recent_vals:
        recent_avg = float(np.mean(recent_vals))
        recent_sd = float(np.std(recent_vals)) if len(recent_vals) >= 3 else 1.15
        recent_max = max(recent_vals)

    # Base spread: strikeouts are discrete and volatile. Higher talent/ceiling
    # expands the upside tail; poor role stability expands uncertainty both ways.
    std = 1.05
    std += min(0.75, max(0.0, recent_sd * 0.22))
    if pk >= 0.285:
        std += 0.25
    elif pk >= 0.255:
        std += 0.15
    if ok >= 0.240:
        std += 0.10
    if ceiling_risk >= 70:
        std += 0.28
    elif ceiling_risk >= 55:
        std += 0.16
    if upside >= 70:
        std += 0.20
    elif upside >= 55:
        std += 0.12
    if bf >= 26:
        std += 0.10
    if role_score < 60:
        std += 0.25
    if starter_score < 60:
        std += 0.18
    if ip_floor is not None and ip_floor < 4.0:
        std += 0.18

    # Keep probabilities realistic; do not allow fake 99% unless the edge is enormous.
    std = float(clamp(std, 0.95, 2.45))

    # Distribution anchors. p90 from the main simulation can inform the ceiling,
    # but cannot drag the current median around.
    floor = max(0.0, mean - 1.15 * std)
    median = mean
    ceiling = mean + 1.25 * std
    if p90 is not None and p90 > 0:
        ceiling = max(ceiling, (mean * 0.70) + (p90 * 0.30))
    if recent_max >= 8:
        ceiling = max(ceiling, mean + 1.45)
    elif recent_max >= 6:
        ceiling = max(ceiling, mean + 0.95)

    # Normal CDF approximation with continuity correction for strikeout counts.
    def norm_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    if line is None:
        over_prob = None
        under_prob = None
    else:
        over_needed = required_ks_for_over(line)
        # P(K >= over_needed) ~= P(X > over_needed - 0.5)
        threshold = over_needed - 0.5
        z = (threshold - mean) / max(std, 0.50)
        over_prob = 1 - norm_cdf(z)
        under_prob = 1 - over_prob

        # Soft UNDER protection: high-ceiling pitchers should rarely show extreme
        # UNDER confidence unless the projection gap is very large.
        if mean < line and ceiling_risk >= 60:
            under_prob = min(under_prob, 0.68 if ceiling_risk >= 75 else 0.72)
            over_prob = 1 - under_prob

        # Fallback lineups are uncertain; pull extreme probabilities slightly toward 50.
        lineup_status = str(p.get("lineup_status") or "").upper()
        if "FALLBACK" in lineup_status:
            over_prob = 0.50 + ((over_prob - 0.50) * 0.88)
            under_prob = 1 - over_prob

        over_prob = float(clamp(over_prob, 0.03, 0.97))
        under_prob = float(clamp(under_prob, 0.03, 0.97))

    return {
        "floor": round(float(floor), 2),
        "median": round(float(median), 2),
        "ceiling": round(float(ceiling), 2),
        "volatility": round(float(std), 2),
        "recent_avg": round(float(recent_avg), 2),
        "recent_max": round(float(recent_max), 2),
        "over_prob": None if over_prob is None else round(float(over_prob), 3),
        "under_prob": None if under_prob is None else round(float(under_prob), 3),
    }


def kproj_sim_hit_rate(proj, line, side, p):
    """Distribution-aware hit-rate proxy for the K PROJ / Upside tab."""
    line = safe_float(line)
    if line is None:
        return None
    dist = kproj_distribution_profile(proj, line, p)
    side_str = str(side).upper()
    if side_str.startswith("OVER"):
        return dist.get("over_prob")
    if side_str.startswith("UNDER"):
        return dist.get("under_prob")
    return 0.50

def kproj_confidence_tier(conf, hit_rate, gap, role_score):
    conf = safe_float(conf, 0.50) or 0.50
    hit_rate = safe_float(hit_rate, 0.50) or 0.50
    gap = abs(safe_float(gap, 0) or 0)

    if conf >= 0.66 and hit_rate >= 0.64 and gap >= 1.25 and role_score >= 72:
        return "A"
    if conf >= 0.62 and hit_rate >= 0.60 and gap >= 0.90 and role_score >= 62:
        return "B"
    if hit_rate >= 0.56 and gap >= 0.55:
        return "C"
    return "PASS"


def kproj_decision(p):
    """
    Projection-first decision logic for the K PROJ / Upside tab.

    Philosophy:
    1) Build the true K projection first.
    2) Use sim probability second.
    3) PASS only when data/role is bad or edge is truly too thin.
    4) Always keep directional output: PASS — OVER / PASS — UNDER.
    """
    line, line_source = kproj_line_for_display(p)
    proj = kproj_upside_projection(p)

    if line is None:
        return {
            "line": None, "line_source": line_source, "projection": proj,
            "side": "NO LINE", "lean_side": "NO LINE", "lean_gap": None,
            "confidence": None, "decision": "🚫 NO UD LINE", "over_needed": None,
            "under_max": None, "line_edge": None, "edge_display": "—", "edge_class": "yellow-badge",
            "hit_rate": None, "tier": "NO LINE", "role_score": None, "starter_score": None,
            "ip_floor": None, "edge_gap": None,
            "note": "No Underdog/active real line found"
        }

    over_needed = required_ks_for_over(line)
    under_max = max_ks_for_under(line)

    # True line edge: this drives model direction. Cash-number logic is still displayed.
    line_edge = round(float(proj - line), 2)
    abs_edge = abs(line_edge)
    model_side = "OVER" if proj >= line else "UNDER"

    # Cash-number edge: useful for explaining half-point lines.
    diff_to_over_cash = proj - over_needed
    diff_to_under_cash = under_max - proj
    pass_direction_gap = line_edge if model_side == "OVER" else -line_edge

    upside = safe_float(p.get("elite_upside_score"), 0.0) or 0.0
    pk = safe_float(p.get("pitcher_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K
    ok = safe_float(p.get("opp_k"), LEAGUE_AVG_K) or LEAGUE_AVG_K

    role_score, role_note, _ = kproj_role_stability_score(p)
    starter_score, starter_note = kproj_starter_confirmation_score(p)
    ip_floor = kproj_probable_innings_floor(p)
    ceiling_risk, ceiling_note = kproj_ceiling_risk_score(p)
    true_floor, true_floor_note = kproj_true_projection_floor(p)

    # Sim probability comes after projection direction.
    hit_rate = kproj_sim_hit_rate(proj, line, model_side, p)
    hit_rate_val = safe_float(hit_rate, 0.50) or 0.50

    # PASS should mean data/role problem or no meaningful edge, not fear of a good projection.
    bad_data = False
    bad_data_reasons = []
    if role_score < 45:
        bad_data = True; bad_data_reasons.append(f"bad role score {role_score}/100")
    if starter_score < 45:
        bad_data = True; bad_data_reasons.append(f"bad starter score {starter_score}/100")
    if ip_floor is not None and ip_floor < 2.6:
        bad_data = True; bad_data_reasons.append(f"bad IP floor {ip_floor}")

    side = "PASS"
    conf = hit_rate_val
    gap = abs_edge
    reasons = []

    if bad_data:
        side = "PASS"
        reasons.extend(bad_data_reasons)
    else:
        if model_side == "OVER":
            # Official OVER: projection edge + sim probability. Keep it usable.
            if abs_edge >= 0.75 and hit_rate_val >= 0.60:
                side = "OVER"
            elif abs_edge >= 0.30 and hit_rate_val >= 0.54:
                side = "OVER LEAN"
            else:
                side = "PASS"
                reasons.append("thin over edge / low sim probability")

            # Role/IP risk downgrades but does not erase direction.
            if side == "OVER" and (role_score < 58 or starter_score < 58 or (ip_floor is not None and ip_floor < 3.7)):
                side = "OVER LEAN"
                reasons.append("downgraded: role/IP floor risk")

        else:
            # Official UNDER is stricter because ceiling arms have been nuking unders.
            dangerous_under = (
                ceiling_risk >= KPROJ_CEILING_RISK_BLOCK_UNDER
                or upside >= 55
                or (pk >= 0.255 and ok >= 0.220)
            )

            if dangerous_under:
                side = "PASS"
                reasons.append(f"blocked under: ceiling/talent risk {ceiling_risk}/100")
            elif abs_edge >= 1.25 and hit_rate_val >= 0.62 and role_score >= 62:
                side = "UNDER"
            elif abs_edge >= 0.45 and hit_rate_val >= 0.55:
                side = "UNDER LEAN"
            else:
                side = "PASS"
                reasons.append("thin under edge / low sim probability")

    # Tier is informational. It should not override a valid projection+sim pick.
    tier = kproj_confidence_tier(conf, hit_rate, gap, role_score)
    if side in ["OVER", "UNDER"] and tier == "PASS":
        tier = "C"

    if side == "OVER":
        decision = "🔥 OVER" if hit_rate_val >= 0.64 and abs_edge >= 1.00 else "✅ OVER"
    elif side == "UNDER":
        decision = "🔥 UNDER" if hit_rate_val >= 0.65 and abs_edge >= 1.50 else "✅ UNDER"
    elif side == "OVER LEAN":
        decision = "⚠️ OVER LEAN"
    elif side == "UNDER LEAN":
        decision = "⚠️ UNDER LEAN"
    else:
        decision = f"🚫 PASS — {model_side}"

    edge_display = f"{line_edge:+.2f} K"
    if line_edge >= 1.5 or line_edge <= -1.25:
        edge_class = "good-badge"
    elif abs(line_edge) >= 0.75:
        edge_class = "yellow-badge"
    else:
        edge_class = "red-badge"

    note_parts = [
        f"Projection-first decision",
        f"Over needs {over_needed}+",
        f"Under wins {under_max} or fewer",
        f"line edge={line_edge:+.2f}",
        f"model lean={model_side}",
        f"hit={round(hit_rate_val * 100, 1)}%",
        f"tier={tier}",
        f"role={role_score}/100",
        f"starter={starter_score}/100",
        f"IP floor={ip_floor}",
        f"ceiling risk={ceiling_risk}/100",
        f"cash over edge={round(diff_to_over_cash, 2)}",
        f"cash under edge={round(diff_to_under_cash, 2)}",
    ]
    if ceiling_note:
        note_parts.append(ceiling_note)
    if true_floor_note:
        note_parts.append(true_floor_note)
    if role_note:
        note_parts.append(role_note)
    if starter_note:
        note_parts.append(starter_note)
    if reasons:
        note_parts.extend(reasons)

    return {
        "line": line, "line_source": line_source, "projection": proj,
        "side": side, "lean_side": model_side, "lean_gap": round(pass_direction_gap, 2),
        "confidence": round(conf, 3), "decision": decision,
        "over_needed": over_needed, "under_max": under_max,
        "line_edge": line_edge, "edge_display": edge_display, "edge_class": edge_class,
        "hit_rate": hit_rate, "tier": tier, "role_score": role_score,
        "starter_score": starter_score, "ip_floor": ip_floor, "edge_gap": round(gap, 2),
        "note": " | ".join(str(x) for x in note_parts if x)
    }

def kproj_bar_html(vals):
    vals = [safe_int(x, 0) or 0 for x in (vals or [])[:10]]
    if not vals:
        return "<span class='small-muted'>No recent starts</span>"
    mx = max(max(vals), 1)
    parts = []
    for v in vals:
        h = int(20 + (v / mx) * 42)
        color = "#31e84f" if v >= 6 else "#a92b2b" if v <= 3 else "#ffbe3c"
        parts.append(f"<span class='mini-k-bar-wrap'><span class='mini-k-bar' style='height:{h}px;background:{color};'></span><span class='mini-k-label'>{v}</span></span>")
    return "<div class='mini-k-bars'>" + "".join(parts) + "</div>"




# =========================
# MOBILE CLICKABLE ENVIRONMENT CARD UI
# UI only. Does not change projections.
# =========================
def _env_ui_clean_label(x):
    s = str(x or "UNKNOWN").replace("_", " ").strip()
    return " ".join(s.split()).title()

def _env_ui_badge_class(label):
    t = str(label or "").upper()
    if any(x in t for x in ["PLUS", "UP", "FRIENDLY", "STRONG"]):
        return "good-badge"
    if any(x in t for x in ["MINUS", "DOWN", "SUPPRESS", "WEAK", "RISK"]):
        return "red-badge"
    return "yellow-badge"

def render_environment_mobile_panel(p):
    """Clickable card section for pitch trend / weather / umpire notes."""
    p = p or {}
    pitch_label = p.get("Pitch Trend Label") or "PITCH_TREND_NEUTRAL"
    weather_label = p.get("Weather Upgrade Label") or "WEATHER_NEUTRAL"
    ump_label = p.get("Umpire Micro Label") or "UMPIRE_NEUTRAL_OR_UNKNOWN"

    pitch_badge = _env_ui_badge_class(pitch_label)
    weather_badge = _env_ui_badge_class(weather_label)
    ump_badge = _env_ui_badge_class(ump_label)

    pitch_note = p.get("Pitch Trend Note") or "Pitch count trend not strong enough to move projection."
    weather_note = p.get("Weather Upgrade Note") or "Weather is not creating a meaningful K adjustment."
    ump_note = p.get("Umpire Micro Note") or "Umpire impact is neutral or unavailable."

    pitch_k = safe_float(p.get("Pitch Trend K Nudge"), 0) or 0
    weather_k = safe_float(p.get("Weather Upgrade K Nudge"), 0) or 0
    weather_bf = safe_float(p.get("Weather Upgrade BF Adj"), 0) or 0
    ump_k = safe_float(p.get("Umpire Micro K Nudge"), 0) or 0

    with st.expander("📌 Matchup Factors: Pitch Trend • Weather • Umpire", expanded=False):
        st.markdown(f"""
        <div class="kpi-strip">
            <div class="kpi-box">
                <div class="kpi-label">📈 Pitch Trend</div>
                <div class="kpi-value"><span class="badge {pitch_badge}">{_env_ui_clean_label(pitch_label)}</span></div>
                <div class="kpi-sub">K Adj {pitch_k:+.2f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">🌦 Weather</div>
                <div class="kpi-value"><span class="badge {weather_badge}">{_env_ui_clean_label(weather_label)}</span></div>
                <div class="kpi-sub">K {weather_k:+.2f} | BF {weather_bf:+.2f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">👨‍⚖️ Umpire</div>
                <div class="kpi-value"><span class="badge {ump_badge}">{_env_ui_clean_label(ump_label)}</span></div>
                <div class="kpi-sub">K Adj {ump_k:+.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="small-muted">
            <b>Pitch Trend:</b> {pitch_note}<br>
            <b>Weather:</b> {weather_note}<br>
            <b>Umpire:</b> {ump_note}<br>\n            <b>Volume:</b> {p.get("Volume Safety Note") or "Volume safety clear."}<br>\n            <b>Needs 7+ Innings:</b> {p.get("Needs 7+ Innings Flag") or "NO"}
        </div>
        """, unsafe_allow_html=True)

        st.caption("Small capped tiebreakers only. Main projection still comes from pitcher skill, expected BF, matchup, lineup, WL2, and line value.")


def render_kproj_pitcher_card(p):
    d = kproj_decision(p)
    dist = kproj_distribution_profile(d.get("projection"), d.get("line"), p)
    putaway, put_label = kproj_putaway_value(p)
    put_display = "—" if putaway is None else f"{putaway:.1f}%"
    pk = safe_float(p.get("pitcher_k"), 0.0) or 0.0
    ok = safe_float(p.get("opp_k"), 0.0) or 0.0
    bf = safe_float(p.get("expected_bf"), 0.0) or 0.0
    line_display = "NO LINE" if d["line"] is None else f"{d['line']:.1f}"
    conf_display = "—" if d["confidence"] is None else f"{d['confidence']*100:.0f}%"
    dist_display = f"F {dist.get('floor')} | M {dist.get('median')} | C {dist.get('ceiling')}"
    edge_display = d.get("edge_display", "—")
    edge_class = d.get("edge_class", "yellow-badge")
    needs_display = "—" if d.get("over_needed") is None else f"{d.get('over_needed')}+"
    under_max_display = "—" if d.get("under_max") is None else f"{d.get('under_max')} or fewer"
    line_badge = "good-badge" if d["line_source"] == "Underdog" else "yellow-badge"
    lineup_badge = "good-badge" if p.get("lineup_locked") else "yellow-badge"
    recent_html = kproj_bar_html(p.get("last_10_ks"))
    st.markdown(f"""
    <div class="pick-card" style="border-color:rgba(90,100,255,.45);box-shadow:0 0 26px rgba(90,100,255,.16);">
      <div style="display:grid;grid-template-columns:1.25fr .75fr .75fr .75fr .9fr;gap:18px;align-items:center;">
        <div>
          <div class="player-name">{p.get('pitcher')}</div>
          <div class="small-muted">{p.get('matchup')} | {p.get('hand')}HP</div>
          <span class="badge {line_badge}">{d['line_source']} Line</span>
          <span class="badge {lineup_badge}">Lineup: {p.get('lineup_status')}</span>
          <span class="badge">K Upside: {p.get('elite_upside_score', 0)}/100</span>
        </div>
        <div><div class="small-muted">K PROJ</div><div class="big-number green">{d['projection']}</div><div class="small-muted">Exp BF {bf:.1f}</div></div>
        <div><div class="small-muted">Line</div><div class="big-number">{line_display}</div><div class="small-muted">Needs {needs_display}</div></div>
        <div><div class="small-muted">Edge</div><div class="big-number green">{edge_display}</div><div class="small-muted">Under wins {under_max_display}</div></div>
        <div><div class="small-muted">Decision</div><div class="big-number green" style="font-size:32px;">{d['decision']}</div><div class="small-muted">Confidence {conf_display}</div></div>
      </div>
      <div class="hr-soft"></div>
      <div class="kpi-strip" style="grid-template-columns:repeat(5,minmax(0,1fr));">
        <div class="kpi-box"><div class="kpi-label">{put_label}</div><div class="kpi-value">{put_display}</div><div class="kpi-sub">Putaway/stuff proxy</div></div>
        <div class="kpi-box"><div class="kpi-label">Pitcher K%</div><div class="kpi-value">{pk*100:.1f}%</div><div class="kpi-sub">Season/recent blend</div></div>
        <div class="kpi-box"><div class="kpi-label">Opp K%</div><div class="kpi-value">{ok*100:.1f}%</div><div class="kpi-sub">Lineup/team matchup</div></div>
        <div class="kpi-box"><div class="kpi-label">Distribution</div><div class="kpi-value" style="font-size:17px;">{dist_display}</div><div class="kpi-sub">Floor | Median | Ceiling</div></div>
        <div class="kpi-box"><div class="kpi-label">Last 10 Starts</div>{recent_html}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    lineup_rows = p.get("lineup_rows") or []
    if lineup_rows:
        with st.expander(f"Batter-by-batter K matchup — {p.get('pitcher')}", expanded=False):
            rows = []
            for i, r in enumerate(lineup_rows[:9], start=1):
                rows.append({
                    "#": i,
                    "Batter": r.get("Batter") or r.get("Name") or r.get("Player") or r.get("player") or "",
                    "K%": r.get("K%") if r.get("K%") is not None else r.get("Raw_K_Rate"),
                    "Source": r.get("K Source") or r.get("Source") or r.get("K_Note") or "",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No confirmed batter-by-batter lineup yet. This tab will improve when lineups lock.")


# =========================
# UNIVERSAL K PROJ DISPLAY SYNC
# Display-only helper. Matches K Upside tab exactly.
# Does NOT change projection math, sims, probabilities, or decisions.
# =========================

    render_environment_mobile_panel(p)
def display_kproj_truth(p):
    """Exact displayed K PROJ used by K Upside tab."""
    try:
        d = kproj_decision(p)
        v = safe_float(d.get("projection"), None)
        if v is not None:
            return round(v, 2)
    except Exception:
        pass
    for key in ["K PROJ", "k_proj", "kproj", "k_projection", "raw_k_proj", "base_k_proj", "upside_projection", "K_PROJ"]:
        v = safe_float((p or {}).get(key), None)
        if v is not None:
            return round(v, 2)
    return None if safe_float((p or {}).get("projection"), None) is None else round(safe_float((p or {}).get("projection")), 2)



# =========================
# PROJECTION-FIRST CONFIDENCE / PASS LOOSENER
# Clean confidence layer:
# - Does NOT remove PASS
# - Does NOT force picks
# - Upgrades only good borderline PASS plays into MONITOR / LEAN
# - Keeps strict PASS for low-BF, volatile, pitch-alert, tiny-edge plays
# =========================
PROJECTION_FIRST_CONFIDENCE_ENABLED = True
PASS_OVER_UPGRADE_EDGE = 0.50
PASS_UNDER_UPGRADE_EDGE = 0.70
PASS_UPGRADE_MIN_CONF = 57.0
PASS_UPGRADE_MIN_LEASH = 44
PASS_UPGRADE_MIN_SAFETY_SCORE = 40

def projection_first_confidence_label(row=None, base_decision=None, base_tier=None):
    row = row or {}
    if not PROJECTION_FIRST_CONFIDENCE_ENABLED:
        return base_decision, base_tier, 0, "OFF", "Projection-first confidence disabled"

    proj = safe_float(row.get("K PROJ") or row.get("Raw K PROJ") or row.get("projection") or row.get("k_proj"), None)
    line = safe_float(row.get("line") or row.get("UD/Line") or row.get("Line") or row.get("underdog_line"), None)
    if proj is None or line is None:
        return base_decision, base_tier, 0, "NO_LINE", "No usable line/projection"

    side = "OVER" if proj > line else "UNDER"
    edge = abs(proj - line)

    lineup = str(row.get("lineup_status") or row.get("Lineup") or "").upper()
    pitch_alert = str(row.get("Pitch Alert") or row.get("pitch_alert") or "").upper()
    safety_tag = str(row.get("Safety Tag") or row.get("safety_tag") or "").upper()
    safety_score = safe_float(row.get("Safety Score") or row.get("safety_score"), 50) or 50
    exp_bf = safe_float(row.get("expected_bf") or row.get("Exp BF"), None)
    leash_score = safe_float(row.get("smart_leash_score") or row.get("Leash Score"), 50) or 50
    smart_label = str(row.get("smart_edge_label") or "").upper()
    smart_nudge = safe_float(row.get("smart_edge_nudge"), 0) or 0
    conf = safe_float(row.get("Confidence %") or row.get("confidence"), None)
    if conf is not None and conf <= 1:
        conf *= 100

    hard_risks = []
    if exp_bf is not None and exp_bf <= 16.5:
        hard_risks.append("LOW_BF")
    if "VOLATILE" in safety_tag and safety_score < PASS_UPGRADE_MIN_SAFETY_SCORE:
        hard_risks.append("VOLATILE_LOW_SCORE")
    if any(x in pitch_alert for x in ["MEDIUM_ALERT", "HIGH_ALERT", "STRICT", "SHORT", "LIMIT"]):
        hard_risks.append("PITCH_ALERT")
    if "FALLBACK" in lineup and edge < 0.85:
        hard_risks.append("FALLBACK_SMALL_EDGE")
    if leash_score < PASS_UPGRADE_MIN_LEASH:
        hard_risks.append("LOW_LEASH")

    edge_need = PASS_OVER_UPGRADE_EDGE if side == "OVER" else PASS_UNDER_UPGRADE_EDGE
    conf_ok = True if conf is None else conf >= PASS_UPGRADE_MIN_CONF
    smart_ok = smart_nudge >= -0.10 and smart_label != "SMART_CUT"

    if hard_risks:
        return base_decision, base_tier, 0, "STRICT_PASS", " | ".join(hard_risks[:4])

    if edge >= edge_need and conf_ok and smart_ok:
        if edge >= edge_need + 0.35:
            new_decision = f"✅ PROJECTION LEAN — {side}"
            new_tier = "B" if base_tier in [None, "", "PASS"] else base_tier
            return new_decision, new_tier, 8, "UPGRADED_LEAN", f"{side} edge {edge:.2f}; projection-first confidence"
        new_decision = f"⚠️ MONITOR — {side}"
        new_tier = "C" if base_tier in [None, "", "PASS"] else base_tier
        return new_decision, new_tier, 5, "UPGRADED_MONITOR", f"{side} edge {edge:.2f}; monitor not forced"

    return base_decision, base_tier, 0, "UNCHANGED", f"{side} edge {edge:.2f}; did not meet upgrade gate"

def apply_projection_first_confidence_to_row(row):
    if not isinstance(row, dict):
        return row
    base_decision = row.get("Decision") or row.get("decision") or row.get("bet_action") or row.get("Main Engine Action")
    base_tier = row.get("Tier") or row.get("tier")
    new_decision, new_tier, boost, label, note = projection_first_confidence_label(row, base_decision, base_tier)
    row["Projection First Label"] = label
    row["Projection First Note"] = note
    row["Projection First Boost"] = boost
    row["Projection First Decision"] = new_decision
    row["Projection First Tier"] = new_tier
    return row



# =========================
# CLOSE-LINE ACE CEILING PROTECTION
# Classification only. No global projection boost.
# =========================
ACE_CEILING_PROTECTION_ENABLED = True
ACE_CLOSE_UNDER_GAP_MAX = 0.60
ACE_MIN_CEILING_OVER_LINE = 2.00
ACE_MIN_K_PCT = 0.265
ACE_MIN_EXP_BF = 20.5
ACE_MIN_IP_FLOOR = 4.8
ACE_PROTECTION_SCORE_BOOST = 6

def ace_ceiling_under_protection(row=None, base_decision=None, base_tier=None):
    row = row or {}
    if not ACE_CEILING_PROTECTION_ENABLED:
        return base_decision, base_tier, 0, "OFF", "Ace ceiling protection disabled"

    proj = safe_float(row.get("K PROJ") or row.get("Raw K PROJ") or row.get("projection") or row.get("k_proj"), None)
    line = safe_float(row.get("line") or row.get("UD/Line") or row.get("Line") or row.get("underdog_line"), None)
    if proj is None or line is None:
        return base_decision, base_tier, 0, "NO_LINE", "No usable projection/line"

    if not (proj < line):
        return base_decision, base_tier, 0, "NOT_UNDER", "Projection is not below line"

    gap = line - proj
    if gap > ACE_CLOSE_UNDER_GAP_MAX:
        return base_decision, base_tier, 0, "UNDER_GAP_OK", f"Under gap {gap:.2f} not close enough"

    ceiling = safe_float(row.get("Ceiling") or row.get("ceiling") or row.get("p90") or row.get("P90"), None)
    pitcher_k = safe_float(row.get("Pitcher K%") or row.get("pitcher_k") or row.get("pitcher_k_pct"), None)
    if pitcher_k is not None and pitcher_k > 1:
        pitcher_k /= 100.0
    exp_bf = safe_float(row.get("Exp BF") or row.get("expected_bf"), None)
    ip_floor = safe_float(row.get("IP Floor") or row.get("ip_floor"), None)
    leash_score = safe_float(row.get("Leash Score") or row.get("smart_leash_score"), 50) or 50
    pitch_count_score = safe_float(row.get("Pitch Count Score") or row.get("smart_pitch_count_score"), 50) or 50

    elite_k = pitcher_k is not None and pitcher_k >= ACE_MIN_K_PCT
    ceiling_ok = ceiling is not None and ceiling >= line + ACE_MIN_CEILING_OVER_LINE
    workload_ok = (
        (exp_bf is not None and exp_bf >= ACE_MIN_EXP_BF) or
        (ip_floor is not None and ip_floor >= ACE_MIN_IP_FLOOR) or
        leash_score >= 58 or
        pitch_count_score >= 65
    )

    if elite_k and ceiling_ok and workload_ok:
        new_decision = f"⚠️ ACE OVER LEAN — O {line}"
        new_tier = "C" if base_tier in [None, "", "PASS"] else base_tier
        note = f"Close under gap {gap:.2f}; elite K ceiling risk; ceiling {ceiling}"
        return new_decision, new_tier, ACE_PROTECTION_SCORE_BOOST, "ACE_OVER_LEAN", note

    if ceiling_ok and workload_ok and gap <= 0.35:
        return "🚫 PASS — UNDER / CEILING RISK", "PASS", 3, "UNDER_CEILING_RISK", f"Close under gap {gap:.2f}; ceiling clears line"

    return base_decision, base_tier, 0, "UNCHANGED", f"Close under checked; elite={elite_k}, ceiling={ceiling_ok}, workload={workload_ok}"

def apply_ace_ceiling_protection_to_row(row):
    if not isinstance(row, dict):
        return row
    base_decision = row.get("Projection First Decision") or row.get("Decision") or row.get("decision") or row.get("bet_action")
    base_tier = row.get("Projection First Tier") or row.get("Tier") or row.get("tier")
    new_decision, new_tier, boost, label, note = ace_ceiling_under_protection(row, base_decision, base_tier)
    row["Ace Ceiling Label"] = label
    row["Ace Ceiling Note"] = note
    row["Ace Ceiling Boost"] = boost
    row["Ace Ceiling Decision"] = new_decision
    row["Ace Ceiling Tier"] = new_tier
    return row




# =========================
# WORKLOAD / LEASH 2.0 + EXPANDED CEILING RECOGNITION
# Real-data layer. No blanket projection boost.
# Focus: workload/leash first, Kyle Harrison type ceiling second, under-risk classification third.
# =========================
WORKLOAD_LEASH_2_ENABLED = True
WL2_MAX_K_NUDGE = 0.42
WL2_MAX_BF_BOOST = 1.20
WL2_MAX_BF_CUT = -1.60
WL2_STRONG_BF = 23.0
WL2_STABLE_BF = 21.0
WL2_HIGH_PITCHES = 92.0
WL2_EFFICIENT_PPB = 3.75
WL2_HIGH_K_PCT = 0.265
WL2_ELITE_PUTAWAY = 30.0
WL2_LINEUP_K_PRESSURE = 23.0
WL2_CEILING_OVER_LINE = 2.0

def _wl2_mean(vals):
    xs = []
    for v in vals or []:
        x = safe_float(v, None)
        if x is not None:
            xs.append(x)
    return float(np.mean(xs)) if xs else None

def _wl2_recent_vals(recent_rows, key, n=5):
    vals = []
    for r in (recent_rows or [])[:n]:
        if isinstance(r, dict):
            vals.append(r.get(key))
    return vals

def workload_leash_2_profile(row=None, recent_rows=None):
    row = row or {}
    recent_rows = recent_rows or row.get('recent_rows') or row.get('Recent Rows') or []
    exp_bf = safe_float(row.get('Exp BF') or row.get('expected_bf'), None)
    ip_floor = safe_float(row.get('IP Floor') or row.get('ip_floor'), None)
    pitcher_k = safe_float(row.get('Pitcher K%') or row.get('pitcher_k') or row.get('pitcher_k_pct'), None)
    if pitcher_k is not None and pitcher_k > 1:
        pitcher_k /= 100.0
    putaway = safe_float(row.get('Putaway/Whiff') or row.get('putaway_whiff') or row.get('putaway_rate') or row.get('Putaway'), None)
    lineup_k = safe_float(row.get('Opp K%') or row.get('Lineup K Pressure') or row.get('opp_k_pct') or row.get('lineup_k_pressure'), None)
    if lineup_k is not None and lineup_k <= 1:
        lineup_k *= 100.0
    avg_bf_l3 = _wl2_mean(_wl2_recent_vals(recent_rows, 'BF', 3))
    avg_bf_l5 = _wl2_mean(_wl2_recent_vals(recent_rows, 'BF', 5))
    avg_ip_l3 = _wl2_mean(_wl2_recent_vals(recent_rows, 'IP_float', 3))
    avg_ip_l5 = _wl2_mean(_wl2_recent_vals(recent_rows, 'IP_float', 5))
    avg_pitches_l3 = _wl2_mean(_wl2_recent_vals(recent_rows, 'Pitches', 3))
    avg_pitches_l5 = _wl2_mean(_wl2_recent_vals(recent_rows, 'Pitches', 5))
    avg_ks_l5 = _wl2_mean(_wl2_recent_vals(recent_rows, 'Ks', 5))
    avg_bb_l3 = _wl2_mean(_wl2_recent_vals(recent_rows, 'BB', 3))
    ppb_l3 = avg_pitches_l3 / avg_bf_l3 if avg_pitches_l3 and avg_bf_l3 and avg_bf_l3 > 0 else None
    score = 50.0; bf_adj = 0.0; k_nudge = 0.0; flags = []
    bf_anchor = avg_bf_l3 * .60 + avg_bf_l5 * .40 if avg_bf_l3 and avg_bf_l5 else (avg_bf_l3 or avg_bf_l5)
    if bf_anchor is not None:
        if bf_anchor >= 24: score += 18; bf_adj += .75; flags.append('STRONG_RECENT_BF')
        elif bf_anchor >= 22: score += 10; bf_adj += .35; flags.append('STABLE_RECENT_BF')
        elif bf_anchor <= 17: score -= 18; bf_adj -= .90; flags.append('LOW_RECENT_BF')
        elif bf_anchor <= 19: score -= 8; bf_adj -= .40; flags.append('LIGHT_RECENT_BF')
    ip_anchor = avg_ip_l3 * .60 + avg_ip_l5 * .40 if avg_ip_l3 and avg_ip_l5 else (avg_ip_l3 or avg_ip_l5)
    if ip_anchor is not None:
        if ip_anchor >= 6.0: score += 12; bf_adj += .35; flags.append('DEEP_IP_TREND')
        elif ip_anchor <= 4.3: score -= 16; bf_adj -= .75; flags.append('SHORT_IP_TREND')
    if avg_pitches_l5 is not None:
        if avg_pitches_l5 >= WL2_HIGH_PITCHES: score += 9; bf_adj += .25; flags.append('PITCH_COUNT_LEASH')
        elif avg_pitches_l5 <= 72: score -= 12; bf_adj -= .50; flags.append('LOW_PITCH_COUNT_LEASH')
    if ppb_l3 is not None:
        if ppb_l3 <= WL2_EFFICIENT_PPB and (avg_pitches_l3 or 0) >= 82: score += 7; bf_adj += .20; flags.append('EFFICIENT_VOLUME')
        elif ppb_l3 >= 4.35: score -= 10; bf_adj -= .40; flags.append('PITCH_STRESS')
    if avg_bb_l3 is not None and avg_bb_l3 >= 3: score -= 8; bf_adj -= .35; flags.append('WALK_STRESS')
    if exp_bf is not None:
        if exp_bf >= WL2_STRONG_BF: score += 10; flags.append('ENGINE_STRONG_BF')
        elif exp_bf >= WL2_STABLE_BF: score += 5; flags.append('ENGINE_STABLE_BF')
        elif exp_bf <= 16.5: score -= 20; flags.append('ENGINE_LOW_BF')
    if ip_floor is not None:
        if ip_floor >= 5.5: score += 8; flags.append('HIGH_IP_FLOOR')
        elif ip_floor < 4.0: score -= 12; flags.append('LOW_IP_FLOOR')
    ceiling_score = 0.0
    if pitcher_k is not None:
        if pitcher_k >= .30: ceiling_score += 28; flags.append('ELITE_K_PROFILE')
        elif pitcher_k >= WL2_HIGH_K_PCT: ceiling_score += 18; flags.append('HIGH_K_PROFILE')
    if putaway is not None:
        if putaway >= 35: ceiling_score += 22; flags.append('ELITE_PUTAWAY')
        elif putaway >= WL2_ELITE_PUTAWAY: ceiling_score += 14; flags.append('PLUS_PUTAWAY')
    if lineup_k is not None:
        if lineup_k >= 25: ceiling_score += 16; flags.append('HIGH_K_LINEUP')
        elif lineup_k >= WL2_LINEUP_K_PRESSURE: ceiling_score += 9; flags.append('PLUS_K_LINEUP')
    if avg_ks_l5 is not None:
        if avg_ks_l5 >= 6.5: ceiling_score += 14; flags.append('RECENT_K_CEILING')
        elif avg_ks_l5 <= 3.0: ceiling_score -= 8; flags.append('LOW_RECENT_KS')
    workload_ok = score >= 58; ceiling_ok = ceiling_score >= 38
    if workload_ok and ceiling_ok:
        k_nudge += .26
        if score >= 72 and ceiling_score >= 54: k_nudge += .12
        flags.append('WL2_CEILING_UPSIDE')
    elif ceiling_ok and score < 48:
        k_nudge -= .12; flags.append('CEILING_BUT_LEASH_BLOCKED')
    bf_adj = float(clamp(bf_adj, WL2_MAX_BF_CUT, WL2_MAX_BF_BOOST))
    k_nudge = float(clamp(k_nudge, -.22, WL2_MAX_K_NUDGE))
    score = int(clamp(round(score), 0, 100)); ceiling_score = int(clamp(round(ceiling_score), 0, 100))
    leash_label = 'STRONG_LEASH_2' if score >= 72 else 'STABLE_LEASH_2' if score >= 58 else 'FRAGILE_LEASH_2' if score >= 42 else 'DANGER_LEASH_2'
    ceiling_label = 'ELITE_CEILING_2' if ceiling_score >= 54 else 'PLUS_CEILING_2' if ceiling_score >= 38 else 'NORMAL_CEILING_2' if ceiling_score >= 22 else 'LOW_CEILING_2'
    return {'active': True, 'leash_score_2': score, 'ceiling_score_2': ceiling_score, 'leash_label_2': leash_label, 'ceiling_label_2': ceiling_label, 'bf_adj_2': round(bf_adj,2), 'k_nudge_2': round(k_nudge,2), 'flags_2': flags[:10], 'note': f'{leash_label} / {ceiling_label} | BF adj {bf_adj:+.2f} | K nudge {k_nudge:+.2f}'}

def apply_workload_leash_2_to_projection(row=None, projection=None, expected_bf=None, recent_rows=None):
    row = row or {}
    if not WORKLOAD_LEASH_2_ENABLED:
        return projection, expected_bf, {'active': False, 'note': 'WL2 off'}
    prof = workload_leash_2_profile(row, recent_rows)
    proj = safe_float(projection, None); bf = safe_float(expected_bf, None)
    if proj is not None:
        proj = round(float(clamp(proj + prof.get('k_nudge_2', 0), 0, 18)), 3)
    if bf is not None:
        bf = round(float(clamp(bf + prof.get('bf_adj_2', 0), 10, 34)), 3)
    row['WL2 Leash Score'] = prof.get('leash_score_2'); row['WL2 Ceiling Score'] = prof.get('ceiling_score_2')
    row['WL2 Label'] = prof.get('leash_label_2'); row['WL2 Ceiling'] = prof.get('ceiling_label_2')
    row['WL2 BF Adj'] = prof.get('bf_adj_2'); row['WL2 K Nudge'] = prof.get('k_nudge_2')
    row['WL2 Flags'] = ' | '.join(prof.get('flags_2', [])); row['WL2 Note'] = prof.get('note')
    return proj, bf, prof

def workload_leash_2_under_risk(row=None, base_decision=None, base_tier=None):
    row = row or {}
    proj = safe_float(row.get('K PROJ') or row.get('Raw K PROJ') or row.get('projection') or row.get('k_proj'), None)
    line = safe_float(row.get('line') or row.get('UD/Line') or row.get('Line') or row.get('underdog_line'), None)
    if proj is None or line is None or not (proj < line):
        return base_decision, base_tier, 0, 'NO_UNDER_RISK', 'Not an under or no line'
    gap = line - proj
    leash_score = safe_float(row.get('WL2 Leash Score'), row.get('Leash Score') or 50) or 50
    ceiling_score = safe_float(row.get('WL2 Ceiling Score'), 0) or 0
    exp_bf = safe_float(row.get('Exp BF') or row.get('expected_bf'), None)
    ceiling = safe_float(row.get('Ceiling') or row.get('ceiling'), None)
    if gap <= .35:
        return '🚫 PASS — UNDER TOO CLOSE', 'PASS', 4, 'UNDER_TOO_CLOSE', f'Under gap only {gap:.2f}'
    if gap <= .75 and (ceiling_score >= 38 or leash_score >= 70 or (exp_bf is not None and exp_bf >= 23)):
        return '🚫 PASS — UNDER VOLUME/CEILING RISK', 'PASS', 5, 'UNDER_VOLUME_CEILING_RISK', f'Gap {gap:.2f}; leash {leash_score}; ceiling {ceiling_score}'
    if gap <= 1.00 and ceiling is not None and ceiling >= line + WL2_CEILING_OVER_LINE and leash_score >= 65:
        return '🚫 PASS — UNDER CEILING PATH', 'PASS', 4, 'UNDER_CEILING_PATH', f'Gap {gap:.2f}; ceiling {ceiling:.1f}; leash {leash_score}'
    return base_decision, base_tier, 0, 'UNDER_OK', f'Under gap {gap:.2f} passed WL2'

def apply_workload_leash_2_classification(row):
    if not isinstance(row, dict): return row
    base_decision = row.get('Ace Ceiling Decision') or row.get('Projection First Decision') or row.get('Decision') or row.get('decision')
    base_tier = row.get('Ace Ceiling Tier') or row.get('Projection First Tier') or row.get('Tier') or row.get('tier')
    new_decision, new_tier, boost, label, note = workload_leash_2_under_risk(row, base_decision, base_tier)
    row['WL2 Under Risk Label'] = label; row['WL2 Under Risk Note'] = note; row['WL2 Under Risk Boost'] = boost
    row['WL2 Decision'] = new_decision; row['WL2 Tier'] = new_tier
    return row





# =========================
# TRUE PROJECTION PLUS: TEAM / MANAGER HOOK PROFILE
# Real-data learning layer:
# - Does NOT overwrite the previous Workload/Leash/Rotowire engine
# - Uses saved graded history when available
# - Uses current pitcher/team leash signals only as fallback
# - Applies tiny capped BF/K adjustments only when evidence is strong
# =========================
TEAM_MANAGER_HOOK_PROFILE_ENABLED = True
TEAM_HOOK_MIN_SAMPLES = 8
TEAM_HOOK_MAX_BF_ADJ = 0.85
TEAM_HOOK_MAX_K_NUDGE = 0.22

def _tmhp_team_key(row=None):
    row = row or {}
    raw = (
        row.get("team")
        or row.get("Team")
        or row.get("Pitcher Team")
        or row.get("pitcher_team")
        or row.get("ML Context Pick")
        or ""
    )
    try:
        return _rw_team_key(raw)
    except Exception:
        return str(raw or "").upper()[:3]

def build_team_manager_hook_profiles_from_results():
    """Build team/manager hook tendency from saved graded/result history.

    This is intentionally conservative because historical rows may not always
    contain BF or pitch-count fields. If not enough samples exist, it returns
    neutral profiles and the engine behaves like the previous file.
    """
    results = load_json(RESULT_LOG, [])
    teams = {}
    for r in results or []:
        if not isinstance(r, dict):
            continue
        team = _tmhp_team_key(r)
        if not team:
            continue

        # Try multiple possible columns because saved rows differ by version.
        exp_bf = safe_float(r.get("Exp BF") or r.get("expected_bf") or r.get("projected_bf") or r.get("bf_projection"), None)
        actual_bf = safe_float(r.get("Actual BF") or r.get("actual_bf") or r.get("batters_faced") or r.get("BF"), None)
        exp_ip = safe_float(r.get("IP Floor") or r.get("ip_floor") or r.get("expected_ip"), None)
        actual_ip = safe_float(r.get("Actual IP") or r.get("actual_ip") or r.get("innings_pitched"), None)
        pitches = safe_float(r.get("Pitches") or r.get("actual_pitches") or r.get("pitch_count"), None)

        # Need at least one volume signal.
        if actual_bf is None and actual_ip is None and pitches is None:
            continue

        d = teams.setdefault(team, {"n": 0, "bf_err": [], "ip_err": [], "pitches": [], "short_hooks": 0, "deep_hooks": 0})
        d["n"] += 1

        if actual_bf is not None and exp_bf is not None:
            d["bf_err"].append(actual_bf - exp_bf)
            if actual_bf <= 18:
                d["short_hooks"] += 1
            if actual_bf >= 24:
                d["deep_hooks"] += 1

        if actual_ip is not None and exp_ip is not None:
            d["ip_err"].append(actual_ip - exp_ip)
            if actual_ip <= 4.5:
                d["short_hooks"] += 1
            if actual_ip >= 6.0:
                d["deep_hooks"] += 1

        if pitches is not None:
            d["pitches"].append(pitches)
            if pitches <= 78:
                d["short_hooks"] += 1
            if pitches >= 95:
                d["deep_hooks"] += 1

    profiles = {}
    for team, d in teams.items():
        n = int(d.get("n") or 0)
        if n < TEAM_HOOK_MIN_SAMPLES:
            continue

        avg_bf_err = _wl2_mean(d.get("bf_err")) or 0.0
        avg_ip_err = _wl2_mean(d.get("ip_err")) or 0.0
        avg_pitches = _wl2_mean(d.get("pitches"))
        short_rate = d.get("short_hooks", 0) / max(1, n)
        deep_rate = d.get("deep_hooks", 0) / max(1, n)

        score = 50.0
        score += clamp(avg_bf_err * 4.0, -14, 14)
        score += clamp(avg_ip_err * 7.0, -10, 10)
        if avg_pitches is not None:
            score += clamp((avg_pitches - 86) * 0.85, -10, 12)
        score += clamp((deep_rate - short_rate) * 22, -16, 16)
        score = int(clamp(round(score), 0, 100))

        if score >= 66:
            label = "TEAM_LONG_LEASH"
        elif score <= 38:
            label = "TEAM_QUICK_HOOK"
        else:
            label = "TEAM_NEUTRAL_HOOK"

        profiles[team] = {
            "team": team,
            "samples": n,
            "score": score,
            "label": label,
            "avg_bf_error": round(avg_bf_err, 2),
            "avg_ip_error": round(avg_ip_err, 2),
            "avg_pitches": None if avg_pitches is None else round(avg_pitches, 1),
            "short_hook_rate": round(short_rate, 3),
            "deep_hook_rate": round(deep_rate, 3),
        }
    return profiles

def team_manager_hook_profile_for_row(row=None):
    row = row or {}
    team = _tmhp_team_key(row)
    profiles = build_team_manager_hook_profiles_from_results()
    prof = profiles.get(team)

    if prof:
        return prof

    # Fallback is neutral and uses current row signals only for display.
    # It does not force a team hook adjustment without real saved samples.
    return {
        "team": team,
        "samples": 0,
        "score": 50,
        "label": "TEAM_HOOK_NEUTRAL_NO_SAMPLE",
        "avg_bf_error": 0,
        "avg_ip_error": 0,
        "avg_pitches": None,
        "short_hook_rate": None,
        "deep_hook_rate": None,
    }

def apply_team_manager_hook_profile(row=None, projection=None, expected_bf=None):
    row = row or {}
    if not TEAM_MANAGER_HOOK_PROFILE_ENABLED:
        return projection, expected_bf, {"active": False, "note": "Team manager hook profile off"}

    prof = team_manager_hook_profile_for_row(row)
    score = safe_float(prof.get("score"), 50) or 50
    samples = int(prof.get("samples") or 0)
    label = prof.get("label") or "TEAM_HOOK_NEUTRAL"

    bf_adj = 0.0
    k_nudge = 0.0

    # Only adjust when enough historical samples exist.
    if samples >= TEAM_HOOK_MIN_SAMPLES:
        if score >= 66:
            bf_adj = clamp((score - 64) / 20.0, 0.10, TEAM_HOOK_MAX_BF_ADJ)
            k_nudge = clamp(bf_adj * 0.16, 0.02, TEAM_HOOK_MAX_K_NUDGE)
        elif score <= 38:
            bf_adj = -clamp((40 - score) / 20.0, 0.10, TEAM_HOOK_MAX_BF_ADJ)
            k_nudge = -clamp(abs(bf_adj) * 0.14, 0.02, TEAM_HOOK_MAX_K_NUDGE)

    proj = safe_float(projection, None)
    bf = safe_float(expected_bf, None)
    if proj is not None:
        proj = round(float(clamp(proj + k_nudge, 0, 18)), 3)
    if bf is not None:
        bf = round(float(clamp(bf + bf_adj, 10, 34)), 3)

    row["Team Hook Label"] = label
    row["Team Hook Score"] = score
    row["Team Hook Samples"] = samples
    row["Team Hook BF Adj"] = round(float(bf_adj), 2)
    row["Team Hook K Nudge"] = round(float(k_nudge), 2)
    row["Team Hook Note"] = f"{label} | samples {samples} | BF adj {bf_adj:+.2f} | K {k_nudge:+.2f}"
    return proj, bf, prof

def final_true_projection_quality_gate(row=None):
    """Adds a non-destructive quality label to help avoid false confidence.

    It does not change projections. It shows whether the current projection has:
    - confirmed/Rotowire lineup support
    - workload/leash support
    - team hook samples
    - ceiling score support
    """
    row = row or {}
    lineup = str(row.get("Lineup") or row.get("lineup") or row.get("Lineup Source") or "").upper()
    wl2 = safe_float(row.get("WL2 Leash Score"), None)
    ceiling = safe_float(row.get("WL2 Ceiling Score"), None)
    hook_samples = safe_float(row.get("Team Hook Samples"), 0) or 0

    score = 50
    notes = []

    if "CONFIRMED" in lineup:
        score += 18; notes.append("confirmed lineup")
    elif "ROTOWIRE" in lineup:
        score += 10; notes.append("rotowire projected")
    else:
        score -= 8; notes.append("fallback lineup")

    if wl2 is not None:
        if wl2 >= 70:
            score += 12; notes.append("strong workload")
        elif wl2 < 42:
            score -= 12; notes.append("fragile workload")

    if ceiling is not None:
        if ceiling >= 54:
            score += 8; notes.append("elite ceiling")
        elif ceiling < 22:
            score -= 4; notes.append("low ceiling")

    if hook_samples >= TEAM_HOOK_MIN_SAMPLES:
        score += 8; notes.append("team hook learned")
    else:
        notes.append("team hook warming")

    score = int(clamp(score, 0, 100))
    if score >= 78:
        label = "TRUE_PROJ_STRONG"
    elif score >= 62:
        label = "TRUE_PROJ_STABLE"
    elif score >= 45:
        label = "TRUE_PROJ_MONITOR"
    else:
        label = "TRUE_PROJ_FRAGILE"

    row["True Projection Label"] = label
    row["True Projection Score"] = score
    row["True Projection Note"] = " | ".join(notes[:6])
    return row







# =========================
# ENVIRONMENT + PITCH COUNT + UMPIRE MICRO OVERLAYS
# Safe capped overlays only. No refresh/player/Underdog changes.
# =========================
PITCH_COUNT_TREND_MODEL_ENABLED = True
UMPIRE_MICRO_MODEL_ENABLED = True
WEATHER_ENGINE_UPGRADE_ENABLED = True
PCT_MAX_BF_ADJ = 0.85
PCT_MAX_K_NUDGE = 0.18
UMPIRE_MAX_K_NUDGE = 0.18
WEATHER_MAX_K_NUDGE = 0.16
WEATHER_MAX_BF_ADJ = 0.45

def _micro_mean(vals):
    vals = [safe_float(v) for v in (vals or []) if safe_float(v) is not None]
    return float(np.mean(vals)) if vals else None

def _micro_slope(vals):
    vals = [safe_float(v) for v in (vals or []) if safe_float(v) is not None]
    if len(vals) < 3:
        return 0.0
    y = np.array(list(reversed(vals)), dtype=float)
    x = np.arange(len(y), dtype=float)
    try:
        return float(np.polyfit(x, y, 1)[0])
    except Exception:
        return 0.0

def pitch_count_trend_profile(recent_rows=None):
    rows = recent_rows or []
    pitches = [safe_float(r.get("Pitches")) for r in rows[:6] if isinstance(r, dict) and safe_float(r.get("Pitches")) is not None]
    bf_vals = [safe_float(r.get("BF")) for r in rows[:6] if isinstance(r, dict) and safe_float(r.get("BF")) is not None]
    ip_vals = [safe_float(r.get("IP_float")) for r in rows[:6] if isinstance(r, dict) and safe_float(r.get("IP_float")) is not None]
    avg_p_l3 = _micro_mean(pitches[:3])
    slope_p = _micro_slope(pitches[:5])
    avg_bf_l3 = _micro_mean(bf_vals[:3])
    avg_ip_l3 = _micro_mean(ip_vals[:3])
    score = 50.0
    flags = []
    if avg_p_l3 is not None:
        if avg_p_l3 >= 96: score += 14; flags.append("HIGH_PITCH_BASE")
        elif avg_p_l3 >= 90: score += 8; flags.append("SOLID_PITCH_BASE")
        elif avg_p_l3 <= 75: score -= 16; flags.append("LOW_PITCH_BASE")
        elif avg_p_l3 <= 82: score -= 8; flags.append("MILD_LOW_PITCH_BASE")
    if slope_p >= 4.0: score += 12; flags.append("PITCH_COUNT_RISING")
    elif slope_p >= 2.0: score += 6; flags.append("PITCH_COUNT_SLIGHT_RISE")
    elif slope_p <= -4.0: score -= 12; flags.append("PITCH_COUNT_FALLING")
    elif slope_p <= -2.0: score -= 6; flags.append("PITCH_COUNT_SLIGHT_DROP")
    if avg_bf_l3 is not None:
        if avg_bf_l3 >= 24: score += 8; flags.append("BF_VOLUME_STRONG")
        elif avg_bf_l3 <= 18: score -= 10; flags.append("BF_VOLUME_LOW")
    if avg_ip_l3 is not None:
        if avg_ip_l3 >= 6.0: score += 7; flags.append("IP_TREND_DEEP")
        elif avg_ip_l3 <= 4.5: score -= 9; flags.append("IP_TREND_SHORT")
    score = int(clamp(round(score), 0, 100))
    label = "PITCH_TREND_UP" if score >= 68 else "PITCH_TREND_DOWN" if score <= 38 else "PITCH_TREND_NEUTRAL"
    bf_adj = k_nudge = 0.0
    if PITCH_COUNT_TREND_MODEL_ENABLED and len(pitches) >= 3:
        if score >= 68:
            bf_adj = clamp((score - 66) / 22.0, 0.10, PCT_MAX_BF_ADJ)
            k_nudge = clamp(bf_adj * 0.16, 0.02, PCT_MAX_K_NUDGE)
        elif score <= 38:
            bf_adj = -clamp((40 - score) / 22.0, 0.10, PCT_MAX_BF_ADJ)
            k_nudge = -clamp(abs(bf_adj) * 0.15, 0.02, PCT_MAX_K_NUDGE)
    return {"label": label, "score": score, "flags": flags, "avg_pitches_l3": None if avg_p_l3 is None else round(avg_p_l3,1), "pitch_slope": round(slope_p,2), "bf_adj": round(float(bf_adj),2), "k_nudge": round(float(k_nudge),2)}

def apply_pitch_count_trend_overlay(row=None, projection=None, expected_bf=None, recent_rows=None):
    row = row or {}
    prof = pitch_count_trend_profile(recent_rows or row.get("recent_rows") or [])
    proj = safe_float(projection, None)
    bf = safe_float(expected_bf, None)
    k_nudge = safe_float(prof.get("k_nudge"), 0) or 0
    bf_adj = safe_float(prof.get("bf_adj"), 0) or 0
    if proj is not None: proj = round(float(clamp(proj + k_nudge, 0, 18)), 3)
    if bf is not None: bf = round(float(clamp(bf + bf_adj, 10, 34)), 3)
    row["Pitch Trend Label"] = prof.get("label")
    row["Pitch Trend Score"] = prof.get("score")
    row["Pitch Trend K Nudge"] = k_nudge
    row["Pitch Trend BF Adj"] = bf_adj
    row["Pitch Trend Note"] = f"{prof.get('label')} | pL3 {prof.get('avg_pitches_l3')} | slope {prof.get('pitch_slope')} | K {k_nudge:+.2f}"
    return proj, bf, prof

def apply_umpire_micro_overlay(row=None, projection=None):
    row = row or {}
    ump_factor = safe_float(row.get("ump_factor"), None)
    umpire_name = row.get("umpire") or row.get("Umpire") or ""
    k_nudge = 0.0
    label = "UMPIRE_NEUTRAL_OR_UNKNOWN"
    score = 50
    if UMPIRE_MICRO_MODEL_ENABLED and ump_factor is not None:
        k_nudge = round(float(clamp((ump_factor - 1.0) * 7.0, -UMPIRE_MAX_K_NUDGE, UMPIRE_MAX_K_NUDGE)), 2)
        score = int(clamp(50 + (ump_factor - 1.0) * 900, 0, 100))
        label = "UMPIRE_K_FRIENDLY" if k_nudge >= 0.06 else "UMPIRE_K_SUPPRESS" if k_nudge <= -0.06 else "UMPIRE_NEUTRAL"
    row["Umpire Micro Label"] = label
    row["Umpire Micro Score"] = score
    row["Umpire Micro K Nudge"] = k_nudge
    row["Umpire Micro Note"] = f"{label} | {umpire_name or 'unknown'} | K {k_nudge:+.2f}"
    proj = safe_float(projection, None)
    if proj is not None: proj = round(float(clamp(proj + k_nudge, 0, 18)), 3)
    return proj, {"label": label, "score": score, "k_nudge": k_nudge}

def apply_weather_engine_upgrade_overlay(row=None, projection=None, expected_bf=None):
    row = row or {}
    base_factor = safe_float(row.get("weather_factor"), None)
    da_factor = safe_float(row.get("density_altitude_factor") or row.get("da_factor"), None)
    temp = safe_float(row.get("temperature") or row.get("temp_f") or row.get("Temp"), None)
    humidity = safe_float(row.get("humidity") or row.get("Humidity"), None)
    wind = safe_float(row.get("wind_speed") or row.get("Wind Speed"), None)
    roof = str(row.get("roof") or row.get("Roof") or "").upper()
    k_nudge = 0.0
    bf_adj = 0.0
    flags = []
    if WEATHER_ENGINE_UPGRADE_ENABLED and not ("DOME" in roof or "CLOSED" in roof):
        factor = 1.0
        if base_factor is not None: factor *= clamp(base_factor, 0.965, 1.035)
        if da_factor is not None: factor *= clamp(da_factor, 0.965, 1.025)
        if temp is not None:
            if temp >= 92: bf_adj -= 0.15; flags.append("HOT_FATIGUE")
            elif 58 <= temp <= 78: bf_adj += 0.08; flags.append("COMFORT_TEMP")
            elif temp <= 45: k_nudge -= 0.04; flags.append("COLD_GRIP")
        if humidity is not None and temp is not None and humidity >= 70 and temp >= 84:
            bf_adj -= 0.12; flags.append("HUMID_FATIGUE")
        if wind is not None and wind >= 15:
            k_nudge -= 0.02; flags.append("WINDY")
        k_nudge += clamp((factor - 1.0) * 5.0, -WEATHER_MAX_K_NUDGE, WEATHER_MAX_K_NUDGE)
    elif WEATHER_ENGINE_UPGRADE_ENABLED:
        flags.append("ROOF_CONTROLLED")
    k_nudge = round(float(clamp(k_nudge, -WEATHER_MAX_K_NUDGE, WEATHER_MAX_K_NUDGE)), 2)
    bf_adj = round(float(clamp(bf_adj, -WEATHER_MAX_BF_ADJ, WEATHER_MAX_BF_ADJ)), 2)
    label = "WEATHER_K_SLIGHT_PLUS" if k_nudge >= 0.06 or bf_adj >= 0.15 else "WEATHER_K_SLIGHT_MINUS" if k_nudge <= -0.06 or bf_adj <= -0.15 else "WEATHER_NEUTRAL"
    row["Weather Upgrade Label"] = label
    row["Weather Upgrade Score"] = int(clamp(50 + (k_nudge * 110) + (bf_adj * 18), 0, 100))
    row["Weather Upgrade K Nudge"] = k_nudge
    row["Weather Upgrade BF Adj"] = bf_adj
    row["Weather Upgrade Note"] = f"{label} | K {k_nudge:+.2f} | BF {bf_adj:+.2f} | {'/'.join(flags[:4])}"
    proj = safe_float(projection, None)
    bf = safe_float(expected_bf, None)
    if proj is not None: proj = round(float(clamp(proj + k_nudge, 0, 18)), 3)
    if bf is not None: bf = round(float(clamp(bf + bf_adj, 10, 34)), 3)
    return proj, bf, {"label": label, "k_nudge": k_nudge, "bf_adj": bf_adj}





# =========================
# HIGH-PROJECTION VOLUME SAFETY TWEAK
# Small capped overlay only:
# - Does NOT flip strong overs to unders
# - Mainly downgrades fragile high-projection overs to B/C/PASS
# - Adds "Needs 7+ Innings" warning flag
# =========================
HIGH_PROJ_VOLUME_SAFETY_ENABLED = True
HIGH_PROJ_VOLUME_TAX_MAX_K = 0.38
HIGH_PROJ_VOLUME_TAX_START = 7.45
HIGH_PROJ_PASS_EDGE_MIN = 0.65

def high_projection_volume_safety_profile(row=None, projection=None, line=None, expected_bf=None):
    row = row or {}
    proj = safe_float(projection, None)
    ln = safe_float(line, None)
    bf = safe_float(expected_bf, None)

    wl2_score = safe_float(row.get("WL2 Leash Score"), None)
    wl2_label = str(row.get("WL2 Label") or "").upper()
    pitch_trend = str(row.get("Pitch Trend Label") or "").upper()
    team_hook = str(row.get("Team Hook Label") or "").upper()

    active = False
    tax = 0.0
    flags = []
    needs_deep = False
    pass_tighten = False

    if not HIGH_PROJ_VOLUME_SAFETY_ENABLED or proj is None:
        return {
            "active": False,
            "tax": 0.0,
            "needs_deep": False,
            "pass_tighten": False,
            "label": "VOLUME_SAFETY_OFF_OR_NO_PROJ",
            "flags": [],
        }

    edge = None if ln is None else proj - ln

    wl2_elite = (wl2_score is not None and wl2_score >= 76) or any(x in wl2_label for x in ["ELITE", "STRONG"])
    pitch_up = "UP" in pitch_trend and "DOWN" not in pitch_trend
    quick_hook = any(x in team_hook for x in ["QUICK", "SHORT", "HOOK"])

    # Deep-start warning. This is mostly UI/decision context.
    if proj >= 7.25 or (bf is not None and bf >= 27.0):
        needs_deep = True
        flags.append("NEEDS_7_PLUS_INNINGS")

    # Small tax only for very high projections that do not have elite volume support.
    if proj >= HIGH_PROJ_VOLUME_TAX_START and not (wl2_elite and pitch_up):
        active = True
        base_tax = 0.16
        if proj >= 8.0:
            base_tax += 0.08
        if proj >= 8.5:
            base_tax += 0.06
        if wl2_score is not None and wl2_score < 60:
            base_tax += 0.08
        if not pitch_up:
            base_tax += 0.05
        if quick_hook:
            base_tax += 0.08
        tax = clamp(base_tax, 0.0, HIGH_PROJ_VOLUME_TAX_MAX_K)
        flags.append("HIGH_PROJ_VOLUME_TAX")

    # Tighten small-edge overs unless workload support is clearly strong.
    if ln is not None and edge is not None and edge > 0:
        if edge < HIGH_PROJ_PASS_EDGE_MIN and not wl2_elite:
            pass_tighten = True
            flags.append("SMALL_EDGE_PASS_TIGHTEN")

    if needs_deep and not wl2_elite:
        flags.append("DEEP_START_NOT_ELITE_CONFIRMED")

    if active:
        label = "VOLUME_TAX_ACTIVE"
    elif pass_tighten:
        label = "PASS_TIGHTEN_ACTIVE"
    elif needs_deep:
        label = "NEEDS_DEEP_START_FLAG"
    else:
        label = "VOLUME_SAFETY_CLEAR"

    return {
        "active": active,
        "tax": round(float(tax), 2),
        "needs_deep": needs_deep,
        "pass_tighten": pass_tighten,
        "label": label,
        "flags": flags,
    }

def apply_high_projection_volume_safety(row=None, projection=None, line=None, expected_bf=None):
    row = row or {}
    prof = high_projection_volume_safety_profile(row, projection, line, expected_bf)
    proj = safe_float(projection, None)
    tax = safe_float(prof.get("tax"), 0) or 0
    if proj is not None and tax > 0:
        proj = round(float(clamp(proj - tax, 0, 18)), 3)

    row["Volume Safety Label"] = prof.get("label")
    row["Volume Safety Tax"] = tax
    row["Needs 7+ Innings Flag"] = "YES" if prof.get("needs_deep") else "NO"
    row["Pass Tighten Flag"] = "YES" if prof.get("pass_tighten") else "NO"
    row["Volume Safety Note"] = f"{prof.get('label')} | tax -{tax:.2f} | {'/'.join(prof.get('flags') or [])}"
    return proj, prof

def apply_volume_safety_classification(row=None):
    row = row or {}
    if row.get("Pass Tighten Flag") == "YES":
        decision = str(row.get("WL2 Decision") or row.get("Ace Ceiling Decision") or row.get("Projection First Decision") or row.get("Decision") or "")
        tier = str(row.get("WL2 Tier") or row.get("Ace Ceiling Tier") or row.get("Projection First Tier") or row.get("Tier") or "")
        # Only soften OVERs; never flip to under.
        if "O" in decision.upper() or "OVER" in decision.upper():
            row["Volume Safety Decision"] = "🚫 PO"
            row["Volume Safety Tier"] = "PASS"
        else:
            row["Volume Safety Decision"] = decision
            row["Volume Safety Tier"] = tier
    elif row.get("Volume Safety Label") == "VOLUME_TAX_ACTIVE":
        decision = str(row.get("WL2 Decision") or row.get("Ace Ceiling Decision") or row.get("Projection First Decision") or row.get("Decision") or "")
        tier = str(row.get("WL2 Tier") or row.get("Ace Ceiling Tier") or row.get("Projection First Tier") or row.get("Tier") or "")
        if "A" in tier and ("O" in decision.upper() or "OVER" in decision.upper()):
            row["Volume Safety Decision"] = decision.replace("🔥", "✅")
            row["Volume Safety Tier"] = "B"
        elif "B" in tier and ("O" in decision.upper() or "OVER" in decision.upper()):
            row["Volume Safety Decision"] = decision.replace("🔥", "⚠️").replace("✅", "⚠️")
            row["Volume Safety Tier"] = "C"
        else:
            row["Volume Safety Decision"] = decision
            row["Volume Safety Tier"] = tier
    return row


def build_kproj_table(board):
    rows = []
    for p in board or []:
        p = normalize_saved_real_line_fields(p)
        d = kproj_decision(p)
        dist = kproj_distribution_profile(d.get("projection"), d.get("line"), p)
        p["K PROJ"] = d.get("projection")
        p["line"] = d.get("line")
        p["Confidence %"] = None if d.get("confidence") is None else round(d.get("confidence") * 100, 1)
        p["Tier"] = d.get("tier")
        p["Decision"] = d.get("decision")
        apply_projection_first_confidence_to_row(p)
        apply_ace_ceiling_protection_to_row(p)
        apply_workload_leash_2_classification(p)
        final_true_projection_quality_gate(p)
        apply_volume_safety_classification(p)
        rows.append({
            "Pitcher": p.get("pitcher"),
            "Matchup": p.get("matchup"),
            "K PROJ": d.get("projection"),
            "Floor": dist.get("floor"),
            "Median": dist.get("median"),
            "Ceiling": dist.get("ceiling"),
            "Volatility": dist.get("volatility"),
            "Over Sim %": None if dist.get("over_prob") is None else round(dist.get("over_prob") * 100, 1),
            "Under Sim %": None if dist.get("under_prob") is None else round(dist.get("under_prob") * 100, 1),
            "UD/Line": d.get("line"),
            "Line Source": d.get("line_source"),
            "Decision": p.get("Volume Safety Decision") or p.get("WL2 Decision") or p.get("Ace Ceiling Decision") or p.get("Projection First Decision") or d.get("decision"),
            "Base Decision": d.get("decision"),
            "Model Lean": d.get("lean_side"),
            "Lean Gap": d.get("lean_gap"),
            "Confidence %": None if d.get("confidence") is None else round(d.get("confidence") * 100, 1),
            "Over Needs": d.get("over_needed"),
            "Pitcher K%": round((safe_float(p.get("pitcher_k"),0) or 0)*100,1),
            "Opp K%": round((safe_float(p.get("opp_k"),0) or 0)*100,1),
            "Exp BF": p.get("expected_bf"),
            "Putaway/Whiff": p.get("statcast_whiff") or p.get("statcast_csw"),
            "Lineup": p.get("lineup_status"),
            "Hit Rate %": None if d.get("hit_rate") is None else round(d.get("hit_rate") * 100, 1),
            "Tier": p.get("Volume Safety Tier") or p.get("WL2 Tier") or p.get("Ace Ceiling Tier") or p.get("Projection First Tier") or d.get("tier"),
            "Confidence Mode": p.get("Projection First Label"),
            "Confidence Note": p.get("Projection First Note"),
            "Ace Ceiling Label": p.get("Ace Ceiling Label"),
            "Ace Ceiling Note": p.get("Ace Ceiling Note"),
            "WL2 Leash Score": p.get("WL2 Leash Score"),
            "WL2 Ceiling Score": p.get("WL2 Ceiling Score"),
            "WL2 Label": p.get("WL2 Label"),
            "WL2 Ceiling": p.get("WL2 Ceiling"),
            "WL2 K Nudge": p.get("WL2 K Nudge"),
            "WL2 BF Adj": p.get("WL2 BF Adj"),
            "WL2 Under Risk": p.get("WL2 Under Risk Label"),
            "Team Hook Label": p.get("Team Hook Label"),
            "Team Hook Score": p.get("Team Hook Score"),
            "True Projection Label": p.get("True Projection Label"),
            "True Projection Score": p.get("True Projection Score"),
            "Pitch Trend Label": p.get("Pitch Trend Label"),
            "Pitch Trend Score": p.get("Pitch Trend Score"),
            "Pitch Trend K Nudge": p.get("Pitch Trend K Nudge"),
            "Umpire Micro Label": p.get("Umpire Micro Label"),
            "Umpire Micro K Nudge": p.get("Umpire Micro K Nudge"),
            "Weather Upgrade Label": p.get("Weather Upgrade Label"),
            "Weather Upgrade K Nudge": p.get("Weather Upgrade K Nudge"),
            "Weather Upgrade BF Adj": p.get("Weather Upgrade BF Adj"),
            "Volume Safety Label": p.get("Volume Safety Label"),
            "Volume Safety Tax": p.get("Volume Safety Tax"),
            "Needs 7+ Innings": p.get("Needs 7+ Innings Flag"),
            "Pass Tighten": p.get("Pass Tighten Flag"),
            "Volume Safety Note": p.get("Volume Safety Note"),
            "Base Tier": d.get("tier"),
            "Role Score": d.get("role_score"),
            "Starter Score": d.get("starter_score"),
            "IP Floor": d.get("ip_floor"),
            "Dynamic Leash": p.get("dynamic_leash_label"),
            "Leash BF Adj": p.get("dynamic_leash_bf_adj"),
            "Smart Edge": p.get("smart_edge_label"),
            "Smart Nudge": p.get("smart_edge_nudge"),
            "Leash Score": p.get("smart_leash_score"),
            "Lineup K Pressure": p.get("smart_lineup_k_score"),
            "Pitch Count Score": p.get("smart_pitch_count_score"),
            "Edge Gap": d.get("edge_gap"),
            "Main Engine Action": p.get("bet_action"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Decision", "Confidence %", "K PROJ"], ascending=[True, False, False])
    return df

def render_kproj_tab(board):
    st.markdown('<div class="section-title-pro">K PROJ / Pure Upside Model</div>', unsafe_allow_html=True)
    st.caption("K Upside now uses true-talent projection + distribution simulation: floor, median, ceiling, volatility, recent Ks, BF, matchup, and Underdog line. Main engine stays separate.")
    if not board:
        st.info("Click 🔄 Refresh Live Board first.")
        return
    df = build_kproj_table(board)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("K Proj Rows", len(df))
    c2.metric("Over Leans", int(df["Decision"].astype(str).str.contains("OVER", regex=False).sum()) if not df.empty else 0)
    c3.metric("Under Leans", int(df["Decision"].astype(str).str.contains("UNDER", regex=False).sum()) if not df.empty else 0)
    c4.metric("Underdog Lines", int((df["Line Source"] == "Underdog").sum()) if not df.empty else 0)

    st.subheader("Projection Board")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Pitcher Cards")
    priority = sorted(board, key=lambda p: ("🔥" in str(kproj_decision(p).get("decision")), safe_float(kproj_decision(p).get("confidence"), 0) or 0, kproj_upside_projection(p)), reverse=True)
    for p in priority[:20]:
        render_kproj_pitcher_card(p)



# =========================
# LIGHT BULLPEN FATIGUE TAX
# Leash/BF-only realism layer. Does NOT change pitcher K skill.
# =========================
LIGHT_BULLPEN_TAX_ENABLED = True
LIGHT_BULLPEN_BF_MIN_FACTOR = 0.985
LIGHT_BULLPEN_BF_MAX_FACTOR = 1.030

def light_bullpen_tax_factor(row=None):
    if not LIGHT_BULLPEN_TAX_ENABLED:
        return 1.0, "OFF", "Bullpen tax off"
    row = row or {}
    text = " ".join(str(row.get(k, "")) for k in [
        "bullpen_status", "bullpen_note", "bullpen_risk", "bp_status",
        "pen_status", "bullpen_fatigue", "bullpen_usage_note"
    ]).upper()
    fatigue_score = safe_float(row.get("bullpen_fatigue_score") or row.get("bp_fatigue_score"), None)

    factor, label, note = 1.0, "NEUTRAL", "Bullpen neutral"
    if fatigue_score is not None:
        if fatigue_score >= 80:
            factor, label, note = 1.030, "TAXED_BP", f"Taxed bullpen score {fatigue_score:.0f}: starter length boost"
        elif fatigue_score >= 65:
            factor, label, note = 1.018, "TIRED_BP", f"Tired bullpen score {fatigue_score:.0f}: slight starter length boost"
        elif fatigue_score <= 30:
            factor, label, note = 0.988, "FRESH_BP", f"Fresh bullpen score {fatigue_score:.0f}: quicker hook risk"
    else:
        if any(x in text for x in ["EXHAUSTED", "EXTREME", "HEAVY", "TAXED", "OVERUSED"]):
            factor, label, note = 1.030, "TAXED_BP", "Taxed bullpen: starter length boost"
        elif any(x in text for x in ["TIRED", "FATIGUED", "USED", "BACK-TO-BACK", "B2B"]):
            factor, label, note = 1.018, "TIRED_BP", "Tired bullpen: slight starter length boost"
        elif any(x in text for x in ["FRESH", "RESTED", "AVAILABLE"]):
            factor, label, note = 0.990, "FRESH_BP", "Fresh bullpen: quicker hook risk"

    factor = clamp(factor, LIGHT_BULLPEN_BF_MIN_FACTOR, LIGHT_BULLPEN_BF_MAX_FACTOR)
    return float(factor), label, note

def apply_light_bullpen_tax_to_bf(expected_bf, row=None):
    bf = safe_float(expected_bf, DEFAULT_BF) or DEFAULT_BF
    factor, label, note = light_bullpen_tax_factor(row)
    new_bf = float(clamp(bf * factor, 14.0, 31.5))
    if isinstance(row, dict):
        row["light_bullpen_tax_factor"] = round(factor, 3)
        row["light_bullpen_tax_label"] = label
        row["light_bullpen_tax_note"] = note
        row["light_bullpen_tax_bf"] = round(new_bf, 2)
    return new_bf, {"factor": round(factor, 3), "label": label, "note": note}


# =========================
# MONEYLINE EDGE TAB — ISOLATED MODULE
# Separate ML tab only. Does NOT change K projections, Underdog props,
# simulations, light true leash/BF, or official K decisions.
# =========================
ML_TEAM_MAP = {
    "ARI":"Arizona Diamondbacks","ATL":"Atlanta Braves","BAL":"Baltimore Orioles","BOS":"Boston Red Sox",
    "CHC":"Chicago Cubs","CWS":"Chicago White Sox","CHW":"Chicago White Sox","CIN":"Cincinnati Reds",
    "CLE":"Cleveland Guardians","COL":"Colorado Rockies","DET":"Detroit Tigers","HOU":"Houston Astros",
    "KC":"Kansas City Royals","LAA":"Los Angeles Angels","LAD":"Los Angeles Dodgers","MIA":"Miami Marlins",
    "MIL":"Milwaukee Brewers","MIN":"Minnesota Twins","NYM":"New York Mets","NYY":"New York Yankees",
    "ATH":"Athletics","OAK":"Athletics","PHI":"Philadelphia Phillies","PIT":"Pittsburgh Pirates",
    "SD":"San Diego Padres","SF":"San Francisco Giants","SEA":"Seattle Mariners","STL":"St. Louis Cardinals",
    "TB":"Tampa Bay Rays","TEX":"Texas Rangers","TOR":"Toronto Blue Jays","WSH":"Washington Nationals",
}
ML_NAME_TO_ABBR = {v.lower().replace(".",""): k for k,v in ML_TEAM_MAP.items()}

def ml_abbr(x):
    s = str(x or "").strip()
    up = s.upper()
    if up in ML_TEAM_MAP:
        return up
    low = s.lower().replace(".","")
    return ML_NAME_TO_ABBR.get(low, up[:3])

def ml_implied(price):
    p = safe_float(price, None)
    if p is None:
        return None
    return 100/(p+100) if p > 0 else abs(p)/(abs(p)+100)

def ml_no_vig(a, h):
    ap, hp = ml_implied(a), ml_implied(h)
    if ap is None or hp is None or ap+hp <= 0:
        return None, None
    return ap/(ap+hp), hp/(ap+hp)

@st.cache_data(ttl=180, show_spinner=False)
def ml_fetch_oddsapi_h2h():
    key = get_secret("ODDS_API_KEY", "")
    if not key:
        return []
    data = safe_get_json(
        f"{ODDS_BASE}/sports/baseball_mlb/odds",
        params={"apiKey": key, "regions": "us", "markets": "h2h", "oddsFormat": "american"},
        timeout=16
    )
    if not isinstance(data, list):
        return []
    games = []
    for g in data:
        away, home = g.get("away_team"), g.get("home_team")
        price_map = {}
        books = []
        for b in g.get("bookmakers", []) or []:
            books.append(b.get("title") or b.get("key") or "")
            for m in b.get("markets", []) or []:
                if m.get("key") != "h2h":
                    continue
                for o in m.get("outcomes", []) or []:
                    nm, pr = o.get("name"), safe_float(o.get("price"), None)
                    if nm and pr is not None:
                        price_map.setdefault(nm.lower().replace(".",""), []).append(pr)
        def avg_price(team):
            vals = price_map.get(str(team or "").lower().replace(".",""), [])
            return None if not vals else int(round(float(np.mean(vals))))
        ap, hp = avg_price(away), avg_price(home)
        av, hv = ml_no_vig(ap, hp)
        games.append({
            "away": away, "home": home, "away_abbr": ml_abbr(away), "home_abbr": ml_abbr(home),
            "away_price": ap, "home_price": hp,
            "away_market": None if av is None else round(av*100, 1),
            "home_market": None if hv is None else round(hv*100, 1),
            "books": ", ".join([x for x in sorted(set(books)) if x][:5])
        })
    return games

def ml_sides(matchup):
    s = str(matchup or "")
    if "@" not in s:
        return None, None
    a,h = [x.strip() for x in s.split("@", 1)]
    return a,h

def ml_team_score_from_pitcher(p):
    if not isinstance(p, dict):
        return 50.0
    proj = safe_float(p.get("projection"), None)
    line = safe_float(p.get("line"), None) if p.get("line") is not None else safe_float(p.get("underdog_line"), None)
    edge = 0 if proj is None or line is None else proj-line
    conf = safe_float(p.get("fair_probability") or p.get("hit_rate"), 55) or 55
    if conf <= 1:
        conf *= 100
    score = 50.0
    if proj is not None:
        score += clamp((proj-4.5)*2.3, -9, 14)
    score += clamp(edge*3.4, -10, 15)
    score += clamp((conf-56)*0.35, -6, 9)
    leash = safe_float(p.get("light_true_leash_score") or p.get("true_leash_score"), None)
    if leash is not None:
        score += clamp((leash-60)*0.10, -4, 4)
    lineup = str(p.get("lineup_status") or "").upper()
    if "TRUE" in lineup or "CONFIRMED" in lineup:
        score += 2
    elif "FALLBACK" in lineup:
        score -= 1.5
    vol = safe_float(p.get("Volatility") or p.get("volatility"), None)
    if vol is not None and vol >= 2.3:
        score -= 2
    return float(clamp(score, 25, 78))

def ml_build_board(board):
    odds = ml_fetch_oddsapi_h2h()
    games = {}
    for p in board or []:
        if not isinstance(p, dict):
            continue
        a,h = ml_sides(p.get("matchup"))
        team = str(p.get("team") or "").upper()
        if not a or not h or not team:
            continue
        rec = games.setdefault(f"{a} @ {h}", {"away":a, "home":h, "pitchers":[]})
        rec["pitchers"].append(p)
    rows = []
    for matchup,g in games.items():
        a,h = g["away"], g["home"]
        ps = g["pitchers"]
        ap = next((p for p in ps if str(p.get("team") or "").upper()==a.upper()), None) or (ps[0] if ps else {})
        hp = next((p for p in ps if str(p.get("team") or "").upper()==h.upper()), None) or (ps[1] if len(ps)>1 else {})
        ascore, hscore = ml_team_score_from_pitcher(ap), ml_team_score_from_pitcher(hp)
        total = max(ascore+hscore, 1e-9)
        amodel = clamp(ascore/total*100, 25, 75)
        hmodel = 100-amodel
        og = next((x for x in odds if x.get("away_abbr")==a and x.get("home_abbr")==h), None)
        amkt = og.get("away_market") if og else None
        hmkt = og.get("home_market") if og else None
        aedge = None if amkt is None else round(amodel-amkt,1)
        hedge = None if hmkt is None else round(hmodel-hmkt,1)
        if aedge is None or hedge is None:
            pick = a if amodel >= hmodel else h
            edge = round(abs(amodel-hmodel),1)
            status = "MODEL ONLY"
            grade = f"MODEL LEAN — {pick}"
        else:
            pick, edge = (a, aedge) if aedge >= hedge else (h, hedge)
            if edge >= 6:
                status, grade = "PLAYABLE", f"🔥 ML EDGE — {pick}"
            elif edge >= 3:
                status, grade = "LEAN", f"✅ ML LEAN — {pick}"
            else:
                status, grade = "PASS", f"🚫 PASS ML — {pick}"
        rows.append({
            "Matchup": matchup, "Pick": pick, "ML Grade": grade, "Status": status, "ML Edge %": edge,
            "Away Model %": round(amodel,1), "Home Model %": round(hmodel,1),
            "Away Market %": amkt, "Home Market %": hmkt,
            "Away Price": og.get("away_price") if og else None, "Home Price": og.get("home_price") if og else None,
            "Away SP": ap.get("pitcher","—") if isinstance(ap,dict) else "—",
            "Home SP": hp.get("pitcher","—") if isinstance(hp,dict) else "—",
            "Source": "OddsAPI + K board" if og else "K board model only"
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("ML Edge %", ascending=False)
    return df


# =========================
# MONEYLINE LOGO CARD UI
# UI-only upgrade. Does not touch K projections or ML math.
# =========================
ML_LOGO_IDS = {
    "ARI":109,"ATL":144,"BAL":110,"BOS":111,"CHC":112,"CWS":145,"CHW":145,
    "CIN":113,"CLE":114,"COL":115,"DET":116,"HOU":117,"KC":118,"KCR":118,
    "LAA":108,"LAD":119,"MIA":146,"MIL":158,"MIN":142,"NYM":121,"NYY":147,
    "ATH":133,"OAK":133,"PHI":143,"PIT":134,"SD":135,"SDP":135,"SF":137,
    "SFG":137,"SEA":136,"STL":138,"TB":139,"TBR":139,"TEX":140,"TOR":141,
    "WSH":120,"WSN":120
}

def ml_team_logo_url(abbr):
    team_id = ML_LOGO_IDS.get(str(abbr or "").upper().strip())
    return "" if not team_id else f"https://www.mlbstatic.com/team-logos/{team_id}.svg"

def ml_split_matchup(matchup):
    s = str(matchup or "")
    if "@" not in s:
        return "", ""
    a, h = [x.strip().upper() for x in s.split("@", 1)]
    return a, h

def render_moneyline_logo_card(r):
    matchup = str(r.get("Matchup", ""))
    away, home = ml_split_matchup(matchup)
    pick = str(r.get("Pick", "—")).upper()
    edge = r.get("ML Edge %", "—")
    status = str(r.get("Status", "—"))
    grade = str(r.get("ML Grade", "—"))
    away_logo = ml_team_logo_url(away)
    home_logo = ml_team_logo_url(home)
    badge_cls = "good-badge" if status == "PLAYABLE" else "yellow-badge" if status == "LEAN" or "MODEL" in status else "red-badge"
    edge_val = safe_float(edge, 0) or 0
    edge_color = "#31e84f" if edge_val >= 6 else "#ffbe3c" if edge_val >= 3 else "#ff5f5f"

    def logo_html(url, abbr):
        if url:
            return f'<img src="{url}" style="width:72px;height:72px;object-fit:contain;filter:drop-shadow(0 0 10px rgba(255,255,255,.20));" alt="{html.escape(abbr)}">'
        return f'<div style="width:72px;height:72px;border-radius:50%;background:#151515;border:1px solid rgba(255,255,255,.15);display:flex;align-items:center;justify-content:center;font-weight:900;">{html.escape(abbr[:3])}</div>'

    st.markdown(f"""
    <div class="pick-card">
      <div style="display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap;">
        <div>
          <div class="small-muted">Moneyline Edge • Logo Card</div>
          <div class="player-name">{html.escape(matchup)}</div>
          <div class="small-muted">Source: {html.escape(str(r.get("Source","—")))}</div>
        </div>
        <div class="badge {badge_cls}">{html.escape(grade)}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:18px;align-items:center;margin-top:18px;">
        <div style="text-align:center;">
          {logo_html(away_logo, away)}
          <div class="big-number" style="font-size:34px;margin-top:4px;">{html.escape(away)}</div>
          <div class="small-muted">SP: {html.escape(str(r.get("Away SP","—")))}</div>
          <div class="small-muted">Model {r.get("Away Model %","—")}% • Market {r.get("Away Market %","—")}% • {r.get("Away Price","—")}</div>
        </div>
        <div style="text-align:center;">
          <div class="small-muted">PICK</div>
          <div class="big-number" style="font-size:40px;color:{edge_color};">{html.escape(pick)}</div>
          <div class="badge {badge_cls}">Edge {edge}%</div>
        </div>
        <div style="text-align:center;">
          {logo_html(home_logo, home)}
          <div class="big-number" style="font-size:34px;margin-top:4px;">{html.escape(home)}</div>
          <div class="small-muted">SP: {html.escape(str(r.get("Home SP","—")))}</div>
          <div class="small-muted">Model {r.get("Home Model %","—")}% • Market {r.get("Home Market %","—")}% • {r.get("Home Price","—")}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)



ML_TEAM_COLORS = {"ARI":"#A71930","ATL":"#CE1141","BAL":"#DF4601","BOS":"#BD3039","CHC":"#0E3386","CWS":"#C4CED4","CHW":"#C4CED4","CIN":"#C6011F","CLE":"#E31937","COL":"#33006F","DET":"#0C2340","HOU":"#EB6E1F","KC":"#004687","KCR":"#004687","LAA":"#BA0021","LAD":"#005A9C","MIA":"#00A3E0","MIL":"#FFC52F","MIN":"#D31145","NYM":"#FF5910","NYY":"#003087","ATH":"#003831","OAK":"#003831","PHI":"#E81828","PIT":"#FDB827","SD":"#2F241D","SDP":"#2F241D","SF":"#FD5A1E","SFG":"#FD5A1E","SEA":"#005C5C","STL":"#C41E3A","TB":"#8FBCE6","TBR":"#8FBCE6","TEX":"#003278","TOR":"#134A8E","WSH":"#AB0003","WSN":"#AB0003"}

def ml_team_color(abbr):
    return ML_TEAM_COLORS.get(str(abbr or "").upper().strip(), "#3fa2ff")

def ml_ring(edge, color):
    val = safe_float(edge, 0) or 0
    pct = max(8, min(100, val * 4.5))
    dash = 2.64 * pct
    return f'<svg width="48" height="48" viewBox="0 0 54 54"><circle cx="27" cy="27" r="21" stroke="rgba(255,255,255,.25)" stroke-width="8" fill="none"/><circle cx="27" cy="27" r="21" stroke="{color}" stroke-width="8" fill="none" stroke-dasharray="{dash:.1f} 264" stroke-linecap="round" transform="rotate(-90 27 27)"/><circle cx="27" cy="27" r="11" fill="#05070d"/></svg>'

def render_moneyline_pro_board(df):
    css = """
    <style>
    .ml-board{border:1px solid rgba(80,145,255,.45);border-radius:18px;overflow:hidden;background:#05070d;box-shadow:0 0 28px rgba(45,125,255,.20);margin:12px 0 22px;}
    .ml-head,.ml-row{display:grid;grid-template-columns:2.1fr 1.05fr 1.75fr 1.05fr;}
    .ml-head div{font-weight:900;color:white;text-align:center;padding:13px;border-right:1px solid rgba(80,145,255,.28);background:#0a1022;letter-spacing:.08em;}
    .ml-row{min-height:76px;border-top:1px solid rgba(80,145,255,.22);background:linear-gradient(90deg,var(--away),rgba(8,13,30,.94),var(--pick));}
    .ml-cell{display:flex;align-items:center;justify-content:center;gap:12px;padding:10px 12px;border-right:1px solid rgba(80,145,255,.18);}
    .ml-logo{width:52px;height:52px;object-fit:contain;filter:drop-shadow(0 0 8px rgba(255,255,255,.25));}
    .ml-abbr{font-size:29px;font-weight:950;color:#fff;text-shadow:0 0 12px rgba(255,255,255,.16);}
    .ml-pick{font-size:32px;font-weight:950;font-style:italic;text-shadow:0 0 12px currentColor;}
    .ml-grade{font-size:22px;font-weight:950;font-style:italic;color:#fff;text-align:center;}
    .ml-edge{font-size:34px;font-weight:950;color:#fff;font-style:italic;}
    .ml-at{font-size:26px;font-weight:900;color:#fff;}
    .ml-sp{font-size:10px;color:rgba(255,255,255,.65);max-width:90px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    @media(max-width:900px){.ml-head{display:none}.ml-row{grid-template-columns:1fr}.ml-cell{border-right:0;border-bottom:1px solid rgba(80,145,255,.18)}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    html_rows = ['<div class="ml-board"><div class="ml-head"><div>MATCHUP</div><div>PICK</div><div>ML GRADE</div><div>ML EDGE %</div></div>']
    for _, r in df.iterrows():
        away, home = ml_split_matchup(r.get("Matchup",""))
        pick = str(r.get("Pick","")).upper().strip()
        edge = r.get("ML Edge %","—")
        grade = str(r.get("ML Grade","—"))
        ac, pc = ml_team_color(away), ml_team_color(pick)
        edge_val = safe_float(edge,0) or 0
        ring_color = "#3fa2ff" if edge_val >= 4 else "#ff415f" if edge_val >= 2 else "#b8c2d8"
        def logo(abbr):
            url = ml_team_logo_url(abbr)
            return f'<img class="ml-logo" src="{url}" alt="{abbr}">' if url else f'<div class="ml-logo ml-abbr">{abbr}</div>'
        grade_colored = grade.replace(pick, f'<span style="color:{pc};">{pick}</span>')
        row_html = f"""
        <div class="ml-row" style="--away:{ac}55;--pick:{pc}55;">
          <div class="ml-cell">{logo(away)}<div><div class="ml-abbr">{away}</div><div class="ml-sp">{r.get("Away SP","—")}</div></div><div class="ml-at">@</div>{logo(home)}<div><div class="ml-abbr">{home}</div><div class="ml-sp">{r.get("Home SP","—")}</div></div></div>
          <div class="ml-cell">{logo(pick)}<div class="ml-pick" style="color:{pc};">{pick}</div></div>
          <div class="ml-cell"><div class="ml-grade">{grade_colored}</div></div>
          <div class="ml-cell">{ml_ring(edge, ring_color)}<div class="ml-edge">{edge}%</div></div>
        </div>"""
        html_rows.append(row_html)
    html_rows.append("</div>")
    st.markdown("".join(html_rows), unsafe_allow_html=True)


def render_moneyline_edge_tab(board, dates=None):
    st.markdown("### 💰 Moneyline Edge")
    st.caption("Separate ML module. Pro-board UI only; it does not modify K projections or ML math.")
    df = ml_build_board(board)
    if df.empty:
        st.info("No ML board yet. Refresh the K board first.")
        return
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Games", len(df))
    c2.metric("Playable", int((df["Status"]=="PLAYABLE").sum()))
    c3.metric("Leans", int((df["Status"]=="LEAN").sum()))
    c4.metric("Odds", "OddsAPI" if any(df["Source"].astype(str).str.contains("OddsAPI", na=False)) else "Model Only")
    st.markdown('<div class="section-title-pro">Moneyline Pro Board</div>', unsafe_allow_html=True)
    render_moneyline_pro_board(df.head(15))
    st.markdown('<div class="section-title-pro">Moneyline Table</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

# =========================
# ELITE SAFETY OVERLAYS
# 1) Confirmed Lineup Lock / Re-Rank
# 2) Pitch-Count Restriction Alerts
# 3) Results Grading Dashboard
#
# These are display / confidence / safety overlays.
# They do NOT change raw K skill math.
# =========================

def elite_lineup_lock_status(p):
    """Classify lineup confidence from existing lineup fields."""
    if not isinstance(p, dict):
        return "UNKNOWN", 0, "No row data"
    txt = " ".join(str(p.get(k, "")) for k in [
        "lineup_status", "Lineup", "lineup", "lineup_source", "confirmed_lineup"
    ]).upper()
    if any(x in txt for x in ["CONFIRMED", "TRUE LINEUP", "OFFICIAL", "LOCKED"]):
        return "CONFIRMED", 100, "Official/true lineup loaded"
    if any(x in txt for x in ["PROJECTED", "PROBABLE"]):
        return "PROJECTED", 70, "Projected lineup; moderate uncertainty"
    if "FALLBACK" in txt or not txt.strip():
        return "FALLBACK", 55, "Fallback team profile; confirm closer to first pitch"
    return "UNKNOWN", 60, "Lineup status unclear"

def elite_pitch_count_alert(p):
    """Detect soft pitch-count / role restriction risk from existing fields."""
    if not isinstance(p, dict):
        return "UNKNOWN", 0, "No row data"

    flags = []
    risk_score = 0

    role_text = " ".join(str(p.get(k, "")) for k in [
        "pitcher_role", "role", "role_note", "starter_note", "leash_risk",
        "risk_label", "manager_hook_status", "true_leash_label",
        "light_true_leash_label"
    ]).upper()

    exp_bf = safe_float(p.get("Exp BF") or p.get("expected_bf") or p.get("light_true_leash_bf") or p.get("true_leash_bf"), None)
    ip_floor = safe_float(p.get("IP Floor") or p.get("ip_floor"), None)
    vol = safe_float(p.get("Volatility") or p.get("volatility"), None)
    starter_score = safe_float(p.get("Starter Score") or p.get("starter_score"), None)
    role_score = safe_float(p.get("Role Score") or p.get("role_score"), None)

    if any(x in role_text for x in ["OPENER", "BULK", "FOLLOWER"]):
        risk_score += 40
        flags.append("OPENER/BULK ROLE")
    if any(x in role_text for x in ["REHAB", "RETURN", "IL", "INJURY", "LIMIT", "CAP", "RESTRICTION"]):
        risk_score += 35
        flags.append("PITCH COUNT RESTRICTION")
    if any(x in role_text for x in ["STRICT", "SHORT", "DANGER"]):
        risk_score += 22
        flags.append("STRICT/SHORT LEASH")
    if exp_bf is not None and exp_bf < 17.0:
        risk_score += 18
        flags.append("LOW BF PATH")
    if ip_floor is not None and ip_floor < 3.7:
        risk_score += 16
        flags.append("LOW IP FLOOR")
    if vol is not None and vol >= 2.25:
        risk_score += 12
        flags.append("HIGH VOLATILITY")
    if starter_score is not None and starter_score < 55:
        risk_score += 18
        flags.append("STARTER SCORE RISK")
    if role_score is not None and role_score < 50:
        risk_score += 14
        flags.append("ROLE SCORE RISK")

    risk_score = int(clamp(risk_score, 0, 100))
    if risk_score >= 60:
        label = "HIGH_ALERT"
    elif risk_score >= 35:
        label = "MEDIUM_ALERT"
    elif risk_score >= 15:
        label = "LOW_ALERT"
    else:
        label = "CLEAR"

    note = " | ".join(flags) if flags else "No obvious pitch-count restriction signal"
    return label, risk_score, note

def elite_pick_safety_overlay(p):
    """Combine lineup + pitch-count alerts into a non-destructive safety label."""
    lineup_label, lineup_score, lineup_note = elite_lineup_lock_status(p)
    pitch_label, pitch_score, pitch_note = elite_pitch_count_alert(p)

    base_conf = safe_float(p.get("fair_probability") or p.get("hit_rate") or p.get("Confidence %"), None)
    if base_conf is not None and base_conf <= 1:
        base_conf *= 100

    penalty = 0
    if lineup_label == "FALLBACK":
        penalty += 5
    elif lineup_label == "PROJECTED":
        penalty += 2
    if pitch_label == "HIGH_ALERT":
        penalty += 12
    elif pitch_label == "MEDIUM_ALERT":
        penalty += 6
    elif pitch_label == "LOW_ALERT":
        penalty += 2

    safety_conf = None if base_conf is None else round(max(0, base_conf - penalty), 1)

    if pitch_label == "HIGH_ALERT":
        safety = "RECHECK / LEASH RISK"
    elif lineup_label == "FALLBACK":
        safety = "WAIT FOR LINEUP"
    elif safety_conf is not None and safety_conf >= 72:
        safety = "CLEAN"
    elif safety_conf is not None and safety_conf >= 62:
        safety = "OK / MONITOR"
    else:
        safety = "MONITOR"

    return {
        "Lineup Lock": lineup_label,
        "Lineup Score": lineup_score,
        "Lineup Note": lineup_note,
        "Pitch Alert": pitch_label,
        "Pitch Alert Score": pitch_score,
        "Pitch Alert Note": pitch_note,
        "Safety Confidence": safety_conf,
        "Safety Overlay": safety,
    }

def apply_elite_safety_overlays_to_board(board):
    """Attach safety overlay fields to board rows. Does not change projection/line/pick."""
    try:
        for p in board or []:
            if isinstance(p, dict):
                p.update(elite_pick_safety_overlay(p))
        return board
    except Exception:
        return board

def render_confirmed_lineup_lock_tab(board, dates=None):
    st.markdown("### ✅ Confirmed Lineup Lock / Re-Rank")
    st.caption("Display-only safety layer. It highlights fallback/projected lineups and pitch-count alerts without changing K projections.")
    board = apply_elite_safety_overlays_to_board(board)
    rows = []
    for p in board or []:
        if not isinstance(p, dict):
            continue
        rows.append({
            "Pitcher": p.get("pitcher"),
            "Matchup": p.get("matchup"),
            "K PROJ": display_kproj_truth(p),
            "Line": p.get("line") or p.get("underdog_line"),
            "Pick": p.get("model_lean") or p.get("lean_side") or p.get("Decision"),
            "Tier": p.get("action_tier") or p.get("Tier"),
            "Lineup Lock": p.get("Lineup Lock"),
            "Pitch Alert": p.get("Pitch Alert"),
            "Safety Overlay": p.get("Safety Overlay"),
            "Safety Confidence": p.get("Safety Confidence"),
            "Lineup Note": p.get("Lineup Note"),
            "Pitch Alert Note": p.get("Pitch Alert Note"),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No board loaded yet.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("Confirmed", int((df["Lineup Lock"] == "CONFIRMED").sum()))
    c3.metric("Fallback", int((df["Lineup Lock"] == "FALLBACK").sum()))
    c4.metric("Pitch Alerts", int(df["Pitch Alert"].astype(str).isin(["HIGH_ALERT","MEDIUM_ALERT"]).sum()))
    order = {"CLEAN":0, "OK / MONITOR":1, "WAIT FOR LINEUP":2, "RECHECK / LEASH RISK":3, "MONITOR":4}
    df["_rank"] = df["Safety Overlay"].map(order).fillna(9)
    df = df.sort_values(["_rank", "Safety Confidence"], ascending=[True, False]).drop(columns=["_rank"])
    st.dataframe(df, use_container_width=True, hide_index=True)

def _grade_pick_result(side, line, actual):
    side = str(side or "").upper()
    line = safe_float(line, None)
    actual = safe_float(actual, None)
    if line is None or actual is None or side not in ["OVER", "UNDER", "O", "U"]:
        return None
    if side in ["OVER", "O"]:
        return "WIN" if actual > line else "LOSS"
    return "WIN" if actual < line else "LOSS"

def build_results_grading_dashboard_frames():
    """Read existing result/pick logs if present. Safe if logs do not exist."""
    picks = load_saved_pick_log_normalized() if "PICK_LOG" in globals() else []
    results = load_json(RESULT_LOG, []) if "RESULT_LOG" in globals() else []

    rows = []
    for r in results or []:
        if not isinstance(r, dict):
            continue
        pitcher = r.get("pitcher") or r.get("player") or r.get("Player")
        side = r.get("pick_side") or r.get("side") or r.get("Model Lean") or r.get("Pick")
        line = safe_float(r.get("line") or r.get("Line"), None)
        actual = safe_float(r.get("actual") or r.get("actual_ks") or r.get("Actual"), None)
        result = r.get("graded_result") or r.get("Result") or _grade_pick_result(side, line, actual)
        rows.append({
            "Date": str(r.get("date") or r.get("graded_at") or "")[:10],
            "Pitcher": pitcher,
            "Matchup": r.get("matchup") or r.get("Matchup"),
            "Pick": side,
            "Line": line,
            "Actual": actual,
            "Result": result,
            "Projection": safe_float(r.get("projection") or r.get("K PROJ"), None),
            "Tier": r.get("tier") or r.get("Tier"),
            "Edge": safe_float(r.get("edge_gap") or r.get("Edge Gap") or r.get("abs_edge"), None),
            "CLV Δ": safe_float(r.get("clv_delta") or r.get("CLV Δ"), None),
            "Lineup Lock": r.get("Lineup Lock") or r.get("lineup_status"),
            "Pitch Alert": r.get("Pitch Alert"),
        })

    return pd.DataFrame(rows)

def render_results_grading_dashboard_tab(board=None, dates=None):
    st.markdown("### 📊 Results Grading Dashboard")
    st.caption("Reads saved graded results. Shows win rate by tier, side, edge, lineup, and alert risk.")
    df = build_results_grading_dashboard_frames()
    if df.empty:
        st.info("No graded results found yet. Save before-game picks and grade after games to populate this dashboard.")
        return

    df["Result"] = df["Result"].astype(str).str.upper()
    wins = int((df["Result"] == "WIN").sum())
    losses = int((df["Result"] == "LOSS").sum())
    graded = wins + losses
    wr = round(wins / graded * 100, 1) if graded else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Graded", graded)
    c2.metric("Record", f"{wins}-{losses}")
    c3.metric("Win Rate", f"{wr}%")
    if "CLV Δ" in df.columns:
        c4.metric("Avg CLV Δ", round(pd.to_numeric(df["CLV Δ"], errors="coerce").dropna().mean(), 2) if len(pd.to_numeric(df["CLV Δ"], errors="coerce").dropna()) else "—")
    else:
        c4.metric("Avg CLV Δ", "—")

    def summary(group_col):
        if group_col not in df.columns:
            return pd.DataFrame()
        out = []
        for k, g in df.groupby(group_col, dropna=False):
            w = int((g["Result"] == "WIN").sum())
            l = int((g["Result"] == "LOSS").sum())
            t = w + l
            out.append({group_col: k, "Graded": t, "Wins": w, "Losses": l, "Win Rate %": round(w/t*100, 1) if t else 0})
        return pd.DataFrame(out).sort_values("Graded", ascending=False)

    st.subheader("By Tier")
    tier_df = summary("Tier")
    if not tier_df.empty:
        st.dataframe(tier_df, use_container_width=True, hide_index=True)

    st.subheader("By Pick Side")
    side_df = summary("Pick")
    if not side_df.empty:
        st.dataframe(side_df, use_container_width=True, hide_index=True)

    st.subheader("By Pitch Alert")
    alert_df = summary("Pitch Alert")
    if not alert_df.empty:
        st.dataframe(alert_df, use_container_width=True, hide_index=True)

    st.subheader("All Results")
    st.dataframe(df.sort_values("Date", ascending=False).head(300), use_container_width=True, hide_index=True)



# =========================
# SAFE / VOLATILE CLASSIFIER
# Non-destructive overlay.
# Helps identify stable leash/volume arms vs ceiling-chaos arms.
# Does NOT modify raw K projections.
# =========================

def elite_safe_volatile_tag(p):
    if not isinstance(p, dict):
        return "UNKNOWN", 50, "No row"

    vol = safe_float(p.get("Volatility") or p.get("volatility"), None)
    whip = safe_float(p.get("WHIP") or p.get("whip"), None)
    bb = safe_float(p.get("BB%") or p.get("walk_rate") or p.get("bb_rate"), None)
    bf = safe_float(p.get("Exp BF") or p.get("expected_bf"), None)
    ip_floor = safe_float(p.get("IP Floor") or p.get("ip_floor"), None)
    role_score = safe_float(p.get("Role Score") or p.get("role_score"), None)
    starter_score = safe_float(p.get("Starter Score") or p.get("starter_score"), None)
    conf = safe_float(p.get("fair_probability") or p.get("hit_rate") or p.get("Confidence %"), None)

    if conf is not None and conf <= 1:
        conf *= 100

    stable = 0
    volatile = 0
    reasons = []

    # Stability signals
    if bf is not None and bf >= 22:
        stable += 20
        reasons.append("STRONG BF")
    elif bf is not None and bf <= 17:
        volatile += 20
        reasons.append("LOW BF")

    if ip_floor is not None and ip_floor >= 5:
        stable += 18
        reasons.append("GOOD IP FLOOR")
    elif ip_floor is not None and ip_floor < 4:
        volatile += 18
        reasons.append("LOW IP FLOOR")

    if starter_score is not None and starter_score >= 75:
        stable += 14
        reasons.append("STRONG STARTER PROFILE")
    elif starter_score is not None and starter_score < 50:
        volatile += 14
        reasons.append("WEAK STARTER PROFILE")

    if role_score is not None and role_score >= 75:
        stable += 10
    elif role_score is not None and role_score < 50:
        volatile += 10

    if conf is not None and conf >= 74:
        stable += 10
    elif conf is not None and conf <= 58:
        volatile += 10

    # Volatility signals
    if vol is not None and vol >= 2.25:
        volatile += 22
        reasons.append("HIGH VOLATILITY")
    elif vol is not None and vol <= 1.55:
        stable += 12
        reasons.append("LOW VOLATILITY")

    if whip is not None and whip >= 1.35:
        volatile += 14
        reasons.append("HIGH WHIP")

    if bb is not None and bb >= 9:
        volatile += 12
        reasons.append("HIGH WALK RATE")

    # Safety overlays / leash alerts
    pitch_alert = str(p.get("Pitch Alert") or "").upper()
    if "HIGH_ALERT" in pitch_alert:
        volatile += 20
        reasons.append("PITCH ALERT")
    elif "MEDIUM_ALERT" in pitch_alert:
        volatile += 10
        reasons.append("MEDIUM ALERT")

    lineup = str(p.get("Lineup Lock") or p.get("lineup_status") or "").upper()
    if "CONFIRMED" in lineup:
        stable += 6
    elif "FALLBACK" in lineup:
        volatile += 6

    score = int(clamp(50 + stable - volatile, 1, 99))

    if score >= 72:
        label = "SAFE"
    elif score <= 42:
        label = "VOLATILE"
    else:
        label = "MODERATE"

    return label, score, " | ".join(reasons[:6])

def apply_safe_volatile_tags(board):
    try:
        for p in board or []:
            if isinstance(p, dict):
                tag, score, note = elite_safe_volatile_tag(p)
                p["Safety Tag"] = tag
                p["Safety Score"] = score
                p["Safety Note"] = note
        return board
    except Exception:
        return board

def render_safe_volatile_tab(board, dates=None):
    st.markdown("### 🛡️ SAFE / VOLATILE CLASSIFIER")
    st.caption("Non-destructive stability classifier. Separates stable leash/BF arms from volatility-heavy ceiling arms.")

    board = apply_safe_volatile_tags(board)

    rows = []
    for p in board or []:
        if not isinstance(p, dict):
            continue
        rows.append({
            "Pitcher": p.get("pitcher"),
            "Matchup": p.get("matchup"),
            "K PROJ": display_kproj_truth(p),
            "Line": p.get("line") or p.get("underdog_line"),
            "Pick": p.get("model_lean") or p.get("Decision"),
            "Tier": p.get("action_tier") or p.get("Tier"),
            "Safety Tag": p.get("Safety Tag"),
            "Safety Score": p.get("Safety Score"),
            "Volatility": p.get("Volatility") or p.get("volatility"),
            "Exp BF": p.get("Exp BF") or p.get("expected_bf"),
            "IP Floor": p.get("IP Floor") or p.get("ip_floor"),
            "Pitch Alert": p.get("Pitch Alert"),
            "Safety Note": p.get("Safety Note"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No board loaded yet.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("SAFE", int((df["Safety Tag"] == "SAFE").sum()))
    c3.metric("VOLATILE", int((df["Safety Tag"] == "VOLATILE").sum()))
    c4.metric("MODERATE", int((df["Safety Tag"] == "MODERATE").sum()))

    rank = {"SAFE":0, "MODERATE":1, "VOLATILE":2}
    df["_r"] = df["Safety Tag"].map(rank).fillna(9)
    df = df.sort_values(["_r", "Safety Score"], ascending=[True, False]).drop(columns=["_r"])

    st.dataframe(df, use_container_width=True, hide_index=True)



# =========================
# AUTO MLB RESULTS GRADER
# Pulls final box scores from MLB StatsAPI and grades saved K picks automatically.
# Safe module: does NOT alter projection math.
# =========================
AUTO_RESULTS_GRADE_FILE = "auto_graded_k_results.json"

def _auto_norm_name(x):
    return re.sub(r"[^a-z]", "", str(x or "").lower())

def _auto_pick_side(p):
    side = str(p.get("model_lean") or p.get("pick_side") or p.get("side") or p.get("Pick") or p.get("Decision") or "").upper()
    if "UNDER" in side or side.startswith("U") or "PU" in side:
        return "UNDER"
    if "OVER" in side or side.startswith("O") or "PO" in side:
        return "OVER"
    return "NO LINE"

def _auto_pick_line(p):
    return safe_float(p.get("line") or p.get("underdog_line") or p.get("Line") or p.get("UD/Line"), None)

def _auto_grade_result(side, line, actual):
    side = str(side or "").upper()
    line = safe_float(line, None)
    actual = safe_float(actual, None)
    if side == "OVER":
        return "WIN" if actual > line else "LOSS"
    if side == "UNDER":
        return "WIN" if actual < line else "LOSS"
    return "NO GRADE"

@st.cache_data(ttl=300, show_spinner=False)
def auto_fetch_mlb_schedule_results(date_str):
    """Return final games with pitcher pitching stats from MLB StatsAPI."""
    try:
        data = safe_get_json(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={"sportId": 1, "date": date_str, "hydrate": "probablePitcher,team"},
            timeout=20
        )
        games = []
        for d in data.get("dates", []) or []:
            for g in d.get("games", []) or []:
                status = ((g.get("status") or {}).get("detailedState") or "").lower()
                if "final" not in status and "completed" not in status:
                    continue
                game_pk = g.get("gamePk")
                teams = g.get("teams") or {}
                away_abbr = ((teams.get("away") or {}).get("team") or {}).get("abbreviation")
                home_abbr = ((teams.get("home") or {}).get("team") or {}).get("abbreviation")
                games.append({"gamePk": game_pk, "away": away_abbr, "home": home_abbr})
        return games
    except Exception:
        return []

@st.cache_data(ttl=300, show_spinner=False)
def auto_fetch_boxscore_pitcher_ks(game_pk):
    """Map normalized pitcher names to strikeouts from MLB boxscore."""
    try:
        data = safe_get_json(f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore", timeout=20)
        out = {}
        teams = data.get("teams") or {}
        for side in ["away", "home"]:
            team = teams.get(side) or {}
            players = team.get("players") or {}
            for _, pl in players.items():
                stats = ((pl.get("stats") or {}).get("pitching") or {})
                if not stats:
                    continue
                name = ((pl.get("person") or {}).get("fullName") or "")
                so = safe_float(stats.get("strikeOuts"), None)
                if name and so is not None:
                    out[_auto_norm_name(name)] = int(so)
        return out
    except Exception:
        return {}

def auto_grade_saved_picks_for_date(date_str):
    """Grades PICK_LOG saved picks for one date using final MLB boxscores."""
    picks = load_saved_pick_log_normalized() if "PICK_LOG" in globals() else []
    schedule = auto_fetch_mlb_schedule_results(date_str)
    all_pitcher_ks = {}
    for g in schedule:
        all_pitcher_ks.update(auto_fetch_boxscore_pitcher_ks(g.get("gamePk")))

    graded = []
    for p in picks or []:
        if not isinstance(p, dict):
            continue
        pdate = str(p.get("date") or p.get("saved_at") or p.get("time") or "")[:10]
        if pdate and pdate != date_str:
            continue
        pitcher = p.get("pitcher") or p.get("player") or p.get("Player")
        if not pitcher:
            continue
        key = _auto_norm_name(pitcher)
        actual = all_pitcher_ks.get(key)
        if actual is None:
            # Try contains match for accents/nickname mismatches
            for k, v in all_pitcher_ks.items():
                if key and (key in k or k in key):
                    actual = v
                    break
        side = _auto_pick_side(p)
        line = _auto_pick_line(p)
        result = _auto_grade_result(side, line, actual) if actual is not None and line is not None else "PENDING"
        graded.append({
            "Date": date_str,
            "Pitcher": pitcher,
            "Matchup": p.get("matchup") or p.get("Matchup"),
            "Pick": side,
            "Line": line,
            "Projection": safe_float(p.get("projection") or p.get("K PROJ"), None),
            "Actual Ks": actual,
            "Result": result,
            "Tier": p.get("tier") or p.get("Tier") or p.get("action_tier"),
            "Saved Decision": p.get("decision") or p.get("Decision") or p.get("bet_action"),
            "Auto Match": "YES" if actual is not None else "NO MATCH",
        })
    return graded

def render_auto_results_grader_tab(board=None, dates=None):
    st.markdown("### 🤖 Auto Results Grader")
    st.caption("Pulls final MLB box scores and auto-grades saved K picks. No manual K entry needed.")

    today_default = str(date.today())
    grade_date = st.date_input("Grade date", value=date.today(), key="auto_grade_date")
    date_str = str(grade_date)

    c1, c2 = st.columns(2)
    run = c1.button("🔄 Pull MLB Results + Grade Saved Picks", use_container_width=True)
    save = c2.button("💾 Save Auto-Graded Results", use_container_width=True)

    if run or save:
        graded = auto_grade_saved_picks_for_date(date_str)
        st.session_state["auto_graded_results_preview"] = graded
    else:
        graded = st.session_state.get("auto_graded_results_preview", [])

    if save and graded:
        existing = load_json(AUTO_RESULTS_GRADE_FILE, [])
        # Deduplicate by date/pitcher/line/pick
        seen = set()
        merged = []
        for row in (existing or []) + graded:
            key = (row.get("Date"), row.get("Pitcher"), row.get("Pick"), row.get("Line"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)
        save_json(AUTO_RESULTS_GRADE_FILE, merged)
        st.success(f"Saved {len(graded)} auto-graded rows.")

    if not graded:
        st.info("No auto-graded rows yet. Save official picks before games, then run this after games finish.")
        return

    df = pd.DataFrame(graded)
    wins = int((df["Result"].astype(str).str.upper() == "WIN").sum()) if "Result" in df.columns else 0
    losses = int((df["Result"].astype(str).str.upper() == "LOSS").sum()) if "Result" in df.columns else 0
    pending = int((df["Result"].astype(str).str.upper() == "PENDING").sum()) if "Result" in df.columns else 0
    total = wins + losses
    wr = round(wins / total * 100, 1) if total else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Wins", wins)
    m2.metric("Losses", losses)
    m3.metric("Pending/No Match", pending)
    m4.metric("Win Rate", f"{wr}%")

    st.dataframe(df, use_container_width=True, hide_index=True)



# =========================
# ELITE REFINEMENT LAYERS
# 1) Advanced Pitch-Type Matchup Layer
# 2) Advanced Umpire K Refinement
# 3) UI Polish Helpers
#
# Safe design:
# - light caps only
# - does not rewrite raw pitcher K skill
# - creates display fields + small projection-quality notes
# =========================

PITCH_TYPE_MATCHUP_ENABLED = True
PITCH_TYPE_K_FACTOR_MIN = 0.965
PITCH_TYPE_K_FACTOR_MAX = 1.040
PITCH_TYPE_MAX_KS_SHIFT_DISPLAY = 0.45

ADV_UMPIRE_REFINEMENT_ENABLED = True
ADV_UMPIRE_FACTOR_MIN = 0.980
ADV_UMPIRE_FACTOR_MAX = 1.020

def _pt_safe_pct(x, default=None):
    v = safe_float(x, default)
    if v is None:
        return default
    if v > 1.0:
        return v / 100.0
    return v

def normalize_pitch_type_key(x):
    t = str(x or "").upper().strip()
    aliases = {
        "4-SEAM": "FF", "4SEAM": "FF", "FOUR-SEAM": "FF", "FASTBALL": "FF", "FB": "FF",
        "SINKER": "SI", "TWO-SEAM": "SI", "2-SEAM": "SI",
        "SLIDER": "SL", "SWEEPER": "ST",
        "CURVE": "CU", "CURVEBALL": "CU", "KNUCKLE CURVE": "KC",
        "CHANGEUP": "CH", "CHANGE": "CH",
        "SPLITTER": "FS", "SPLIT": "FS", "SPL": "FS",
        "CUTTER": "FC", "CUT": "FC",
    }
    return aliases.get(t, t)

def extract_pitch_mix_from_row(row):
    """Return pitch mix list from existing fields if present.
    Expected supported formats:
    - row['pitch_mix'] list/dict
    - row['pitch_type_rows'] list
    - columns like FF%, SL%, CH%
    """
    row = row or {}
    mix = []

    raw = row.get("pitch_mix") or row.get("arsenal") or row.get("pitch_type_mix")
    if isinstance(raw, dict):
        for k, v in raw.items():
            usage = _pt_safe_pct(v, None)
            if usage is not None:
                mix.append({"pitch": normalize_pitch_type_key(k), "usage": usage})
    elif isinstance(raw, list):
        for r in raw:
            if isinstance(r, dict):
                pt = r.get("pitch") or r.get("pitch_type") or r.get("type") or r.get("name")
                usage = _pt_safe_pct(r.get("usage") or r.get("usage_pct") or r.get("pct") or r.get("percent"), None)
                whiff = _pt_safe_pct(r.get("whiff") or r.get("whiff_pct") or r.get("whiff_rate"), None)
                if pt and usage is not None:
                    mix.append({"pitch": normalize_pitch_type_key(pt), "usage": usage, "whiff": whiff})
    ptr = row.get("pitch_type_rows")
    if isinstance(ptr, list):
        for r in ptr:
            if isinstance(r, dict):
                pt = r.get("pitch_type") or r.get("pitch") or r.get("type")
                usage = _pt_safe_pct(r.get("usage") or r.get("usage_pct") or r.get("pitch_pct"), None)
                whiff = _pt_safe_pct(r.get("whiff") or r.get("whiff_pct") or r.get("whiff_rate"), None)
                if pt and usage is not None:
                    mix.append({"pitch": normalize_pitch_type_key(pt), "usage": usage, "whiff": whiff})

    # Column fallback.
    for key in ["FF","SI","FC","SL","ST","CU","KC","CH","FS","SPL","CRV","CUT","FB"]:
        for suffix in ["%", "_pct", "_usage", " usage"]:
            val = row.get(f"{key}{suffix}")
            usage = _pt_safe_pct(val, None)
            if usage is not None:
                mix.append({"pitch": normalize_pitch_type_key(key), "usage": usage})

    # Deduplicate by pitch type, keep max usage.
    dedup = {}
    for r in mix:
        pt = normalize_pitch_type_key(r.get("pitch"))
        usage = _pt_safe_pct(r.get("usage"), None)
        if not pt or usage is None or usage <= 0:
            continue
        old = dedup.get(pt, {})
        if usage > old.get("usage", -1):
            dedup[pt] = {"pitch": pt, "usage": usage, "whiff": r.get("whiff")}
    out = sorted(dedup.values(), key=lambda x: x.get("usage", 0), reverse=True)
    return out[:6]

def opponent_pitch_type_weakness(row, pitch):
    """Light opponent weakness lookup. Falls back to neutral if not available."""
    row = row or {}
    pt = normalize_pitch_type_key(pitch)
    keys = [
        f"opp_whiff_vs_{pt}", f"opp_k_vs_{pt}", f"lineup_whiff_vs_{pt}",
        f"team_whiff_vs_{pt}", f"opp_contact_vs_{pt}", f"opp_slg_vs_{pt}",
    ]
    whiff = None
    contact = None
    slg = None
    for k in keys:
        lk = k.lower()
        v = _pt_safe_pct(row.get(k) or row.get(lk), None)
        if v is None:
            continue
        if "contact" in lk:
            contact = v
        elif "slg" in lk:
            slg = safe_float(row.get(k) or row.get(lk), None)
        else:
            whiff = v
    # Convert known attributes into weakness score around neutral 0.
    score = 0.0
    if whiff is not None:
        score += clamp((whiff - 0.25) / 0.10, -1.0, 1.0)
    if contact is not None:
        score += clamp((0.76 - contact) / 0.10, -1.0, 1.0)
    if slg is not None:
        score += clamp((0.430 - slg) / 0.120, -1.0, 1.0)
    return clamp(score, -1.5, 1.5)

def advanced_pitch_type_matchup_factor(row):
    """Small arsenal-vs-lineup factor.
    Uses available pitch mix + opponent pitch-type weakness. Neutral if no data.
    """
    if not PITCH_TYPE_MATCHUP_ENABLED:
        return 1.0, "OFF", "Pitch-type matchup off", []
    mix = extract_pitch_mix_from_row(row)
    if not mix:
        return 1.0, "UNKNOWN", "No pitch-type mix available", []

    weighted = 0.0
    total_usage = 0.0
    details = []
    for r in mix:
        pt = normalize_pitch_type_key(r.get("pitch"))
        usage = _pt_safe_pct(r.get("usage"), 0) or 0
        whiff = _pt_safe_pct(r.get("whiff"), None)
        opp = opponent_pitch_type_weakness(row, pt)

        # Pitcher's own pitch whiff vs rough league baseline, light.
        own_pitch_edge = 0.0
        league = LEAGUE_AVG_WHIFF_BY_PITCH_TYPE.get(pt, 0.25) if "LEAGUE_AVG_WHIFF_BY_PITCH_TYPE" in globals() else 0.25
        if whiff is not None:
            own_pitch_edge = clamp((whiff - league) / 0.10, -1.0, 1.0)

        pitch_score = (opp * 0.70) + (own_pitch_edge * 0.30)
        weighted += usage * pitch_score
        total_usage += usage
        details.append(f"{pt} {usage*100:.0f}% score {pitch_score:+.2f}")

    if total_usage <= 0:
        return 1.0, "UNKNOWN", "No usable pitch mix", []

    matchup_score = weighted / total_usage
    factor = clamp(1.0 + matchup_score * 0.026, PITCH_TYPE_K_FACTOR_MIN, PITCH_TYPE_K_FACTOR_MAX)

    if factor >= 1.020:
        label = "ARSENAL_EDGE"
    elif factor <= 0.985:
        label = "ARSENAL_RISK"
    else:
        label = "ARSENAL_NEUTRAL"

    note = f"{label}: pitch-type matchup factor x{factor:.3f}"
    return float(factor), label, note, details[:5]

def advanced_umpire_k_refinement_factor(row):
    """Light advanced umpire K refinement using existing umpire fields if available."""
    if not ADV_UMPIRE_REFINEMENT_ENABLED:
        return 1.0, "OFF", "Advanced umpire off"

    row = row or {}
    ump_factor_existing = safe_float(row.get("ump_factor") or row.get("umpire_factor"), None)
    called_strike = _pt_safe_pct(row.get("ump_called_strike_rate") or row.get("called_strike_rate"), None)
    zone = _pt_safe_pct(row.get("ump_zone_boost") or row.get("zone_boost"), None)
    walk = _pt_safe_pct(row.get("ump_walk_rate") or row.get("walk_rate_allowed"), None)
    text = " ".join(str(row.get(k, "")) for k in ["umpire", "umpire_note", "umpire_profile", "umpire_label"]).upper()

    factor = 1.0
    reasons = []

    if ump_factor_existing is not None:
        factor *= clamp(ump_factor_existing, 0.985, 1.015)
        reasons.append(f"base {ump_factor_existing:.3f}")

    if called_strike is not None:
        if called_strike >= 0.175:
            factor *= 1.010
            reasons.append("high called strikes")
        elif called_strike <= 0.155:
            factor *= 0.990
            reasons.append("low called strikes")

    if walk is not None:
        if walk >= 0.095:
            factor *= 0.990
            reasons.append("walk-prone zone")
        elif walk <= 0.070:
            factor *= 1.006
            reasons.append("low-walk zone")

    if any(x in text for x in ["WIDE", "STRIKE", "PITCHER", "K BOOST"]):
        factor *= 1.008
        reasons.append("pitcher-friendly")
    elif any(x in text for x in ["TIGHT", "HITTER", "LOW K", "SMALL ZONE"]):
        factor *= 0.992
        reasons.append("hitter-friendly")

    factor = clamp(factor, ADV_UMPIRE_FACTOR_MIN, ADV_UMPIRE_FACTOR_MAX)

    if factor >= 1.008:
        label = "UMP_K_BOOST"
    elif factor <= 0.992:
        label = "UMP_K_DRAG"
    else:
        label = "UMP_NEUTRAL"
    note = f"{label}: x{factor:.3f}" + (f" ({', '.join(reasons[:3])})" if reasons else "")
    return float(factor), label, note

def apply_elite_refinement_overlays(board):
    """Attach pitch-type and advanced umpire fields only. Does not change raw projections."""
    try:
        for p in board or []:
            if not isinstance(p, dict):
                continue
            pt_factor, pt_label, pt_note, pt_details = advanced_pitch_type_matchup_factor(p)
            ump_factor, ump_label, ump_note = advanced_umpire_k_refinement_factor(p)
            p["Pitch-Type Factor"] = round(pt_factor, 3)
            p["Pitch-Type Label"] = pt_label
            p["Pitch-Type Note"] = pt_note
            p["Pitch-Type Details"] = " | ".join(pt_details)
            p["Advanced Umpire Factor"] = round(ump_factor, 3)
            p["Advanced Umpire Label"] = ump_label
            p["Advanced Umpire Note"] = ump_note

            # Display-only refined read, capped. Does not replace K PROJ.
            proj = safe_float(p.get("projection") or p.get("K PROJ"), None)
            if proj is not None:
                factor = clamp(pt_factor * ump_factor, 0.955, 1.055)
                refined = proj * factor
                shift = clamp(refined - proj, -PITCH_TYPE_MAX_KS_SHIFT_DISPLAY, PITCH_TYPE_MAX_KS_SHIFT_DISPLAY)
                p["Refined Read"] = round(proj + shift, 2)
                p["Refined Shift"] = round(shift, 2)
        return board
    except Exception:
        return board

def render_pitchtype_umpire_refinement_tab(board, dates=None):
    st.markdown("### 🎯 Pitch-Type + Umpire Refinement")
    st.caption("Display-only refinement layer. Shows arsenal matchup and umpire K influence without rewriting the base K projection.")
    board = apply_elite_refinement_overlays(board)

    rows = []
    for p in board or []:
        if not isinstance(p, dict):
            continue
        rows.append({
            "Pitcher": p.get("pitcher"),
            "Matchup": p.get("matchup"),
            "K PROJ": display_kproj_truth(p),
            "Refined Read": p.get("Refined Read"),
            "Refined Shift": p.get("Refined Shift"),
            "Line": p.get("line") or p.get("underdog_line"),
            "Pick": p.get("model_lean") or p.get("Decision"),
            "Tier": p.get("action_tier") or p.get("Tier"),
            "Safety Tag": p.get("Safety Tag"),
            "Pitch-Type Label": p.get("Pitch-Type Label"),
            "Pitch-Type Factor": p.get("Pitch-Type Factor"),
            "Advanced Umpire Label": p.get("Advanced Umpire Label"),
            "Advanced Umpire Factor": p.get("Advanced Umpire Factor"),
            "Pitch-Type Note": p.get("Pitch-Type Note"),
            "Pitch-Type Details": p.get("Pitch-Type Details"),
            "Advanced Umpire Note": p.get("Advanced Umpire Note"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No board loaded yet.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("Arsenal Edges", int((df["Pitch-Type Label"] == "ARSENAL_EDGE").sum()))
    c3.metric("Arsenal Risks", int((df["Pitch-Type Label"] == "ARSENAL_RISK").sum()))
    c4.metric("Ump K Boosts", int((df["Advanced Umpire Label"] == "UMP_K_BOOST").sum()))

    df["_abs_shift"] = pd.to_numeric(df["Refined Shift"], errors="coerce").abs()
    df = df.sort_values("_abs_shift", ascending=False).drop(columns=["_abs_shift"])
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_elite_ui_polish_header(board):
    """Compact visual readout for safest/most volatile profile. UI-only."""
    try:
        board = apply_safe_volatile_tags(board) if "apply_safe_volatile_tags" in globals() else board
        board = apply_elite_refinement_overlays(board)
        rows = [p for p in (board or []) if isinstance(p, dict)]
        if not rows:
            return
        safe_count = sum(1 for p in rows if p.get("Safety Tag") == "SAFE")
        volatile_count = sum(1 for p in rows if p.get("Safety Tag") == "VOLATILE")
        arsenal_edges = sum(1 for p in rows if p.get("Pitch-Type Label") == "ARSENAL_EDGE")
        lineup_confirmed = sum(1 for p in rows if str(p.get("Lineup Lock") or "").upper() == "CONFIRMED")
        st.markdown(f"""
        <div class="hero-panel">
            <div class="big-title">Elite Board Control Center</div>
            <div class="sub-title">SAFE/VOLATILE • Pitch-Type Matchup • Umpire Refinement • Lineup Lock</div>
            <div class="kpi-strip">
                <div class="kpi-box"><div class="kpi-label">SAFE</div><div class="kpi-value green">{safe_count}</div><div class="kpi-sub">stable profiles</div></div>
                <div class="kpi-box"><div class="kpi-label">VOLATILE</div><div class="kpi-value red">{volatile_count}</div><div class="kpi-sub">chaos watch</div></div>
                <div class="kpi-box"><div class="kpi-label">ARSENAL EDGE</div><div class="kpi-value green">{arsenal_edges}</div><div class="kpi-sub">pitch-type boost</div></div>
                <div class="kpi-box"><div class="kpi-label">LINEUP LOCK</div><div class="kpi-value orange">{lineup_confirmed}</div><div class="kpi-sub">confirmed</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        return



# =========================
# FINAL BOARD TAB
# Merged decision center: K projection + lineup + safety + pitch alert
# + pitch-type/umpire refinement + line edge.
# Display/decision layer only. Does not rewrite core K math.
# =========================
def _fb_side(p):
    s = str(p.get("model_lean") or p.get("Model Lean") or p.get("Decision") or p.get("Pick") or "").upper()
    if "UNDER" in s or s.startswith("U") or "PU" in s:
        return "UNDER"
    if "OVER" in s or s.startswith("O") or "PO" in s:
        return "OVER"
    proj = safe_float(p.get("projection") or p.get("K PROJ"), None)
    line = safe_float(p.get("line") or p.get("underdog_line") or p.get("Line"), None)
    if proj is None or line is None:
        return "NO LINE"
    return "OVER" if proj > line else "UNDER"



# =========================
# FINAL BOARD ML CONTEXT LAYER
# Light confidence-only layer.
# DOES NOT change K PROJ, simulations, or OVER/UNDER direction.
# Uses Moneyline context only to slightly adjust Final Board trust.
# =========================
ML_CONTEXT_ENABLED = True
ML_CONTEXT_MAX_SCORE_SWING = 5

def _ml_context_pitcher_team(p):
    """Best-effort pitcher team from matchup and home/away fields."""
    p = p or {}
    matchup = str(p.get("matchup") or p.get("Matchup") or "")
    away, home = ("", "")
    if "@" in matchup:
        away, home = [x.strip().upper() for x in matchup.split("@", 1)]

    team = str(
        p.get("team") or p.get("Team") or p.get("pitcher_team") or
        p.get("player_team") or p.get("abbr") or ""
    ).upper().strip()

    if team:
        return team
    # fallback: if the row has home_away marker
    ha = str(p.get("home_away") or p.get("Home/Away") or "").upper()
    if "HOME" in ha:
        return home
    if "AWAY" in ha:
        return away
    return ""

def _ml_context_lookup(board, matchup):
    """Find moneyline row for same matchup from ml_build_board, safely."""
    try:
        df = ml_build_board(board)
        if df is None or df.empty:
            return None
        m = str(matchup or "").upper().replace(" ", "")
        for _, r in df.iterrows():
            rm = str(r.get("Matchup", "")).upper().replace(" ", "")
            if rm == m:
                return r.to_dict()
    except Exception:
        return None
    return None

def final_board_ml_context(p, board=None):
    """Return light ML context fields for Final Board scoring only."""
    if not ML_CONTEXT_ENABLED:
        return {"ML Context": "OFF", "ML Context Score": 0, "ML Context Note": "Off"}

    p = p or {}
    matchup = p.get("matchup") or p.get("Matchup")
    ml = _ml_context_lookup(board, matchup) if board is not None else None
    if not ml:
        return {
            "ML Context": "UNKNOWN",
            "ML Context Score": 0,
            "ML Context Note": "No ML row matched",
        }

    pitcher_team = _ml_context_pitcher_team(p)
    ml_pick = str(ml.get("Pick") or "").upper().strip()
    edge = safe_float(ml.get("ML Edge %"), 0) or 0
    grade = str(ml.get("ML Grade") or "")
    status = str(ml.get("Status") or "")

    # Small, confidence-only context.
    score = 0
    label = "NEUTRAL"
    note_parts = []

    if pitcher_team and ml_pick:
        if pitcher_team == ml_pick:
            if edge >= 8:
                score += 5
                label = "FAVORABLE"
                note_parts.append("ML supports pitcher team strongly")
            elif edge >= 4:
                score += 3
                label = "FAVORABLE"
                note_parts.append("ML supports pitcher team")
            elif edge >= 2:
                score += 1
                label = "SLIGHT_SUPPORT"
                note_parts.append("Small ML support")
        else:
            if edge >= 8:
                score -= 5
                label = "GAME_SCRIPT_RISK"
                note_parts.append("ML strongly against pitcher team")
            elif edge >= 4:
                score -= 3
                label = "RISK"
                note_parts.append("ML against pitcher team")
            elif edge >= 2:
                score -= 1
                label = "SLIGHT_RISK"
                note_parts.append("Small ML risk")
    else:
        note_parts.append("Pitcher team unknown")

    # If ML is model-only, slightly reduce influence.
    if "MODEL ONLY" in status.upper() or "MODEL ONLY" in grade.upper():
        score = int(round(score * 0.7))
        note_parts.append("model-only ML")

    score = int(clamp(score, -ML_CONTEXT_MAX_SCORE_SWING, ML_CONTEXT_MAX_SCORE_SWING))
    if score == 0 and label not in ["FAVORABLE", "RISK", "GAME_SCRIPT_RISK"]:
        label = "NEUTRAL"

    return {
        "ML Context": label,
        "ML Context Score": score,
        "ML Context Note": " | ".join(note_parts) if note_parts else "Neutral ML context",
        "ML Context Pick": ml_pick,
        "ML Context Edge": edge,
    }



def final_board_true_kproj_old_unused(p):
    """Return the exact K Upside projection source when available.

    This prevents Final Board from showing an adjusted/risk projection as Raw K PROJ.
    Priority is the same displayed K PROJ used by the K Upside tab.
    """
    p = p or {}
    for key in [
        "K PROJ", "k_proj", "kproj", "k_projection",
        "raw_k_proj", "raw_projection", "base_k_proj",
        "mean", "sim_mean", "upside_projection", "projection_mean"
    ]:
        v = safe_float(p.get(key), None)
        if v is not None:
            return v

    # Last fallback only: existing projection field.
    return safe_float(p.get("projection"), None)



# =========================
# FINAL BOARD TRUE K PROJ SYNC
# Display/data-source sync only.
# Does NOT touch K projections, simulations, probabilities, or K Upside math.
# =========================
def _fb_norm_key_name(x):
    try:
        return normalize_name(x)
    except Exception:
        return str(x or "").strip().lower()

def _fb_norm_matchup(x):
    return str(x or "").upper().replace(" ", "").strip()

def build_true_kproj_lookup(board):
    """Map pitcher+matchup to the exact K Upside K PROJ.

    IMPORTANT:
    K Upside table displays:
        d = kproj_decision(p)
        K PROJ = d["projection"]

    So this lookup calls kproj_decision(p) directly instead of using p["projection"],
    because p["projection"] can be the main/risk adjusted projection.
    """
    lookup = {}
    for r in board or []:
        if not isinstance(r, dict):
            continue
        pitcher = r.get("pitcher") or r.get("Pitcher")
        matchup = r.get("matchup") or r.get("Matchup")
        if not pitcher:
            continue

        k_val = None
        try:
            k_val = display_kproj_truth(r)
        except Exception:
            k_val = None

        # Fallbacks only if kproj_decision is unavailable.
        if k_val is None:
            for key in ["K PROJ", "k_proj", "kproj", "k_projection", "raw_k_proj", "base_k_proj", "upside_projection", "K_PROJ"]:
                v = safe_float(r.get(key), None)
                if v is not None:
                    k_val = v
                    break

        if k_val is None:
            continue

        name_key = _fb_norm_key_name(pitcher)
        matchup_key = _fb_norm_matchup(matchup)
        lookup[("name", name_key)] = k_val
        if matchup_key:
            lookup[("name_matchup", name_key, matchup_key)] = k_val
    return lookup


def final_board_true_kproj(p, true_lookup=None):
    """Return exact K Upside projection for this pitcher when available."""
    p = p or {}
    pitcher = p.get("pitcher") or p.get("Pitcher")
    matchup = p.get("matchup") or p.get("Matchup")
    name_key = _fb_norm_key_name(pitcher)
    matchup_key = _fb_norm_matchup(matchup)

    if true_lookup:
        if ("name_matchup", name_key, matchup_key) in true_lookup:
            return true_lookup[("name_matchup", name_key, matchup_key)]
        if ("name", name_key) in true_lookup:
            return true_lookup[("name", name_key)]

    # Direct fallback must match K Upside.
    try:
        v = display_kproj_truth(p)
        if v is not None:
            return v
    except Exception:
        pass

    for key in ["K PROJ", "k_proj", "kproj", "k_projection", "raw_k_proj", "base_k_proj", "upside_projection", "K_PROJ"]:
        v = safe_float(p.get(key), None)
        if v is not None:
            return v

    return safe_float(p.get("projection"), None)


def _fb_score_row(p, board=None, true_k_lookup=None):
    """Final Board scorer.

    Raw K PROJ is forced to match K Upside:
        kproj_decision(p)["projection"]

    Risk Read can still use the main/risk projection path.
    """
    risk_proj = safe_float(p.get("projection"), None)
    raw_kproj = final_board_true_kproj(p, true_k_lookup)
    proj = raw_kproj if raw_kproj is not None else risk_proj
    line = safe_float(p.get("line") or p.get("underdog_line") or p.get("Line"), None)

    # Small pitch-type/umpire read only. Never allow huge suppression.
    pt_factor = safe_float(p.get("Pitch-Type Factor"), 1.0) or 1.0
    ump_factor = safe_float(p.get("Advanced Umpire Factor"), 1.0) or 1.0
    raw_factor = clamp(pt_factor * ump_factor, 0.970, 1.035)

    # Risk Read starts from the main/risk projection source when available.
    # Raw K PROJ remains the exact K Upside projection.
    risk_base = risk_proj if risk_proj is not None else proj
    if risk_base is not None:
        refined_raw = risk_base * raw_factor
        max_shift = 0.35
        refined = risk_base + clamp(refined_raw - risk_base, -max_shift, max_shift)
    else:
        refined = None

    # Direction comes from K PROJ, not from safety-suppressed reads.
    if proj is None or line is None:
        side = "NO LINE"
    else:
        side = "OVER" if proj > line else "UNDER"

    edge = None if proj is None or line is None else abs(proj - line)

    conf = safe_float(p.get("fair_probability") or p.get("hit_rate") or p.get("Confidence %"), None)
    if conf is not None and conf <= 1:
        conf *= 100

    lineup = str(p.get("Lineup Lock") or p.get("lineup_status") or p.get("Lineup") or "").upper()
    safety = str(p.get("Safety Tag") or "MODERATE").upper()
    alert = str(p.get("Pitch Alert") or "").upper()
    arsenal = str(p.get("Pitch-Type Label") or "").upper()
    ump = str(p.get("Advanced Umpire Label") or "").upper()
    tier = str(p.get("action_tier") or p.get("Tier") or "").upper()

    ml_ctx = final_board_ml_context(p, board)
    ml_context_label = ml_ctx.get("ML Context", "UNKNOWN")
    ml_context_score = safe_float(ml_ctx.get("ML Context Score"), 0) or 0
    ml_context_note = ml_ctx.get("ML Context Note", "")

    exp_bf = safe_float(p.get("Exp BF") or p.get("expected_bf"), None)
    ip_floor = safe_float(p.get("IP Floor") or p.get("ip_floor"), None)
    volatility = safe_float(p.get("Volatility") or p.get("volatility"), None)

    score = 50.0

    # Raw edge + sim confidence drive the score.
    if conf is not None:
        score += clamp((conf - 55) * 0.45, -8, 18)
    if edge is not None:
        score += clamp(edge * 7.0, -4, 24)

    # Risk layers modify confidence only.
    if safety == "SAFE":
        score += 8
    elif safety == "MODERATE":
        score += 2
    elif safety == "VOLATILE":
        score -= 7 if (edge is not None and edge >= 1.5) else 10

    if "CONFIRMED" in lineup or "TRUE" in lineup:
        score += 8
    elif "FALLBACK" in lineup or not lineup:
        score -= 5 if (edge is not None and edge >= 1.25) else 8
    elif "PROJECTED" in lineup:
        score -= 3

    if "HIGH_ALERT" in alert:
        score -= 12
    elif "MEDIUM_ALERT" in alert:
        score -= 7
    elif "LOW_ALERT" in alert:
        score -= 3
    elif "CLEAR" in alert:
        score += 4

    # BF/leash realism: important, but not projection-destroying.
    if exp_bf is not None:
        if exp_bf >= 22:
            score += 5
        elif exp_bf < 16.5:
            score -= 9
        elif exp_bf < 18:
            score -= 5

    if ip_floor is not None:
        if ip_floor >= 5:
            score += 4
        elif ip_floor < 3.6:
            score -= 7

    if volatility is not None:
        if volatility >= 2.25:
            score -= 5
        elif volatility <= 1.55:
            score += 3

    if "ARSENAL_EDGE" in arsenal:
        score += 5
    elif "ARSENAL_RISK" in arsenal:
        score -= 5

    if "UMP_K_BOOST" in ump:
        score += 2
    elif "UMP_K_DRAG" in ump:
        score -= 2

    # ML context is confidence-only and capped very lightly.
    score += clamp(ml_context_score, -ML_CONTEXT_MAX_SCORE_SWING, ML_CONTEXT_MAX_SCORE_SWING)

    if tier == "A":
        score += 5
    elif tier == "B":
        score += 2
    elif tier == "C":
        score -= 2
    elif "PASS" in tier:
        score -= 4 if (edge is not None and edge >= 1.25) else 8

    if side == "NO LINE" or line is None:
        score = min(score, 30)

    score = int(clamp(round(score), 0, 100))

    # Final labels: lineup confirmed earns true FINAL PLAY, otherwise strong raw edge is STRONG LEAN/MONITOR.
    if score >= 84 and ("CONFIRMED" in lineup or "TRUE" in lineup):
        label = "🔥 FINAL PLAY"
        cls = "good-badge"
    elif score >= 78:
        label = "✅ STRONG LEAN"
        cls = "good-badge"
    elif score >= 64:
        label = "⚠️ MONITOR"
        cls = "yellow-badge"
    else:
        label = "🚫 PASS / WAIT"
        cls = "red-badge"

    warnings, positives = [], []
    if "FALLBACK" in lineup or not lineup:
        warnings.append("WAIT LINEUP")
    elif "CONFIRMED" in lineup or "TRUE" in lineup:
        positives.append("LINEUP LOCKED")

    if safety == "VOLATILE":
        warnings.append("VOLATILE")
    elif safety == "SAFE":
        positives.append("SAFE")

    if "HIGH_ALERT" in alert or "MEDIUM_ALERT" in alert:
        warnings.append(alert.replace("_", " "))
    elif "CLEAR" in alert:
        positives.append("CLEAR ALERT")

    if "ARSENAL_EDGE" in arsenal:
        positives.append("ARSENAL EDGE")
    elif "ARSENAL_RISK" in arsenal:
        warnings.append("ARSENAL RISK")

    if "UMP_K_BOOST" in ump:
        positives.append("UMP BOOST")
    if ml_context_score >= 3:
        positives.append("ML SUPPORT")
    elif ml_context_score <= -3:
        warnings.append("ML SCRIPT RISK")

    if edge is not None and edge >= 1.5:
        positives.append("BIG RAW EDGE")
    elif edge is not None and edge < 0.5:
        warnings.append("SMALL EDGE")

    if exp_bf is not None and exp_bf < 18:
        warnings.append("LOW BF")
    elif exp_bf is not None and exp_bf >= 22:
        positives.append("STRONG BF")

    return {
        "Pitcher": p.get("pitcher"),
        "Matchup": p.get("matchup"),
        "Side": side,
        "Line": line,
        "Projection": None if proj is None else round(proj, 2),
        "Raw K PROJ": None if proj is None else round(proj, 2),
        "Risk Read": None if refined is None else round(refined, 2),
        "Refined": None if refined is None else round(refined, 2),
        "Refined Shift": None if proj is None or refined is None else round(refined - proj, 2),
        "Edge": None if edge is None else round(edge, 2),
        "Final Score": score,
        "Final Label": label,
        "Final Class": cls,
        "Safety Tag": safety,
        "Lineup": lineup or "UNKNOWN",
        "Pitch Alert": alert or "UNKNOWN",
        "Arsenal": arsenal or "UNKNOWN",
        "Umpire": ump or "UNKNOWN",
        "Tier": tier,
        "Exp BF": exp_bf,
        "IP Floor": ip_floor,
        "ML Context": ml_context_label,
        "ML Context Score": ml_context_score,
        "ML Context Note": ml_context_note,
        "ML Context Pick": ml_ctx.get("ML Context Pick"),
        "ML Context Edge": ml_ctx.get("ML Context Edge"),
        "Warnings": " | ".join(warnings) if warnings else "—",
        "Positives": " | ".join(positives) if positives else "—",
    }


def build_final_board_rows(board):
    # Build lookup from original K Upside board BEFORE any overlays mutate board.
    true_k_lookup = build_true_kproj_lookup(board)

    try:
        if "apply_elite_safety_overlays_to_board" in globals():
            board = apply_elite_safety_overlays_to_board(board)
        if "apply_safe_volatile_tags" in globals():
            board = apply_safe_volatile_tags(board)
        if "apply_elite_refinement_overlays" in globals():
            board = apply_elite_refinement_overlays(board)
    except Exception:
        pass

    rows = [
        _fb_score_row(p, board, true_k_lookup)
        for p in (board or [])
        if isinstance(p, dict) and p.get("pitcher")
    ]
    rows.sort(key=lambda r: (r.get("Final Score") or 0, r.get("Edge") or 0), reverse=True)
    return rows


def render_final_pick_card(r):
    score = safe_float(r.get("Final Score"), 0) or 0
    proj = safe_float(r.get("Projection"), None)
    ref = safe_float(r.get("Refined"), proj)
    shift = 0 if proj is None or ref is None else ref - proj
    line = r.get("Line")
    line_txt = "NO LINE" if line is None else f"{line:g}"
    bar = int(clamp(score, 4, 100))
    color = "#31e84f" if score >= 70 else "#ffbe3c" if score >= 58 else "#ff5f5f"
    st.markdown(f"""
    <div class="pick-card">
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
        <div>
          <div class="small-muted">FINAL BOARD • merged decision layer</div>
          <div class="player-name">{html.escape(str(r.get("Pitcher","—")))}</div>
          <div class="small-muted">{html.escape(str(r.get("Matchup","—")))}</div>
        </div>
        <div class="badge {r.get("Final Class","yellow-badge")}">{html.escape(str(r.get("Final Label","—")))}</div>
      </div>
      <div class="kpi-strip" style="grid-template-columns:repeat(5,minmax(0,1fr));">
        <div class="kpi-box"><div class="kpi-label">Pick</div><div class="kpi-value">{html.escape(str(r.get("Side","—")))} {line_txt}</div><div class="kpi-sub">line</div></div>
        <div class="kpi-box"><div class="kpi-label">Raw K PROJ</div><div class="kpi-value">{proj if proj is not None else "—"}</div><div class="kpi-sub">true projection</div></div>
        <div class="kpi-box"><div class="kpi-label">Risk Read</div><div class="kpi-value">{ref if ref is not None else "—"}</div><div class="kpi-sub">shift {shift:+.2f}</div></div>
        <div class="kpi-box"><div class="kpi-label">Edge</div><div class="kpi-value">{r.get("Edge","—")}</div><div class="kpi-sub">vs line</div></div>
        <div class="kpi-box"><div class="kpi-label">Final Score</div><div class="kpi-value" style="color:{color};">{int(score)}</div><div class="kpi-sub">0-100</div></div>
      </div>
      <div class="progress-wrap"><div class="progress-green" style="width:{bar}%;"></div></div>
      <div style="margin-top:12px;">
        <span class="badge">{html.escape(str(r.get("Safety Tag","—")))}</span>
        <span class="badge">{html.escape(str(r.get("Lineup","—")))}</span>
        <span class="badge">{html.escape(str(r.get("Pitch Alert","—")))}</span>
        <span class="badge">{html.escape(str(r.get("Arsenal","—")))}</span>
        <span class="badge">{html.escape(str(r.get("Umpire","—")))}</span>
        <span class="badge">ML Context: {html.escape(str(r.get("ML Context","—")))}</span>
      </div>
      <div class="hr-soft"></div>
      <div><b>Positives:</b> {html.escape(str(r.get("Positives","—")))}</div>
      <div><b>Warnings:</b> {html.escape(str(r.get("Warnings","—")))}</div>
    </div>
    """, unsafe_allow_html=True)

def render_final_board_tab(board, dates=None):
    st.markdown("### 🧠 FINAL BOARD — Final Decision Center")
    st.caption("Raw K PROJ is synced from the K Upside tab. Risk Read/Final Score are confidence layers only.")
    rows = build_final_board_rows(board)
    if not rows:
        st.info("No board loaded yet. Refresh the live board first.")
        return
    df = pd.DataFrame(rows)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Final Plays", int(df["Final Label"].astype(str).str.contains("FINAL PLAY").sum()))
    c2.metric("Strong Leans", int(df["Final Label"].astype(str).str.contains("STRONG LEAN").sum()))
    c3.metric("Wait Lineup", int(df["Warnings"].astype(str).str.contains("WAIT LINEUP").sum()))
    c4.metric("Avg Score", round(pd.to_numeric(df["Final Score"], errors="coerce").mean(), 1))
    st.markdown('<div class="section-title-pro">Top Final Cards</div>', unsafe_allow_html=True)
    for r in rows[:10]:
        render_final_pick_card(r)
    st.markdown('<div class="section-title-pro">Final Board Table</div>', unsafe_allow_html=True)
    keep = ["Pitcher","Matchup","Side","Line","Raw K PROJ","Risk Read","Refined Shift","Edge","Final Score","Final Label","Safety Tag","Lineup","Pitch Alert","Arsenal","Umpire","ML Context","ML Context Score","ML Context Pick","ML Context Edge","Exp BF","IP Floor","Warnings","Positives"]
    st.dataframe(df[[c for c in keep if c in df.columns]], use_container_width=True, hide_index=True)


# =========================
# VISIBLE LOWER TABS RESTORE
# UI-only render helpers for ALL PITCHERS / SAVE-GRADE / CALIBRATION / SOURCE LOG / SETTINGS.
# Does NOT touch K projections, Final Board math, ML, or grading logic.
# =========================
def _safe_df(obj):
    try:
        return pd.DataFrame(obj or [])
    except Exception:
        return pd.DataFrame()

def render_all_pitchers_visible_tab(board, dates=None):
    st.markdown("### 📋 All Pitchers")
    st.caption("Full current board. Display-only.")
    df = _safe_df(board)
    if df.empty:
        st.info("No pitcher board loaded yet. Refresh the live board first.")
        return
    preferred = [
        "pitcher","matchup","projection","line","bet_action","decision","data_score",
        "pitcher_k","opp_k","expected_bf","lineup_status","Safety Tag","Pitch Alert",
        "Pitch-Type Label","Advanced Umpire Label"
    ]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

def render_official_save_grade_visible_tab(board, dates=None):
    st.markdown("### 💾 Official Save / Grade")
    st.caption("Save before-game snapshots and review saved/graded picks.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save current board snapshot", use_container_width=True):
            try:
                picks = []
                for p in board or []:
                    if not isinstance(p, dict):
                        continue
                    d = {}
                    try:
                        d = kproj_decision(p)
                    except Exception:
                        d = {}
                    row = dict(p)
                    row["pick_id"] = row.get("pick_id") or f"{row.get('game_pk','NA')}_{row.get('pitcher_id', row.get('pitcher',''))}_{row.get('line', row.get('underdog_line',''))}_{row.get('pick_side', d.get('lean_side',''))}"
                    row["k_proj_snapshot"] = d.get("projection", row.get("projection"))
                    row["line"] = d.get("line", row.get("line", row.get("underdog_line")))
                    row["pick_side"] = d.get("lean_side", row.get("pick_side"))
                    row["decision"] = d.get("decision", row.get("decision", row.get("bet_action")))
                    row["saved_from_tab"] = "OFFICIAL_SAVE_GRADE"
                    picks.append(row)
                added = save_many_once(picks) if "save_many_once" in globals() else 0
                st.success(f"Saved {added} new snapshot rows.")
            except Exception as e:
                st.error(f"Save failed: {e}")
    with c2:
        if st.button("✅ Auto-grade finished games", use_container_width=True):
            try:
                graded = grade_finished_games() if "grade_finished_games" in globals() else 0
                st.success(f"Graded {graded} finished picks.")
            except Exception as e:
                st.error(f"Grade failed: {e}")

    picks = load_saved_pick_log_normalized() if "PICK_LOG" in globals() else []
    results = load_json(RESULT_LOG, []) if "RESULT_LOG" in globals() else []
    st.markdown("#### Saved Picks")
    if picks:
        st.dataframe(pd.DataFrame(picks[-250:]), use_container_width=True, hide_index=True)
    else:
        st.info("No saved picks yet.")
    st.markdown("#### Results")
    if results:
        st.dataframe(pd.DataFrame(results[-250:]), use_container_width=True, hide_index=True)
    else:
        st.info("No graded results yet.")

def render_calibration_visible_tab(board=None, dates=None):
    st.markdown("### 🧪 Calibration")
    st.caption("Calibration dashboard based on graded result history.")
    results = load_json(RESULT_LOG, []) if "RESULT_LOG" in globals() else []
    if not results:
        st.info("No graded results yet. Calibration will populate after results are graded.")
        return
    try:
        profile, df = build_true_calibration_dashboard(results)
        c1, c2, c3 = st.columns(3)
        c1.metric("Samples", profile.get("samples", len(results)) if isinstance(profile, dict) else len(results))
        c2.metric("Buckets", len(df) if df is not None else 0)
        if isinstance(profile, dict):
            c3.metric("Overall Bias", profile.get("overall_bias", "—"))
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No calibration buckets yet.")
    except Exception as e:
        st.warning(f"Calibration dashboard unavailable: {e}")
        st.dataframe(pd.DataFrame(results[-250:]), use_container_width=True, hide_index=True)

def render_source_log_visible_tab(board=None, dates=None):
    st.markdown("### 🧾 Source Log")
    st.caption("Recent API/source diagnostics and request records.")
    possible_logs = []
    for name in ["REQUEST_LOG", "SOURCE_LOG", "DEBUG_LOG"]:
        if name in globals():
            possible_logs.append(globals().get(name))
    loaded_any = False
    for log_path in possible_logs:
        try:
            rows = load_json(log_path, [])
            if rows:
                loaded_any = True
                st.markdown(f"#### {log_path}")
                st.dataframe(pd.DataFrame(rows[-250:]), use_container_width=True, hide_index=True)
        except Exception:
            pass
    if not loaded_any:
        st.info("No source log rows yet for this session.")
        try:
            if board:
                preview = []
                for p in board[:100]:
                    if isinstance(p, dict):
                        preview.append({
                            "Pitcher": p.get("pitcher"),
                            "Matchup": p.get("matchup"),
                            "Line": p.get("line") or p.get("underdog_line"),
                            "Line Source": p.get("line_source") or p.get("source"),
                            "Lineup": p.get("lineup_status"),
                            "Data Score": p.get("data_score"),
                        })
                if preview:
                    st.markdown("#### Current board source preview")
                    st.dataframe(pd.DataFrame(preview), use_container_width=True, hide_index=True)
        except Exception:
            pass

def render_settings_visible_tab(board=None, dates=None):
    st.markdown("### ⚙️ Settings")
    st.caption("Current model gates and app settings. Display-only.")
    settings = {
        "MIN_BETTABLE_GAP_KS": globals().get("MIN_BETTABLE_GAP_KS", "—"),
        "DYNAMIC_LEASH_BF_ENABLED": globals().get("DYNAMIC_LEASH_BF_ENABLED", "—"),
        "SMART_EDGE_UPGRADES_ENABLED": globals().get("SMART_EDGE_UPGRADES_ENABLED", "—"),
        "PROJECTION_FIRST_CONFIDENCE_ENABLED": globals().get("PROJECTION_FIRST_CONFIDENCE_ENABLED", "—"),
        "ACE_CEILING_PROTECTION_ENABLED": globals().get("ACE_CEILING_PROTECTION_ENABLED", "—"),
        "ACE_CLOSE_UNDER_GAP_MAX": globals().get("ACE_CLOSE_UNDER_GAP_MAX", "—"),
        "PASS_OVER_UPGRADE_EDGE": globals().get("PASS_OVER_UPGRADE_EDGE", "—"),
        "PASS_UNDER_UPGRADE_EDGE": globals().get("PASS_UNDER_UPGRADE_EDGE", "—"),
        "SMART_EDGE_MAX_PROJ_NUDGE": globals().get("SMART_EDGE_MAX_PROJ_NUDGE", "—"),
        "DYNAMIC_LEASH_BF_MAX_BOOST": globals().get("DYNAMIC_LEASH_BF_MAX_BOOST", "—"),
        "MIN_ELITE_DATA_SCORE": globals().get("MIN_ELITE_DATA_SCORE", "—"),
        "MIN_BETTABLE_PROB": globals().get("MIN_BETTABLE_PROB", "—"),
        "MIN_BETTABLE_EV": globals().get("MIN_BETTABLE_EV", "—"),
        "MIN_OFFICIAL_SAVE_SCORE": globals().get("MIN_OFFICIAL_SAVE_SCORE", "—"),
        "MAX_RECOMMENDED_KELLY": globals().get("MAX_RECOMMENDED_KELLY", "—"),
        "WEATHER_FACTOR_MIN": globals().get("WEATHER_FACTOR_MIN", "—"),
        "WEATHER_FACTOR_MAX": globals().get("WEATHER_FACTOR_MAX", "—"),
        "UMPIRE_FACTOR_MIN": globals().get("UMPIRE_FACTOR_MIN", "—"),
        "UMPIRE_FACTOR_MAX": globals().get("UMPIRE_FACTOR_MAX", "—"),
        "APP_VERSION": globals().get("APP_VERSION", "—"),
    }
    st.dataframe(pd.DataFrame([{"Setting": k, "Value": v} for k, v in settings.items()]), use_container_width=True, hide_index=True)



# =========================
# MOBILE K UPSIDE PLAYER CARD FIX
# CSS/UI only. Does NOT affect projections, decisions, Final Board, ML, grading, or data.
# =========================
def inject_mobile_k_card_fix():
    st.markdown("""
    <style>
    @media (max-width: 780px) {
        html, body, [data-testid="stAppViewContainer"], .main, .block-container {
            max-width: 100vw !important;
            overflow-x: hidden !important;
        }
        .block-container {
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }

        .pick-card, .kproj-card, .player-card, .pitcher-card {
            width: 100% !important;
            max-width: calc(100vw - 1.2rem) !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
            padding: 18px 16px !important;
            border-radius: 22px !important;
        }

        .kproj-top, .card-top, .pick-top, .player-top, .hero-grid, .main-grid,
        .kproj-main-row, .projection-row, .edge-row, .card-main-row {
            display: grid !important;
            grid-template-columns: 1fr !important;
            gap: 14px !important;
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
        }

        .kpi-strip, .metric-strip, .stats-strip, .kproj-metrics,
        .card-metrics, .mini-metrics {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 12px !important;
            width: 100% !important;
            max-width: 100% !important;
            overflow: visible !important;
        }

        .kpi-box, .metric-box, .stat-box, .mini-card, .metric-card {
            min-width: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            padding: 13px 10px !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            text-align: center !important;
        }

        .kpi-label, .metric-label, .stat-label, .mini-label, .k-label, .label {
            white-space: normal !important;
            word-break: keep-all !important;
            overflow-wrap: normal !important;
            hyphens: none !important;
            font-size: 11px !important;
            line-height: 1.2 !important;
            letter-spacing: 0.03em !important;
            text-align: center !important;
        }

        .kpi-value, .metric-value, .stat-value, .mini-value, .big-number {
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: normal !important;
            font-size: clamp(24px, 8vw, 42px) !important;
            line-height: 1.02 !important;
            text-align: center !important;
        }

        .kpi-sub, .metric-sub, .stat-sub, .mini-sub {
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: normal !important;
            font-size: 12px !important;
            line-height: 1.25 !important;
            text-align: center !important;
        }

        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
            width: 100% !important;
        }

        div[data-testid="column"] {
            min-width: 0 !important;
        }

        .pick-card div[data-testid="column"],
        .kproj-card div[data-testid="column"],
        .player-card div[data-testid="column"],
        .pitcher-card div[data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        .decision-box, .edge-box, .pick-decision, .final-decision {
            width: 100% !important;
            max-width: 100% !important;
            text-align: center !important;
            overflow: hidden !important;
        }

        .last10, .last-10, .mini-k-bars, .distribution-box, .distribution {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
            white-space: nowrap !important;
        }

        div[data-testid="stDataFrame"] {
            max-width: 100% !important;
            overflow-x: auto !important;
        }
    }

    @media (max-width: 430px) {
        .kpi-strip, .metric-strip, .stats-strip, .kproj-metrics,
        .card-metrics, .mini-metrics {
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
        }
        .kpi-box, .metric-box, .stat-box, .mini-card, .metric-card {
            padding: 12px 8px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


tab_kproj, tab_final_board, tab_moneyline_edge, tab_lineup_lock, tab_results_dash, tab_auto_results, tab_safe_vol, tab_pitch_ump, tab2, tab3, tab4, tab5, tab6, tab_calibration_audit= st.tabs([
    'K PROJ / UPSIDE',
    'FINAL BOARD',
    'MONEYLINE EDGE',
    'LINEUP LOCK',
    'RESULTS DASH',
    'AUTO RESULTS',
    'SAFE/VOLATILE',
    'PITCH TYPE / UMP',
    'ALL PITCHERS',
    'OFFICIAL SAVE / GRADE',
    'CALIBRATION',
    'SOURCE LOG',
    'SETTINGS',
    "🧠 Calibration Audit"])

with tab_kproj:
    render_kproj_tab(board)

with tab_final_board:
    render_final_board_tab(board, dates)

with tab_moneyline_edge:
    render_moneyline_edge_tab(board, dates)

with tab_lineup_lock:
    render_confirmed_lineup_lock_tab(board, dates)

with tab_results_dash:
    render_results_grading_dashboard_tab(board, dates)

with tab_auto_results:
    render_auto_results_grader_tab(board, dates)

with tab_safe_vol:
    render_safe_volatile_tab(board, dates)

with tab_pitch_ump:
    render_pitchtype_umpire_refinement_tab(board, dates)

with tab2:
    render_all_pitchers_visible_tab(board, dates)

with tab3:
    render_official_save_grade_visible_tab(board, dates)

with tab4:
    render_calibration_visible_tab(board, dates)

with tab5:
    render_source_log_visible_tab(board, dates)

with tab6:
    render_settings_visible_tab(board, dates)
# =========================
# MULTI-PROP TAB RENDERERS
# =========================
try:
    _multi_prop_rows = st.session_state.get("projections", [])

except NameError:
    pass

# =========================
# CALIBRATION AUDIT TAB RENDERER
# =========================
try:
    with tab_calibration_audit:
        render_calibration_audit_tab()
except NameError:
    pass
