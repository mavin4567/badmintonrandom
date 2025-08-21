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
if "round_played" not in st.session_state:
    st.session_state.round_played = set()

# -----------------------------
# Helper Functions
# -----------------------------
def make_teams(players):
    random.shuffle(players)
    teams = [players[i:i+2] for i in range(0, len(players), 2)]
    return teams

def start_new_round():
    st.session_state.teams = make_teams(st.session_state.players)
    st.session_state.round_played = set()
    st.session_state.current_match = (st.session_state.teams[0], st.session_state.teams[1])
    st.session_state.winner_streak = {"team": None, "count": 0}

def process_result(winner_side):
    team_left, team_right = st.session_state.current_match
    winner = team_left if winner_side == "left" else team_right
    loser = team_right if winner_side == "left" else team_left

    # บันทึกประวัติ
    st.session_state.history.append(f"{winner} ชนะ {loser}")

    # อัปเดต streak
    if st.session_state.winner_streak["team"] == winner:
        st.session_state.winner_streak["count"] += 1
    else:
        st.session_state.winner_streak = {"team": winner, "count": 1}

    # ตรวจ streak ชนะ 2 ครั้งติด
    if st.session_state.winner_streak["count"] == 2:
        # เอาทีมที่แพ้รอบแรกกลับมาเจอ
        st.session_state.current_match = (loser, random.choice(st.session_state.teams))
        st.session_state.winner_streak = {"team": None, "count": 0}
    else:
        # หาทีมใหม่มาเจอ
        next_team = random.choice(st.session_state.teams)
        st.session_state.current_match = (winner, next_team)

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

if st.button("เริ่มเกมใหม่"):
    if len(players) < 4:
        st.error("ต้องมีอย่างน้อย 4 คนขึ้นไป")
    else:
        st.session_state.players = players
        start_new_round()
        st.success("เริ่มเกมใหม่เรียบร้อย!")

# แสดงแมตช์ปัจจุบัน
if st.session_state.current_match:
    team_left, team_right = st.session_state.current_match
    st.subheader("แมตช์ปัจจุบัน")
    st.write(f"🏆 ทีมซ้าย: {team_left}  VS  ทีมขวา: {team_right}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ ทีมซ้ายชนะ"):
            process_result("left")
    with col2:
        if st.button("✅ ทีมขวาชนะ"):
            process_result("right")

# ประวัติย้อนหลัง
st.subheader("📜 ประวัติการแข่งขัน")
for i, match in enumerate(st.session_state.history, 1):
    st.write(f"{i}. {match}")
