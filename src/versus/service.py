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


def record_match(
    mode: int, winners: list[tuple[int, str]], losers: list[tuple[int, str]]
) -> list[tuple[int, str]]:
    if mode not in (1, 2, 3):
        raise InvalidSelection("Mode must be 1, 2 or 3")
    if len(winners) != mode or len(losers) != mode:
        raise InvalidSelection(
            f"Mode {mode}v{mode} requires exactly {mode} winners and {mode} losers"
        )

    winner_ids = [p[0] for p in winners]
    loser_ids = [p[0] for p in losers]

    all_ids = winner_ids + loser_ids

    if len(set(all_ids)) != 2 * mode:
        raise InvalidSelection("Duplicate players in selection")
    if set(winner_ids) & set(loser_ids):
        raise InvalidSelection("A player cannot be on both teams")

    db.insert_match(mode, winner_ids, loser_ids)

    return winners


def get_leaderboard(mode: int | None = None) -> list[dict]:
    rows = db.fetch_leaderboard(mode)
    entries = []

    for name, matches, wins, losses in rows:
        matches = matches or 0
        wins = wins or 0
        losses = losses or 0
        win_rate = ((wins / matches) * 100) if matches > 0 else 0.0
        entry = {
            "name": name,
            "matches": matches,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
        }

        if mode is None:
            entry["per_mode"] = {}
        entries.append(entry)

    if mode is None:
        by_name = {e["name"]: e for e in entries}
        for name, m_mode, matches, wins, losses in db.fetch_leaderboard_per_mode():
            entry = by_name.get(name)
            if entry is None:
                continue
            entry["per_mode"][m_mode] = {
                "matches": matches or 0,
                "wins": wins or 0,
                "losses": losses or 0,
            }

    return entries
