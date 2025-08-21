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
st.markdown("ระบบจะสุ่มทีมอัตโนมัติและจ
