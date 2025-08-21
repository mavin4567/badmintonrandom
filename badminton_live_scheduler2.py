import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Scheduler (Multi-court)
# ============================================================

ss = st.session_state
DEFAULTS = {
    "players": [],
    "current_matches": [],   # <-- รองรับหลายคอร์ท
    "queue": [],
    "winner_streaks": {},    # {court_index: {"team": ..., "count": ..., "first_loser": ...}}
    "history": [],
    "stats": {},
    "resting_player": None,
    "last_matches": [],      # กันซ้ำทีละคอร์ท
    "num_courts": 2,         # 🔑 จำนวนคอร์ท
}
for k, v in DEFAULTS.items():
    if k not in ss:
        ss[k] = v

def force_rerun():
    try: st.rerun()
    except: st.experimental_rerun()

def init_stats(players: List[str]):
    ss.stats = {p: {"played": 0, "win": 0} for p in players}

def _choose_resting_player(players: List[str]) -> Optional[str]:
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
        ss.current_matches = []
        ss.queue = []
        return

    ss.resting_player = _choose_resting_player(players)
    active = [p for p in players if p != ss.resting_player]

    teams = _pair_teams(active)
    matches = []
    queue = []

    # จัดให้ไม่เกินจำนวนคอร์ท
    for i in range(ss.num_courts):
        if len(teams) >= 2:
            left, right = teams[0], teams[1]
            teams = teams[2:]
            # หลีกเลี่ยงซ้ำกับ last match
            if i < len(ss.last_matches):
                last_left, last_right = ss.last_matches[i]
                if {tuple(left), tuple(right)} == {tuple(last_left), tuple(last_right)}:
                    if teams:
                        random.shuffle(teams)
                        left, right = teams[0], teams[1]
                        teams = teams[2:]
            matches.append((left, right))
            ss.winner_streaks[i] = {"team": None, "count": 0, "first_loser": None}

    queue.extend(teams)
    ss.current_matches = matches
    ss.queue = queue
    ss.last_matches = matches[:]

def _update_stats(team: List[str], *, is_winner: bool):
    for p in team:
        ss.stats[p]["played"] += 1
        if is_winner:
            ss.stats[p]["win"] += 1

def _fmt_team(team: List[str]) -> str:
    return " & ".join(team)

def process_result(winner_side: str, court_index: int):
    if court_index >= len(ss.current_matches):
        return

    left, right = ss.current_matches[court_index]
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    ss.history.append(f"คอร์ท {court_index+1}: {_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    streak = ss.winner_streaks.get(court_index, {"team": None, "count": 0, "first_loser": None})
    if streak["team"] == winner:
        streak["count"] += 1
    else:
        streak = {"team": winner, "count": 1, "first_loser": loser}
    ss.winner_streaks[court_index] = streak

    # Case: ชนะ 2 ติด → ต้องออก
    if streak["count"] >= 2:
        first_loser = streak["first_loser"]
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_matches[court_index] = (first_loser, incoming)
            ss.winner_streaks[court_index] = {"team": None, "count": 0, "first_loser": None}
        else:
            start_new_round()
    else:
        # ทีมชนะอยู่ต่อ + หาคู่ใหม่
        if ss.queue:
            incoming = ss.queue.pop(0)
            ss.current_matches[court_index] = (winner, incoming)
        else:
            start_new_round()

    ss.last_matches[court_index] = ss.current_matches[court_index]
    force_rerun()

# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Scheduler (หลายคอร์ท)")

names_input = st.text_area("👥 ใส่รายชื่อผู้เล่น (ขึ้นบรรทัดใหม่)", "", height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

ss.num_courts = st.number_input("🏟 จำนวนคอร์ท", min_value=1, max_value=4, value=ss.num_courts)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คน")
        elif len(players) > 32:
            st.error("สูงสุด 32 คน")
        else:
            ss.players = players
            init_stats(players)
            start_new_round()
            st.success("เริ่มเกมใหม่แล้ว!")
            force_rerun()
with c2:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        st.success("ล้างสถานะแล้ว")
        force_rerun()
with c3:
    if st.button("🔃 Refresh"):
        force_rerun()

if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พักรอบนี้: **{ss.resting_player}**")

if ss.get("current_matches"):
    for i, (left, right) in enumerate(ss.current_matches, 1):
        st.subheader(f"🎯 คอร์ท {i}")
        st.markdown(f"**ทีมซ้าย:** {_fmt_team(left)} 🆚 **ทีมขวา:** {_fmt_team(right)}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"✅ ทีมซ้ายชนะ (คอร์ท {i})"):
                process_result("left", i-1)
        with c2:
            if st.button(f"✅ ทีมขวาชนะ (คอร์ท {i})"):
                process_result("right", i-1)
else:
    if ss.get("players"):
        st.warning("ยังไม่มีแมตช์ — กดเริ่มเกมใหม่")

if ss.get("queue"):
    st.caption("คิวถัดไป:")
    for i, t in enumerate(ss.queue, 1):
        st.write(f"• {_fmt_team(t)}")

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
