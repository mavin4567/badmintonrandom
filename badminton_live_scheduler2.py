import streamlit as st
import random

# รายชื่อผู้เล่น
players = ["วิน", "โต๊ด", "ติน", "ต่อ", "มุก", "เฟิร์น", "กันดั้ม", "โก้"]

# ฟังก์ชันสุ่มทีม
def make_teams(players):
    shuffled = players[:]
    random.shuffle(shuffled)
    return [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]

# ฟังก์ชัน reset เกม
def reset_game():
    shuffled = players[:]
    random.shuffle(shuffled)
    st.session_state.teams = [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]
    st.session_state.current_team = st.session_state.teams[0]
    st.session_state.queue = st.session_state.teams[1:]
    st.session_state.streak = {}
    st.session_state.match_no = 1
    st.session_state.rounds_played = 0
    st.session_state.total_rounds = len(players)//2
    st.session_state.history = []  # เก็บประวัติผลการแข่งขัน

# เริ่มต้นค่าใน session_state
if "teams" not in st.session_state:
    reset_game()

st.title("🏸 Badminton Live Scheduler")

# ปุ่ม Reset เกม
if st.button("🔄 Reset เกมใหม่"):
    reset_game()
    st.success("เกมถูกรีเซ็ตและสุ่มทีมใหม่เรียบร้อยแล้ว!")

# แสดงทีมทั้งหมด
st.subheader("ทีมที่สุ่มได้")
for i, t in enumerate(st.session_state.teams, 1):
    st.write(f"ทีม {i}: {t[0]} + {t[1]}")

# ถ้ามีทีมในคิว
if st.session_state.queue:
    challenger = st.session_state.queue[0]
    st.markdown(f"### แมตช์ {st.session_state.match_no}")
    st.write(f"{st.session_state.current_team[0]} + {st.session_state.current_team[1]}  VS  {challenger[0]} + {challenger[1]}")

    col1, col2 = st.columns(2)
    win_choice = None
    if col1.button("ทีมซ้ายชนะ ✅", key=f"left_{st.session_state.match_no}"):
        win_choice = "current"
    if col2.button("ทีมขวาชนะ ✅", key=f"right_{st.session_state.match_no}"):
        win_choice = "challenger"

    if win_choice:
        if win_choice == "current":
            winner = st.session_state.current_team
            loser = challenger
        else:
            winner = challenger
            loser = st.session_state.current_team
            st.session_state.current_team = challenger

        key = "+".join(winner)
        st.session_state.streak[key] = st.session_state.streak.get(key, 0) + 1
        st.success(f"ผู้ชนะ: {winner[0]} + {winner[1]} (ชนะติดกัน {st.session_state.streak[key]} ครั้ง)")

        # เก็บประวัติการแข่งขัน
        st.session_state.history.append({
            "แมตช์": st.session_state.match_no,
            "ทีมชนะ": f"{winner[0]} + {winner[1]}",
            "ทีมแพ้": f"{loser[0]} + {loser[1]}"
        })

        # ถ้าชนะติดกัน 2 ครั้ง → ออกไปพัก
        if st.session_state.streak[key] >= 2:
            st.warning(f"ทีม {winner[0]}+{winner[1]} ชนะ 2 แมตช์ติด ต้องออกไปรอก่อน!")
            st.session_state.queue.pop(0)  # เอาทีม challenger ออก
            if st.session_state.queue:
                st.session_state.current_team = st.session_state.queue.pop(0)
        else:
            # แมตช์ปกติ → challenger เล่นไปแล้ว เอาออกจากคิว
            st.session_state.queue.pop(0)

        # ไปแมตช์ถัดไป
        st.session_state.match_no += 1

        # ถ้าคิวหมด = ครบรอบ
        if not st.session_state.queue:
            st.session_state.rounds_played += 1
            if st.session_state.rounds_played >= st.session_state.total_rounds:
                st.info("🎲 ครบรอบแล้ว! สุ่มทีมใหม่ทั้งหมด")
                reset_game()

# แสดงประวัติการแข่งขันย้อนหลัง
if st.session_state.history:
    st.subheader("📜 ประวัติผลการแข่งขัน")
    for record in st.session_state.history[::-1]:
        st.write(f"แมตช์ {record['แมตช์']}: 🏆 {record['ทีมชนะ']} ชนะ ❌ {record['ทีมแพ้']}")
