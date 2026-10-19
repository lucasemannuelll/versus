import sqlite3
from contextlib import contextmanager

DB_NAME = "tracker_1v1.py"

_CREATE_PLAYERS = """
    CREATE TABLE IF NOT EXISTS players (
        id INTERGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
    )
"""

_CREATE_MATCHES = """
    CREATE TABLE IF NOT EXISTS matches_1v1 (
        id INTERGER PRIMARY KEY,
        winner_id INTERGER NOT NULL REFERENCES players(id),
        loser_id INTERGER NOT NULL REFERENCES players(id),
        date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        CHECK (winner_id <> loser_id)
    )
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_matches_winner ON matches_1v1(winner_id)",
    "CREATE INDEX IF NOT EXISTS idx_matches_loser ON matches_1v1(loser_id)",
]

_LEADERBOARD = """
    SELECT
        p.name,
        COUNT(m.player_id) AS total_matches,
        SUM(m.role = 'winner') AS wins,
        SUM(m.role = 'loser') AS losses
    FROM players p
    LEFT JOIN (
        SELECT winner_id AS player_id, 'winner' AS role FROM matches_1v1
        UNION ALL
        SELECT loser_id AS player_id, 'loser' AS role FROM matches_1v1
    ) m ON m.player_id = p.id
    GROUP BY p.id
    ORDER BY wins DESC, total_matches DESC
"""
