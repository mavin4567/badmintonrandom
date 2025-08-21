import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Live Scheduler — Logic เวอร์ชันใหม่
# ============================================================

ss = st.session_state
DEFAULT_NAMES = ""

# -----------------------------
# Session State Initialization
# -----------------------------
DEFAULTS = {
    "players": [],
    "current_match": None,
    "queue": [],
    "winner_streak": {"team": None, "count": 0},
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
            st.experimental_rerun()
        except Exception:
            pass


def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}


def _choose_resting_player(players: List[str]) -> Optional[str]:
    """เลือกคนพักจากคนที่เล่นน้อยสุด"""
    if len(players) % 2 == 0:
        return None
    min_played = min(ss.stats.get(p, {"played": 0})["played"] for p in players)
    candidates = [p for p in players if ss.stats.get(p, {"played": 0})["played"] == min_played]
    return random.choice(candidates)


def _pair_teams(players: List[str]) -> List[List[str]]:
    shuffled = players[:]
    random.shuffle(shuffled)
    return [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]


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

    ss.current_match = (teams[0], teams[1])
    ss.queue = teams[2:]
    ss.winner_streak = {"team": None, "count": 0}


def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1


def _fmt_team(team: List[str]) -> str:
    return " & ".join(team)


def _pick_next_team() -> Optional[List[str]]:
    """ดึงทีมจากคิว หรือจัดใหม่ถ้าคิวหมด"""
    if ss.queue:
        return ss.queue.pop(0)

    # ถ้าคิวหมด → เปิดรอบใหม่
    start_new_round()
    if ss.current_match:
        left, right = ss.current_match
        return right  # ให้ทีมขวาเป็นทีมใหม่
    return None


def process_result(winner_side: str):
    if not ss.current_match:
        return

    left, right = ss.current_match
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    ss.history.append(f"{_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # อัปเดต streak
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1}

    # ถ้าชนะ 2 ครั้งติด → ออกทั้งทีม
    if ss.winner_streak["count"] >= 2:
        team1 = _pick_next_team()
        team2 = _pick_next_team()
        if team1 and team2:
            ss.current_match = (team1, team2)
        else:
            start_new_round()
        ss.winner_streak = {"team": None, "count": 0}
    else:
        # ทีมชนะอยู่ต่อ
        incoming = _pick_next_team()
        if incoming:
            ss.current_match = (winner, incoming)
        else:
            start_new_round()

    force_rerun()


# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Live Scheduler")
st.caption("ทุกคนได้เล่นอย่างยุติธรรม — ทีมชนะอยู่ต่อ, ทีมแพ้ออก, ชนะติด 2 แมตช์ต้องพัก ✨")

# รายชื่อผู้เล่น
st.subheader("👥 รายชื่อผู้เล่น (สูงสุด 16 คน)")
names_input = st.text_area("พิมพ์รายชื่อ (ขึ้นบรรทัดใหม่สำหรับแต่ละคน)", DEFAULT_NAMES, height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คน")
        elif len(players) > 16:
            st.error("รองรับสูงสุด 16 คน")
        else:
            ss.players = players
            init_stats(players)
            start_new_round()
            force_rerun()
with c2:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        force_rerun()
with c3:
    if st.button("🔃 Refresh"):
        force_rerun()

# ผู้พัก
if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พักรอบนี้: **{ss.resting_player}**")

# แมตช์ปัจจุบัน
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
        for t in ss.queue:
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
    rows = [
        {
            "ผู้เล่น": name,
            "จำนวนแมตช์": data["played"],
            "ชนะ": data["win"],
            "อัตราชนะ (%)": round((data["win"]/data["played"]*100) if data["played"] else 0, 1),
        }
        for name, data in ordered
    ]
    st.table(rows)
