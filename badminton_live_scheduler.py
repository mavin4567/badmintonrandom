import streamlit as st
import random
from typing import List, Optional, Tuple

# ============================================================
# 🏸 Badminton Live Scheduler — เวอร์ชันล่าสุด
# - ใส่รายชื่อผู้เล่น (ขึ้นบรรทัดใหม่)
# - สุ่มจับคู่ 2 คนต่อทีม, A&B == B&A
# - มีระบบพัก (สำหรับจำนวนคี่)
# - ทุกคนได้เล่นใกล้เคียงกัน (เลือกพัก/เลือกคู่จากสถิติ)
# - ทีมชนะอยู่ต่อ แต่ถ้าชนะ 2 แมตช์ติด → ต้องออก
# ============================================================

ss = st.session_state

DEFAULTS = {
    "players": [],
    "current_match": None,          # (team_left, team_right)
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
# Helpers
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


def _normalize_team(team: List[str]) -> Tuple[str, str]:
    """จัดเรียงชื่อในทีมเสมอ เพื่อป้องกัน A&B != B&A"""
    return tuple(sorted(team))


def _choose_resting_player(players: List[str]) -> Optional[str]:
    if len(players) % 2 == 0:
        return None
    if not ss.stats:
        return random.choice(players)
    min_played = min(ss.stats[p]["played"] for p in players)
    candidates = [p for p in players if ss.stats[p]["played"] == min_played]
    return random.choice(candidates)


def _pair_teams(active_players: List[str]) -> List[Tuple[str, str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:
        shuffled = shuffled[:-1]
    return [_normalize_team(shuffled[i:i+2]) for i in range(0, len(shuffled), 2)]


def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_match, ss.queue = None, []
        return

    ss.resting_player = _choose_resting_player(players)
    if ss.resting_player:
        active = [p for p in players if p != ss.resting_player]
    else:
        active = players[:]

    teams = _pair_teams(active)
    if len(teams) < 2:
        ss.current_match, ss.queue = None, []
        return

    ss.current_match = (teams[0], teams[1])
    ss.queue = teams[2:]
    ss.winner_streak = {"team": None, "count": 0, "first_loser": None}


def _update_stats(team: Tuple[str, str], *, is_winner: bool):
    for p in team:
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1


def _fmt_team(team: Tuple[str, str]) -> str:
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

    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    if ss.winner_streak["count"] >= 2:
        # ทีมชนะออก → ดึง first_loser + ทีมใหม่
        first_loser = ss.winner_streak.get("first_loser") or loser
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (first_loser, incoming)
        else:
            start_new_round()
        ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
    else:
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (winner, incoming)
        else:
            start_new_round()

    force_rerun()


def force_substitute_resting():
    """ปล่อยให้คนพักกลับมาเล่น โดยหาคู่ที่เล่นน้อยสุด"""
    if not ss.resting_player:
        return

    available = [p for p in ss.players if p != ss.resting_player]
    if not available:
        return

    min_played = min(ss.stats[p]["played"] for p in available)
    candidates = [p for p in available if ss.stats[p]["played"] == min_played]
    partner = random.choice(candidates)

    new_team = _normalize_team([ss.resting_player, partner])
    ss.queue.append(new_team)
    ss.resting_player = None
    force_rerun()


# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Live Scheduler")
st.caption("จัดคิวให้ทุกคนได้เล่นเท่าๆกัน — มีระบบพัก/อยู่ต่อ/ออกอัตโนมัติ ✨")

st.subheader("👥 รายชื่อผู้เล่น")
names_input = st.text_area("ใส่รายชื่อ (ขึ้นบรรทัดใหม่)", "", height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c_start, c_reset, c_refresh = st.columns(3)
with c_start:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คน")
        elif len(players) > 16:
            st.error("สูงสุด 16 คน")
        else:
            ss.players = players
            init_stats(players)
            start_new_round()
            st.success("เริ่มเกมใหม่เรียบร้อย!")
            force_rerun()
with c_reset:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        force_rerun()
with c_refresh:
    if st.button("🔃 Refresh"):
        force_rerun()

if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นพัก: **{ss.resting_player}**")
    if st.button("👉 ปล่อยคนพักกลับมาเล่น"):
        force_substitute_resting()

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

    if ss.queue:
        st.caption("คิวถัดไป:")
        for t in ss.queue:
            st.write(f"• {_fmt_team(t)}")
else:
    if ss.get("players"):
        st.warning("ยังไม่มีแมตช์ — กดเริ่มเกมใหม่")

if ss.get("history"):
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, h in enumerate(ss.history, 1):
        st.write(f"{i}. {h}")

if ss.get("stats"):
    st.subheader("📊 สถิติผู้เล่น")
    ordered = sorted(ss.stats.items(), key=lambda kv: (kv[1]["played"], -kv[1]["win"]))
    table = [
        {
            "ผู้เล่น": name,
            "จำนวนแมตช์": data["played"],
            "ชนะ": data["win"],
            "อัตราชนะ (%)": round((data["win"]/data["played"]*100) if data["played"] else 0, 1),
        }
        for name, data in ordered
    ]
    st.table(table)
