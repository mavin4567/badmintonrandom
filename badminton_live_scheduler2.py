import streamlit as st
import random
from typing import List, Optional, Tuple

# ============================================================
# 🏸 Badminton Live Scheduler — Stable + Auto Refresh
# ============================================================

DEFAULT_NAMES = ""
ss = st.session_state

# -----------------------------
# Session State Initialization
# -----------------------------
DEFAULTS = {
    "players": [],
    "current_match": None,  # Tuple[List[str], List[str]] | None
    "queue": [],
    "winner_streak": {"team": None, "count": 0, "first_loser": None},
    "history": [],
    "stats": {},
    "resting_player": None,
}
for k, v in DEFAULTS.items():
    if k not in ss:
        ss[k] = v

# -----------------------------
# Utilities
# -----------------------------
def force_rerun():
    """รองรับทั้ง st.rerun() และ experimental (fallback)"""
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()  # type: ignore[attr-defined]
        except Exception:
            pass

def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}

def _choose_resting_player(players: List[str]) -> Optional[str]:
    """เลือกคนพักแบบยุติธรรม: คนที่เล่นน้อยสุด ถ้าเท่ากันสุ่ม"""
    if len(players) % 2 == 0:
        return None
    if not ss.stats:
        return random.choice(players)
    min_played = min(ss.stats.get(p, {"played": 0})["played"] for p in players)
    candidates = [p for p in players if ss.stats.get(p, {"played": 0})["played"] == min_played]
    return random.choice(candidates) if candidates else None

def _pair_teams(active_players: List[str]) -> List[List[str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:
        shuffled = shuffled[:-1]
    return [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]

def _fmt_team(team: List[str]) -> str:
    return " & ".join(team)

def _valid_match(m) -> bool:
    """ตรวจสอบว่า current_match ถูกต้องเป็น (teamA, teamB) และแต่ละทีมมี 2 คน"""
    if not isinstance(m, (list, tuple)) or len(m) != 2:
        return False
    a, b = m
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)):
        return False
    if len(a) != 2 or len(b) != 2:
        return False
    return True

# -----------------------------
# Round / Flow
# -----------------------------
def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_match = None
        ss.queue = []
        return

    ss.resting_player = _choose_resting_player(players)
    active = [p for p in players if p != ss.resting_player] if ss.resting_player else players[:]

    teams = _pair_teams(active)
    if len(teams) < 2:
        ss.current_match = None
        ss.queue = []
        return

    ss.current_match = (teams[0], teams[1])
    ss.queue = teams[2:]
    # รีเซ็ตสตรีคเมื่อตั้งรอบใหม่
    ss.winner_streak = {"team": None, "count": 0, "first_loser": None}

def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats.setdefault(p, {"played": 0, "win": 0})
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1

def process_result(winner_side: str):
    """บันทึกผลและจัดคู่ใหม่ ตามกติกา + กันพังทุกกรณี + refresh อัตโนมัติ"""
    m = ss.get("current_match")
    if not m or not _valid_match(m):
        # ไม่มีแมตช์ที่ถูกต้อง — พยายามเปิดรอบใหม่ให้
        start_new_round()
        return

    left, right = m  # แต่ละทีมเป็น list[str] ยาว 2
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    # ป้องกันกรณีข้อมูลทีมผิดรูป
    if not (isinstance(winner, (list, tuple)) and isinstance(loser, (list, tuple))):
        start_new_round()
        return

    # ประวัติ + สถิติ
    ss.history.append(f"{_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # สตรีค
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    # ชนะครบ 2 → ทีมชนะออก, เอา first_loser กลับมาเจอทีมใหม่
    if ss.winner_streak["count"] >= 2:
        first_loser = ss.winner_streak.get("first_loser") or loser
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (first_loser, incoming)
            # เริ่มนับสตรีคใหม่ตั้งแต่แมตช์ถัดไป
            ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
        else:
            start_new_round()
    else:
        # ทีมชนะอยู่ต่อ เจอทีมใหม่จากคิว
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (winner, incoming)
        else:
            start_new_round()

    force_rerun()

# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Live Scheduler")
st.caption("สุ่มทีมอัตโนมัติ จัดคิวลื่นไหล เน้นให้ทุกคนได้เล่นอย่างยุติธรรม ✨")

st.subheader("👥 ใส่รายชื่อผู้เล่น (สูงสุด 16 คน)")
names_input = st.text_area("พิมพ์รายชื่อ (ขึ้นบรรทัดใหม่สำหรับแต่ละคน)", DEFAULT_NAMES, height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c_start, c_reset, c_refresh = st.columns(3)
with c_start:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คนขึ้นไป")
        elif len(players) > 16:
