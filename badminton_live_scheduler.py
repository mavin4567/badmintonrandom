import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Live Scheduler — เล่นวน + ไม่เจอคู่ซ้ำติดกัน
# ============================================================

ss = st.session_state
DEFAULTS = {
    "players": [],
    "current_match": None,
    "queue": [],
    "winner_streak": {"team": None, "count": 0, "first_loser": None},
    "history": [],
    "stats": {},
    "resting_player": None,
    "last_match": None,   # กันไม่ให้จับคู่ซ้ำทันที
}
for k, v in DEFAULTS.items():
    if k not in ss:
        ss[k] = v


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
    """เลือกคนพักจากผู้ที่เล่นน้อยสุด"""
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
        ss.current_match, ss.queue = None, []
        return

    ss.resting_player = _choose_resting_player(players)
    active = [p for p in players if p != ss.resting_player] if ss.resting_player else players[:]

    for _ in range(20):  # ลองสุ่มไม่ให้ซ้ำคู่เดิม
        teams = _pair_teams(active)
        if len(teams) < 2:
            ss.current_match, ss.queue = None, []
            return

        new_match = {frozenset(teams[0]), frozenset(teams[1])}
        if ss.last_match is None or new_match != ss.last_match:
            ss.current_match = (teams[0], teams[1])
            ss.queue = teams[2:]
            ss.last_match = new_match
            ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
            return

    # ถ้าลองแล้วก็ยังซ้ำ → ยอมรับ
    ss.current_match = (teams[0], teams[1])
    ss.queue = teams[2:]
    ss.last_match = {frozenset(teams[0]), frozenset(teams[1])}


def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats.setdefault(p, {"played": 0, "win": 0})
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

    # เช็ค streak
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    # ถ้าชนะ 2 เกมติด → ออก
    if ss.winner_streak["count"] >= 2:
        first_loser = ss.winner_streak.get("first_loser") or loser
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (first_loser, incoming)
            ss.winner_streak = {"team": None, "count": 0, "first_loser": None}
        else:
            start_new_round()
    else:
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_match = (winner, incoming)
        else:
            start_new_round()

    force_rerun()


# ---------------- UI ----------------
st.title("🏸 Badminton Live Scheduler")
st.caption("สุ่มทีมวนไปเรื่อย ๆ + กันไม่ให้เจอคู่เดิมซ้ำทันที")

st.subheader("👥 รายชื่อผู้เล่น (สูงสุด 16)")
names_input = st.text_area("ใส่ชื่อ (ขึ้นบรรทัดใหม่)", height=180)
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
            st.success("เริ่มใหม่แล้ว")
            force_rerun()
with c2:
    if st.button("♻️ Reset ทั้งหมด"):
        for k in list(ss.keys()):
            del ss[k]
        st.success("ล้างทั้งหมดแล้ว")
        force_rerun()
with c3:
    if st.button("🔃 Refresh"):
        force_rerun()

if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พัก: **{ss.resting_player}**")

if ss.get("current_match_
