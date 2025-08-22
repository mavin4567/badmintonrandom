import streamlit as st
import random
from typing import List, Optional

# (ออปชัน) Auto-refresh ถ้ามีปลั๊กอิน
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTO = True
except Exception:
    HAS_AUTO = False

# ============================================================
# 🏸 Badminton Scheduler (Fair Winner + Balanced Rotation)
# ============================================================

# -----------------------------
# Session State Initialization
# -----------------------------
ss = st.session_state
DEFAULTS = {
    "players": [],
    "current_match": None,
    "queue": [],
    "winner_streak": {"team": None, "count": 0, "first_loser": None},
    "history": [],
    "stats": {},
    "resting_player": None,
    "last_match": None,   # ป้องกันไม่ให้เจอคู่เดิมซ้ำทันที
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
    """พักจากคนที่เล่นเยอะที่สุด"""
    if len(players) % 2 == 0:
        return None
    max_played = max(ss.stats.get(p, {"played": 0})["played"] for p in players)
    candidates = [p for p in players if ss.stats[p]["played"] == max_played]
    return random.choice(candidates)

def _pair_teams(active_players: List[str]) -> List[List[str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:
        shuffled = shuffled[:-1]
    return [sorted(shuffled[i:i+2]) for i in range(0, len(shuffled), 2)]

def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_match = None
        ss.queue = []
        return

    ss.resting_player = _choose_resting_player(players)
    active = [p for p in players if p != ss.resting_player]

    teams = _pair_teams(active)
    if len(teams) < 2:
        ss.current_match = None
        ss.queue = []
        return

    # หลีกเลี่ยงจับคู่ซ้ำกับ last_match
    first, second = teams[0], teams[1]
    if ss.last_match:
        last_left, last_right = ss.last_match
        if {tuple(first), tuple(second)} == {tuple(last_left), tuple(last_right)}:
            if len(teams) > 2:
                random.shuffle(teams)
                first, second = teams[0], teams[1]

    ss.current_match = (first, second)
    ss.queue = teams[2:]
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

    ss.history.append(f"{_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # จัดการ streak
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    # ชนะ 2 ติด → ผู้ชนะออก แล้วให้ "ทีมที่แพ้ครั้งแรกของสตรีค" เจอกับทีมใหม่จากคิว
    if ss.winner_streak["count"] >= 2:
        first_loser = ss.winner_streak["first_loser"]
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (first_loser, incoming)
            ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
        else:
            start_new_round()
    else:
        # ทีมชนะอยู่ต่อ เจอกับทีมใหม่จากคิว
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (winner, incoming)
        else:
            start_new_round()

    ss.last_match = ss.current_match

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Badminton Scheduler", layout="centered")
st.title("🏸 Badminton Scheduler ก๊วนลุงๆ🧔🏻")

# (ออปชัน) Auto-refresh ถ้ามีปลั๊กอิน
if HAS_AUTO:
    st_autorefresh(interval=10_000, key="autorefresh")

names_input = st.text_area("👥 ใส่รายชื่อผู้เล่น (ขึ้นบรรทัดใหม่)", "", height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คน")
        elif len(players) > 16:
            st.error("สูงสุด 16 คน")
        else:
            ss.players = players
            init_stats(players)
            start_new_round()
            st.success("เริ่มเกมใหม่แล้ว!")
            st.rerun()  # <- rerun ทันที
with c2:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        st.success("ล้างสถานะแล้ว")
        st.rerun()
with c3:
    if st.button("🔃 Refresh"):
        st.rerun()

if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พักรอบนี้: **{ss.resting_player}**")

if ss.get("current_match"):
    left, right = ss.current_match
    st.subheader("🎯 แมตช์ปัจจุบัน")
    st.markdown(f"**ทีมซ้าย:** {_fmt_team(left)} 🆚 **ทีมขวา:** {_fmt_team(right)}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ ทีมซ้ายชนะ"):
            process_result("left")
            st.rerun()  # <- rerun ทันทีหลังบันทึกผล
    with c2:
        if st.button("✅ ทีมขวาชนะ"):
            process_result("right")
            st.rerun()  # <- rerun ทันทีหลังบันทึกผล
    if ss.get("queue"):
        st.caption("คิวถัดไป:")
        for i, t in enumerate(ss.queue, 1):
            st.write(f"• {_fmt_team(t)}")
else:
    if ss.get("players"):
        st.warning("ยังไม่มีแมตช์ — กดเริ่มเกมใหม่")

if ss.get("history"):
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, line in enumerate(ss.history, 1):
        st.write(f"{i}. {line}")

if ss.get("stats"):
    st.subheader("📊 สถิติผู้เล่น")
    ordered = sorted(ss.stats.items(), key=lambda kv: (kv[1]["played"], -kv[1]["win"]))
    st.table([
        {
            "ผู้เล่น": name,
            "แมตช์": data["played"],
            "ชนะ": data["win"],
            "อัตราชนะ (%)": round((data["win"]/data["played"]*100) if data["played"] else 0, 1),
        }
        for name, data in ordered
    ])
