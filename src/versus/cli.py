import shutil
import subprocess
import sys

from . import service


def _prompt_int(prompt: str) -> int:
    raw = input(prompt).strip()
    try:
        return int(raw)
    except ValueError as e:
        raise service.InvalidSelection("Please enter a valid number") from e


def _print_menu() -> None:
    print("\n=== VERSUS ===")
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


def _run_fzf(players: list[tuple[int, str]], prompt: str, count: int):
    if shutil.which("fzf") is None:
        raise service.InvalidSelection("fzf is not installed")

    names = "\n".join(name for _, name in players)
    result = subprocess.run(
        [
            "fzf",
            "--multi",
            "--prompt",
            prompt,
            "--height",
            "40%",
            "--reverse",
            "--bind",
            "enter:accept",
        ],
        input=names,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    selected_names = [
        line for line in result.stdout.splitlines() if line.strip()
    ]
    if len(selected_names) != count:
        raise service.InvalidSelection(f"Select exactly {count} players")

    by_name = {name: (pid, name) for pid, name in players}
    selected = []

    for name in selected_names:
        if name not in by_name:
            raise service.InvalidSelection(f"Unknown player: {name}")
        selected.append(by_name[name])

    return selected


def _prompt_mode() -> int | None:
    print("\nSelect mode:")
    print("[1] 1v1")
    print("[2] 2v2")
    print("[3] 3v3")
    print("[0] Cancel")
    choice = input("Select option: ").strip()
    if choice == "0":
        return None
    if choice in ("1", "2", "3"):
        return int(choice)
    raise service.InvalidSelection("Invalid mode")


def _handle_record_match(mode_hint: int | None = None) -> None:
    players = service.list_players()

    if mode_hint is None:
        try:
            mode = _prompt_mode()
        except service.InvalidSelection as e:
            print(f"-> Error: {e}")
            return
    else:
        mode = mode_hint

    if mode is None:
        print("-> Canceled")
        return

    needed = 2 * mode
    if len(players) < needed:
        print(
            f"-> Error: {mode}v{mode} needs {needed} players; "
            f"you have {len(players)}"
        )
        return

    try:
        selected = _run_fzf(
            players, f"Select {needed} players ({mode}v{mode})> ", needed
        )
        if selected is None:
            print("-> Canceled")
            return

        winners = _run_fzf(selected, f"Select {mode} winners> ", mode)
        if winners is None:
            print("-> Canceled")
            return
    except service.InvalidSelection as e:
        print(f"-> Error: {e}")
        return

    winner_ids = {p[0] for p in winners}
    losers = [p for p in selected if p[0] not in winner_ids]

    try:
        result = service.record_match(mode, winners, losers)
    except service.InvalidSelection as e:
        print(f"-> Error: {e}")
        return

    names = ", ".join(name for _, name in result)
    print(f"\n{mode}v{mode} match registered! Winners: {names}")


def _format_per_mode(per_mode: dict[int, str]) -> str:
    parts = []
    for m in sorted(per_mode):
        count = per_mode[m]["matches"]
        if count > 0:
            parts.append(f"{count}x{m}v{m}")
    return ", ".join(parts)


def _handle_view_leaderboard() -> None:
    print("\nLeaderboard mode:")
    print("[0] Global")
    print("[1] 1v1")
    print("[2] 2v2")
    print("[3] 3v3")
    choice = input("Select option: ").strip()
    if choice not in ("0", "1", "2", "3"):
        print("-> Error: Invalid option")
        return

    mode = None if choice == "0" else int(choice)
    entries = service.get_leaderboard(mode)
    if not entries:
        print("\n-> No match history recorded yet")
        return

    show_mode = mode is None
    header = (
        f"{'Player':<15} | {'Played':<6} | {'Wins':<5} | {'Losses':<6} | {'Win%':<6}"
    )
    if show_mode:
        header += " | Mode"
    print("\n" + "=" * (50 if not show_mode else 72))
    print(header)
    print("-" * (50 if not show_mode else 72))
    for e in entries:
        line = (
            f"{e['name']:<15} | {e['matches']:<6} | {e['wins']:<5} | "
            f"{e['losses']:<6} | {e['win_rate']:>5.1f}%"
        )
        if show_mode:
            line += f" | {_format_per_mode(e['per_mode'])}"
        print(line)
    print("=" * (50 if not show_mode else 72))


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
