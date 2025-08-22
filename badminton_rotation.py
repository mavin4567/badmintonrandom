import streamlit as st
import random

# -----------------------------
# Session State Initialization
# -----------------------------
if "players" not in st.session_state:
    st.session_state.players = []
if "matches" not in st.session_state:
    st.session_state.matches = []
if "current_match" not in st.session_state:
    st.session_state.current_match = None
if "win_streak" not in st.session_state:
    st.session_state.win_streak = {}
if "games_played" not in st.session_state:
    st.session_state.games_played = {}
if "resting" not in st.session_state:
    st.session_state.resting = None


# -----------------------------
# Utility Functions
# -----------------------------
def reset_game():
    st.session_state.matches = []
    st.session_state.current_match = None
    st.session_state.win_streak = {p: 0 for p in st.session_state.players}
    st.session_state.games_played = {p: 0 for p in st.session_state.players}
    st.session_state.resting = None
    make_new_round()


def make_teams(players):
    random.shuffle(players)
    teams = [players[i:i+2] for i in range(0, len(players), 2)]
    return teams


def make_new_round():
    players = st.session_state.players.copy()

    # ถ้าจำนวนคนเป็นคี่ → ให้พักคนที่เล่นเยอะที่สุด
    if len(players) % 2 == 1:
        most_played = max(st.session_state.games_played, key=st.session_state.games_played.get)
        st.session_state.resting = most_played
        players.remove(most_played)
    else:
        st.session_state.resting = None

    teams = make_teams(players)

    # สร้างแมตช์ใหม่จากทีม
    st.session_state.matches = []
    for i in range(0, len(teams), 2):
        if i+1 < len(teams):
            st.session_state.matches.append((teams[i], teams[i+1]))

    if st.session_state.matches:
        st.session_state.current_match = st.session_state.matches.pop(0)
    else:
        st.session_state.current_match = None


def process_result(winner_side):
    match = st.session_state.current_match
    if not match:
        return

    left, right = match
    winner = left if winner_side == "left" else right
    loser = right if winner_side == "left" else left

    # update games played
    for p in winner + loser:
        st.session_state.games_played[p] += 1

    # update win streak
    for p in winner:
        st.session_state.win_streak[p] += 1
    for p in loser:
        st.session_state.win_streak[p] = 0

    # ถ้าชนะติด 2 ครั้ง → ต้องออก
    if all(st.session_state.win_streak[p] >= 2 for p in winner):
        for p in winner:
            st.session_state.win_streak[p] = 0
        survivor = None
    else:
        survivor = winner

    # คนใหม่เข้ามาแทนที่
    available = [p for p in st.session_state.players if p not in winner + loser]
    if st.session_state.resting:
        available.append(st.session_state.resting)

    if available:
        # เลือกคนเล่นน้อยสุดเข้ามา
        sorted_players = sorted(available, key=lambda x: st.session_state.games_played[x])
        new_players = sorted_players[:len(loser)]
    else:
        new_players = []

    if survivor:
        st.session_state.current_match = (survivor, new_players)
    else:
        if len(new_players) == 4:
            st.session_state.current_match = (new_players[:2], new_players[2:])
        else:
            make_new_round()


# -----------------------------
# UI
# -----------------------------
st.title("🏸 Badminton Match Rotation")

# Input players
if not st.session_state.players:
    st.subheader("ใส่รายชื่อผู้เล่น (สูงสุด 16 คน, กด Enter เพื่อขึ้นบรรทัดใหม่)")
    names_text = st.text_area("รายชื่อผู้เล่น", "")
    if st.button("เริ่มเกม"):
        players = [n.strip() for n in names_text.split("\n") if n.strip()]
        if 2 <= len(players) <= 16:
            st.session_state.players = players
            reset_game()
            st.rerun()
        else:
            st.warning("กรุณาใส่ผู้เล่นระหว่าง 2 ถึง 16 คน")
else:
    # Current Match
    if st.session_state.current_match:
        left, right = st.session_state.current_match
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.subheader("ทีมซ้าย")
            st.write(", ".join(left))
            if st.button("✅ ทีมซ้ายชนะ"):
                process_result("left")
                st.rerun()

        with col2:
            st.subheader("VS")

        with col3:
            st.subheader("ทีมขวา")
            st.write(", ".join(right))
            if st.button("✅ ทีมขวาชนะ"):
                process_result("right")
                st.rerun()

    else:
        st.info("รอบนี้จบแล้ว ✅ เริ่มรอบใหม่...")
        if st.button("เริ่มรอบใหม่"):
            make_new_round()
            st.rerun()

    # Stats
    st.subheader("📊 สถิติผู้เล่น")
    for p in st.session_state.players:
        st.write(f"{p}: เล่น {st.session_state.games_played[p]} ครั้ง | Win Streak: {st.session_state.win_streak[p]}")

    if st.session_state.resting:
        st.info(f"🛑 พัก: {st.session_state.resting}")

    # Controls
    st.subheader("⚙️ การจัดการ")
    if st.button("🔄 Reset เกม"):
        reset_game()
        st.rerun()
    if st.button("🔃 Refresh"):
        st.rerun()
