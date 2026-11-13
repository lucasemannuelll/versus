# versus

A minimal command-line match win/loss tracker. Record 1v1, 2v2, and 3v3 matches, then view a leaderboard with per-mode breakdowns.

## Features

- **Add players** — register names; duplicates are rejected.
- **Record matches** — pick a mode (1v1, 2v2, 3v3), select players, then pick winners.
- **Interactive selection** — uses [`fzf`](https://github.com/junegunn/fzf) for fuzzy, multi-select player picking.
- **Leaderboard** — global or per-mode standings with matches, wins, losses, win %, and a breakdown of matches played per mode.
- **SQLite storage** — everything persisted locally in `versus.db`.

## Requirements

- Python **3.14+**
- [`fzf`](https://github.com/junegunn/fzf) installed and on your `PATH` (needed to record matches)

## Installation

```sh
pip install .
```

Or, for development, run from the source tree:

```sh
python -m versus
```

## Usage

Launch the app:

```sh
python -m versus
```

You'll see the main menu:

```
=== VERSUS ===
[1] Add Player
[2] Record Match Result
[3] View Leaderboard
[4] Exit
```

### Adding players

Choose `[1]`, then enter a name. Empty names and duplicates are rejected with an error.

### Recording a match

Choose `[2]`, then:

1. Select a mode: `1v1`, `2v2`, or `3v3` (or `0` to cancel).
2. Use `fzf` to select exactly `2 × mode` players.
3. Use `fzf` again to select exactly `mode` winners from those players.

The remaining players are recorded as losers. You need at least `2 × mode` players registered before recording a match in that mode.

### Viewing the leaderboard

Choose `[3]`, then pick a scope:

- `[0]` Global — all matches, with a per-mode breakdown column.
- `[1]`–`[3]` — standings for that mode only.

Columns: `Player`, `Played`, `Wins`, `Losses`, `Win%` (and `Mode` breakdown in global view).

## Data storage

All data lives in a SQLite database named `versus.db` in the current working directory. Tables:

| Table                | Purpose                                          |
| -------------------- | ------------------------------------------------ |
| `players`            | Unique player names                              |
| `matches`            | One row per match (`mode`, `played_at`)          |
| `match_teams`        | Teams (0 = winners, 1 = losers) per match        |
| `match_participants` | Which player played on which team in which match |

The schema is created automatically on first run.

## Development

Run the app directly from source:

```sh
python -m versus
```

Project layout:

```
src/versus/
├── __init__.py
├── __main__.py   # entry point
├── cli.py        # menus, prompts, fzf integration
├── db.py         # SQLite schema and queries
└── service.py    # business logic and validation
```

## Notes & limitations

- Player selection requires `fzf`; without it, match recording is unavailable.
- Deleting or editing players/matches is not supported yet.
- `versus.db` is created in whatever directory you run the app from — run it from a consistent location to keep one leaderboard.
