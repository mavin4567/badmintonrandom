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
    st.session_state.winner_streak = {"team": None, "count": 0, "first_loser": None}
if "history" not in st.session_state:
    st.session_state.history = []
if "queue" not in st.session_state:
    st.session_state.queue = []
if "stats" not in st.session_state:
    st.session_state.stats = {}

# -----------------------------
# Helper Functions
# -----------------------------
def init_stats(players):
    st.session_state.stats = {p: {"played": 0, "win": 0} for p in players}

def make_teams(players):
    """สุ่มผู้เล่นแล้วแบ่งเป็นทีม (ถ้าเลขคี่ ให้สุ่มคนหนึ่งนั่งพัก)"""
    players = players[:]
    random.shuffle(players)
    if len(players) % 2 == 1:
        rest = players.pop()   # คนสุดท้ายพัก
        st.info(f"👤 {rest} พักรอบนี้")
    teams = [players[i:i+2] for i in range(0, len(players), 2)]
    return teams

def start_new_round():
    teams = make_teams(st.session_state.players)
    st.session_state.teams = teams
    st.session_state.queue = teams[2:] if len(teams) > 2 else []
    if len(teams) >= 2:
        st.session_state.current_match = (teams[0], teams[1])
    else:
        st.session_state.current_match = None
    st.session_state.winner_streak = {"team": None, "count": 0, "first_loser": None}
    st.session_state.history = []

def update_stats(players, winner=False):
    for p in players:
        st.session_state.stats[p]["played"] += 1
        if winner:
            st.session_state.stats[p]["win"] += 1

def process_result(winner_side):
    team_left, team_right = st.session_state.current_match
    winner = team_left if winner_side == "left" else team_right
    loser = team_right if winner_side == "left" else team_left

    # บันทึกผลการแข่งขัน
    st.session_state.history.append(
        f"{' & '.join(winner)} ✅ ชนะ {' & '.join(loser)} ❌"
    )

    # อัปเดตสถิติ
    update_stats(winner, winner=True)
    update_stats(loser, winner=False)

    # อัปเดต streak
    if st.session_state.winner_streak["team"] == winner:
        st.session_state.winner_streak["count"] += 1
    else:
        st.session_state.winner_streak = {"team": winner, "count": 1, "first_loser": loser}

    # ถ้าชนะ 2 ครั้งติด
    if st.session_state.winner_streak["count"] == 2:
        if st.session_state.queue:
            next_team = st.session_state.queue.pop(0)
            st.session_state.current_match = (
                st.session_state.winner_streak["first_loser"],
                next_team,
            )
        else:
            start_new_round()
    else:
        if st.session_state.queue:
            next_team = st.session_state.queue.pop(0)
            st.session_state.current_match = (winner, next_team)
        else:
            start_new_round()

    # 🔄 Refresh อัตโนมัติ
    st.rerun()

# -----------------------------
# UI
# -----------------------------
st.title("🏸 ระบบจัดตารางการแข่งขันแบดมินตัน")

# ใส่รายชื่อผู้เล่น
st.subheader("ใส่รายชื่อผู้เล่น (สูงสุด 16 คน)")
names_input = st.text_area(
    "พิมพ์รายชื่อ (ขึ้นบรรทัดใหม่สำหรับแต่ละคน)", 
    "วิน\nโต๊ด\nติน\nต่อ\nมุก\nเฟิร์น\nกันดั้ม\nโก้"
)
players = [n.strip() for n in names_input.split("\n") if n.strip()]

col_start, col_reset = st.columns(2)
with col_start:
    if st.button("▶️ เริ่มเกมใหม่"):
        if len(players) < 4:
            st.error("ต้องมีอย่างน้อย 4 คนขึ้นไป")
        else:
            st.session_state.players = players
            init_stats(players)
            start_new_round()
            st.success("เริ่มเกมใหม่เรียบร้อย!")

with col_reset:
    if st.button("🔄 รีเซ็ตทั้งหมด"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# แสดงแมตช์ปัจจุบัน
if st.session_state.current_match:
    team_left, team_right = st.sessi
