"""
MilkyWay Interactive Shell
──────────────────────────
SET / Metasploit-style prompt: mw>
Supports all planet commands, tab-completion, history, and inline help.
"""

from __future__ import annotations

import os
import readline
import shlex
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.text import Text

from milkyway import __version__
from milkyway.core.db import SaturnDB
from milkyway.core.challenge_manager import ChallengeManager

console = Console()

# ─── ASCII banner ─────────────────────────────────────────────────────────────

BANNER = r"""
  __  __ _ _ _          __        __
 |  \/  (_) | | ___   __\ \      / /_ _ _   _
 | |\/| | | | |/ / | | \ \ /\ / / _` | | | |
 | |  | | | |   <| |_| |\ V  V / (_| | |_| |
 |_|  |_|_|_|_|\_\\__, | \_/\_/ \__,_|\__, |
                  |___/                |___/"""

AUTHOR_BLOCK = """\
        [---]   The Galactic CTF Orchestrator (MilkyWay)   [---]
        [---]   Created by : Kazim  (kazim-45)              [---]
        [---]   Version    : {version}                        [---]
        [---]   Codename   : 'NebulaDawn'                   [---]
        [---]   GitHub     : github.com/kazim-45/milkyway   [---]
        [---]   Twitter    : @milkyway_ctf                  [---]"""

TAGLINE = "        Welcome to MilkyWay — The one-stop shop for all your CTF needs."

# ─── Menu definitions ─────────────────────────────────────────────────────────

PLANETS = [
    ("☿", "mercury",   "Web Security",          ["fuzz", "sql", "request", "headers", "extract", "scan"]),
    ("♀", "venus",     "Cryptography",          ["identify", "hash", "crack", "encode", "decode", "xor", "factor"]),
    ("♁", "earth",     "Forensics",             ["info", "carve", "strings", "hexdump", "steg", "pcap"]),
    ("♂", "mars",      "Reverse Engineering",   ["disassemble", "info", "symbols", "trace", "r2"]),
    ("♃", "jupiter",   "Binary Exploitation",   ["checksec", "rop", "template", "cyclic"]),
    ("♆", "neptune",   "Cloud & Misc",          ["jwt", "cloud", "url"]),
    ("♇", "pluto",     "AI Assistant",          ["suggest", "analyze", "cheatsheet"]),
    ("🪐", "saturn",   "Version Control",       ["log", "diff", "redo", "status", "annotate", "export"]),
]

GLOBAL_CMDS = [
    ("challenge new <n>",  "Create a new challenge workspace"),
    ("challenge list",     "List all challenges"),
    ("challenge note",     "Add a note to a challenge"),
    ("session start <n>",  "Start a named work session"),
    ("tools",              "Check tool availability"),
    ("config show",        "Show configuration"),
    ("tui",                "Launch graphical TUI dashboard"),
    ("help",               "Show this menu"),
    ("exit / quit",        "Exit MilkyWay"),
]

EXAMPLES = [
    ("mercury fuzz http://target.com/FUZZ",            "Directory brute-force"),
    ("mercury sql 'http://target.com/page?id=1'",      "SQL injection scan"),
    ("venus identify '5f4dcc3b5aa765d61d8327deb882cf99'", "Identify hash type"),
    ("venus decode 'aGVsbG8=' --enc base64",           "Base64 decode"),
    ("earth strings ./suspicious_file --grep flag",    "Hunt for flags in binary"),
    ("earth carve ./firmware.bin",                     "Extract embedded files"),
    ("mars disassemble ./binary",                      "Disassemble with objdump"),
    ("jupiter template ./binary --host ctf.io --port 1337", "Generate pwntools template"),
    ("neptune jwt 'eyJ...'",                           "Decode & audit JWT token"),
    ("pluto suggest 'I found a base64 string'",        "Get AI tool suggestion"),
    ("saturn log",                                     "View full run history"),
    ("saturn redo 42",                                 "Replay a previous run"),
]


def print_banner() -> None:
    """Print the full SET-style startup banner."""
    console.print()
    console.print(BANNER, style="bold cyan", highlight=False)
    console.print()
    console.print(AUTHOR_BLOCK.format(version=__version__), style="green", highlight=False)
    console.print()
    console.print(TAGLINE, style="bold green")
    console.print()
    console.print("        Join us on GitHub: github.com/kazim-45/milkyway", style="dim")
    console.print()
    console.print(
        "        MilkyWay is a product of the open-source CTF community.",
        style="bold",
    )
    console.print()
    console.rule(style="cyan dim")


def print_menu() -> None:
    """Print the numbered planet menu — SET style."""
    console.print()
    console.print("  [bold]Select from the menu:[/bold]")
    console.print()
    for i, (symbol, name, desc, _) in enumerate(PLANETS, 1):
        console.print(
            f"  [bold cyan]{i:>2})[/bold cyan]  {symbol}  [bold]{name.capitalize():<12}[/bold]"
            f"  [dim]—[/dim]  {desc}"
        )
    console.print()
    console.print(f"  [bold cyan]  h)[/bold cyan]     [bold]help[/bold]"
                  f"              [dim]—[/dim]  Show full command reference")
    console.print(f"  [bold cyan]  e)[/bold cyan]     [bold]examples[/bold]"
                  f"          [dim]—[/dim]  Show usage examples")
    console.print(f"  [bold cyan] 99)[/bold cyan]     [bold]exit[/bold]"
                  f"              [dim]—[/dim]  Exit MilkyWay")
    console.print()


def print_planet_menu(planet_idx: int) -> None:
    """Print sub-menu for a selected planet."""
    symbol, name, desc, commands = PLANETS[planet_idx]
    console.print()
    console.print(
        f"  [{symbol}] [bold cyan]{name.capitalize()}[/bold cyan] — {desc}",
        highlight=False,
    )
    console.print()
    console.print("  [bold]Commands:[/bold]")
    console.print()
    for i, cmd in enumerate(commands, 1):
        console.print(f"    [bold cyan]{i:>2})[/bold cyan]  {name} {cmd}")
    console.print()
    console.print(f"    [bold cyan]  b)[/bold cyan]  back  [dim](return to main menu)[/dim]")
    console.print()


def print_help() -> None:
    """Full command reference — all planets."""
    console.print()
    console.rule("[bold cyan] MilkyWay — Full Command Reference [/bold cyan]")
    console.print()

    for symbol, name, desc, cmds in PLANETS:
        console.print(f"  {symbol} [bold cyan]{name.upper()}[/bold cyan]  [dim]— {desc}[/dim]")
        for cmd in cmds:
            console.print(f"      [green]mw>[/green] [white]{name} {cmd}[/white] [dim]...[/dim]")
        console.print()

    console.rule("[bold cyan] Global Commands [/bold cyan]")
    console.print()
    for cmd, desc in GLOBAL_CMDS:
        console.print(f"    [green]mw>[/green] [white]{cmd:<30}[/white]  [dim]{desc}[/dim]")
    console.print()


def print_examples() -> None:
    """Print curated examples — SET style."""
    console.print()
    console.rule("[bold cyan] Usage Examples [/bold cyan]")
    console.print()
    for i, (cmd, desc) in enumerate(EXAMPLES, 1):
        console.print(f"  [bold cyan]{i:>2})[/bold cyan]  [green]mw>[/green] {cmd}")
        console.print(f"        [dim]{desc}[/dim]")
        console.print()


def print_tools_status() -> None:
    """Quick tool availability check inline."""
    from milkyway.core.runner import check_tool

    TOOL_PLANETS = {
        "ffuf": "mercury", "sqlmap": "mercury", "nuclei": "mercury", "curl": "mercury",
        "hashcat": "venus", "john": "venus", "openssl": "venus",
        "binwalk": "earth", "strings": "earth", "file": "earth",
        "exiftool": "earth", "tshark": "earth", "steghide": "earth",
        "objdump": "mars", "r2": "mars", "strace": "mars", "ltrace": "mars",
        "gdb": "jupiter", "ROPgadget": "jupiter", "checksec": "jupiter",
        "aws": "neptune",
    }

    table = Table(
        title="  Tool Availability",
        header_style="bold cyan",
        border_style="dim cyan",
        show_lines=False,
    )
    table.add_column("Tool", style="white", width=14)
    table.add_column("Planet", style="cyan", width=10)
    table.add_column("Status", width=12)

    for tool, planet in TOOL_PLANETS.items():
        found = check_tool(tool)
        status = "[bold green]✓  found[/bold green]" if found else "[red]✗  missing[/red]"
        table.add_row(tool, planet, status)

    console.print()
    console.print(table)
    console.print()


# ─── Tab completion ────────────────────────────────────────────────────────────

ALL_COMPLETIONS: List[str] = []

def _build_completions() -> List[str]:
    completions = []
    for _, name, _, cmds in PLANETS:
        completions.append(name)
        for cmd in cmds:
            completions.append(f"{name} {cmd}")
    for cmd, _ in GLOBAL_CMDS:
        completions.append(cmd.split()[0])
    completions += ["help", "examples", "tools", "exit", "quit", "back", "tui",
                    "challenge new", "challenge list", "challenge note",
                    "session start", "session end", "config show", "config set"]
    return sorted(set(completions))


def _completer(text: str, state: int) -> Optional[str]:
    global ALL_COMPLETIONS
    if not ALL_COMPLETIONS:
        ALL_COMPLETIONS = _build_completions()
    options = [c for c in ALL_COMPLETIONS if c.startswith(text)]
    return options[state] if state < len(options) else None


def _setup_readline() -> None:
    history_file = Path.home() / ".milkyway" / ".history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        readline.read_history_file(str(history_file))
    except FileNotFoundError:
        pass
    readline.set_history_length(500)
    readline.set_completer(_completer)
    readline.parse_and_bind("tab: complete")
    import atexit
    atexit.register(readline.write_history_file, str(history_file))


# ─── Command dispatcher ────────────────────────────────────────────────────────

def _dispatch(line: str, db: SaturnDB, cm: ChallengeManager) -> bool:
    """
    Dispatch a shell line to the appropriate planet/command.
    Returns False if the shell should exit.
    """
    line = line.strip()
    if not line:
        return True

    # Map number shortcuts from main menu
    if line in [str(i) for i in range(1, len(PLANETS) + 1)]:
        idx = int(line) - 1
        print_planet_menu(idx)
        return True

    lower = line.lower()

    # Exit
    if lower in ("exit", "quit", "q", "99"):
        console.print("\n[bold cyan]  [*] Exiting MilkyWay. Clear skies! 🌌[/bold cyan]\n")
        return False

    # Help / menu
    if lower in ("help", "h", "?", "menu"):
        print_help()
        return True

    if lower in ("examples", "e", "ex"):
        print_examples()
        return True

    if lower in ("tools",):
        print_tools_status()
        return True

    if lower in ("tui",):
        from milkyway.tui.app import launch_tui
        launch_tui()
        return True

    if lower in ("back", "b"):
        print_menu()
        return True

    # Delegate to Click CLI via subprocess-like invocation
    _run_cli_command(line, db, cm)
    return True


def _run_cli_command(line: str, db: SaturnDB, cm: ChallengeManager) -> None:
    """
    Route shell input through the Click CLI programmatically.
    Supports shorthand: 'mercury fuzz ...' → 'milkyway mercury fuzz ...'
    Also supports number shortcuts: '1 fuzz ...' → mercury fuzz ...
    """
    from milkyway.cli.main import cli
    from click.testing import CliRunner

    # Expand numeric planet prefix: "1 fuzz url" → "mercury fuzz url"
    parts = shlex.split(line)
    if parts and parts[0].isdigit():
        idx = int(parts[0]) - 1
        if 0 <= idx < len(PLANETS):
            parts[0] = PLANETS[idx][1]  # replace with planet name
        line = " ".join(shlex.quote(p) for p in parts)
        parts = shlex.split(line)

    # Invoke through the real CLI but stream output to console live
    try:
        from click import Context
        ctx = cli.make_context("mw", parts, resilient_parsing=False)
        with ctx:
            cli.invoke(ctx)
    except SystemExit as e:
        # Click calls sys.exit(0) on success — that's fine
        if e.code and e.code != 0:
            console.print(f"[red]  [!] Exit code {e.code}[/red]")
    except Exception as exc:
        # Print nicely without a stack trace for user errors
        console.print(f"\n  [bold red][!][/bold red] {exc}\n")


# ─── Main REPL ────────────────────────────────────────────────────────────────

def run_shell() -> None:
    """Launch the interactive MilkyWay shell (mw> prompt)."""
    db = SaturnDB()
    cm = ChallengeManager(db)

    _setup_readline()
    print_banner()
    print_menu()

    while True:
        # Dynamic prompt: show current challenge if inside one
        ch = cm.get_current_challenge()
        if ch:
            prompt_label = f"[{ch.name}] mw> "
        else:
            prompt_label = "mw> "

        try:
            line = input(prompt_label)
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[bold cyan]  [*] Use 'exit' to quit MilkyWay.[/bold cyan]\n")
            continue

        if not _dispatch(line, db, cm):
            break
