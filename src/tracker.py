import sqlite3
import sys

DB_NAME = "tracker_1v1.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches_1v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            p1_id INTEGER,
            p2_id INTEGER,
            winner_id INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(p1_id) REFERENCES players(id),
            FOREIGN KEY(p2_id) REFERENCES players(id),
            FOREIGN KEY(winner_id) REFERENCES players(id)
        )
    """)
    conn.commit()
    conn.close()


def get_players():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM players ORDER BY name")
    players = cursor.fetchall()
    conn.close()
    return players


def add_player():
    name = input("\nEnter player name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        print(f"-> Successfully added player: {name}")
    except sqlite3.IntegrityError:
        print("-> Error: Player already exists.")


def record_match():
    players = get_players()
    if len(players) < 2:
        print("\n-> Error: You need at least 2 registered players first.")
        return

    print("\n--- Registered Players ---")
    for idx, (pid, name) in enumerate(players, 1):
        print(f"[{idx}] {name}")

    try:
        p1_idx = int(input("\nSelect Player 1 (number): ")) - 1
        p2_idx = int(input("Select Player 2 (number): ")) - 1

        if p1_idx == p2_idx or not (
            0 <= p1_idx < len(players) and 0 <= p2_idx < len(players)
        ):
            print("-> Error: Invalid selection or same player selected.")
            return

        p1_id, p1_name = players[p1_idx]
        p2_id, p2_name = players[p2_idx]

        print(f"\nWho won the match between {p1_name} and {p2_name}?")
        print(f"[1] {p1_name}")
        print(f"[2] {p2_name}")

        winner_choice = input("Select winner (1 or 2): ").strip()

        if winner_choice == "1":
            winner_id = p1_id
            winner_name = p1_name
        elif winner_choice == "2":
            winner_id = p2_id
            winner_name = p2_name
        else:
            print("-> Error: Invalid selection. Match not recorded.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO matches_1v1 (p1_id, p2_id, winner_id)
            VALUES (?, ?, ?)
        """,
            (p1_id, p2_id, winner_id),
        )
        conn.commit()
        conn.close()

        print(f"\n-> Match recorded! Winner: {winner_name}")

    except ValueError:
        print("-> Error: Please enter valid numbers.")


def view_leaderboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT 
            p.name,
            COUNT(m.id) AS total_matches,
            SUM(CASE WHEN m.winner_id = p.id THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN m.winner_id != p.id AND m.winner_id IS NOT NULL THEN 1 ELSE 0 END) AS losses
        FROM players p
        LEFT JOIN matches_1v1 m ON p.id = m.p1_id OR p.id = m.p2_id
        GROUP BY p.id
        ORDER BY wins DESC, total_matches DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    if not data:
        print("\n-> No match history recorded yet.")
        return

    print("\n" + "=" * 50)
    print(f"{'Player':<15} | {'Played':<6} | {'Wins':<5} | {'Losses':<6} | {'Win%':<6}")
    print("-" * 50)

    for row in data:
        name, matches, wins, losses = row
        matches = matches or 0
        wins = wins or 0
        losses = losses or 0

        win_rate = (wins / matches * 100) if matches > 0 else 0.0

        print(
            f"{name:<15} | {matches:<6} | {wins:<5} | {losses:<6} | {win_rate:>5.1f}%"
        )
    print("=" * 50)


def main():
    init_db()
    while True:
        print("\n=== 1v1 WIN/LOSS TRACKER ===")
        print("[1] Add Player")
        print("[2] Record Match Result")
        print("[3] View Leaderboard")
        print("[4] Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            add_player()
        elif choice == "2":
            record_match()
        elif choice == "3":
            view_leaderboard()
        elif choice == "4":
            print("Exiting...")
            sys.exit(0)
        else:
            print("-> Invalid option. Try again.")


if __name__ == "__main__":
    main()
