"""
MilkyWay Interactive Shell — v1.1
──────────────────────────────────
Dexter-inspired terminal UI:
  • Colored live status line (▶ Task / ✓ Done / ✗ Error / : Thinking...)
  • Bordered info panels
  • Per-planet color coding
  • Animated spinner on long commands
  • Full SET-style banner + numbered menu
"""

from __future__ import annotations

import os
import readline
import shlex
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from milkyway import __version__
from milkyway.core.db import SaturnDB
from milkyway.core.challenge_manager import ChallengeManager

# ─── Per-planet color palette ────────────────────────────────────────────────
#  Mirrors the Dexter cyan-on-dark aesthetic but per planet

PLANET_COLORS = {
    "mercury": "cyan",
    "venus":   "magenta",
    "earth":   "green",
    "mars":    "red",
    "jupiter": "yellow",
    "neptune": "blue",
    "uranus":  "bright_blue",
    "vulcan":  "bright_red",
    "titan":   "bright_yellow",
    "pluto":   "purple",
    "saturn":  "cyan",
}

MW_THEME = Theme({
    "banner":    "bold cyan",
    "prompt":    "bold green",
    "info":      "cyan",
    "success":   "bold green",
    "warning":   "yellow",
    "error":     "bold red",
    "dim_text":  "dim white",
    "task_hdr":  "bold cyan",
    "task_box":  "cyan",
    "step_done": "green",
    "step_run":  "bold cyan",
    "step_err":  "bold red",
    "muted":     "dim",
})

console = Console(theme=MW_THEME, highlight=False)


# ─── ASCII banner ─────────────────────────────────────────────────────────────

BANNER_ART = r"""
  __  __ _ _ _          __        __
 |  \/  (_) | | ___   __\ \      / /_ _ _   _
 | |\/| | | | |/ / | | \ \ /\ / / _` | | | |
 | |  | | | |   <| |_| |\ V  V / (_| | |_| |
 |_|  |_|_|_|_|\_\__, | \_/\_/ \__,_|\__, |
                  |___/               |___/ """

INFO_ROWS = [
    ("[---]", "The Galactic CTF Orchestrator (MilkyWay)", "[---]"),
    ("[---]", f"Created by : Kazim  (kazim-45)",           "[---]"),
    ("[---]", f"Version    : {__version__:<30}",           "[---]"),
    ("[---]", "Codename   : 'NebulaDawn'",                  "[---]"),
    ("[---]", "GitHub     : github.com/kazim-45/milkyway",  "[---]"),
    ("[---]", "Twitter    : @milkyway_ctf",                 "[---]"),
]

# ─── Planet registry ──────────────────────────────────────────────────────────

PLANETS = [
    ("☿",  "mercury", "Web Security",          ["fuzz","sql","request","headers","extract","scan"],          "cyan"),
    ("♀",  "venus",   "Cryptography",          ["identify","hash","crack","encode","decode","xor","factor"],  "magenta"),
    ("♁",  "earth",   "Forensics",             ["info","carve","strings","hexdump","steg","pcap"],            "green"),
    ("♂",  "mars",    "Reverse Engineering",   ["disassemble","info","symbols","trace","r2"],                 "red"),
    ("♃",  "jupiter", "Binary Exploitation",   ["checksec","rop","template","cyclic"],                        "yellow"),
    ("♆",  "neptune", "Cloud & Misc",          ["jwt","cloud","url"],                                         "blue"),
    ("♅",  "uranus",  "Mobile / IoT",          ["decompile","info","permissions","instrument","adb","strings","ssl-bypass"], "bright_blue"),
    ("🌋", "vulcan",  "Network Recon & OSINT", ["portscan","quickscan","whois","dns","subdomain","banner"],   "bright_red"),
    ("🪐", "titan",   "Password Attacks",      ["brute","spray","wordlist","cewl","analyze","mutate"],         "bright_yellow"),
    ("♇",  "pluto",   "AI Assistant",          ["suggest","analyze","cheatsheet"],                            "purple"),
    ("🪐", "saturn",  "Version Control",       ["log","diff","redo","status","annotate","export"],             "cyan"),
]

GLOBAL_CMDS = [
    ("challenge new <n>",  "Create a new challenge workspace"),
    ("challenge list",     "List all challenges"),
    ("challenge note",     "Add a note to a challenge"),
    ("session start <n>",  "Start a named work session"),
    ("tools",              "Check all tool availability"),
    ("config show",        "Show current configuration"),
    ("tui",                "Launch graphical TUI dashboard"),
    ("help",               "Show full command reference"),
    ("examples",           "Show usage examples"),
    ("exit / quit",        "Exit MilkyWay"),
]

EXAMPLES = [
    ("mercury",  "fuzz http://target.com/FUZZ",                    "Directory brute-force"),
    ("mercury",  "sql 'http://target.com/page?id=1'",              "SQL injection scan"),
    ("venus",    "identify '5f4dcc3b5aa765d61d8327deb882cf99'",    "Identify hash type"),
    ("venus",    "decode 'aGVsbG8=' --enc base64",                 "Base64 decode"),
    ("earth",    "strings ./suspicious_file --grep flag",          "Hunt for flags in binary"),
    ("earth",    "carve ./firmware.bin",                           "Extract embedded files"),
    ("mars",     "disassemble ./binary",                           "Disassemble with objdump"),
    ("jupiter",  "template ./binary --host ctf.io --port 1337",   "Generate pwntools template"),
    ("uranus",   "decompile ./app.apk",                            "Decompile Android APK"),
    ("uranus",   "permissions ./app.apk",                          "List APK permissions"),
    ("vulcan",   "quickscan 10.10.10.10",                          "Fast top-100 port scan"),
    ("vulcan",   "subdomain example.com",                          "Enumerate subdomains"),
    ("titan",    "brute 10.10.10.10 ssh -l admin -w rockyou.txt", "SSH brute-force"),
    ("titan",    "wordlist -o pass.txt --charset alnum --min 6",   "Generate wordlist"),
    ("neptune",  "jwt 'eyJ...'",                                   "Decode & audit JWT"),
    ("pluto",    "suggest 'I found a base64 string'",             "Get AI tool suggestion"),
    ("saturn",   "log",                                            "View full run history"),
    ("saturn",   "redo 42",                                        "Replay a previous run"),
]


# ─── Dexter-style status printing ─────────────────────────────────────────────

def _status_thinking(msg: str = "Thinking...") -> None:
    console.print(f": [dim]{msg}[/dim]")


def _status_task(msg: str, planet: str = "") -> None:
    color = PLANET_COLORS.get(planet, "cyan")
    console.print(f"\n[bold {color}]▶ Task:[/bold {color}] {msg}")


def _status_done(msg: str = "") -> None:
    console.print(f"[bold green]✓[/bold green] {msg}" if msg else "[bold green]✓[/bold green]")


def _status_error(msg: str) -> None:
    console.print(f"[bold red]✗[/bold red] [red]{msg}[/red]")


def _status_running(tool: str, args_preview: str = "") -> None:
    console.print(f"[bold green]✓[/bold green] Executing [bold green]{tool}[/bold green] [bold green]✓[/bold green]")
    if args_preview:
        console.print(f"  [bold yellow]⚡[/bold yellow] [dim]{tool} ({args_preview})[/dim]")


def _status_complete(msg: str, success: bool = True) -> None:
    icon = "[bold green]✓ Completed[/bold green]" if success else "[bold red]✗ Failed[/bold red]"
    console.print(f"[bold green]✓[/bold green] {icon} [dim]| {msg}[/dim]")


def _info_box(lines: List[str], title: str = "", color: str = "cyan") -> None:
    """Print a Dexter-style bordered info box."""
    content = "\n".join(f"  [bold {color}]+[/bold {color}] {l}" for l in lines)
    if title:
        console.print(Panel(content, title=f"[bold {color}]{title}[/bold {color}]",
                            border_style=color, expand=False))
    else:
        console.print(Panel(content, border_style=color, expand=False))


# ─── Banner & menu ────────────────────────────────────────────────────────────

def print_banner() -> None:
    console.print()
    console.print(BANNER_ART, style="bold cyan", highlight=False)
    console.print()

    # Info block — Dexter style
    for left, mid, right in INFO_ROWS:
        console.print(
            f"        [green]{left}[/green]   [bold green]{mid}[/bold green]   [green]{right}[/green]",
            highlight=False,
        )
    console.print()
    console.print(
        "        [bold green]Welcome to MilkyWay — The one-stop shop for all your CTF needs.[/bold green]",
        highlight=False,
    )
    console.print()
    console.print(
        "        [dim]Join us at: github.com/kazim-45/milkyway  ·  Discord: discord.gg/milkyway[/dim]",
        highlight=False,
    )
    console.print()
    console.print(
        "        [bold]MilkyWay is a product of the open-source CTF community.[/bold]",
        highlight=False,
    )
    console.print()
    console.rule(style="cyan dim")


def print_menu() -> None:
    console.print()
    console.print("  [bold]Select from the menu:[/bold]")
    console.print()

    for i, (symbol, name, desc, _, color) in enumerate(PLANETS, 1):
        num = f"[bold {color}]{i:>2})[/bold {color}]"
        sym = f"[{color}]{symbol}[/{color}]"
        nm  = f"[bold {color}]{name.capitalize():<14}[/bold {color}]"
        console.print(f"  {num}  {sym}  {nm}  [dim]—[/dim]  {desc}")

    console.print()
    console.print(f"  [bold cyan]  h)[/bold cyan]     [bold]help[/bold]              [dim]—[/dim]  Full command reference")
    console.print(f"  [bold cyan]  e)[/bold cyan]     [bold]examples[/bold]          [dim]—[/dim]  Curated usage examples")
    console.print(f"  [bold cyan] 99)[/bold cyan]     [bold]exit[/bold]              [dim]—[/dim]  Exit MilkyWay")
    console.print()


def print_planet_menu(planet_idx: int) -> None:
    symbol, name, desc, commands, color = PLANETS[planet_idx]
    console.print()

    # Dexter-style task header
    console.print(f"\n  [{color}]{symbol}[/{color}] [bold {color}]{name.capitalize()}[/bold {color}] [dim]— {desc}[/dim]")
    console.print()

    lines = [f"[bold {color}]{name} {cmd}[/bold {color}]" for cmd in commands]
    _info_box(lines, title="Commands", color=color)

    console.print()
    console.print(f"    [bold {color}]b)[/bold {color}]  [bold]back[/bold]  [dim](return to main menu)[/dim]")
    console.print()


def print_help() -> None:
    console.print()
    console.rule(f"[bold cyan] MilkyWay v{__version__} — Full Command Reference [/bold cyan]")
    console.print()

    for symbol, name, desc, cmds, color in PLANETS:
        console.print(f"  [{color}]{symbol}[/{color}] [bold {color}]{name.upper():<12}[/bold {color}]  [dim]— {desc}[/dim]")
        for cmd in cmds:
            console.print(f"      [bold green]mw>[/bold green] [white]{name} {cmd}[/white]")
        console.print()

    console.rule("[bold cyan] Global Commands [/bold cyan]")
    console.print()
    for cmd, desc in GLOBAL_CMDS:
        console.print(f"    [bold green]mw>[/bold green] [white]{cmd:<32}[/white]  [dim]{desc}[/dim]")
    console.print()


def print_examples() -> None:
    console.print()
    console.rule("[bold cyan] Usage Examples [/bold cyan]")
    console.print()

    for i, (planet, cmd, desc) in enumerate(EXAMPLES, 1):
        color = PLANET_COLORS.get(planet, "cyan")
        console.print(
            f"  [bold cyan]{i:>2})[/bold cyan]  "
            f"[bold green]mw>[/bold green] "
            f"[bold {color}]{planet}[/bold {color}] {cmd}"
        )
        console.print(f"        [dim]{desc}[/dim]")
        if i % 3 == 0:
            console.print()
    console.print()


def print_tools_status() -> None:
    from milkyway.core.runner import check_tool

    TOOL_META = [
        ("ffuf",      "mercury",  "cyan"),
        ("sqlmap",    "mercury",  "cyan"),
        ("nuclei",    "mercury",  "cyan"),
        ("curl",      "mercury",  "cyan"),
        ("hashcat",   "venus",    "magenta"),
        ("john",      "venus",    "magenta"),
        ("openssl",   "venus",    "magenta"),
        ("binwalk",   "earth",    "green"),
        ("strings",   "earth",    "green"),
        ("file",      "earth",    "green"),
        ("exiftool",  "earth",    "green"),
        ("tshark",    "earth",    "green"),
        ("steghide",  "earth",    "green"),
        ("objdump",   "mars",     "red"),
        ("r2",        "mars",     "red"),
        ("strace",    "mars",     "red"),
        ("ltrace",    "mars",     "red"),
        ("gdb",       "jupiter",  "yellow"),
        ("ROPgadget", "jupiter",  "yellow"),
        ("checksec",  "jupiter",  "yellow"),
        ("apktool",   "uranus",   "bright_blue"),
        ("jadx",      "uranus",   "bright_blue"),
        ("frida",     "uranus",   "bright_blue"),
        ("adb",       "uranus",   "bright_blue"),
        ("nmap",      "vulcan",   "bright_red"),
        ("whois",     "vulcan",   "bright_red"),
        ("hydra",     "titan",    "bright_yellow"),
        ("medusa",    "titan",    "bright_yellow"),
        ("crunch",    "titan",    "bright_yellow"),
        ("aws",       "neptune",  "blue"),
    ]

    table = Table(
        title="\n  🛠  Tool Availability",
        header_style="bold cyan",
        border_style="dim cyan",
        show_lines=False,
    )
    table.add_column("Tool",   style="white", width=12)
    table.add_column("Planet", width=10)
    table.add_column("Status", width=14)

    found = 0
    for tool, planet, color in TOOL_META:
        ok = check_tool(tool)
        if ok:
            found += 1
        pname  = f"[{color}]{planet}[/{color}]"
        status = "[bold green]✓  found[/bold green]" if ok else "[red]✗  missing[/red]"
        table.add_row(tool, pname, status)

    console.print()
    console.print(table)
    missing = len(TOOL_META) - found
    console.print(
        f"\n  [dim]{found}/{len(TOOL_META)} tools found"
        + (f"  ·  run [bold]tools --install[/bold] for hints" if missing else "  ·  fully equipped! 🚀")
        + "[/dim]\n"
    )


# ─── Tab completion ────────────────────────────────────────────────────────────

_ALL_COMPLETIONS: List[str] = []


def _build_completions() -> List[str]:
    comps = []
    for _, name, _, cmds, _ in PLANETS:
        comps.append(name)
        for cmd in cmds:
            comps.append(f"{name} {cmd}")
    comps += [
        "help", "examples", "tools", "tui", "exit", "quit", "back",
        "challenge new", "challenge list", "challenge note", "challenge cd", "challenge delete",
        "session start", "session end",
        "config show", "config set", "config get",
    ]
    return sorted(set(comps))


def _completer(text: str, state: int) -> Optional[str]:
    global _ALL_COMPLETIONS
    if not _ALL_COMPLETIONS:
        _ALL_COMPLETIONS = _build_completions()
    options = [c for c in _ALL_COMPLETIONS if c.startswith(text)]
    return options[state] if state < len(options) else None


def _setup_readline() -> None:
    hist = Path.home() / ".milkyway" / ".history"
    hist.parent.mkdir(parents=True, exist_ok=True)
    try:
        readline.read_history_file(str(hist))
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)
    readline.set_completer(_completer)
    readline.parse_and_bind("tab: complete")
    import atexit
    atexit.register(readline.write_history_file, str(hist))


# ─── Spinner ──────────────────────────────────────────────────────────────────

class _Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, msg: str = "Running"):
        self._msg = msg
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _spin(self) -> None:
        i = 0
        while self._running:
            frame = self.FRAMES[i % len(self.FRAMES)]
            sys.stdout.write(f"\r  [bold cyan]{frame}[/bold cyan] {self._msg} ")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1


# ─── Command dispatcher ────────────────────────────────────────────────────────

def _dispatch(line: str, db: SaturnDB, cm: ChallengeManager) -> bool:
    line = line.strip()
    if not line:
        return True

    lower = line.lower()

    # Exit
    if lower in ("exit", "quit", "q", "99"):
        console.print("\n[bold cyan]  [*] Exiting MilkyWay. Clear skies! 🌌[/bold cyan]\n")
        return False

    # Number → planet sub-menu
    if lower.isdigit():
        idx = int(lower) - 1
        if 0 <= idx < len(PLANETS):
            print_planet_menu(idx)
        else:
            _status_error(f"No planet #{lower}. Choose 1–{len(PLANETS)}.")
        return True

    # Built-in keywords
    if lower in ("help", "h", "?", "menu"):
        print_help(); return True
    if lower in ("examples", "e", "ex"):
        print_examples(); return True
    if lower in ("tools", "tools --install"):
        print_tools_status(); return True
    if lower in ("tui",):
        from milkyway.tui.app import launch_tui
        launch_tui(); return True
    if lower in ("back", "b", "m"):
        print_menu(); return True

    # Delegate to Click CLI
    _run_cli_command(line, db, cm)
    return True


def _run_cli_command(line: str, db: SaturnDB, cm: ChallengeManager) -> None:
    from milkyway.cli.main import cli

    try:
        parts = shlex.split(line)
    except ValueError as e:
        _status_error(f"Parse error: {e}")
        return

    # Numeric planet prefix: "3 strings ./file" → "earth strings ./file"
    if parts and parts[0].isdigit():
        idx = int(parts[0]) - 1
        if 0 <= idx < len(PLANETS):
            parts[0] = PLANETS[idx][1]

    # Detect planet for color
    planet = parts[0] if parts else ""
    color  = PLANET_COLORS.get(planet, "cyan")

    # Dexter-style: print the task being executed
    _status_task(" ".join(parts[:3]) + ("…" if len(parts) > 3 else ""), planet=planet)
    _status_thinking()

    try:
        ctx = cli.make_context("mw", parts, resilient_parsing=False)
        _status_running(planet or parts[0], " ".join(parts[1:3]))
        with ctx:
            cli.invoke(ctx)
        _status_complete(" ".join(parts[:4]), success=True)
    except SystemExit as e:
        if e.code and e.code != 0:
            _status_complete(" ".join(parts[:4]), success=False)
    except Exception as exc:
        _status_error(str(exc))


# ─── Prompt builder ───────────────────────────────────────────────────────────

def _build_prompt(cm: ChallengeManager) -> str:
    """
    Return the ANSI-escaped prompt string for input().
    Green 'mw>' — with challenge name prefix if inside a workspace.
    """
    ch = cm.get_current_challenge()
    # ANSI green + reset (readline-safe: wrap in \001 \002)
    GREEN  = "\001\033[1;32m\002"
    CYAN   = "\001\033[1;36m\002"
    RESET  = "\001\033[0m\002"

    if ch:
        return f"{CYAN}[{ch.name}]{RESET} {GREEN}mw>{RESET} "
    return f"{GREEN}mw>{RESET} "


# ─── Main REPL ────────────────────────────────────────────────────────────────

def run_shell() -> None:
    """Launch the interactive MilkyWay shell."""
    db = SaturnDB()
    cm = ChallengeManager(db)

    _setup_readline()
    print_banner()
    print_menu()

    while True:
        try:
            line = input(_build_prompt(cm))
        except (EOFError, KeyboardInterrupt):
            console.print(
                "\n\n[bold cyan]  [*] Use 'exit' or '99' to quit MilkyWay.[/bold cyan]\n"
            )
            continue

        if not _dispatch(line, db, cm):
            break
