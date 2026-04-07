"""
MilkyWay Interactive Shell v2.1
================================
Flow:
  Main menu  →  enter 1-11 to SELECT a planet
  Planet sub-shell  →  enter 1-N to run that planet's command
  Planet sub-shell  →  b / 0 to go back to main menu
  Main menu  →  0 / exit to quit

The prompt changes to show active planet:
  mw>              (main menu)
  [mercury] mw>    (planet selected)

Typing just a number inside a planet sub-shell runs that command.
Arguments are prompted interactively.
"""

from __future__ import annotations
import os, readline, shlex, sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from milkyway import __version__
from milkyway.core.db import SaturnDB
from milkyway.core.challenge_manager import ChallengeManager

# ─── Colors ───────────────────────────────────────────────────────────────────

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
    "saturn":  "bright_cyan",
}

console = Console(highlight=False)

# ─── ASCII banner ─────────────────────────────────────────────────────────────

LOGO = r"""
     *    .  *       .       *   .      *     .      *
  .    *        *  .    .  *   .    .  *   .      *
   __  __ _ _ _          __        __
  |  \/  (_) | | ___   __\ \      / /_ _ _   _
  | |\/| | | | |/ / | | \ \ /\ / / _` | | | |
  | |  | | | |   <| |_| |\ V  V / (_| | |_| |
  |_|  |_|_|_|_|\_\__, | \_/\_/ \__,_|\__, |
                   |___/    W A Y      |___/
  *   .      *   .      *   .      *   .      *
     .    *        *  .    .  *   .    .  *   .
"""

INFO_ROWS = [
    ("[ === ]", "The Galactic CTF Orchestrator",  "[ === ]"),
    ("[ --- ]", f"Created by  : Kazim  (kazim-45)","[ --- ]"),
    ("[ --- ]", f"Version     : {__version__}",    "[ --- ]"),
    ("[ --- ]", "Codename    : 'NebulaDawn'",       "[ --- ]"),
    ("[ --- ]", "GitHub      : kazim-45/milkyway",  "[ --- ]"),
    ("[ --- ]", "Twitter     : @milkyway_ctf",      "[ --- ]"),
]

# ─── Planet + command registry ────────────────────────────────────────────────
# (planet_num, symbol, name, description, commands, color)
# commands = list of (cmd_name, help_text, required_args, optional_args)
#   required_args = list of (arg_name, prompt_text)
#   optional_args = list of (flag, prompt_text, default)

PLANETS: List[Tuple] = [
    (1, "☿", "mercury", "Web Security", [
        ("fuzz",    "Directory/file fuzzing",      [("url","Target URL (put FUZZ where wordlist goes)")], [("--wordlist","Wordlist path",""),("--threads","Threads","40"),("--extensions","Extensions e.g. .php,.html",""),("--status-codes","Status codes to match","200,301,302,403")]),
        ("sql",     "SQL injection scan",           [("url","Target URL (e.g. http://site.com/page?id=1)")], [("--data","POST data",""),("--dbs","Enumerate databases (y/n)","n")]),
        ("request", "Craft HTTP request",           [("url","Target URL")], [("--method","Method (GET/POST/PUT)","GET"),("--data","Request body",""),("--header","Add header (e.g. 'Authorization: Bearer TOKEN')","")]),
        ("headers", "Inspect HTTP headers",         [("url","Target URL")], []),
        ("extract", "Extract links/forms/emails",   [("file","HTML file to parse")], [("--type","What to extract (links/forms/cookies/comments/emails)","links")]),
        ("scan",    "Nuclei template scan",          [("url","Target URL")], [("--templates","Template path","")]),
    ], "cyan"),

    (2, "♀", "venus", "Cryptography", [
        ("identify","Identify hash type",           [("hash_str","Hash or encoded string to identify")], []),
        ("hash",    "Compute hash",                 [("text","Text to hash")], [("--algo","Algorithm (md5/sha1/sha256/sha512)","md5")]),
        ("crack",   "Crack hash with wordlist",     [("hash_str","Hash to crack")], [("--wordlist","Wordlist path",""),("--type","Hashcat mode (0=MD5, 100=SHA1)","")]),
        ("encode",  "Encode text",                  [("text","Text to encode")], [("--enc","Encoding (base64/hex/rot13/url/binary/morse)","base64")]),
        ("decode",  "Decode text",                  [("text","Text to decode")], [("--enc","Encoding (base64/hex/rot13/url/binary)","base64")]),
        ("xor",     "XOR data with key",            [("data","Data (hex by default)"),("key","XOR key")], [("--format","Input format (hex/base64/text)","hex")]),
        ("factor",  "Factor number (RSA)",          [("number","Number to factor")], []),
        ("rsa",     "RSA decrypt/attack",           [("--n","RSA modulus n"),("--e","Public exponent e"),("--c","Ciphertext c")], [("--d","Private exponent d (if known)","")]),
    ], "magenta"),

    (3, "♁", "earth", "Forensics", [
        ("info",    "File type, hashes, metadata",  [("file","File to analyse")], []),
        ("carve",   "Extract embedded files",       [("file","File to carve")], [("--output-dir","Output directory","")]),
        ("strings", "Extract printable strings",    [("file","File to search")], [("--min-len","Minimum string length","4"),("--grep","Filter regex","")]),
        ("hexdump", "Hex dump file contents",       [("file","File to dump")], [("--length","Bytes to show","256"),("--offset","Start offset","0")]),
        ("steg",    "Steganography extraction",     [("file","Image file (jpg/png)")], [("--password","Steghide password","")]),
        ("pcap",    "Analyse network capture",      [("file","PCAP file")], [("--filter","Wireshark filter",""),("--follow","Follow stream (tcp/udp/http)","")]),
    ], "green"),

    (4, "♂", "mars", "Reverse Engineering", [
        ("disassemble","Disassemble binary",        [("file","Binary file")], [("--section","Section to disassemble",".text"),("--syntax","Syntax (intel/att)","intel")]),
        ("info",    "ELF/PE headers + security",    [("file","Binary file")], []),
        ("symbols", "List binary symbols",          [("file","Binary file")], [("--no-demangle","Don't demangle C++ names (y/n)","n")]),
        ("trace",   "Syscall/library trace",        [("file","Binary to trace")], [("--mode","Trace mode (syscall/library)","syscall"),("--args","Arguments to pass to binary","")]),
        ("r2",      "Radare2 batch command",        [("file","Binary file")], [("--cmd","Radare2 commands","aaa;pdf @main")]),
    ], "red"),

    (5, "♃", "jupiter", "Binary Exploitation", [
        ("checksec","Check security mitigations",   [("file","Binary file")], []),
        ("rop",     "Find ROP gadgets",             [("file","Binary file")], [("--search","Gadget search pattern","")]),
        ("template","Generate pwntools template",   [("binary","Binary file")], [("--host","Remote host","localhost"),("--port","Remote port","4444"),("--output","Output filename","")]),
        ("cyclic",  "De Bruijn cyclic pattern",     [("length","Pattern length (number)")], [("--find","Find offset of sub-pattern","")]),
    ], "yellow"),

    (6, "♆", "neptune", "Cloud & Misc", [
        ("jwt",     "Decode / audit JWT token",     [("token","JWT token string")], [("--secret","HMAC secret for verification","")]),
        ("cloud",   "AWS/K8s enumeration",          [], [("--provider","Provider (aws/k8s)","aws"),("--cmd","Command to run","whoami")]),
        ("url",     "URL parse / encode / decode",  [("target","URL or encoded string")], [("--action","Action (info/decode/encode)","info")]),
    ], "blue"),

    (7, "♅", "uranus", "Mobile / IoT", [
        ("decompile",  "Decompile APK",             [("apk","APK file path")], [("--tool","Tool (apktool/jadx)","apktool"),("--output-dir","Output directory","")]),
        ("info",       "APK metadata",              [("apk","APK file path")], []),
        ("permissions","APK permissions (rated)",   [("apk","APK file path")], []),
        ("instrument", "Frida/Objection dynamic",   [("target","Package name or app")], [("--script","Frida JS script path",""),("--mode","Mode (frida/objection)","frida")]),
        ("adb",        "ADB device commands",       [("command","ADB command (e.g. shell ls /data)")], []),
        ("strings",    "Extract APK secrets",       [("apk","APK file path")], [("--grep","Regex filter","")]),
        ("ssl-bypass", "SSL pinning bypass",        [("package","Package name")], []),
    ], "bright_blue"),

    (8, "🌋", "vulcan", "Network Recon", [
        ("portscan",  "Full nmap port scan",        [("target","Target IP or hostname")], [("--ports","Port range","1-1000"),("--speed","Speed T1-T5","3"),("--script","Nmap script","")]),
        ("quickscan", "Fast top-100 scan",          [("target","Target IP or hostname")], []),
        ("whois",     "WHOIS lookup",               [("target","Domain or IP")], []),
        ("dns",       "DNS record lookup",          [("target","Domain")], [("--type","Record type (A/MX/NS/TXT/CNAME/ANY)","A")]),
        ("subdomain", "Subdomain brute-force",      [("domain","Domain to enumerate")], [("--wordlist","Wordlist path","")]),
        ("banner",    "Service banner grab",        [("host","Host to connect to"),("port","Port number")], []),
    ], "bright_red"),

    (9, "🪐", "titan", "Password Attacks", [
        ("brute",    "Login brute-force (Hydra)",   [("target","Target IP/host"),("service","Service (ssh/ftp/http-post-form…)")], [("--username","Single username",""),("--user-list","Username list path",""),("--wordlist","Password wordlist path",""),("--port","Port (if non-default)",""),("--threads","Threads","4")]),
        ("spray",    "Password spray attack",       [("target","Target IP/host"),("service","Service (ssh/ftp…)")], [("--password","Password to spray","Password123"),("--user-list","Username list","")]),
        ("wordlist", "Generate custom wordlist",    [("--output","Output file","wordlist.txt")], [("--charset","Character set (alpha/alnum/digits/special/hex)","alnum"),("--min","Min length","6"),("--max","Max length","8"),("--prefix","Word prefix",""),("--suffix","Word suffix","")]),
        ("cewl",     "Spider site → wordlist",      [("url","Target URL to spider")], [("--depth","Spider depth","2"),("--min-word","Min word length","5"),("--output","Output file","cewl.txt")]),
        ("analyze",  "Wordlist statistics",         [("wordlist","Wordlist file path")], []),
        ("mutate",   "Apply mutation rules",        [("wordlist","Wordlist file path")], [("--output","Output file","mutated.txt")]),
    ], "bright_yellow"),

    (10, "♇", "pluto", "AI Assistant", [
        ("suggest",    "AI tool suggestion",        [("description","Describe what you found or need")], [("--model","Override AI model","")]),
        ("analyze",    "Analyze file → next steps", [("file","File to analyze")], []),
        ("cheatsheet", "Quick reference sheet",     [("topic","Topic (web/crypto/forensics)")], []),
    ], "purple"),

    (11, "⟳", "saturn", "Version Control", [
        ("log",      "Show run history",            [], [("--limit","Number of runs","20"),("--planet","Filter by planet",""),("--search","Search in commands","")]),
        ("diff",     "Compare two runs",            [("run_id1","First run ID"),("run_id2","Second run ID")], []),
        ("redo",     "Replay a previous run",       [("run_id","Run ID to replay")], []),
        ("status",   "Current context & stats",     [], []),
        ("annotate", "Add note to a run",           [("run_id","Run ID to annotate"),("text","Annotation text")], []),
        ("export",   "Export session → markdown",   [("session_id","Session ID")], [("--output","Output file","")]),
    ], "bright_cyan"),
]

# Fast lookup by name
PLANET_BY_NAME: Dict[str, tuple] = {p[2]: p for p in PLANETS}

GLOBAL_MENU = [
    ("A", "challenge new <n>", "Create challenge workspace"),
    ("B", "challenge list",    "List all challenges"),
    ("C", "session start <n>","Start a work session"),
    ("D", "saturn status",     "Context & stats"),
    ("E", "tools",             "Tool availability"),
    ("F", "config show",       "Configuration"),
    ("H", "help",              "Full command reference"),
    ("X", "examples",          "Usage examples"),
    ("0", "exit",              "Exit MilkyWay"),
]

EXAMPLES = [
    ("mercury","fuzz http://target.com/FUZZ",                    "Directory brute-force"),
    ("mercury","sql 'http://target.com/page?id=1'",              "SQLi detection"),
    ("venus",  "identify '5f4dcc3b5aa765d61d8327deb882cf99'",    "Hash identification"),
    ("venus",  "decode 'aGVsbG8=' --enc base64",                 "Base64 decode"),
    ("earth",  "strings ./binary --grep flag",                   "Flag hunting"),
    ("earth",  "carve ./firmware.bin",                           "File carving"),
    ("mars",   "disassemble ./binary",                           "Disassembly"),
    ("jupiter","checksec ./binary",                              "Security mitigations"),
    ("jupiter","cyclic 200",                                     "Buffer overflow offset"),
    ("uranus", "permissions ./app.apk",                          "APK permissions"),
    ("vulcan", "quickscan 10.10.10.10",                          "Fast port scan"),
    ("vulcan", "subdomain example.com",                          "Subdomain enum"),
    ("titan",  "wordlist --charset digits --min 4 --max 4",      "PIN wordlist"),
    ("titan",  "mutate names.txt",                               "Password mutation"),
    ("neptune","jwt 'eyJ...'",                                   "JWT audit"),
    ("pluto",  "suggest 'I found a base64 string'",              "AI suggestion"),
    ("saturn", "log --limit 20",                                 "Run history"),
    ("saturn", "redo 42",                                        "Replay run"),
]

# ─── Banner & main menu ───────────────────────────────────────────────────────

def print_banner() -> None:
    console.print()
    console.print(LOGO, style="bold cyan", highlight=False)
    console.print()
    for left, mid, right in INFO_ROWS:
        console.print(
            f"        [bright_green]{left}[/bright_green]"
            f"   [bold green]{mid}[/bold green]"
            f"   [bright_green]{right}[/bright_green]",
            highlight=False,
        )
    console.print()
    console.print(
        "        [bold bright_green]Welcome to MilkyWay — The one-stop shop for all your CTF needs.[/bold bright_green]",
        highlight=False,
    )
    console.print(
        "        [dim]github.com/kazim-45/milkyway  "
        "|  discord.gg/milkyway  |  @milkyway_ctf[/dim]",
        highlight=False,
    )
    console.print()
    console.rule(style="cyan dim")


def _planet_row(p: tuple) -> str:
    num, sym, name, desc, _, color = p
    return (
        f"[bold {color}]{num:>2}.[/bold {color}]  "
        f"[{color}]{sym}[/{color}] "
        f"[bold {color}]{name.capitalize():<12}[/bold {color}] "
        f"[dim]{desc}[/dim]"
    )


def print_menu() -> None:
    console.print()
    half = (len(PLANETS) + 1) // 2
    ptable = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    ptable.add_column("Left",  no_wrap=True)
    ptable.add_column("Right", no_wrap=True)
    left_col  = PLANETS[:half]
    right_col = PLANETS[half:]
    for i in range(half):
        l = _planet_row(left_col[i])  if i < len(left_col)  else ""
        r = _planet_row(right_col[i]) if i < len(right_col) else ""
        ptable.add_row(l, r)
    console.print(Panel(ptable,
                        title="[bold yellow]  ★ PLANETS — enter number to select  ★[/bold yellow]",
                        border_style="yellow", padding=(1, 2)))

    half_g = (len(GLOBAL_MENU) + 1) // 2
    gtable = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    gtable.add_column("Left",  no_wrap=True)
    gtable.add_column("Right", no_wrap=True)
    left_g  = GLOBAL_MENU[:half_g]
    right_g = GLOBAL_MENU[half_g:]
    for i in range(half_g):
        def _grow(g):
            k, cmd, desc = g
            return f"[bold cyan]{k}.[/bold cyan]  [white]{cmd:<26}[/white] [dim]{desc}[/dim]"
        l = _grow(left_g[i])  if i < len(left_g)  else ""
        r = _grow(right_g[i]) if i < len(right_g) else ""
        gtable.add_row(l, r)
    console.print(Panel(gtable,
                        title="[bold cyan]  GLOBAL COMMANDS  [/bold cyan]",
                        border_style="cyan", padding=(0, 2)))
    console.print()
    console.print("  [bold green]Select option >[/bold green]  "
                  "[dim]enter 1-11 to enter a planet[/dim]")
    console.print()


# ─── Planet sub-shell ─────────────────────────────────────────────────────────

def print_planet_menu(planet: tuple) -> None:
    """Show the planet's commands, numbered for quick selection."""
    num, sym, name, desc, commands, color = planet
    console.print()
    half = (len(commands) + 1) // 2
    ctable = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    ctable.add_column("Left",  no_wrap=True)
    ctable.add_column("Right", no_wrap=True)
    left_c  = commands[:half]
    right_c = commands[half:]
    for i in range(half):
        def _crow(cmd_list, j):
            if j >= len(cmd_list):
                return ""
            cmd_name, help_text, req_args, opt_args = cmd_list[j]
            idx_in_all = commands.index(cmd_list[j]) + 1
            req_str = " ".join(f"<{a[0]}>" for a in req_args)
            return (
                f"[bold {color}]{idx_in_all:>2}.[/bold {color}]  "
                f"[bold {color}]{name} {cmd_name}[/bold {color}] "
                f"[dim]{req_str}[/dim]"
                f"  [dim italic]{help_text}[/dim italic]"
            )
        ctable.add_row(_crow(left_c, i), _crow(right_c, i))

    console.print(Panel(
        ctable,
        title=f"[bold {color}]  {sym} {name.upper()} — {desc}  [/bold {color}]",
        border_style=color,
        padding=(1, 2),
    ))
    console.print(
        f"  [bold {color}]Enter number to run command,[/bold {color}] "
        f"or type [bold {color}]{name} <command> [args][/bold {color}] directly."
    )
    console.print(
        f"  [dim]Type [bold]b[/bold] or [bold]0[/bold] to go back to the main menu.[/dim]"
    )
    console.print()


def _ask_args(planet_name: str, cmd_name: str, cmd_def: tuple, color: str) -> Optional[List[str]]:
    """
    Interactively ask for required args + optional args, return CLI parts list.
    Returns None if user aborted (empty required arg).
    """
    _, _, _, req_args, opt_args = (None, None, None, cmd_def[2], cmd_def[3])
    parts = [planet_name, cmd_name]

    console.print()
    console.print(f"  [{color}]▶[/{color}] [bold]{planet_name} {cmd_name}[/bold]  [dim]{cmd_def[1]}[/dim]")
    console.print()

    # Required positional args
    for arg_name, prompt_text in req_args:
        # Handle flag-style required args (--n, --e, etc.)
        if arg_name.startswith("--"):
            val = _safe_input(f"  [{color}]?[/{color}] {prompt_text}: ", color)
            if val is None:
                return None
            if val.strip():
                parts += [arg_name, val.strip()]
        else:
            val = _safe_input(f"  [{color}]?[/{color}] {prompt_text}: ", color)
            if val is None:
                return None
            val = val.strip()
            if not val:
                console.print(f"  [red]✗ '{arg_name}' is required. Cancelled.[/red]\n")
                return None
            parts.append(val)

    # Optional args — only ask if there are any, and offer skip
    if opt_args:
        console.print(
            f"  [dim]Optional flags below — press Enter to skip each one[/dim]"
        )
        for flag, prompt_text, default in opt_args:
            hint = f" [dim](default: {default})[/dim]" if default else " [dim](press Enter to skip)[/dim]"
            val = _safe_input(f"  [{color}]?[/{color}] {prompt_text}{hint}: ", color)
            if val is None:
                break
            val = val.strip()
            if not val:
                continue
            # Handle boolean-style flags
            if default in ("y", "n"):
                if val.lower() in ("y", "yes", "1", "true"):
                    parts.append(flag)
            else:
                parts += [flag, val]

    console.print()
    return parts


def _safe_input(prompt_str: str, color: str = "cyan") -> Optional[str]:
    """Show a colored prompt and read input. Returns None on Ctrl+C."""
    try:
        # Strip rich markup for actual input() call
        import re
        clean = re.sub(r'\[.*?\]', '', prompt_str)
        console.print(prompt_str, end="")
        return input("")
    except (KeyboardInterrupt, EOFError):
        console.print()
        return None


# ─── Command runner ───────────────────────────────────────────────────────────

def _run_parts(parts: List[str]) -> None:
    """Execute a list of CLI argument parts through the Click CLI."""
    from milkyway.cli.main import cli

    planet = parts[0] if parts else ""
    color  = PLANET_COLORS.get(planet, "cyan")

    # Echo the full command being run
    cmd_display = " ".join(shlex.quote(p) for p in parts)
    console.print(f"\n  [dim]$ mw {cmd_display}[/dim]")
    console.print(f"  [{color}]▶ Task:[/{color}] [bold]{' '.join(parts[:3])}{'…' if len(parts) > 3 else ''}[/bold]")
    console.print(f"  : [dim]Running...[/dim]")

    try:
        ctx = cli.make_context("mw", parts, resilient_parsing=False)
        console.print(f"  [bold green]✓[/bold green] Executing [bold green]{planet}[/bold green] [bold green]✓[/bold green]")
        with ctx:
            cli.invoke(ctx)
        console.print(f"\n  [bold green]✓ Completed[/bold green] [dim]| {' '.join(parts[:4])}[/dim]\n")
    except SystemExit as e:
        if e.code and e.code != 0:
            console.print(f"\n  [bold red]✗ Failed[/bold red] [dim]| exit code {e.code}[/dim]\n")
    except Exception as exc:
        console.print(f"\n  [bold red]✗[/bold red] [red]{exc}[/red]\n")


def _run_line(line: str) -> None:
    """Parse a full command string and run it."""
    from milkyway.cli.main import cli
    try:
        parts = shlex.split(line)
    except ValueError as e:
        console.print(f"\n  [red]Parse error: {e}[/red]\n")
        return
    _run_parts(parts)


# ─── Planet sub-shell REPL ────────────────────────────────────────────────────

def planet_shell(planet: tuple, db: SaturnDB, cm: ChallengeManager) -> None:
    """
    Enter a planet's sub-shell.
    User types:
      1-N        → pick that planet command, args prompted interactively
      cmd [args] → run planet command directly
      b / 0      → back to main menu
      help       → show this planet's commands
    """
    num, sym, name, desc, commands, color = planet

    # Update tab completion to include planet commands without planet prefix
    _update_planet_completions(name, commands)

    print_planet_menu(planet)

    while True:
        prompt = _build_prompt(cm, planet=name)

        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            console.print()
            console.print(f"  [dim](Ctrl+C — type b to go back, 0 to exit)[/dim]\n")
            continue

        line = line.strip()
        if not line:
            continue

        lower = line.lower()

        # Exit
        if lower in ("exit", "quit", "q"):
            console.print("\n  [bold cyan][*] Exiting MilkyWay. Clear skies! 🌌[/bold cyan]\n")
            sys.exit(0)

        # Back to main menu
        if lower in ("b", "back", "0", "m", "menu", "main"):
            console.print(f"  [dim]↩ Back to main menu[/dim]\n")
            return

        # Help — re-show this planet's command list
        if lower in ("h", "help", "?", "commands", "cmds"):
            print_planet_menu(planet)
            continue

        # Numbered command shortcut: "1", "2", ... run that planet's command
        if lower.isdigit():
            idx = int(lower) - 1
            if 0 <= idx < len(commands):
                cmd_def = commands[idx]
                args = _ask_args(name, cmd_def[0], cmd_def, color)
                if args is not None:
                    _run_parts(args)
            else:
                console.print(
                    f"  [red]✗ No command #{lower}. Choose 1–{len(commands)}. "
                    f"Type 'h' to see commands.[/red]\n"
                )
            continue

        # Direct command: "fuzz http://..." or "mercury fuzz http://..."
        try:
            parts = shlex.split(line)
        except ValueError as e:
            console.print(f"  [red]Parse error: {e}[/red]\n")
            continue

        # If user typed the planet name first, keep it; otherwise prepend it
        if parts and parts[0].lower() == name:
            pass  # already has planet prefix
        elif parts and parts[0].lower() in [c[0] for c in commands]:
            parts = [name] + parts  # prepend planet
        else:
            # Treat as full milkyway command (global commands like 'saturn log')
            _run_parts(parts)
            continue

        _run_parts(parts)


# ─── Help & examples ──────────────────────────────────────────────────────────

def print_help() -> None:
    console.print()
    console.rule(f"[bold cyan] MilkyWay v{__version__} — Full Command Reference [/bold cyan]")
    console.print()
    for num, sym, name, desc, commands, color in PLANETS:
        console.print(
            f"  [{color}]{sym}[/{color}] [bold {color}]{name.upper():<12}[/bold {color}]  [dim]{desc}[/dim]"
        )
        cmd_names = " · ".join(c[0] for c in commands)
        console.print(f"    [{color}]{cmd_names}[/{color}]")
        console.print()
    console.rule("[bold cyan] Global Commands [/bold cyan]")
    console.print()
    for k, cmd, desc in GLOBAL_MENU:
        console.print(f"  [bold green]mw>[/bold green] [white]{cmd:<32}[/white]  [dim]{desc}[/dim]")
    console.print()


def print_examples() -> None:
    console.print()
    console.rule("[bold cyan] Usage Examples [/bold cyan]")
    console.print()
    half = (len(EXAMPLES) + 1) // 2
    etable = Table(show_header=False, box=None, pad_edge=False, padding=(0, 1))
    etable.add_column("Left",  no_wrap=True)
    etable.add_column("Right", no_wrap=True)
    left_e  = EXAMPLES[:half]
    right_e = EXAMPLES[half:]
    for i in range(half):
        def _erow(ex):
            planet, cmd, desc = ex
            col = PLANET_COLORS.get(planet, "cyan")
            return (
                f"[bold green]mw>[/bold green] "
                f"[bold {col}]{planet}[/bold {col}] {cmd}  "
                f"[dim]{desc}[/dim]"
            )
        l = _erow(left_e[i])  if i < len(left_e)  else ""
        r = _erow(right_e[i]) if i < len(right_e) else ""
        etable.add_row(l, r)
    console.print(Panel(etable,
                        title="[bold cyan]  EXAMPLES  [/bold cyan]",
                        border_style="cyan", padding=(1, 2)))
    console.print()


def print_tools_status() -> None:
    from milkyway.core.runner import check_tool
    TOOLS = [
        ("curl","mercury","cyan"),("ffuf","mercury","cyan"),("sqlmap","mercury","cyan"),
        ("hashcat","venus","magenta"),("john","venus","magenta"),("openssl","venus","magenta"),
        ("binwalk","earth","green"),("strings","earth","green"),("file","earth","green"),
        ("exiftool","earth","green"),("tshark","earth","green"),("steghide","earth","green"),
        ("objdump","mars","red"),("readelf","mars","red"),("nm","mars","red"),
        ("strace","mars","red"),("ltrace","mars","red"),("r2","mars","red"),
        ("gdb","jupiter","yellow"),("checksec","jupiter","yellow"),("ROPgadget","jupiter","yellow"),
        ("apktool","uranus","bright_blue"),("jadx","uranus","bright_blue"),("adb","uranus","bright_blue"),
        ("nmap","vulcan","bright_red"),("whois","vulcan","bright_red"),("dig","vulcan","bright_red"),
        ("hydra","titan","bright_yellow"),("crunch","titan","bright_yellow"),
        ("aws","neptune","blue"),
    ]
    half  = (len(TOOLS) + 1) // 2
    table = Table(show_header=True, header_style="bold cyan",
                  border_style="dim cyan", show_lines=False)
    for _ in range(2):
        table.add_column("Tool",   style="white", width=12)
        table.add_column("Planet", width=10)
        table.add_column("Status", width=12)
    left_t = TOOLS[:half]; right_t = TOOLS[half:]
    found = 0
    for i in range(half):
        row = []
        for side in [left_t, right_t]:
            if i < len(side):
                tool, planet, color = side[i]
                ok = check_tool(tool)
                if ok: found += 1
                status = "[bold green]✓  found[/bold green]" if ok else "[red]✗  missing[/red]"
                row += [tool, f"[{color}]{planet}[/{color}]", status]
            else:
                row += ["", "", ""]
        table.add_row(*row)
    console.print()
    console.print(Panel(table,
                        title="[bold cyan]  Tool Availability  [/bold cyan]",
                        border_style="cyan", padding=(1, 1)))
    console.print(
        f"\n  [dim]{found}/{len(TOOLS)} tools installed. "
        "All commands have pure-Python fallbacks — zero extra setup needed.[/dim]\n"
    )


# ─── Tab completion ───────────────────────────────────────────────────────────

_ALL_COMPLETIONS: List[str] = []


def _build_completions() -> List[str]:
    comps = []
    for _, _, name, _, commands, _ in PLANETS:
        comps.append(name)
        for cmd_name, *_ in commands:
            comps.append(f"{name} {cmd_name}")
            comps.append(cmd_name)          # bare command works inside planet shell
    comps += [
        "help", "examples", "tools", "tui", "exit", "quit",
        "back", "b", "menu", "0",
        "challenge new", "challenge list", "challenge note", "challenge cd",
        "session start", "session end",
        "config show", "config set", "config get",
    ]
    return sorted(set(comps))


def _update_planet_completions(planet_name: str, commands: list) -> None:
    """Hot-update completions with bare command names when inside a planet."""
    global _ALL_COMPLETIONS
    base = _build_completions()
    extras = [c[0] for c in commands] + [f"{i+1}" for i in range(len(commands))]
    _ALL_COMPLETIONS = sorted(set(base + extras))


def _completer(text: str, state: int) -> Optional[str]:
    global _ALL_COMPLETIONS
    if not _ALL_COMPLETIONS:
        _ALL_COMPLETIONS = _build_completions()
    opts = [c for c in _ALL_COMPLETIONS if c.startswith(text)]
    return opts[state] if state < len(opts) else None


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


# ─── Prompt builder ───────────────────────────────────────────────────────────

def _build_prompt(cm: ChallengeManager, planet: str = "") -> str:
    GREEN  = "\001\033[1;32m\002"
    CYAN   = "\001\033[1;36m\002"
    YELLOW = "\001\033[1;33m\002"
    RESET  = "\001\033[0m\002"

    ch = cm.get_current_challenge()
    ch_str = f"{CYAN}[{ch.name}]{RESET} " if ch else ""

    if planet:
        color_code = {
            "cyan": "\001\033[0;36m\002", "magenta": "\001\033[0;35m\002",
            "green": "\001\033[0;32m\002", "red": "\001\033[0;31m\002",
            "yellow": "\001\033[0;33m\002", "blue": "\001\033[0;34m\002",
            "bright_blue": "\001\033[0;94m\002", "bright_red": "\001\033[0;91m\002",
            "bright_yellow": "\001\033[0;93m\002", "purple": "\001\033[0;35m\002",
            "bright_cyan": "\001\033[0;96m\002",
        }.get(PLANET_COLORS.get(planet, "cyan"), "\001\033[0;36m\002")
        planet_str = f"{color_code}[{planet}]{RESET} "
    else:
        planet_str = ""

    return f"{ch_str}{planet_str}{GREEN}mw>{RESET} "


# ─── Main shell REPL ──────────────────────────────────────────────────────────

def run_shell() -> None:
    """Main interactive shell. Enters planet sub-shells on number selection."""
    db = SaturnDB()
    cm = ChallengeManager(db)
    _setup_readline()
    print_banner()
    print_menu()

    LETTER_MAP = {
        "a": "challenge new", "b_global": "challenge list",
        "c": "session start",  "d": "saturn status",
        "e": "tools",          "f": "config show",
    }

    while True:
        try:
            line = input(_build_prompt(cm))
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n  [bold cyan][*] Use 'exit' or '0' to quit MilkyWay.[/bold cyan]\n")
            continue

        line = line.strip()
        if not line:
            continue

        lower = line.lower()

        # Exit
        if lower in ("exit", "quit", "q", "0", "99"):
            console.print("\n  [bold cyan][*] Exiting MilkyWay. Clear skies! 🌌[/bold cyan]\n")
            break

        # Planet selection by number (1–11) → enter planet sub-shell
        if lower.isdigit():
            idx = int(lower) - 1
            if 0 <= idx < len(PLANETS):
                planet_shell(PLANETS[idx], db, cm)
                # Back from planet sub-shell → reprint main menu
                print_menu()
            else:
                console.print(f"  [red]✗ No planet #{lower}. Choose 1–{len(PLANETS)}.[/red]\n")
            continue

        # Planet selection by name (e.g. "mercury") → enter sub-shell
        if lower in PLANET_BY_NAME:
            planet_shell(PLANET_BY_NAME[lower], db, cm)
            print_menu()
            continue

        # Global shortcuts
        if lower == "h" or lower in ("help", "?", "menu"):
            print_help(); continue
        if lower in ("x", "examples", "ex"):
            print_examples(); continue
        if lower in ("e", "tools"):
            print_tools_status(); continue
        if lower == "tui":
            from milkyway.tui.app import launch_tui
            launch_tui(); continue

        # Letter shortcuts → expand to command then run
        if lower in ("a", "c", "d", "f"):
            expanded = LETTER_MAP.get(lower, lower)
            console.print(f"  [dim]→ {expanded}[/dim]")
            line = expanded

        # Full command pass-through: "mercury fuzz http://..."
        _run_line(line)
