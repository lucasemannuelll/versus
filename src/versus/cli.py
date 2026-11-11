import shutil
import subprocess

from . import service


def _display_menu() -> None:
    print("\n=== VERSUS ===")
    print("[1] Add Player")
    print("[2] Record Match Result")
    print("[3] View Leaderboard")
    print("[4] Exit")


def _handle_add_player() -> None:
    raw_player_name = input("\nEnter player name: ").strip()
    try:
        normalized_name = service.add_player(raw_player_name)
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return
    print(f"-> Successfully added player: {normalized_name}")


def _require_fzf() -> None:
    if shutil.which("fzf") is None:
        raise service.DependencyError(
            "fzf is required to record matches; install it and try again"
        )


def _select_with_fzf(
    players, prompt_text, required_amount
) -> list[tuple[int, str]] | None:
    player_names = "\n".join(
        f"{player_id}\t{player_name}"
        for player_id, player_name in players
    )
    fzf_result = subprocess.run(
        [
            "fzf",
            "--multi",
            "--prompt", prompt_text,
            "--height", "40%",
            "--reverse",
            "--bind", "enter:accept",
            "--with-nth", "2..",
            "--delimiter", "\t",
        ],
        input=player_names,
        capture_output=True,
        text=True,
        check=False,
    )
    if fzf_result.returncode != 0:
        return None

    selected_players = []
    for output_line in fzf_result.stdout.splitlines():
        if not output_line.strip():
            continue
        player_id_text, _, player_name = output_line.partition("\t")
        try:
            player_id = int(player_id_text)
        except ValueError:
            raise service.ValidationError(f"Malformed fzf output: {output_line!r}")
        selected_players.append((player_id, player_name))

    if len(selected_players) != required_amount:
        raise service.ValidationError(f"Select exactly {required_amount} players")

    valid_player_ids = {player_id for player_id, _ in players}
    for player_id, _ in selected_players:
        if player_id not in valid_player_ids:
            raise service.ValidationError(f"Unknown player id: {player_id}")

    if len({player_id for player_id, _ in selected_players}) != required_amount:
        raise service.ValidationError("Duplicate players in selection")

    return selected_players


def _prompt_mode() -> int | None:
    print("\nSelect mode:")
    print("[1] 1v1")
    print("[2] 2v2")
    print("[3] 3v3")
    print("[0] Cancel")
    selected_option = input("Select option: ").strip()
    if selected_option == "0":
        return None
    if selected_option in ("1", "2", "3"):
        return int(selected_option)
    raise service.ValidationError("Invalid mode")


def _handle_record_match() -> None:
    try:
        _require_fzf()
    except service.DependencyError as e:
        print(f"-> Setup error: {e}")
        return

    try:
        game_mode = _prompt_mode()
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return
    if game_mode is None:
        print("-> Canceled")
        return

    players = service.list_players()
    required_amount = 2 * game_mode
    if len(players) < required_amount:
        print(
            f"-> Error: {game_mode}v{game_mode} needs {required_amount} players; "
            f"you have {len(players)}"
        )
        return

    try:
        selected_players = _select_with_fzf(
            players, f"Select {required_amount} players ({game_mode}v{game_mode})> ", required_amount
        )
        if selected_players is None:
            print("-> Canceled")
            return

        winning_team = _select_with_fzf(selected_players, f"Select {game_mode} winners> ", game_mode)
        if winning_team is None:
            print("-> Canceled")
            return
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return

    winning_player_ids = {player_id for player_id, _ in winning_team}
    losing_team = [(player_id, player_name) for player_id, player_name in selected_players if player_id not in winning_player_ids]

    try:
        match_result = service.record_match(game_mode, winning_team, losing_team)
    except service.ValidationError as e:
        print(f"-> Error: {e}")
        return

    winning_players_names = ", ".join(player_name for _, player_name in match_result)
    print(f"\n{game_mode}v{game_mode} match registered! Winners: {winning_players_names}")


def _format_per_mode(per_mode_stats) -> str:
    mode_summaries = [
        f"{per_mode_stats[mode]['matches']}x{mode}v{mode}"
        for mode in sorted(per_mode_stats)
        if per_mode_stats[mode].get("matches", 0) > 0
    ]
    return ", ".join(mode_summaries) if mode_summaries else "–"


def _handle_view_leaderboard() -> None:
    print("\nLeaderboard mode:")
    print("[0] Global")
    print("[1] 1v1")
    print("[2] 2v2")
    print("[3] 3v3")
    selected_option = input("Select option: ").strip()
    if selected_option not in ("0", "1", "2", "3"):
        print("-> Error: Invalid option")
        return

    leaderboard_mode = None if selected_option == "0" else int(selected_option)
    leaderboard_entries = service.get_leaderboard(leaderboard_mode)
    if not leaderboard_entries:
        print("\n-> No match history recorded yet")
        return

    show_mode_column = leaderboard_mode is None
    table_header = (
        f"{'Player':<15} | {'Played':<6} | {'Wins':<5} | "
        f"{'Losses':<6} | {'Win%':<6}"
    )
    if show_mode_column:
        table_header += " | Mode"
    separator = "=" * len(table_header)
    print("\n" + separator)
    print(table_header)
    print("-" * len(table_header))
    for entry in leaderboard_entries:
        table_row = (
            f"{entry['name']:<15} | {entry['matches']:<6} | "
            f"{entry['wins']:<5} | {entry['losses']:<6} | "
            f"{entry['win_rate']:>5.1f}%"
        )
        if show_mode_column:
            table_row += f" | {_format_per_mode(entry['per_mode'])}"
        print(table_row)
    print(separator)


def main() -> None:
    service.init_storage()
    menu_handlers = {
        "1": _handle_add_player,
        "2": _handle_record_match,
        "3": _handle_view_leaderboard,
    }

    try:
        while True:
            _display_menu()
            selected_option = input("\nSelect option: ").strip()
            if selected_option == "4":
                print("Exiting...")
                return
            selected_handler = menu_handlers.get(selected_option)
            if selected_handler is None:
                print("-> Invalid option. Try again")
                continue
            selected_handler()
    except KeyboardInterrupt:
        print("\nExiting...")
        return
