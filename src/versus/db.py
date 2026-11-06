import sqlite3
from contextlib import contextmanager

DB_NAME = "versus.db"

_CREATE_PLAYERS = """
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
"""

_CREATE_MATCHES = """
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        mode INTEGER NOT NULL CHECK (mode in (1, 2, 3)),
        played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
"""

_CREATE_MATCH_TEAMS = """
    CREATE TABLE IF NOT EXISTS match_teams (
        match_id INTEGER NOT NULL REFERENCES matches(id),
        team INTEGER NOT NULL CHECK (team IN (0, 1)),
        PRIMARY KEY (match_id, team)
    )
"""

_CREATE_MATCHES_PARTICIPANTS = """
    CREATE TABLE IF NOT EXISTS match_participants (
        match_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL REFERENCES players(id),
        team INTEGER NOT NULL,

        PRIMARY KEY (match_id, player_id),
        FOREIGN KEY (match_id, team) REFERENCES match_teams (match_id, team)
    )
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS "
    "idx_participants_player_match ON match_participants(player_id, match_id)",
    "CREATE INDEX IF NOT EXISTS idx_matches_mode ON matches(mode)",
]

_LEADERBOARD = """
    SELECT
        p.id,
        p.name,
        COUNT(mp.match_id) AS total_matches,
        SUM(mp.team = 0) AS wins,
        SUM(mp.team = 1) AS losses
    FROM players p
    LEFT JOIN match_participants mp ON mp.player_id = p.id
    LEFT JOIN matches m ON m.id = mp.match_id
    WHERE (:mode IS NULL OR m.mode = :mode)
    GROUP BY p.id, p.name
    ORDER BY
        (COUNT(mp.match_id) = 0) ASC,   -- players with matches first
        wins DESC,
        total_matches DESC,
        p.name ASC
"""

_LEADERBOARD_PER_MODE = """
    SELECT
        mp.player_id,
        m.mode,
        COUNT(*) AS matches,
        SUM(mp.team = 0) AS wins,
        SUM(mp.team = 1) AS losses
    FROM match_participants mp
    JOIN matches m ON m.id = mp.match_id
    GROUP BY mp.player_id, m.mode
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute(_CREATE_PLAYERS)
        cursor.execute(_CREATE_MATCHES)
        cursor.execute(_CREATE_MATCH_TEAMS)
        cursor.execute(_CREATE_MATCHES_PARTICIPANTS)
        for stmt in _CREATE_INDEXES:
            cursor.execute(stmt)


def fetch_players() -> list[tuple[int, str]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players ORDER BY name")
        return cursor.fetchall()


def insert_player(name) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))


def insert_match(mode, winner_ids, loser_ids) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO matches (mode) VALUES (?)",
            (mode,),
        )
        match_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO match_teams (match_id, team) "
            "VALUES (?, 0)", (match_id,)
        )
        cursor.execute(
            "INSERT INTO match_teams (match_id, team) "
            "VALUES (?, 1)", (match_id,)
        )

        for player_id in winner_ids:
            cursor.execute(
                "INSERT INTO match_participants (match_id, player_id, team) "
                "VALUES (?, ?, 0)",
                (match_id, player_id),
            )

        for player_id in loser_ids:
            cursor.execute(
                "INSERT INTO match_participants (match_id, player_id, team) "
                "VALUES (?, ?, 1)",
                (match_id, player_id),
            )

        return match_id


def fetch_leaderboard(mode=None) -> list[tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_LEADERBOARD, {"mode": mode})
        return cursor.fetchall()


def fetch_leaderboard_per_mode() -> list[tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_LEADERBOARD_PER_MODE)
        return cursor.fetchall()
