# 🪐 Saturn — Version Control Engine

Saturn is MilkyWay's versioning backbone. Every tool run is automatically recorded, giving you a full, reproducible audit trail of your CTF work.

## How It Works

Saturn uses a **SQLite database** (WAL mode) stored at:

```
~/.milkyway/global.db          # Global runs across all challenges
~/<challenge>/.milkyway/local.db  # Per-challenge local DB (auto-created)
```

Every `milkyway <planet> <command>` call:
1. Executes the tool
2. Captures stdout + stderr
3. Computes an output hash (SHA-256, first 16 chars)
4. Saves the full output to `~/.milkyway/outputs/<planet>_<action>_<timestamp>.txt`
5. Records the run with metadata (planet, action, command line, exit code, duration)

## Commands

### `saturn log` — Browse run history

```bash
milkyway saturn log                      # Last 20 runs
milkyway saturn log --limit 50           # More runs
milkyway saturn log --planet mercury     # Filter by planet
milkyway saturn log --challenge web1     # Filter by challenge
milkyway saturn log --search 'fuzz'      # Search command lines
milkyway saturn log --json               # Machine-readable JSON
```

### `saturn diff` — Compare two runs

```bash
milkyway saturn diff 12 13
```

Shows a unified diff of the outputs of runs #12 and #13. Useful for spotting what changed between two fuzz scans.

### `saturn redo` — Replay a run

```bash
milkyway saturn redo 42              # Replay run #42
milkyway saturn redo 42 --dry-run    # Print command only
```

Re-executes the exact command from run #42 in its original working directory.

### `saturn status` — Current context

```bash
milkyway saturn status
```

Shows:
- Current challenge (detected from cwd)
- Active session (from `MILKYWAY_SESSION` env var)
- Run statistics

### `saturn annotate` — Add notes to runs

```bash
milkyway saturn annotate 42 "This found the admin panel"
milkyway saturn annotate 7 "Worked! Got the flag from /backup.zip"
```

### `saturn export` — Export session as write-up

```bash
milkyway saturn export abc12345
milkyway saturn export abc12345 -o writeup.md
```

Generates a Markdown write-up of all runs in a session, perfect for CTF write-ups.

## Sessions

Sessions group related runs together. Useful for organizing a competition round or a single challenge attempt.

```bash
# Start a session
milkyway session start web_round_1 --challenge pico_web1

# Set the session ID so subsequent runs are tagged
export MILKYWAY_SESSION=abc12345

# Now all runs are tagged with this session
milkyway mercury fuzz http://target.com/FUZZ
milkyway mercury sql 'http://target.com/page?id=1'

# End the session
milkyway session end abc12345

# Export as markdown
milkyway saturn export abc12345 -o web_round_1_writeup.md
```

## Database Schema

```sql
CREATE TABLE runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    planet          TEXT    NOT NULL,
    action          TEXT    NOT NULL,
    command_line    TEXT    NOT NULL,
    parameters_json TEXT,
    exit_code       INTEGER,
    output_hash     TEXT,           -- SHA-256[:16] of output
    output_file     TEXT,           -- Path to saved output
    working_dir     TEXT,
    challenge_id    INTEGER,        -- FK to challenges
    session_id      TEXT,           -- FK to sessions
    notes           TEXT
);
```

## Tips

- **Never lose your work**: Saturn records everything, even if you close the terminal mid-competition
- **Reproduce any result**: `saturn redo <id>` replays the exact command
- **Compare runs**: `saturn diff` shows exactly what changed between two scans
- **Write-up ready**: `saturn export` turns your session into a publishable write-up automatically
