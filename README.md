# onevone

A simple command-line 1v1 win/loss tracker. Add players, record match results, and view a leaderboard with wins, losses, and win percentages. Data is stored locally in a SQLite database (`tracker_1v1.db`).

## Features

- Add players
- Record 1v1 match results
- View a leaderboard (matches played, wins, losses, win %)

## Run normally

Requires Python 3.10+.

```bash
python -m onevone
```

> Run this from the directory containing the `onevone` package.

## Run with uv

No manual environment setup needed — `uv` handles it.

```bash
uv run python -m onevone
```

Or, if you prefer an explicit project setup:

```bash
uv init
uv run python -m onevone
```

## Usage

On launch you'll see a menu:

```
=== 1v1 WIN TRACKER ===
[1] Add Player
[2] Record Match Result
[3] View Leaderboard
[4] Exit
```

Add at least two players, then record matches between them. The leaderboard updates automatically.
