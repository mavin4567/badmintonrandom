import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Scheduler (Multi-Court Version)
# ============================================================

# -----------------------------
# Session State Initialization
# -----------------------------
ss = st.session_state
DEFAULTS = {
    "players": [],
    "current_matches": [],   # รายชื่อแมตช์ทั้งหมดของแต่ละคอร์ท
    "queues": {},            # คิวแยกตามคอร์ท
    "winner_streaks": {},    # streak ต่อคอร์ท
    "history": [],
    "stats": {},
    "resting_players": [],
    "last_matches": {},      # ป้องกันเจอคู่เดิมซ้ำทันที
    "num_courts": 1,
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
    except:
        try:
            st.experimental_rerun()
        except:
            pass

def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}

def _choose_resting_players(players: List[str], num_rest: int) -> List[str]:
    """พักจากคนที่เล่นเยอะที่สุด ตามจำนวนที่ต้องการ"""
    if num_rest <= 0:
        return []
    max_played = max(ss.stats.get(p, {"played": 0})["played"] for p in players)
    candidates = [p for p in players if ss.stats[p]["played"] == max_played]
    return random.sample(candidates, min(num_rest, len(candidates)))

def _pair_teams(active_players: List[str]) -> List[List[str]]:
    shuffled = active_players[:]
    random.shuffle(shuffled)
    if len(shuffled) % 2 == 1:
        shuffled = shuffled[:-1]
    return [sorted(shuffled[i:i+2]) for i in range(0, len(shuffled), 2)]

def start_new_round():
    players = ss.players[:]
    if len(players) < ss.num_courts * 4:
        ss.current_matches = []
        ss.queues = {}
        return

    ss.current_matches = []
    ss.queues = {}
    ss.resting_players = _choose_resting_players(players, len(players) % 2)

    active = [p for p in players if p not in ss.resting_players]
    teams = _pair_teams(active)

    for c in range(ss.num_courts):
        if len(teams) < 2:
            ss.current_matches.append(None)
            ss.queues[c] = []
            continue

        first, second = teams[0], teams[1]
        teams = teams[2:]

        # หลีกเลี่ยงซ้ำจาก last_matches
        if ss.last_matches.get(c):
            last_left, last_right = ss.last_matches[c]
            if {tuple(first), tuple(second)} == {tuple(last_left), tuple(last_right)}:
                if len(teams) >= 2:
                    random.shuffle(teams)
                    first, second = teams[0], teams[1]
                    teams = teams[2:]

        ss.current_matches.append((first, second))
        ss.queues[c] = teams[:]
        teams = []

        ss.winner_streaks[c] = {"team": None, "count": 0, "first_loser": None}

def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1

def _fmt_team(team: List[str]) -> str:
    return " & ".join(team)

def process_result(winner_side: str, court_idx: int):
    if not ss.current_matches or not ss.current_matches[court_idx]:
        return

    left, right = ss.current_matches[court_idx]
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    ss.history.append(
        f"🏟️ คอร์ท {court_idx+1}: {_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌"
    )
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # streak
    if ss.winner_streaks[court_idx]["team"] == winner:
        ss.winner_streaks[court_idx]["count"] += 1
    else:
        ss.winner_streaks[court_idx] = {"team": winner, "count": 1, "first_loser": loser}

    # ชนะ 2 ติด → ต้องออก
    if ss.winner_streaks[court_idx]["count"] >= 2:
        first_loser = ss.winner_streaks[court_idx]["first_loser"]
        if ss.queues[court_idx]:
            incoming = ss.queues[court_idx].pop(0)
            ss.current_matches[court_idx] = (first_loser, incoming)
            ss.winner_streaks[court_idx] = {"team": None, "count": 0, "first_loser": None}
        else:
            start_new_round()
    else:
        if ss.queues[court_idx]:
            incoming = ss.queues[court_idx].pop(0)
            ss.current_matches[court_idx] = (winner, incoming)
        else:
            start_new_round()

    ss.last_matches[court_idx] = ss.current_matches[court_idx]

# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Scheduler (Multi-Court)")

names_input = st.text_area("👥 ใส่รายชื่อผู้เล่น (ขึ้นบรรทัดใหม่)", "", height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

c1, c2, c3 = st.columns(3)
with c1:
    ss.num_courts = st.selectbox("🏟️ จำนวนคอร์ท", [1, 2, 3], index=0)

with c2:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < ss.num_courts * 4:
            st.error(f"ต้องมีอย่างน้อย {ss.num_courts*4} คน")
        else:
            ss.players = players
            init_stats(players)
            start_new_round()
            st.success("เริ่มเกมใหม่แล้ว!")
            force_rerun()

with c3:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        st.success("ล้างสถานะแล้ว")
        force_rerun()

# -----------------------------
# Matches per Court (Grid)
# -----------------------------
if ss.get("current_matches"):
    cols = st.columns(ss.num_courts)
    selections = {}

    for i, match in enumerate(ss.current_matches):
        with cols[i]:
            if match:
                left, right = match
                st.subheader(f"🏟️ คอร์ท {i+1}")
                st.markdown(f"**ทีมซ้าย:** {_fmt_team(left)} 🆚 **ทีมขวา:** {_fmt_team(right)}")
                winner_choice = st.radio(
                    f"เลือกผู้ชนะ (คอร์ท {i+1})",
                    options=["ยังไม่เลือก", "ทีมซ้าย", "ทีมขวา"],
                    index=0,
                    key=f"winner_court_{i}",
                )
                selections[i] = winner_choice

                if ss.queues.get(i):
                    st.caption("คิวถัดไป:")
                    for j, t in enumerate(ss.queues[i], 1):
                        st.write(f"{j}. {_fmt_team(t)}")
            else:
                st.warning(f"คอร์ท {i+1} ยังไม่พร้อม")

    if st.button("✅ ส่งผลการแข่งขันทั้งหมด"):
        for i, choice in selections.items():
            if choice == "ทีมซ้าย":
                process_result("left", i)
            elif choice == "ทีมขวา":
                process_result("right", i)
        force_rerun()

# -----------------------------
# History & Stats
# -----------------------------
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
