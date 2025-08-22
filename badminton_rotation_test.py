import streamlit as st
import random
from typing import List, Optional

# ============================================================
# 🏸 Badminton Scheduler (Fair for Winner + Balanced Rotation)
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
    "last_match": None,     # ป้องกันไม่ให้เจอคู่เดิมซ้ำทันที
    "pending_reruns": 0,    # ใช้ขับ rerun ต่อเนื่องหลังจบแมตช์ (แก้ปัญหา refresh มือถือ)
}
for k, v in DEFAULTS.items():
    if k not in ss:
        ss[k] = v

# -----------------------------
# Helper Functions
# -----------------------------
def schedule_soft_refresh(times: int = 2):
    """ตั้งค่าให้ rerun ตัวเองอีก N รอบ (แก้ปัญหา UI ไม่อัปเดตในมือถือ)"""
    ss.pending_reruns = max(ss.pending_reruns, times)
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def tick_soft_refresh():
    """เรียกไว้ท้ายไฟล์ เพื่อลดตัวนับและ rerun ต่อเนื่องจนหมด"""
    if ss.get("pending_reruns", 0) > 0:
        ss.pending_reruns -= 1
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
    """พักจากคนที่เล่นเยอะที่สุด (ถ้าจำนวนคนเป็นคี่)"""
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

    # หลีกเลี่ยงจับคู่ซ้ำกับ last_match (ทันที)
    first, second = teams[0], teams[1]
    if ss.last_match:
        last_left, last_right = ss.last_match
        if {tuple(first), tuple(second)} == {tuple(last_left), tuple(last_right)} and len(teams) > 2:
            random.shuffle(teams)
            first, second = teams[0], teams[1]

    ss.current_match = (first, second)
    ss.queue = teams[2:]
    ss.winner_streak = {"team": None, "count": 0, "first_loser": None}

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

    ss.history.append(f"{_fmt_team(winner)} ✅ ชนะ {_fmt_team(loser)} ❌")
    _update_stats(winner, is_winner=True)
    _update_stats(loser, is_winner=False)

    # จัดการสตรีค
    if ss.winner_streak["team"] == winner:
        ss.winner_streak["count"] += 1
    else:
        ss.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    # กติกา: ชนะ 2 ติด → ทีมชนะต้องออก / ดึงทีมใหม่มาเจอ "ทีมที่แพ้แมตช์แรกในสตรีค"
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

    # 🔄 หลังบันทึกผลแล้ว ตั้งให้ rerun ต่อเนื่องอีก 2 รอบ (ช่วยให้มือถืออัปเดตชัวร์)
    schedule_soft_refresh(times=2)

# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Scheduler ก๊วนลุงๆ🧔🏻")

# รายชื่อผู้เล่น (input)
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
            schedule_soft_refresh(times=1)
with c2:
    if st.button("♻️ Reset"):
        for k in list(ss.keys()):
            del ss[k]
        st.success("ล้างสถานะแล้ว")
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()
with c3:
    if st.button("🔃 Refresh"):
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

# ผู้เล่นที่พัก
if ss.get("resting_player"):
    st.info(f"👤 ผู้เล่นที่พักรอบนี้: **{ss.resting_player}**")

# -----------------------------
# Current Match
# -----------------------------
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
else:
    if ss.get("players"):
        st.warning("ยังไม่มีแมตช์ — กดเริ่มเกมใหม่")

# -----------------------------
# All Players (Always show)
# -----------------------------
st.subheader("👥 ผู้เล่นทั้งหมด")
if ss.get("players"):
    chips = []
    for p in ss.players:
        is_rest = (p == ss.get("resting_player"))
        chips.append(
            f"<span style='display:inline-block;padding:6px 10px;margin:4px;"
            f"border-radius:999px;background:{'#ffe8e8' if is_rest else '#eef3ff'};"
            f"border:1px solid { '#ffb3b3' if is_rest else '#c7d2fe'}; "
            f"font-size:0.9rem;'>{'🛌 ' if is_rest else '🏸 '}{p}</span>"
        )
    st.markdown("<div>" + "".join(chips) + "</div>", unsafe_allow_html=True)
else:
    st.info("ยังไม่ได้เพิ่มรายชื่อผู้เล่น")

# -----------------------------
# Queue (Always show)
# -----------------------------
st.subheader("📋 คิวถัดไป")
if ss.get("queue"):
    for i, team in enumerate(ss.queue, 1):
        st.markdown(
            f"""
            <div style='padding:8px; margin-bottom:6px; border-radius:10px; 
                        background-color:#f7f8fa; border:1px solid #e6e8ef;'>
                <b>#{i}</b> 🎽 {_fmt_team(team)}
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("ยังไม่มีคิวถัดไป ✨")

# -----------------------------
# History
# -----------------------------
if ss.get("history"):
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, line in enumerate(ss.history, 1):
        st.write(f"{i}. {line}")

# -----------------------------
# Stats (hide index)
# -----------------------------
if ss.get("stats"):
    st.subheader("📊 สถิติผู้เล่น")
    import pandas as pd
    ordered = sorted(ss.stats.items(), key=lambda kv: (kv[1]["played"], -kv[1]["win"]))
    df = pd.DataFrame(
        [
            {
                "ลำดับ": i + 1,
                "ผู้เล่น": name,
                "แมตช์": data["played"],
                "ชนะ": data["win"],
                "อัตราชนะ (%)": round((data["win"] / data["played"] * 100) if data["played"] else 0, 1),
            }
            for i, (name, data) in enumerate(ordered)
        ]
    )
    # ซ่อน index ซ้ายสุดไม่ให้เห็นเลข 0,1,2
    st.table(df.style.hide(axis="index"))

# -----------------------------
# Soft refresh driver (run at the end)
# -----------------------------
tick_soft_refresh()
