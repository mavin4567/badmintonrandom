import random

# รายชื่อผู้เล่น
players = ["วิน", "โต๊ด", "ติน", "ต่อ", "มุก", "เฟิร์น", "กันดั้ม", "โก้"]

# ฟังก์ชันสุ่มแบ่งทีม
def make_teams(players):
    shuffled = players[:]
    random.shuffle(shuffled)
    return [shuffled[i:i+2] for i in range(0, len(shuffled), 2)]

# ฟังก์ชันแสดงทีม
def show_teams(teams):
    for i, team in enumerate(teams, 1):
        print(f"ทีม {i}: {team[0]} + {team[1]}")

# ฟังก์ชันจำลองการแข่งแบบสด
def live_schedule(players):
    streak = {}  # เก็บจำนวนครั้งที่ทีมชนะติดกัน
    teams = make_teams(players)
    show_teams(teams)
    print("\nเริ่มแข่ง!")

    current_team = teams[0]
    queue = teams[1:]
    match_no = 1
    rounds_played = 0
    total_rounds = len(players) // 2  # ครบรอบเมื่อทุกทีมได้ลงครบ

    while True:
        if not queue:
            # ครบรอบแล้ว → สุ่มทีมใหม่
            rounds_played += 1
            if rounds_played >= total_rounds:
                print("\n--- ครบรอบแล้ว สุ่มทีมใหม่ทั้งหมด ---")
                streak.clear()
                teams = make_teams(players)
                show_teams(teams)
                current_team = teams[0]
                queue = teams[1:]
                rounds_played = 0

        challenger = queue.pop(0)
        print(f"\nแมตช์ {match_no}: {current_team[0]}+{current_team[1]} VS {challenger[0]}+{challenger[1]}")

        winner = random.choice(["current", "challenger"])  # สุ่มผู้ชนะ
        if winner == "current":
            win_team = current_team
        else:
            win_team = challenger
            current_team = challenger

        win_key = "+".join(win_team)
        streak[win_key] = streak.get(win_key, 0) + 1

        print(f"ผู้ชนะ: {win_team[0]}+{win_team[1]} (ชนะติดกัน {streak[win_key]} ครั้ง)")

        # ถ้าชนะติดกัน 2 ครั้ง ให้ออกไปนั่งรอ แต่ยังไม่สุ่มทีมใหม่จนกว่าจะครบทุกทีม
        if streak[win_key] >= 2:
            print(f"ทีม {win_team[0]}+{win_team[1]} ชนะครบ 2 ครั้ง ต้องออกไปรอก่อน!")
            if queue:
                current_team = queue.pop(0)

        match_no += 1


# เริ่มใช้งาน live schedule
if __name__ == "__main__":
    live_schedule(players)
