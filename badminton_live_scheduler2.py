import streamlit as st
import random

# -----------------------------
# Session State Initialization
# -----------------------------
if "players" not in st.session_state:
    st.session_state.players = []
if "teams" not in st.session_state:
    st.session_state.teams = []
if "current_match" not in st.session_state:
    st.session_state.current_match = None
if "winner_streak" not in st.session_state:
    st.session_state.winner_streak = {"team": None, "count": 0}
if "history" not in st.session_state:
    st.session_state.history = []
if "queue" not in st.session_state:
    st.session_state.queue = []   # ทีมที่รอคิวลงแข่ง
if "stats" not in st.session_state:
    st.session_state.stats = {}   # เก็บสถิติ {player: {"played":0, "win":0}}

# -----------------------------
# Helper Functions
# -----------------------------
def init_stats(players):
    st.session_state.stats = {p: {"played": 0, "win": 0} for p in players}

def make_teams(players):
    """สุ่มผู้เล่นแล้วแบ่งเป็นทีม"""
    random.shuffle(players)
    teams = [players[i:i+2] for i in range(0, len(players), 2)]
    return teams

def start_new_round():
    """เริ่มรอบใหม่: สุ่มทีมทั้งหมดแล้วจัดเข้าคิว"""
    teams = make_teams(st.session_state.players)
    st.session_state.teams = teams
    st.session_state.queue = teams[2:] if len(teams) > 2 else []
    if len(teams) >= 2:
        st.session_state.current_match = (teams[0], teams[1])
    else:
        st.session_state.current_match = None
    st.session_state.winner_streak = {"team": None, "count": 0}
    st.session_state.history = []

def update_stats(players, winner=False):
    """อัปเดตสถิติของผู้เล่น"""
    for p in players:
        st.session_state.stats[p]["played"] += 1
        if winner:
            st.session_state.stats[p]["win"] += 1

def process_result(winner_side):
    """บันทึกผลการแข่งขันและจัดคู่ใหม่"""
    team_left, team_right = st.session_state.current_match
    winner = team_left if winner_side == "left" else team_right
    loser = team_right if winner_side == "left" else team_left

    # บันทึกผล
    st.session_state.history.append(f"{' & '.join(winner)} ✅ ชนะ {' & '.join(loser)} ❌")

    # อัปเดตสถิติ
    update_stats(winner, winner=True)
    update_stats(loser, winner=False)

    # อัปเดต streak
    if st.session_state.winner_streak["team"] == winner:
        st.session_state.winner_streak["count"] += 1
    else:
        st.session_state.winner_streak = {"team": winner, "count": 1}

    # ถ้าชนะ 2 ครั้งติด -> ให้ออก
    if st.session_state.winner_streak["count"] == 2:
        if st.session_state.queue:
            next_team = st.session_state.queue.pop(0)
            st.session_state.current_match = (loser, next_team)
        else:
            start_new_round()
    else:
        # ทีมชนะอยู่ต่อ -> เจอทีมใหม่จากคิว
        if st.session_state.queue:
            next_team = st.session_state.queue.pop(0)
            st.session_state.current_match = (winner, next_team)
        else:
            start_new_round()

# -----------------------------
# UI
# -----------------------------
st.title("🏸 ระบบจัดตารางการแข่งขันแบดมินตัน")
st.markdown("ระบบจะสุ่มทีมอัตโนมัติและจัดคิวการเล่น เพื่อให้ทุกคนได้เล่นครบถ้วน")

# ใส่รายชื่อผู้เล่น
st.subheader("👥 ใส่รายชื่อผู้เล่น (สูงสุด 16 คน)")
names_input = st.text_area(
    "พิมพ์รายชื่อ (ขึ้นบรรทัดใหม่สำหรับแต่ละคน)", 
)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

col_start, col_reset, col_refresh = st.columns(3)
with col_start:
    if st.button("🚀 เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("❌ ต้องมีอย่างน้อย 4 คนขึ้นไป")
        else:
            st.session_state.players = players
            init_stats(players)
            start_new_round()
            st.success("✅ เริ่มเกมใหม่เรียบร้อย!")
with col_reset:
    if st.button("🔄 Reset เกม"):
        st.session_state.players = []
        st.session_state.teams = []
        st.session_state.current_match = None
        st.session_state.winner_streak = {"team": None, "count": 0}
        st.session_state.history = []
        st.session_state.queue = []
        st.session_state.stats = {}
        st.success("♻️ ล้างข้อมูลเรียบร้อย")
with col_refresh:
    if st.button("🔃 Refresh สถานะ"):
        st.experimental_rerun()

# แสดงแมตช์ปัจจุบัน
if st.session_state.current_match:
    team_left, team_right = st.session_state.current_match
    st.subheader("🎯 แมตช์ปัจจุบัน")
    st.markdown(f"**ทีมซ้าย:** {' & '.join(team_left)}  🆚  **ทีมขวา:** {' & '.join(team_right)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ ทีมซ้ายชนะ"):
            process_result("left")
            st.experimental_rerun()
    with col2:
        if st.button("✅ ทีมขวาชนะ"):
            process_result("right")
            st.experimental_rerun()

# ประวัติย้อนหลัง
if st.session_state.history:
    st.subheader("📜 ประวัติการแข่งขัน")
    for i, match in enumerate(st.session_state.history, 1):
        st.write(f"{i}. {match}")

# ตารางสถิติ
if st.session_state.stats:
    st.subheader("📊 สถิติผู้เล่น")
    stats_table = [
        {
            "ผู้เล่น": p,
            "จำนวนแมตช์": st.session_state.stats[p]["played"],
            "ชนะ": st.session_state.stats[p]["win"],
            "อัตราชนะ (%)": round(
                (st.session_state.stats[p]["win"] / st.session_state.stats[p]["played"] * 100)
                if st.session_state.stats[p]["played"] > 0 else 0,
                1
            )
        }
        for p in st.session_state.stats
    ]
    st.table(stats_table)
