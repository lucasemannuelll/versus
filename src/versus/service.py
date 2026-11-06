import sqlite3

from . import db


class VersusError(Exception):
    """Base class for all versus errors."""


class ValidationError(VersusError):
    """Raised when user-supplied input fails validation."""


class DependencyError(VersusError):
    """Raised when a required external tool is missing."""


class DuplicatePlayer(ValidationError):
    """Raised when a player name already exists."""


def init_storage() -> None:
    db.init_db()


def list_players() -> list[tuple[int, str]]:
    return db.fetch_players()


def add_player(name) -> str:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationError("Name cannot be empty")
    try:
        db.insert_player(clean_name)
    except sqlite3.IntegrityError as e:
        raise DuplicatePlayer(f"Player '{clean_name}' already exists") from e

    return clean_name


def record_match(mode, winners, losers) -> list[tuple[int, str]]:
    if mode not in (1, 2, 3):
        raise ValidationError("Mode must be 1, 2 or 3")
    if len(winners) != mode or len(losers) != mode:
        raise ValidationError(
            f"Mode {mode}v{mode} requires exactly "
            f"{mode} winners and {mode} losers"
        )

    winner_ids = {player[0] for player in winners}
    loser_ids = {player[0] for player in losers}

    if len(winner_ids | loser_ids) != 2 * mode:
        raise ValidationError("Duplicate players in selection")

    db.insert_match(mode, winner_ids, loser_ids)

    return winners


def get_leaderboard(mode=None) -> list[dict]:
    rows = db.fetch_leaderboard(mode)
    entries = []

    for player_id, name, matches, wins, losses in rows:
        matches = matches or 0
        wins = wins or 0
        losses = losses or 0
        win_rate = ((wins / matches) * 100) if matches > 0 else 0.0
        entry = {
            "player_id": player_id,
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
        by_id = {e["player_id"]: e for e in entries}
        for player_id, m_mode, matches, wins, losses in (
            db.fetch_leaderboard_per_mode()
        ):
            entry = by_id.get(player_id)
            if entry is None:
                continue
            entry["per_mode"][m_mode] = {
                "matches": matches or 0,
                "wins": wins or 0,
                "losses": losses or 0,
            }

    return entries
