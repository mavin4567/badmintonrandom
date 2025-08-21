import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Scheduler (Dynamic Multi-court + Grid Queue)
# ============================================================

ss = st.session_state
DEFAULTS = {
    "players": [],
    "current_matches": [],
    "queues": {},  # คิว per court {0: [...], 1: [...]} 
    "winner_streaks": {},
    "history": [],
    "stats": {},
    "resting_player": None,
    "last_matches": [],
    "num_courts": 2,
}
for k, v in DEFAULTS.items():
    if k not in ss:
        ss[k] = v


def force_rerun():
    try:
        st.rerun()
    except:
        st.experimental_rerun()


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
    return [sorted(shuffled[i : i + 2]) for i in range(0, len(shuffled), 2)]


def start_new_round():
    players = ss.players[:]
    if len(players) < 4:
        ss.current_matches = []
        ss.queues = {}
        return

    ss.resting_player = _choose_resting_player(players)
    active = [p for p in players if p != ss.resting_player]

    teams = _pair_teams(active)
    matches = []
    queues = {i: [] for i in range(ss.num_courts)}

    for i in range(ss.num_courts):
        if len(teams) >= 2:
            left, right = teams[0], teams[1]
            teams = teams[2:]
            if i < len(ss.last_matches):
                last_left, last_right = ss.last_matches[i]
                if {tuple(left), tuple(right)} == {tuple(last_left), tuple(last_right)}:
                    if teams:
                        random.shuffle(teams)
                        left, right = teams[0], teams[1]
                        teams = teams[2:]
            matches.append((left, right))
            ss.winner_streaks[i] = {"team": None, "count": 0, "first_loser": None}

    # แจกทีมที่เหลือเข้า queue ของแต่ละคอร์ทแบบวนรอบ
    for idx, team in enumerate(teams):
        queues[idx % ss.num_courts].append(team)

    ss.current_matches = matches
    ss.queues = queues
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

    ss.history.append(
        f"คอร์ท {court_index+1}: {_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌"
    )
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    streak = ss.winner_streaks.get(
        court_index, {"team": None, "count": 0, "first_loser": None}
    )
    if streak["team"] == winner:
        streak["count"] += 1
    else:
        streak = {"team": winner, "count": 1, "first_loser": loser}
    ss.winner_streaks[court_index] = streak

    if streak["count"] >= 2:  # ทีมชนะ 2 ครั้งติด
        first_loser = streak["first_loser"]
        if ss.queues.get(court_index):
            incoming = ss.queues[court_index].pop(0)
            ss.current_matches[court_index] = (first_loser, incoming)
            ss.winner_streaks[court_index] = {
                "team": None,
                "count": 0,
                "first_loser": None,
            }
        else:
            start_new_round()
    else:
        if ss.queues.get(court_index):
            incoming = ss.queues[court_index].pop(0)
            ss.current_matches[court_index] = (winner, incoming)
        else:
            start_new_round()

    if court_index < len(ss.current_matches):
        ss.last_matches[court_index] = ss.current_matches[court_index]
    force_rerun()


def adjust_courts():
    """ปรับจำนวนคอร์ทแบบ dynamic"""
    current = len(ss.current_matches)
    if ss.num_courts > current:  # เพิ่มคอร์ท
        for _ in range(ss.num_courts - current):
            if sum(len(v) for v in ss.queues.values()) >= 2:
                # ดึงจาก queue รวม
                all_queue = []
                for q in ss.queues.values():
                    all_queue.extend(q)
                if len(all_queue) >= 2:
                    left, right = all_queue.pop(0), all_queue.pop(0)
                    ss.current_matches.append((left, right))
                    ss.queues[len(ss.current_matches) - 1] = []
                    ss.winner_streaks[len(ss.current_matches) - 1] = {
                        "team": None,
                        "count": 0,
                        "first_loser": None,
                    }
    elif ss.num_courts < current:  # ลดคอร์ท
        while len(ss.current_matches) > ss.num_courts:
            left, right = ss.current_matches.pop()
            ss.queues.setdefault(0, []).insert(0, left)
            ss.queues[0].insert(0, right)
            ss.winner_streaks.pop(len(ss.current_matches), None)


# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Scheduler (Dynamic Courts + Grid Queue)")

names_input = st.text_area("👥 ใส่รายชื่อผู้เล่น (ขึ้นบรรทัดใหม่)", "", height=180)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

ss.num_courts = st.slider("🏟 จำนวนคอร์ท (เปลี่ยนได้ตลอด)", 1, 4, ss.num_courts)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คน")
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

adjust_courts()

if ss.get("current_matches"):
    cols = st.columns(ss.num_courts)
    for i, (left, right) in enumerate(ss.current_matches):
        with cols[i]:
            st.subheader(f"🎯 คอร์ท {i+1}")
            st.markdown(
                f"**ทีมซ้าย:** {_fmt_team(left)} 🆚 **ทีมขวา:** {_fmt_team(right)}"
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"✅ ทีมซ้ายชนะ (คอร์ท {i+1})"):
                    process_result("left", i)
            with c2:
                if st.button(f"✅ ทีมขวาชนะ (คอร์ท {i+1})"):
                    process_result("right", i)

            if ss.queues.get(i):
                st.caption("คิวถัดไป:")
                for j, t in enumerate(ss.queues[i], 1):
                    st.write(f"{j}. {_fmt_team(t)}")

if ss.get("history"):
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, line in enumerate(ss.history, 1):
        st.write(f"{i}. {line}")

if ss.get("stats"):
    st.subheader("📊 สถิติผู้เล่น")
    ordered = sorted(
        ss.stats.items(), key=lambda kv: (kv[1]["played"], -kv[1]["win"])
    )
    st.table(
        [
            {
                "ผู้เล่น": name,
                "แมตช์": data["played"],
                "ชนะ": data["win"],
                "อัตราชนะ (%)": round(
                    (data["win"] / data["played"] * 100) if data["played"] else 0, 1
                ),
            }
            for name, data in ordered
        ]
    )
