import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Live Scheduler — Winner Stay + Fair Rotation
# - ใส่รายชื่อแบบขึ้นบรรทัดใหม่ (สูงสุด 16 คน)
# - สุ่มจัดทีมต่อรอบ (เวียนให้ทุกคนได้เล่นเท่าๆกัน)
# - ถ้าจำนวนผู้เล่นเป็นเลขคี่: เลือก "คนที่เล่นมากที่สุด" พัก
# - ทีมชนะอยู่ต่อ, ถ้าชนะ 2 แมตช์ติด → ต้องออก
# - ทีมแพ้ต้องออกเสมอ
# - ห้ามเจอคู่เดิมซ้ำทันที
# - บันทึกสถิติ Played/Win ต่อคน
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
    "winner_streak": {"team": None, "count": 0, "first_loser": None},
    "history": [],
    "stats": {},
    "resting_player": None,
    "last_match_pairs": set(),  # กันซ้ำ
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
            st.experimental_rerun()  # type: ignore
        except Exception:
            pass


def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}


def _choose_resting_player(players: List[str]) -> Optional[str]:
    """เลือกคนพัก (จำนวนคี่ → เลือกคนที่เล่นมากที่สุดให้ออกไปพัก)"""
    if len(players) % 2 == 0:
        return None
    if not ss.stats:
        return random.choice(players)
    max_played = max(ss.stats[p]["played"] for p in players)
    candidates = [p for p in players if ss.stats[p]["played"] == max_played]
    return random.choice(candidates)


def _pair_teams(active_players: List[str]) -> List[List[str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:
        shuffled = shuffled[:-1]
    return [shuffled[i:i + 2] for i in range(0, len(shuffled), 2)]


def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_match = None
        ss.queue = []
        return

    # เลือกคนพัก (กรณีคี่)
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

    # ทีมแรกสองทีมลงสนาม
    ss.current_match = (teams[0], teams[1])
    ss.queue = teams[2:]

    # รีเซ็ต streak
    ss.winner_streak = {"team": None, "count": 0, "first_loser": None}


def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats.setdefault(p, {"played": 0, "win": 0})
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1


def _fmt_team(team: List[str]) -> str:
    return " & ".join(team)


def _team_key(team: List[str]) -> str:
    return "-".join(sorted(team))


def process_result(winner_side: str):
    if not ss.current_match:
        return

    left, right = ss.current_match
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    # กันเจอซ้ำ: บันทึกคู่นี้
    ss.last_match_pairs.add(frozenset((_team_key(left), _team_key(right))))

    # บันทึกประวัติ + stats
    ss.history.append(f"{_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # streak logic
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    if ss.winner_streak["count"] >= 2:
        # ทีมชนะต้องออก → ดึงทีมใหม่มาเจอกับทีมแพ้แรก
        first_loser = ss.winner_streak.get("first_loser") or loser
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (first_loser, incoming)
        else:
            start_new_round()
        ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
    else:
        # ทีมชนะอยู่ต่อ
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
st.caption("Winner Stay, 2 Wins Out, Fair Rotation ✨")

# Input รายชื่อ
st.subheader("👥 รายชื่อผู้เล่น (สูงสุด 16)")
names_input = st.text_area(
    "พิมพ์รายชื่อ (ขึ้นบรรทัดใหม่แต่ละคน)",
    DEFAULT_NAMES,
    height=180,
)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c_start, c_reset, c_refresh = st.columns(3)
with c_start:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คน")
        elif len(players) > 16:
            st.error("รองรับได้สูงสุด 16 คน")
        else:
            ss.players = players
            init_stats(players)
            start_new_round()
            force_rerun()
with c_reset:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        force_rerun()
with c_refresh:
    if st.button("🔃 Refresh"):
        force_rerun()

# คนพัก
if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พักรอบนี้: **{ss.resting_player}**")

# Match ปัจจุบัน
if ss.get("current_match"):
    left, right = ss.current_match
    st.subheader("🎯 แมตช์ปัจจุบัน")
    st.markdown(f"**ทีมซ้าย:** {_fmt_team(left)} 🆚 **ทีมขวา:** {_fmt_team(right)}")

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
        st.warning("ยังไม่มีแมตช์ → กดเริ่มเกมใหม่")

# ประวัติ
if ss.get("history"):
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, line in enumerate(ss.history, 1):
        st.write(f"{i}. {line}")

# สถิติ
if ss.get("stats"):
    st.subheader("📊 สถิติผู้เล่น")
    ordered = sorted(
        ss.stats.items(),
        key=lambda kv: (kv[1].get("played", 0), -kv[1].get("win", 0)),
    )
    table_rows = [
        {
            "ผู้เล่น": name,
            "จำนวนแมตช์": data.get("played", 0),
            "ชนะ": data.get("win", 0),
            "อัตราชนะ (%)": round(
                (data.get("win", 0) / data.get("played", 0) * 100)
                if data.get("played", 0)
                else 0,
                1,
            ),
        }
        for name, data in ordered
    ]
    st.table(table_rows)
