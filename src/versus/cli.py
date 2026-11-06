import shutil
import subprocess

from . import service


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
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return
    print(f"-> Successfully added player: {clean}")


def _require_fzf() -> None:
    if shutil.which("fzf") is None:
        raise service.DependencyError(
            "fzf is required to record matches; install it and try again"
        )


def _run_fzf(players, prompt, count) -> list[tuple[int, str]] | None:
    names = "\n".join(f"{pid}\t{name}" for pid, name in players)
    result = subprocess.run(
        [
            "fzf",
            "--multi",
            "--prompt", prompt,
            "--height", "40%",
            "--reverse",
            "--bind", "enter:accept",
            "--with-nth", "2..",
            "--delimiter", "\t",
        ],
        input=names,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    selected = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        pid_s, _, name = line.partition("\t")
        try:
            pid = int(pid_s)
        except ValueError:
            raise service.ValidationError(f"Malformed fzf output: {line!r}")
        selected.append((pid, name))

    if len(selected) != count:
        raise service.ValidationError(f"Select exactly {count} players")

    # Verify every returned id was in the input set.
    valid_ids = {pid for pid, _ in players}
    for pid, _ in selected:
        if pid not in valid_ids:
            raise service.ValidationError(f"Unknown player id: {pid}")

    # Verify distinctness.
    if len({pid for pid, _ in selected}) != count:
        raise service.ValidationError("Duplicate players in selection")

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
    raise service.ValidationError("Invalid mode")


def _handle_record_match() -> None:
    try:
        _require_fzf()
    except service.DependencyError as e:
        print(f"-> Setup error: {e}")
        return

    try:
        mode = _prompt_mode()
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return
    if mode is None:
        print("-> Canceled")
        return

    players = service.list_players()
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
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return

    winner_ids = {pid for pid, _ in winners}
    losers = [(pid, name) for pid, name in selected if pid not in winner_ids]

    try:
        result = service.record_match(mode, winners, losers)
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return

    names = ", ".join(name for _, name in result)
    print(f"\n{mode}v{mode} match registered! Winners: {names}")


def _format_per_mode(per_mode) -> str:
    parts = [
        f"{per_mode[m]['matches']}x{m}v{m}"
        for m in sorted(per_mode)
        if per_mode[m].get("matches", 0) > 0
    ]
    return ", ".join(parts) if parts else "–"


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
        f"{'Player':<15} | {'Played':<6} | {'Wins':<5} | "
        f"{'Losses':<6} | {'Win%':<6}"
    )
    if show_mode:
        header += " | Mode"
    sep = "=" * len(header)
    print("\n" + sep)
    print(header)
    print("-" * len(header))
    for e in entries:
        line = (
            f"{e['name']:<15} | {e['matches']:<6} | {e['wins']:<5} | "
            f"{e['losses']:<6} | {e['win_rate']:>5.1f}%"
        )
        if show_mode:
            line += f" | {_format_per_mode(e['per_mode'])}"
        print(line)
    print(sep)


def main() -> None:
    service.init_storage()
    handlers = {
        "1": _handle_add_player,
        "2": _handle_record_match,
        "3": _handle_view_leaderboard,
    }

    try:
        while True:
            _print_menu()
            choice = input("\nSelect option: ").strip()
            if choice == "4":
                print("Exiting...")
                return
            handler = handlers.get(choice)
            if handler is None:
                print("-> Invalid option. Try again")
                continue
            handler()
    except KeyboardInterrupt:
        print("\nExiting...")
        return
