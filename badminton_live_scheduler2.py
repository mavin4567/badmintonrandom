import streamlit as st
import random

# ฟังก์ชัน reset เกม
def reset_game():
    players = [p.strip() for p in st.session_state.player_input.split("\n") if p.strip()]
    st.session_state.players = players

    # ถ้ามีเลขคี่ ให้ 1 คนพักก่อน
    if len(players) % 2 == 1:
        st.session_state.resting_player = players[-1]
        st.session_state.active_players = players[:-1]
    else:
        st.session_state.resting_player = None
        st.session_state.active_players = players[:]

    shuffled = st.session_state.active_players[:]
    random.shuffle(shuffled)
    st.session_state.teams = [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]
    st.session_state.current_team = st.session_state.teams[0]
    st.session_state.queue = st.session_state.teams[1:]
    st.session_state.streak = {}
    st.session_state.match_no = 1
    st.session_state.history = []
    st.session_state.last_winner = None
    st.session_state.loser_pool = []

# เริ่มต้นค่าใน session_state
if "players" not in st.session_state:
    st.session_state.players = []
    st.session_state.player_input = ""

st.title("🏸 Badminton Live Scheduler")

# ส่วนกรอกชื่อผู้เล่น
st.subheader("ใส่รายชื่อผู้เล่น (สูงสุด 16 คน)")
st.session_state.player_input = st.text_area(
    "กรอกชื่อผู้เล่นทีละบรรทัด:",
    st.session_state.player_input,
    height=200
)

if st.button("✅ เริ่มเกมใหม่"):
    if st.session_state.player_input.strip() == "":
        st.warning("กรุณากรอกชื่อผู้เล่นก่อนเริ่มเกม")
    else:
        reset_game()
        st.success("เริ่มเกมใหม่เรียบร้อยแล้ว!")

# แสดงผลเฉพาะถ้ามีการตั้งค่าผู้เล่นแล้ว
if st.session_state.players:
    st.subheader("รายชื่อผู้เล่น")
    for i, p in enumerate(st.session_state.players, 1):
        if st.session_state.resting_player == p:
            st.write(f"{i}. {p} (พักรอบนี้)")
        else:
            st.write(f"{i}. {p}")

    st.subheader("ทีมที่สุ่มได้")
    for i, t in enumerate(st.session_state.teams, 1):
        st.write(f"ทีม {i}: {t[0]} + {t[1]}")

    # ถ้ามีทีมในคิวและทีมปัจจุบัน
    if st.session_state.queue and st.session_state.current_team:
        challenger = st.session_state.queue[0]
        st.markdown(f"### แมตช์ {st.session_state.match_no}")
        st.write(f"{st.session_state.current_team[0]} + {st.session_state.current_team[1]}  VS  {challenger[0]} + {challenger[1]}")

        col1, col2, col3 = st.columns(3)
        win_choice = None
        if col1.button("ทีมซ้ายชนะ ✅", key=f"left_{st.session_state.match_no}"):
            win_choice = "current"
        if col2.button("ทีมขวาชนะ ✅", key=f"right_{st.session_state.match_no}"):
            win_choice = "challenger"
        if col3.button("➡️ ต่อไป", key=f"next_{st.session_state.match_no}"):
            win_choice = st.session_state.last_winner

        if win_choice:
            if win_choice == "current":
                winner = st.session_state.current_team
                loser = challenger
                st.session_state.loser_pool.append(challenger)
            elif win_choice == "challenger":
                winner = challenger
                loser = st.session_state.current_team
                st.session_state.loser_pool.append(st.session_state.current_team)
                st.session_state.current_team = challenger
            else:
                winner = None
                loser = None

            if winner:
                key = "+".join(winner)
                st.session_state.streak[key] = st.session_state.streak.get(key, 0) + 1
                st.success(f"ผู้ชนะ: {winner[0]} + {winner[1]} (ชนะติดกัน {st.session_state.streak[key]} ครั้ง)")

                # เก็บประวัติการแข่งขัน
                st.session_state.history.append({
                    "แมตช์": st.session_state.match_no,
                    "ทีมชนะ": f"{winner[0]} + {winner[1]}",
                    "ทีมแพ้": f"{loser[0]} + {loser[1]}"
                })

                # บันทึกผู้ชนะล่าสุด
                st.session_state.last_winner = win_choice

                # ถ้าชนะติดกัน 2 ครั้ง → ออกไปพัก และทีมใหม่เจอทีมที่แพ้รอบแรก
                if st.session_state.streak[key] >= 2:
                    st.warning(f"ทีม {winner[0]}+{winner[1]} ชนะ 2 แมตช์ติด ต้องออกไปรอก่อน!")

                    if st.session_state.queue:
                        st.session_state.current_team = st.session_state.queue.pop(0)
                        if st.session_state.loser_pool:
                            st.session_state.queue.insert(0, st.session_state.loser_pool.pop(0))
                    else:
                        st.session_state.current_team = None
                else:
                    st.session_state.queue.pop(0)

                # ไปแมตช์ถัดไป
                st.session_state.match_no += 1

                # ถ้าคิวหมด = ครบรอบ → เวียนผู้เล่นใหม่
                if not st.session_state.queue:
                    # ถ้ามีผู้เล่นพัก → ส่งกลับมา active
                    if st.session_state.resting_player:
                        st.session_state.active_players.append(st.session_state.resting_player)
                        st.session_state.resting_player = None

                    # เลือกผู้เล่นพักใหม่ถ้าเป็นเลขคี่
                    if len(st.session_state.players) % 2 == 1:
                        st.session_state.resting_player = random.choice(st.session_state.active_players)
                        st.session_state.active_players.remove(st.session_state.resting_player)

                    shuffled = st.session_state.active_players[:]
                    random.shuffle(shuffled)
                    st.session_state.teams = [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]
                    st.session_state.current_team = st.session_state.teams[0]
                    st.session_state.queue = st.session_state.teams[1:]

            else:
                st.warning("❗ ต้องเลือกทีมที่ชนะก่อน ถึงจะกดต่อไปได้")

    # โหมดแสดงผลการแข่งขัน (ข้อความ)
    st.subheader("📊 ประวัติผลการแข่งขัน")
    if st.session_state.history:
        for record in st.session_state.history[::-1]:
            st.write(f"แมตช์ {record['แมตช์']}: 🏆 {record['ทีมชนะ']} ชนะ ❌ {record['ทีมแพ้']}")
    else:
        st.info("ยังไม่มีผลการแข่งขัน")
