import sqlite3

from . import db


class DuplicatePlayer(Exception):
    """Raised when a player name already exists"""


class InvalidSelection(Exception):
    """Raised when a player choice is out of range or duplicated"""


def init_storage() -> None:
    db.init_db()


def list_players() -> list[tuple[int, str]]:
    return db.fetch_players()


def add_player(name: str) -> str:
    name = name.strip()
    if not name:
        raise InvalidSelection("Name cannot be empty")
    try:
        db.insert_player(name)
    except sqlite3.IntegrityError as e:
        raise DuplicatePlayer(f"Player '{name}' already exists") from e

    return name


def pick_two_players(
    players: list[tuple[int, str]], player1_idx: int, player2_id: int
) -> tuple[tuple[int, str], tuple[int, str]]:
    player_count = len(players)
    if player1_idx == player2_id or not (
        0 <= player1_idx < player_count and 0 <= player2_id < player_count
    ):
        raise InvalidSelection("Invalid selection or same player selected")
    return players[player1_idx], players[player2_id]


def record_match(
    player1: tuple[int, str], player2: tuple[int, str], winner_choice: int
):
    if winner_choice == 1:
        winner, loser = player1, player2
    elif winner_choice == 2:
        winner, loser = player2, player1
    else:
        raise InvalidSelection("Invalid winner selection")

    db.insert_match(winner[0], loser[0])
    return winner


def get_leaderboard() -> list[dict]:
    rows = db.fetch_leaderboard()
    entries = []

    for name, matches, wins, losses in rows:
        matches = matches or 0
        wins = wins or 0
        losses = losses or 0
        win_rate = ((wins / matches) * 100) if matches > 0 else 0.0
        entries.append(
            {
                "name": name,
                "matches": matches,
                "wins": wins,
                "losses": losses,
                "win_rate": win_rate,
            }
        )

    return entries
