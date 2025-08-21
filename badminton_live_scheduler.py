import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Live Scheduler — เวอร์ชันล่าสุด
# - ใส่รายชื่อแบบขึ้นบรรทัดใหม่ (สูงสุด 16 คน)
# - สุ่มจัดทีมเป็นคู่ ๆ ต่อรอบ (รองรับจำนวนคี่: มีคนพักแบบยุติธรรม)
# - ทีมชนะอยู่ต่อ, ทีมแพ้ออก
# - ทีมชนะครบ 2 แมตช์ติด → ต้องออก และให้ทีมใหม่เข้ามา
# - ระบบพักผู้เล่นอัตโนมัติ (เลือกจากคนที่เล่นน้อยสุด)
# - ปุ่ม "➡️ หยุดพัก" เพื่อให้ผู้เล่นที่พักกลับมาเล่นทันที
# - บันทึกประวัติ และสถิติ Played/Win ต่อคน
# ============================================================

# -----------------------------
# Session State Initialization
# -----------------------------
DEFAULT_NAMES = ""
ss = st.session_state

DEFAULTS = {
    "players": [],                 
    "current_match": None,         
    "queue": [],                   
    "winner_streak": {             
        "team": None,              
        "count": 0,
        "first_loser": None        
    },
    "history": [],                 
    "stats": {},                   
    "resting_player": None,        
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
            st.experimental_rerun()  # สำหรับเวอร์ชันเก่า
        except Exception:
            pass


def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}


def _choose_resting_player(players: List[str]) -> Optional[str]:
    """เลือกคนพักแบบยุติธรรม (เล่นน้อยที่สุด, ถ้าเสมอให้สุ่ม)"""
    if len(players) % 2 == 0:
        return None
    if not ss.stats:  # เริ่มแรก
        return random.choice(players)
    min_played = min(ss.stats[p]["played"] for p in players)
    candidates = [p for p in players if ss.stats[p]["played"] == min_played]
    return random.choice(candidates)


def _pair_teams(active_players: List[str]) -> List[List[str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:  # ตัดให้เหลือคู่
        shuffled = shuffled[:-1]
    return [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]


def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_match = None
        ss.queue = []
        return

    # เลือกคนพัก (ถ้า odd)
    if ss.resting_player is None:
        ss.resting_player = _choose_resting_player(players)

    if ss.resting_player:
        active = [p for p in players if p != ss.resting_player]
    else:
        active = players[:]

    teams = _pair_teams(active)
    if len(teams) < 2:
        ss.current_match = None
        ss.queue = []
        return

    ss.current_match = (teams[0], teams[1])
    ss.queue = teams[2:]

    # reset streak
    ss.winner_streak = {"team": None, "count": 0, "first_loser": None}


def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1


def _fmt_team(team: List[str]) -> str:
    return " & ".join(team)


def process_result(winner_side: str):
    if not ss.current_match:
        return

    left, right = ss.current_match
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    # บันทึกผล
    ss.history.append(f"{_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # streak
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    if ss.winner_streak["count"] >= 2:
        first_loser = ss.winner_streak.get("first_loser") or loser
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (first_loser, incoming)
            ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
        else:
            ss.resting_player = None
            start_new_round()
    else:
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (winner, incoming)
        else:
            ss.resting_player = None
            start_new_round()

    force_rerun()


# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Live Scheduler")
st.caption("สุ่มทีมอัตโนมัติ จัดคิวลื่นไหล เน้นให้ทุกคนได้เล่นอย่างยุติธรรม ✨")

# รายชื่อผู้เล่น
st.subheader("👥 ใส่รายชื่อผู้เล่น (สูงสุด 16 คน)")
names_input = st.text_area(
    "พิมพ์รายชื่อ (ขึ้นบรรทัดใหม่สำหรับแต่ละคน)",
    DEFAULT_NAMES,
    height=180,
)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c_start, c_reset, c_refresh = st.columns(3)
with c_start:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คนขึ้นไป")
        elif len(players) > 16:
            st.error("รองรับได้สูงสุด 16 คน")
        else:
            ss.players = players
            init_stats(players)
            ss.resting_player = None
            start_new_round()
            st.success("เริ่มเกมใหม่เรียบร้อย!")
            force_rerun()
with c_reset:
    if st.button("♻️ Reset ทั้งหมด"):
        for k in list(ss.keys()):
            del ss[k]
        st.success("ล้างสถานะทั้งหมดแล้ว")
        force_rerun()
with c_refresh:
    if st.button("🔃 Refresh สถานะ"):
        force_rerun()

# คนที่พัก
if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พักรอบนี้: **{ss.resting_player}**")
    if st.button("➡️ หยุดพัก (ให้กลับมาเล่น)"):
        ss.resting_player = None
        start_new_round()
        force_rerun()

# แมตช์ปัจจุบัน
if ss.get("current_match"):
    left, right = ss.current_match
    st.subheader("🎯 แมตช์ปัจจุบัน")
    st.markdown(f"**ทีมซ้าย:** {_fmt_team(left)}  \t🆚\t  **ทีมขวา:** {_fmt_team(right)}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ ทีมซ้ายชนะ"):
            process_result("left")
    with c2:
        if st.button("✅ ทีมขวาชนะ"):
            process_result("right")

    if ss.get("queue"):
        st.caption("คิวถัดไป:")
        for i, t in enumerate(ss.queue, 1):
            st.write(f"• {_fmt_team(t)}")
else:
    if ss.get("players"):
        st.warning("ยังไม่มีแมตช์ให้เล่น — กด \"เริ่มเกมใหม่\" เพื่อเริ่มรอบใหม่")

# ประวัติ
if ss.get("history"):
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, line in enumerate(ss.history, 1):
        st.write(f"{i}. {line}")

# สถิติ
if ss.get("stats"):
    st.subheader("📊 สถิติผู้เล่น")
    ordered = sorted(ss.stats.items(), key=lambda kv: (kv[1]["played"], -kv[1]["win"]))
    table_rows = [
        {
            "ผู้เล่น": name,
            "จำนวนแมตช์": data["played"],
            "ชนะ": data["win"],
            "อัตราชนะ (%)": round((data["win"] / data["played"] * 100) if data["played"] else 0, 1),
        }
        for name, data in ordered
    ]
    st.table(table_rows)
