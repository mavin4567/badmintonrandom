import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Live Scheduler — เวอร์ชัน (เพิ่มปุ่มพัก/กลับมา)
# ============================================================

# -----------------------------
# Session State Initialization
# -----------------------------
DEFAULT_NAMES = ""
ss = st.session_state

DEFAULTS = {
    "players": [],                 # รายชื่อทั้งหมด
    "current_match": None,         # (team_left, team_right)
    "queue": [],                   # ทีมในคิว
    "winner_streak": {             # streak ทีมชนะ
        "team": None,
        "count": 0,
        "first_loser": None
    },
    "history": [],                 # ประวัติการแข่งขัน
    "stats": {},                   # {player: {played:int, win:int}}
    "resting_player": None,        # ผู้เล่นที่พัก (กรณีจำนวนคี่/เลือกพักเอง)
}
for k, v in DEFAULTS.items():
    if k not in ss:
        ss[k] = v


# -----------------------------
# Helper Functions
# -----------------------------
def force_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}


def _choose_resting_player(players: List[str]) -> Optional[str]:
    """เลือกคนพักแบบยุติธรรม: คนที่เล่นน้อยที่สุด"""
    if len(players) % 2 == 0:
        return None
    min_played = min(ss.stats.get(p, {"played": 0})["played"] for p in players)
    candidates = [p for p in players if ss.stats.get(p, {"played": 0})["played"] == min_played]
    return random.choice(candidates)


def _pair_teams(active_players: List[str]) -> List[List[str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:
        shuffled = shuffled[:-1]
    return [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]


def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_match = None
        ss.queue = []
        return

    # ใช้ resting_player ถ้ามีจาก manual, ถ้าไม่มีใช้ auto
    if ss.resting_player:
        active = [p for p in players if p != ss.resting_player]
    else:
        auto_rest = _choose_resting_player(players)
        ss.resting_player = auto_rest
        active = [p for p in players if p != auto_rest] if auto_rest else players[:]

    teams = _pair_teams(active)
    if len(teams) < 2:
        ss.current_match = None
        ss.queue = []
