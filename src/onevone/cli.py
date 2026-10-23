import sys
import shutil
import subprocess

from . import service


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


def _pick_with_fzf(
    players: list[tuple[int, str]],
) -> tuple[tuple[int, str], tuple[int, str]] | None:
    if shutil.which("fzf") is None:
        raise service.InvalidSelection("fzf is not installed")

    names = "\n".join(name for _, name in players)
    result = subprocess.run(
        [
            "fzf",
            "--multi",
            "--prompt",
            "Select 2 players>",
            "--height",
            "40%",
            "--reverse",
            "--bind",
            "enter:accept",
        ],
        input=names,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    selected_names = [line for line in result.stdout.splitlines() if line.strip()]

    if len(selected_names) != 2:
        raise service.InvalidSelection("Select exactly 2 players")

    selected = [next(p for p in players if p[1] == name) for name in selected_names]

    return selected[0], selected[1]


def _handle_record_match() -> None:
    players = service.list_players()
    if len(players) < 2:
        print("\n-> Error: You need at least 2 registered players first")
        return

    try:
        picked = _pick_with_fzf(players)
        if picked is None:
            print("-> Canceled")
            return
        player1, player2 = picked
    except service.InvalidSelection as e:
        print(f"-> Error: {e}")

    try:
        winner_choice = _prompt_int(
            f"\nWho won?\n[1]. {player1[1]}\n[2]. {player2[1]}\nSelect (1 or 2): "
        )
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
