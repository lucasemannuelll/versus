import sys

import service


def _prompt_int(prompt: str) -> int:
    raw = input(prompt).strip()
    try:
        return int(raw)
    except ValueError as e:
        raise service.InvalidSelection("Please enter a valid number") from e


def _print_menu() -> None:
    print("\n=== 1v1 WIN TRACKER ===")
    print("[1] Add Player")
    print("[2] Record Match Result")
    print("[3] View Leaderboard")
    print("[4] Exit")


def _handle_add_player() -> None:
    name = input("\nEnter player name: ").strip()
    try:
        clean = service.add_player(name)
        print(f"-> Successfully added player: {clean}")
    except service.DuplicatePlayer() as e:
        print(f"-> Error: {e}")
    except service.InvalidSelection as e:
        print(f"-> Error: {e}")


def _handle_record_match() -> None:
    players = service.list_players()
    if len(players) < 2:
        print("\n-> Error: You need at least 2 registered players first")
        return

    print("\n--- Registeres Players ---")
    for idx, (_, name) in enumerate(players, 1):
        print(f"[{idx}] {name}")

    try:
        player1_idx = _prompt_int("\nSelect player 1: ") - 1
        player2_idx = _prompt_int("\nSelect player 2: ") - 1
        player1, player2 = service.pick_two_players(players, player1_idx, player2_idx)
    except service.InvalidSelection as e:
        print(f"-> Error: {e}")
        return

    print(f"\nWho won the match between {player1[1]} and {player2[1]}?")
    print(f"[1] {player1[1]}")
    print(f"[2] {player2[1]}")

    try:
        winner_choice = _prompt_int("Select winner (1 or 2): ")
        winner = service.record_match(player1, player2, winner_choice)
    except service.InvalidSelection as e:
        print(f"-> Error: {e}")
        return

    print(f"\nMatch recorded! Winner: {winner[1]}")


def _handle_view_leaderboard() -> None:
    entries = service.get_leaderboard()
    if not entries:
        print("\n-> No match history recorded yet")
        return

    print("\n" + "=" * 50)
    print(f"{'Player':<15} | {'Played':<6} | {'Wins':<5} | {'Losses':<6} | {'Win%':<6}")
    print("-" * 50)
    for e in entries:
        print(
            f"{e['name']:<15} | {e['matches']:<6} | {e['wins']:<5} | "
            f"{e['losses']:<6} | {e['win_rate']:>5.1f}%"
        )
    print("=" * 50)


def main() -> None:
    service.init_storage()
    handlers = {
        "1": _handle_add_player,
        "2": _handle_record_match,
        "3": _handle_view_leaderboard,
    }

    while True:
        _print_menu()
        choice = input("\nSelect option: ").strip()
        if choice == "4":
            print("Exiting...")
            sys.exit(0)
        handler = handlers.get(choice)
        if handler is None:
            print("-> Invalid option. Try again")
            continue
        handler()
