"""
MilkyWay Interactive Shell v2.0
Universe logo + ARGUS two-column bordered menu + per-planet colors
"""
from __future__ import annotations
import os, readline, shlex, sys, time
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

PLANET_COLORS = {
    "mercury":"cyan","venus":"magenta","earth":"green","mars":"red",
    "jupiter":"yellow","neptune":"blue","uranus":"bright_blue",
    "vulcan":"bright_red","titan":"bright_yellow","pluto":"purple","saturn":"bright_cyan",
}
console = Console(highlight=False)

# Universe ASCII logo - pure ASCII, terminal safe
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
    ("[ === ]","The Galactic CTF Orchestrator","[ === ]"),
    ("[ --- ]",f"Created by  : Kazim  (kazim-45)","[ --- ]"),
    ("[ --- ]",f"Version     : {__version__}","[ --- ]"),
    ("[ --- ]","Codename    : 'NebulaDawn'","[ --- ]"),
    ("[ --- ]","GitHub      : kazim-45/milkyway","[ --- ]"),
    ("[ --- ]","Twitter     : @milkyway_ctf","[ --- ]"),
]

PLANETS = [
    (1,"☿","mercury","Web Security",      ["fuzz","sql","request","headers","extract","scan"],"cyan"),
    (2,"♀","venus",  "Cryptography",      ["identify","hash","crack","encode","decode","xor","factor","rsa"],"magenta"),
    (3,"♁","earth",  "Forensics",         ["info","carve","strings","hexdump","steg","pcap"],"green"),
    (4,"♂","mars",   "Reverse Eng.",      ["disassemble","info","symbols","trace","r2"],"red"),
    (5,"♃","jupiter","Binary Exploit",    ["checksec","rop","template","cyclic"],"yellow"),
    (6,"♆","neptune","Cloud & Misc",      ["jwt","cloud","url"],"blue"),
    (7,"♅","uranus", "Mobile / IoT",      ["decompile","info","permissions","instrument","adb","strings","ssl-bypass"],"bright_blue"),
    (8,"🌋","vulcan", "Network Recon",     ["portscan","quickscan","whois","dns","subdomain","banner"],"bright_red"),
    (9,"🪐","titan",  "Password Attacks",  ["brute","spray","wordlist","cewl","analyze","mutate"],"bright_yellow"),
    (10,"♇","pluto", "AI Assistant",      ["suggest","analyze","cheatsheet"],"purple"),
    (11,"⟳","saturn","Version Control",   ["log","diff","redo","status","annotate","export"],"bright_cyan"),
]

GLOBAL_MENU = [
    ("A","challenge new <n>","Create challenge workspace"),
    ("B","challenge list","List all challenges"),
    ("C","session start <n>","Start a work session"),
    ("D","saturn status","Context & stats"),
    ("E","tools","Tool availability"),
    ("F","config show","Configuration"),
    ("H","help","Full command reference"),
    ("X","examples","Usage examples"),
    ("0","exit","Exit MilkyWay"),
]

EXAMPLES = [
    ("mercury","fuzz http://target.com/FUZZ","Directory brute-force"),
    ("mercury","sql 'http://target.com/page?id=1'","SQLi detection"),
    ("venus","identify '5f4dcc3b5aa765d61d8327deb882cf99'","Hash identification"),
    ("venus","decode 'aGVsbG8=' --enc base64","Base64 decode"),
    ("venus","rsa --n 3233 --e 17 --c 2790","RSA attack"),
    ("earth","strings ./binary --grep flag","Flag hunting"),
    ("earth","carve ./firmware.bin","File carving"),
    ("earth","steg ./image.jpg","Steganography"),
    ("mars","disassemble ./binary","Disassembly"),
    ("jupiter","checksec ./binary","Security mitigations"),
    ("jupiter","cyclic 200 --find 'aaab'","Buffer offset"),
    ("uranus","permissions ./app.apk","APK permissions"),
    ("vulcan","quickscan 10.10.10.10","Fast port scan"),
    ("vulcan","subdomain example.com","Subdomain enum"),
    ("titan","wordlist --charset digits --min 4 --max 4","PIN wordlist"),
    ("titan","mutate names.txt","Password mutation"),
    ("neptune","jwt 'eyJ...'","JWT audit"),
    ("pluto","suggest 'I found a base64 string'","AI suggestion"),
    ("saturn","log --limit 20","Run history"),
    ("saturn","redo 42","Replay run"),
]

def print_banner():
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
    console.print()
    console.print(
        "        [dim]github.com/kazim-45/milkyway  "
        "|  discord.gg/milkyway  |  @milkyway_ctf[/dim]",
        highlight=False,
    )
    console.print()
    console.rule(style="cyan dim")

def _planet_row(p):
    num, sym, name, desc, _, color = p
    return (
        f"[bold {color}]{num:>2}.[/bold {color}]  "
        f"[{color}]{sym}[/{color}] "
        f"[bold {color}]{name.capitalize():<12}[/bold {color}] "
        f"[dim]{desc}[/dim]"
    )

def print_menu():
    console.print()
    half = (len(PLANETS) + 1) // 2
    table = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    table.add_column("Left", no_wrap=True)
    table.add_column("Right", no_wrap=True)
    left_col  = PLANETS[:half]
    right_col = PLANETS[half:]
    for i in range(half):
        l = _planet_row(left_col[i]) if i < len(left_col) else ""
        r = _planet_row(right_col[i]) if i < len(right_col) else ""
        table.add_row(l, r)
    console.print(Panel(table, title="[bold yellow]  PLANETS  [/bold yellow]",
                        border_style="yellow", padding=(1, 2)))

    half_g = (len(GLOBAL_MENU) + 1) // 2
    gtable = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    gtable.add_column("Left",  no_wrap=True)
    gtable.add_column("Right", no_wrap=True)
    left_g  = GLOBAL_MENU[:half_g]
    right_g = GLOBAL_MENU[half_g:]
    for i in range(half_g):
        def grow(g):
            k, cmd, desc = g
            return (f"[bold cyan]{k}.[/bold cyan]  "
                    f"[white]{cmd:<26}[/white] [dim]{desc}[/dim]")
        l = grow(left_g[i]) if i < len(left_g) else ""
        r = grow(right_g[i]) if i < len(right_g) else ""
        gtable.add_row(l, r)
    console.print(Panel(gtable, title="[bold cyan]  GLOBAL  [/bold cyan]",
                        border_style="cyan", padding=(0, 2)))
    console.print()
    console.print("  [bold green]Select option >[/bold green]  "
                  "[dim](number, planet name, or full command)[/dim]")
    console.print()

def print_planet_menu(planet_idx):
    num, sym, name, desc, commands, color = PLANETS[planet_idx]
    console.print()
    half = (len(commands) + 1) // 2
    ctable = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    ctable.add_column("Left",  no_wrap=True)
    ctable.add_column("Right", no_wrap=True)
    left_c  = commands[:half]
    right_c = commands[half:]
    for i in range(half):
        def crow(cmd_list, j):
            if j < len(cmd_list):
                cmd = cmd_list[j]
                idx = commands.index(cmd) + 1
                return (f"[bold {color}]{idx:>2}.[/bold {color}]  "
                        f"[bold {color}]{name} {cmd}[/bold {color}]")
            return ""
        ctable.add_row(crow(left_c, i), crow(right_c, i))
    console.print(Panel(ctable,
                        title=f"[bold {color}]  {sym} {name.upper()} — {desc}  [/bold {color}]",
                        border_style=color, padding=(1, 2)))
    console.print(f"  [bold {color}]b.[/bold {color}]  [bold]back[/bold]  [dim]→ main menu[/dim]\n")

def print_help():
    console.print()
    console.rule(f"[bold cyan] MilkyWay v{__version__} — Full Command Reference [/bold cyan]")
    console.print()
    for num, sym, name, desc, cmds, color in PLANETS:
        console.print(
            f"  [{color}]{sym}[/{color}] [bold {color}]{name.upper():<12}[/bold {color}]  [dim]{desc}[/dim]")
        half = (len(cmds) + 1) // 2
        for i in range(half):
            l = f"[bold green]mw>[/bold green] {name} {cmds[i]}" if i < len(cmds) else ""
            r = f"[bold green]mw>[/bold green] {name} {cmds[i+half]}" if i+half < len(cmds) else ""
            console.print(f"    {l:<52}    {r}")
        console.print()
    console.rule("[bold cyan] Global [/bold cyan]")
    for k, cmd, desc in GLOBAL_MENU:
        console.print(f"  [bold green]mw>[/bold green] [white]{cmd:<32}[/white]  [dim]{desc}[/dim]")
    console.print()

def print_examples():
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
        def erow(ex):
            planet, cmd, desc = ex
            col = PLANET_COLORS.get(planet, "cyan")
            return (f"[bold green]mw>[/bold green] "
                    f"[bold {col}]{planet}[/bold {col}] {cmd}  [dim]{desc}[/dim]")
        l = erow(left_e[i]) if i < len(left_e) else ""
        r = erow(right_e[i]) if i < len(right_e) else ""
        etable.add_row(l, r)
    console.print(Panel(etable, title="[bold cyan]  EXAMPLES  [/bold cyan]",
                        border_style="cyan", padding=(1, 2)))
    console.print()

def print_tools_status():
    from milkyway.core.runner import check_tool
    TOOLS = [
        ("curl","mercury","cyan"),("requests","mercury","cyan"),
        ("ffuf","mercury","cyan"),("sqlmap","mercury","cyan"),
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
    half = (len(TOOLS) + 1) // 2
    table = Table(show_header=True, header_style="bold cyan",
                  border_style="dim cyan", show_lines=False)
    table.add_column("Tool",style="white",width=12); table.add_column("Planet",width=10); table.add_column("Status",width=12)
    table.add_column("Tool",style="white",width=12); table.add_column("Planet",width=10); table.add_column("Status",width=12)
    left_t  = TOOLS[:half]; right_t = TOOLS[half:]
    found = 0
    for i in range(half):
        rows = []
        for side in [left_t, right_t]:
            if i < len(side):
                tool, planet, color = side[i]
                ok = check_tool(tool)
                if ok: found += 1
                status = "[bold green]✓  found[/bold green]" if ok else "[red]✗  missing[/red]"
                rows += [tool, f"[{color}]{planet}[/{color}]", status]
            else:
                rows += ["","",""]
        table.add_row(*rows)
    console.print()
    console.print(Panel(table, title="[bold cyan]  Tool Availability  [/bold cyan]",
                        border_style="cyan", padding=(1, 1)))
    console.print(
        f"\n  [dim]{found}/{len(TOOLS)} tools installed. "
        "Missing tools use built-in Python fallbacks — zero extra setup needed.[/dim]\n"
    )

# ── Tab completion ─────────────────────────────────────────────────────────────
_ALL_COMPLETIONS: List[str] = []
def _build_completions():
    comps = []
    for _,_,name,_,cmds,_ in PLANETS:
        comps.append(name)
        for cmd in cmds: comps.append(f"{name} {cmd}")
    comps += ["help","examples","tools","tui","exit","quit","back","menu",
              "challenge new","challenge list","challenge note","challenge cd",
              "session start","session end","config show","config set","config get"]
    return sorted(set(comps))

def _completer(text, state):
    global _ALL_COMPLETIONS
    if not _ALL_COMPLETIONS: _ALL_COMPLETIONS = _build_completions()
    options = [c for c in _ALL_COMPLETIONS if c.startswith(text)]
    return options[state] if state < len(options) else None

def _setup_readline():
    hist = Path.home() / ".milkyway" / ".history"
    hist.parent.mkdir(parents=True, exist_ok=True)
    try: readline.read_history_file(str(hist))
    except FileNotFoundError: pass
    readline.set_history_length(1000)
    readline.set_completer(_completer)
    readline.parse_and_bind("tab: complete")
    import atexit
    atexit.register(readline.write_history_file, str(hist))

# ── Status lines ──────────────────────────────────────────────────────────────
def _status_task(msg, planet=""):
    color = PLANET_COLORS.get(planet, "cyan")
    console.print(f"\n  [bold {color}]▶ Task:[/bold {color}] {msg}")

def _status_thinking():
    console.print("  : [dim]Thinking...[/dim]")

def _status_running(tool, args_preview=""):
    console.print(f"  [bold green]✓[/bold green] Executing [bold green]{tool}[/bold green] [bold green]✓[/bold green]")
    if args_preview:
        console.print(f"  [bold yellow]⚡[/bold yellow] [dim]{tool} {args_preview}[/dim]")

def _status_complete(msg, success=True):
    icon = "[bold green]✓ Completed[/bold green]" if success else "[bold red]✗ Failed[/bold red]"
    console.print(f"  [bold green]✓[/bold green] {icon} [dim]| {msg}[/dim]\n")

def _status_error(msg):
    console.print(f"\n  [bold red]✗[/bold red] [red]{msg}[/red]\n")

# ── Dispatcher ────────────────────────────────────────────────────────────────
def _dispatch(line, db, cm):
    line = line.strip()
    if not line: return True
    lower = line.lower()
    if lower in ("exit","quit","q","0","99"):
        console.print("\n  [bold cyan][*] Exiting MilkyWay. Clear skies! 🌌[/bold cyan]\n")
        return False
    if lower.isdigit():
        idx = int(lower) - 1
        if 0 <= idx < len(PLANETS): print_planet_menu(idx)
        else: _status_error(f"No planet #{lower}. Choose 1–{len(PLANETS)}.")
        return True
    LETTER = {"a":"challenge new","b":"challenge list","c":"session start",
               "d":"saturn status","e":"tools","f":"config show"}
    if lower in LETTER:
        console.print(f"  [dim]→ {LETTER[lower]}[/dim]")
        line = LETTER[lower]; lower = line.lower()
    if lower in ("help","h","?","menu","m"): print_help(); return True
    if lower in ("examples","x","ex"): print_examples(); return True
    if lower in ("tools",): print_tools_status(); return True
    if lower in ("tui",):
        from milkyway.tui.app import launch_tui; launch_tui(); return True
    if lower in ("back","b"): print_menu(); return True
    _run_cli_command(line, db, cm)
    return True

def _run_cli_command(line, db, cm):
    from milkyway.cli.main import cli
    try: parts = shlex.split(line)
    except ValueError as e: _status_error(f"Parse error: {e}"); return
    if parts and parts[0].isdigit():
        idx = int(parts[0]) - 1
        if 0 <= idx < len(PLANETS): parts[0] = PLANETS[idx][2]
    planet = parts[0] if parts else ""
    _status_task(" ".join(parts[:3]) + ("…" if len(parts) > 3 else ""), planet=planet)
    _status_thinking()
    try:
        ctx = cli.make_context("mw", parts, resilient_parsing=False)
        _status_running(planet or (parts[0] if parts else ""), " ".join(parts[1:3]))
        with ctx: cli.invoke(ctx)
        _status_complete(" ".join(parts[:4]), success=True)
    except SystemExit as e:
        if e.code and e.code != 0: _status_complete(" ".join(parts[:4]), success=False)
    except Exception as exc:
        _status_error(str(exc))

def _build_prompt(cm):
    GREEN="\001\033[1;32m\002"; CYAN="\001\033[1;36m\002"; RESET="\001\033[0m\002"
    ch = cm.get_current_challenge()
    return (f"{CYAN}[{ch.name}]{RESET} {GREEN}mw>{RESET} " if ch else f"{GREEN}mw>{RESET} ")

def run_shell():
    db = SaturnDB(); cm = ChallengeManager(db)
    _setup_readline()
    print_banner()
    print_menu()
    while True:
        try: line = input(_build_prompt(cm))
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n  [bold cyan][*] Use 'exit' or '0' to quit.[/bold cyan]\n"); continue
        if not _dispatch(line, db, cm): break
