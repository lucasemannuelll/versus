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


def add_player(player_name) -> str:
    normalized_player_name = player_name.strip()
    if not normalized_player_name:
        raise ValidationError("Name cannot be empty")

    try:
        db.insert_player(normalized_player_name)
    except sqlite3.IntegrityError as e:
        raise DuplicatePlayer(
            f"Player '{normalized_player_name}' already exists"
        ) from e

    return normalized_player_name


def record_match(
    game_mode, winning_team, losing_team
) -> list[tuple[int, str]]:
    if game_mode not in (1, 2, 3):
        raise ValidationError("Mode must be 1, 2 or 3")

    if len(winning_team) != game_mode or len(losing_team) != game_mode:
        raise ValidationError(
            f"Mode {game_mode}v{game_mode} requires exactly "
            f"{game_mode} winners and {game_mode} losers"
        )

    winning_player_ids = {player[0] for player in winning_team}
    losing_player_ids = {player[0] for player in losing_team}

    if len(winning_player_ids | losing_player_ids) != 2 * game_mode:
        raise ValidationError("Duplicate players in selection")

    db.insert_match(game_mode, winning_player_ids, losing_player_ids)

    return winning_team


def get_leaderboard(game_mode=None) -> list[dict]:
    leaderboard_rows = db.fetch_leaderboard(game_mode)
    leaderboard_entries = []

    for (
        player_id, player_name, total_matches, total_wins, total_losses
    ) in leaderboard_rows:
        total_matches = total_matches or 0
        total_wins = total_wins or 0
        total_losses = total_losses or 0
        win_rate = (
            (total_wins / total_matches) * 100 if total_matches > 0 else 0.0
        )
        entry = {
            "player_id": player_id,
            "name": player_name,
            "matches": total_matches,
            "wins": total_wins,
            "losses": total_losses,
            "win_rate": win_rate,
        }
        if game_mode is None:
            entry["per_mode"] = {}
        leaderboard_entries.append(entry)

    if game_mode is None:
        entries_by_player_id = {
            entry["player_id"]: entry for entry in leaderboard_entries
        }
        for player_id, game_modes, total_matches, total_wins, total_losses in (
            db.fetch_leaderboard_per_mode()
        ):
            entry = entries_by_player_id.get(player_id)
            if entry is None:
                continue
            entry["per_mode"][game_mode] = {
                "matches": total_matches or 0,
                "wins": total_wins or 0,
                "losses": total_losses or 0,
            }

    return leaderboard_entries
