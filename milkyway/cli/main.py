"""
MilkyWay CLI — Root entrypoint.
All planets registered as Click command groups.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway import __version__
from milkyway.core.db import SaturnDB
from milkyway.core.challenge_manager import ChallengeManager
from milkyway.core import config

console = Console()

BANNER = f"""[bold cyan]
  ███╗   ███╗██╗██╗     ██╗  ██╗██╗   ██╗██╗    ██╗ █████╗ ██╗   ██╗
  ████╗ ████║██║██║     ██║ ██╔╝╚██╗ ██╔╝██║    ██║██╔══██╗╚██╗ ██╔╝
  ██╔████╔██║██║██║     █████╔╝  ╚████╔╝ ██║ █╗ ██║███████║ ╚████╔╝
  ██║╚██╔╝██║██║██║     ██╔═██╗   ╚██╔╝  ██║███╗██║██╔══██║  ╚██╔╝
  ██║ ╚═╝ ██║██║███████╗██║  ██╗   ██║   ╚███╔███╔╝██║  ██║   ██║
  ╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝
[/bold cyan]
[dim]  v{__version__} · The Galactic CTF Orchestrator · github.com/kazim-45/milkyway[/dim]
[italic dim]  "Not all who wander are lost — some are just fuzzing."[/italic dim]
"""


class MilkyWayContext:
    def __init__(self, verbose: bool, record: bool, challenge: Optional[str], timeout: int):
        self.verbose = verbose
        self.record = record
        self.challenge = challenge
        self.timeout = timeout
        self.db = SaturnDB()
        self.cm = ChallengeManager(self.db)

    def make_planet(self, PlanetClass):
        return PlanetClass(
            db=self.db,
            verbose=self.verbose,
            record=self.record,
            challenge=self.challenge,
            timeout=self.timeout,
        )


pass_ctx = click.make_pass_decorator(MilkyWayContext)


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", message="MilkyWay %(version)s | The Galactic CTF Orchestrator")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Verbose output")
@click.option("--no-record", is_flag=True, default=False, help="Do NOT record run to Saturn")
@click.option("--challenge", "-c", default=None, help="Associate with challenge name")
@click.option("--timeout", "-t", default=300, show_default=True, help="Command timeout (seconds)")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, no_record: bool, challenge: Optional[str], timeout: int):
    """
    MilkyWay - The Galactic CTF Orchestrator

    \b
    Planets:
      mercury   Web Security (fuzz, sql, request, headers, extract)
      venus     Cryptography (identify, hash, crack, encode, decode, xor, factor)
      earth     Forensics (info, carve, strings, hexdump, steg, pcap)
      mars      Reverse Engineering (disassemble, info, symbols, trace, r2)
      jupiter   Binary Exploitation (checksec, rop, template, cyclic)
      neptune   Cloud & Misc (jwt, cloud, url)
      pluto     AI Assistant (suggest, analyze, cheatsheet)
      saturn    Version Control (log, diff, redo, status, export)

    \b
    Examples:
      milkyway mercury fuzz http://target.com/FUZZ
      milkyway venus identify 'd8578edf8458ce06fbc5bb76a58c5ca4'
      milkyway earth strings ./suspicious_file --grep flag
      milkyway pluto suggest "I found a base64 string in the response"
      milkyway saturn log
    """
    ctx.ensure_object(dict)

    if not challenge:
        cfg_file = Path.cwd() / ".milkyway" / "config.json"
        if cfg_file.exists():
            import json
            try:
                cfg_data = json.loads(cfg_file.read_text())
                challenge = cfg_data.get("name")
            except Exception:
                pass

    ctx.obj = MilkyWayContext(
        verbose=verbose,
        record=not no_record,
        challenge=challenge,
        timeout=timeout,
    )

    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        try:
            from milkyway.tui.app import launch_tui
            launch_tui()
        except Exception as e:
            console.print(f"[yellow]TUI: {e}[/yellow]\n")
            console.print(ctx.get_help())


# ═══════════════════════════════════════════════════════════════════════════════
# MERCURY
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("mercury", short_help="Web Security (fuzz, sql, request, headers, extract)")
@pass_ctx
def mercury_group(ctx: MilkyWayContext):
    """Mercury - Web Security. Tools: ffuf, sqlmap, curl, nuclei"""
    pass


@mercury_group.command("fuzz")
@click.argument("url")
@click.option("--wordlist", "-w", default=None)
@click.option("--method", "-X", default="GET")
@click.option("--extensions", "-e", default="")
@click.option("--status-codes", "-mc", default="200,301,302,403")
@click.option("--threads", "-t", default=40, show_default=True)
@click.option("--rate", default=0)
@click.option("--recursion", is_flag=True, default=False)
@click.option("--output", "-o", default=None)
@click.option("--extra", default="")
@pass_ctx
def mercury_fuzz(ctx, url, wordlist, method, extensions, status_codes, threads, rate, recursion, output, extra):
    """Directory/file fuzzing with ffuf.\n\nExample: milkyway mercury fuzz http://target.com/FUZZ"""
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).fuzz(url, wordlist, method, extensions, status_codes, threads, rate, recursion, output, extra)


@mercury_group.command("sql")
@click.argument("url")
@click.option("--data", "-d", default=None)
@click.option("--technique", default="BEUSTQ")
@click.option("--level", default=1, type=int)
@click.option("--risk", default=1, type=int)
@click.option("--dbs", is_flag=True, default=False)
@click.option("--dump", is_flag=True, default=False)
@click.option("--extra", default="")
@pass_ctx
def mercury_sql(ctx, url, data, technique, level, risk, dbs, dump, extra):
    """SQL injection scan with sqlmap.\n\nExample: milkyway mercury sql 'http://target.com/page?id=1'"""
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).sql(url, data, technique, level, risk, dbs, dump, extra=extra)


@mercury_group.command("request")
@click.argument("url")
@click.option("--method", "-X", default="GET")
@click.option("--data", "-d", default=None)
@click.option("--header", "-H", multiple=True)
@click.option("--cookie", "-b", default=None)
@click.option("--no-follow", is_flag=True, default=False)
@click.option("--output", "-o", default=None)
@click.option("--verbose", "-v", is_flag=True, default=False)
@pass_ctx
def mercury_request(ctx, url, method, data, header, cookie, no_follow, output, verbose):
    """Make a crafted HTTP request.\n\nExample: milkyway mercury request http://target.com"""
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).request(url, method, data, list(header), cookie, not no_follow, output, verbose)


@mercury_group.command("headers")
@click.argument("url")
@pass_ctx
def mercury_headers(ctx, url):
    """Inspect HTTP response headers.\n\nExample: milkyway mercury headers http://target.com"""
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).headers(url)


@mercury_group.command("extract")
@click.argument("file")
@click.option("--type", "-t", "extract_type", default="links",
              type=click.Choice(["links", "forms", "cookies", "comments", "emails"]))
@pass_ctx
def mercury_extract(ctx, file, extract_type):
    """Extract info from HTML files.\n\nExample: milkyway mercury extract response.html --type links"""
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).extract(file, extract_type)


@mercury_group.command("scan")
@click.argument("url")
@click.option("--templates", "-t", default=None)
@pass_ctx
def mercury_scan(ctx, url, templates):
    """Vulnerability scan with nuclei.\n\nExample: milkyway mercury scan http://target.com"""
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).scan(url, templates)


# ═══════════════════════════════════════════════════════════════════════════════
# VENUS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("venus", short_help="Cryptography (identify, hash, crack, encode, decode, xor, factor)")
@pass_ctx
def venus_group(ctx: MilkyWayContext):
    """Venus - Cryptography. Tools: openssl, hashcat, john"""
    pass


@venus_group.command("identify")
@click.argument("hash_str")
@pass_ctx
def venus_identify(ctx, hash_str):
    """Identify hash type.\n\nExample: milkyway venus identify 'd8578edf8458ce06fbc5bb76a58c5ca4'"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).identify(hash_str)


@venus_group.command("hash")
@click.argument("text")
@click.option("--algo", "-a", default="md5", show_default=True,
              type=click.Choice(["md5", "sha1", "sha256", "sha512", "sha224", "sha384"]))
@pass_ctx
def venus_hash(ctx, text, algo):
    """Compute hash.\n\nExample: milkyway venus hash 'hello world' --algo sha256"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).hash(text, algo)


@venus_group.command("crack")
@click.argument("hash_str")
@click.option("--wordlist", "-w", default=None)
@click.option("--hash-type", "-m", default=None, type=int)
@pass_ctx
def venus_crack(ctx, hash_str, wordlist, hash_type):
    """Crack hash with hashcat or john.\n\nExample: milkyway venus crack '<hash>'"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).crack(hash_str, wordlist, hash_type)


@venus_group.command("encode")
@click.argument("text")
@click.option("--enc", "-e", default="base64",
              type=click.Choice(["base64", "base32", "hex", "url", "rot13", "binary"]))
@pass_ctx
def venus_encode(ctx, text, enc):
    """Encode text.\n\nExample: milkyway venus encode 'hello' --enc hex"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).encode(text, enc)


@venus_group.command("decode")
@click.argument("text")
@click.option("--enc", "-e", default="base64",
              type=click.Choice(["base64", "base32", "hex", "url", "rot13", "binary"]))
@pass_ctx
def venus_decode(ctx, text, enc):
    """Decode text.\n\nExample: milkyway venus decode 'aGVsbG8=' --enc base64"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).decode(text, enc)


@venus_group.command("xor")
@click.argument("data")
@click.argument("key")
@click.option("--format", "-f", "input_format", default="hex",
              type=click.Choice(["hex", "base64", "text"]))
@pass_ctx
def venus_xor(ctx, data, key, input_format):
    """XOR data with key.\n\nExample: milkyway venus xor 'deadbeef' 'key'"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).xor(data, key, input_format)


@venus_group.command("factor")
@click.argument("number")
@pass_ctx
def venus_factor(ctx, number):
    """Factor a number.\n\nExample: milkyway venus factor 1234567890"""
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).factor(number)


# ═══════════════════════════════════════════════════════════════════════════════
# EARTH
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("earth", short_help="Forensics (info, carve, strings, hexdump, steg, pcap)")
@pass_ctx
def earth_group(ctx: MilkyWayContext):
    """Earth - Forensics. Tools: binwalk, strings, file, exiftool, steghide, tshark"""
    pass


@earth_group.command("info")
@click.argument("file")
@pass_ctx
def earth_info(ctx, file):
    """Full file recon.\n\nExample: milkyway earth info ./image.png"""
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).info(file)


@earth_group.command("carve")
@click.argument("file")
@click.option("--output-dir", "-o", default=None)
@pass_ctx
def earth_carve(ctx, file, output_dir):
    """Extract embedded files with binwalk.\n\nExample: milkyway earth carve ./firmware.bin"""
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).carve(file, output_dir)


@earth_group.command("strings")
@click.argument("file")
@click.option("--min-len", "-n", default=4, show_default=True)
@click.option("--grep", "-g", default=None, help="Grep pattern (regex)")
@pass_ctx
def earth_strings(ctx, file, min_len, grep):
    """Extract strings from file.\n\nExample: milkyway earth strings ./binary --grep flag"""
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).strings(file, min_len, grep)


@earth_group.command("hexdump")
@click.argument("file")
@click.option("--length", "-l", default=256, show_default=True)
@click.option("--offset", "-s", default=0, show_default=True)
@pass_ctx
def earth_hexdump(ctx, file, length, offset):
    """Hex dump of file.\n\nExample: milkyway earth hexdump ./file"""
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).hexdump(file, length, offset)


@earth_group.command("steg")
@click.argument("file")
@click.option("--password", "-p", default=None)
@click.option("--output", "-o", default="steg_output.txt")
@pass_ctx
def earth_steg(ctx, file, password, output):
    """Extract steganographic data.\n\nExample: milkyway earth steg ./image.jpg"""
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).steg_extract(file, password, output)


@earth_group.command("pcap")
@click.argument("file")
@click.option("--filter", "-f", "display_filter", default="")
@click.option("--follow", default=None, type=click.Choice(["tcp", "udp", "http"]))
@pass_ctx
def earth_pcap(ctx, file, display_filter, follow):
    """Analyze PCAP with tshark.\n\nExample: milkyway earth pcap ./capture.pcap -f 'http'"""
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).pcap(file, display_filter, follow)


# ═══════════════════════════════════════════════════════════════════════════════
# MARS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("mars", short_help="Reverse Engineering (disassemble, info, symbols, trace, r2)")
@pass_ctx
def mars_group(ctx: MilkyWayContext):
    """Mars - Reverse Engineering. Tools: objdump, readelf, nm, strace, ltrace, r2"""
    pass


@mars_group.command("disassemble")
@click.argument("file")
@click.option("--section", "-s", default=".text", show_default=True)
@click.option("--syntax", default="intel", type=click.Choice(["intel", "att"]))
@pass_ctx
def mars_disassemble(ctx, file, section, syntax):
    """Disassemble binary with objdump.\n\nExample: milkyway mars disassemble ./binary"""
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).disassemble(file, section, syntax)


@mars_group.command("info")
@click.argument("file")
@pass_ctx
def mars_info(ctx, file):
    """Binary info (type, arch, security).\n\nExample: milkyway mars info ./binary"""
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).info(file)


@mars_group.command("symbols")
@click.argument("file")
@click.option("--no-demangle", is_flag=True, default=False)
@pass_ctx
def mars_symbols(ctx, file, no_demangle):
    """List symbols with nm.\n\nExample: milkyway mars symbols ./binary"""
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).symbols(file, not no_demangle)


@mars_group.command("trace")
@click.argument("file")
@click.option("--mode", "-m", default="syscall", type=click.Choice(["syscall", "library"]))
@click.option("--args", "args_str", default="")
@pass_ctx
def mars_trace(ctx, file, mode, args_str):
    """Trace syscalls or library calls.\n\nExample: milkyway mars trace ./binary --mode library"""
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).trace(file, mode, args_str)


@mars_group.command("r2")
@click.argument("file")
@click.option("--cmd", "-c", default="aaa;pdf @main", show_default=True)
@pass_ctx
def mars_r2(ctx, file, cmd):
    """Run radare2 in batch mode.\n\nExample: milkyway mars r2 ./binary --cmd 'aaa;afl'"""
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).r2(file, cmd)


# ═══════════════════════════════════════════════════════════════════════════════
# JUPITER
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("jupiter", short_help="Binary Exploitation (checksec, rop, template, cyclic)")
@pass_ctx
def jupiter_group(ctx: MilkyWayContext):
    """Jupiter - Binary Exploitation. Tools: checksec, ROPgadget, ropper"""
    pass


@jupiter_group.command("checksec")
@click.argument("file")
@pass_ctx
def jupiter_checksec(ctx, file):
    """Check binary security (NX, PIE, RELRO, canary).\n\nExample: milkyway jupiter checksec ./binary"""
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).checksec(file)


@jupiter_group.command("rop")
@click.argument("file")
@click.option("--search", "-s", default=None)
@pass_ctx
def jupiter_rop(ctx, file, search):
    """Find ROP gadgets.\n\nExample: milkyway jupiter rop ./binary --search 'pop rdi'"""
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).rop(file, search)


@jupiter_group.command("template")
@click.argument("binary")
@click.option("--name", "-n", default=None)
@click.option("--host", "-H", default="localhost", show_default=True)
@click.option("--port", "-p", default=4444, show_default=True)
@click.option("--output", "-o", default=None)
@pass_ctx
def jupiter_template(ctx, binary, name, host, port, output):
    """Generate pwntools exploit template.\n\nExample: milkyway jupiter template ./vuln_binary"""
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).template(binary, name, host, port, output)


@jupiter_group.command("cyclic")
@click.option("--length", "-l", default=100, show_default=True)
@click.option("--find", "-f", default=None)
@pass_ctx
def jupiter_cyclic(ctx, length, find):
    """De Bruijn pattern generator/finder.\n\nExample: milkyway jupiter cyclic --length 200"""
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).cyclic(length, find)


# ═══════════════════════════════════════════════════════════════════════════════
# NEPTUNE
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("neptune", short_help="Cloud & Misc (jwt, cloud, url)")
@pass_ctx
def neptune_group(ctx: MilkyWayContext):
    """Neptune - Cloud & Misc. Tools: aws-cli, kubectl, jwt_tool"""
    pass


@neptune_group.command("jwt")
@click.argument("token")
@click.option("--secret", "-s", default=None)
@click.option("--crack", is_flag=True, default=False)
@pass_ctx
def neptune_jwt(ctx, token, secret, crack):
    """Decode and analyze JWT tokens.\n\nExample: milkyway neptune jwt 'eyJhbGci...'"""
    from milkyway.cli.planets.neptune import Neptune
    ctx.make_planet(Neptune).jwt(token, secret, crack)


@neptune_group.command("cloud")
@click.option("--provider", "-p", default="aws", type=click.Choice(["aws", "k8s"]))
@click.option("--command", "-c", default="whoami", show_default=True)
@pass_ctx
def neptune_cloud(ctx, provider, command):
    """Cloud enumeration.\n\nExample: milkyway neptune cloud --provider aws --command buckets"""
    from milkyway.cli.planets.neptune import Neptune
    ctx.make_planet(Neptune).cloud(provider, command)


@neptune_group.command("url")
@click.argument("target")
@click.option("--action", "-a", default="info", type=click.Choice(["info", "decode", "encode"]))
@pass_ctx
def neptune_url(ctx, target, action):
    """URL analysis.\n\nExample: milkyway neptune url 'http://example.com/page?id=1%27'"""
    from milkyway.cli.planets.neptune import Neptune
    ctx.make_planet(Neptune).url(target, action)


# ═══════════════════════════════════════════════════════════════════════════════
# PLUTO
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("pluto", short_help="AI Assistant (suggest, analyze, cheatsheet)")
@pass_ctx
def pluto_group(ctx: MilkyWayContext):
    """Pluto - AI-powered Tool Suggestions"""
    pass


@pluto_group.command("suggest")
@click.argument("description")
@click.option("--model", "-m", default=None)
@pass_ctx
def pluto_suggest(ctx, description, model):
    """Get tool suggestions for a challenge description.\n\nExample: milkyway pluto suggest 'I found a base64 string'"""
    from milkyway.cli.planets.pluto import Pluto
    ctx.make_planet(Pluto).suggest(description, model)


@pluto_group.command("analyze")
@click.argument("file")
@pass_ctx
def pluto_analyze(ctx, file):
    """Analyze a file and suggest tools.\n\nExample: milkyway pluto analyze ./mystery_file"""
    from milkyway.cli.planets.pluto import Pluto
    ctx.make_planet(Pluto).analyze(file)


@pluto_group.command("cheatsheet")
@click.argument("topic", type=click.Choice(["web", "crypto", "forensics"]))
@pass_ctx
def pluto_cheatsheet(ctx, topic):
    """Show category cheatsheet.\n\nExample: milkyway pluto cheatsheet web"""
    from milkyway.cli.planets.pluto import Pluto
    ctx.make_planet(Pluto).cheatsheet(topic)


# ═══════════════════════════════════════════════════════════════════════════════
# SATURN
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("saturn", short_help="Version Control (log, diff, redo, status, export, inspect)")
@pass_ctx
def saturn_group(ctx: MilkyWayContext):
    """Saturn - Version Control Engine. Every command is recorded."""
    pass


@saturn_group.command("log")
@click.option("--limit", "-n", default=20, show_default=True)
@click.option("--challenge", "-c", default=None)
@click.option("--planet", "-p", default=None)
@click.option("--search", "-s", default=None)
@click.option("--failed", is_flag=True, default=False)
@pass_ctx
def saturn_log(ctx, limit, challenge, planet, search, failed):
    """Show run history.\n\nExample: milkyway saturn log --limit 50 --planet mercury"""
    db = ctx.db
    challenge_id = None
    if challenge:
        ch = db.get_challenge(challenge)
        if ch:
            challenge_id = ch.id

    runs = db.get_runs(limit=limit, challenge_id=challenge_id, planet=planet, search=search)
    if failed:
        runs = [r for r in runs if r.exit_code != 0]

    if not runs:
        console.print("[dim]No runs recorded yet. Start hacking![/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Timestamp", width=19)
    table.add_column("Planet", width=10)
    table.add_column("Action", width=12)
    table.add_column("Command", width=55)
    table.add_column("Exit", width=5)

    for run in runs:
        exit_style = "bold green" if run.exit_code == 0 else "bold red"
        table.add_row(
            str(run.id),
            run.timestamp_str,
            f"[cyan]{run.planet}[/cyan]",
            run.action,
            run.command_line[:55] + ("..." if len(run.command_line) > 55 else ""),
            f"[{exit_style}]{run.exit_code}[/{exit_style}]",
        )

    console.print(f"\n[bold]Saturn Log[/bold] [dim]({len(runs)} runs)[/dim]\n")
    console.print(table)


@saturn_group.command("diff")
@click.argument("run_id1", type=int)
@click.argument("run_id2", type=int)
@pass_ctx
def saturn_diff(ctx, run_id1, run_id2):
    """Compare outputs of two runs.\n\nExample: milkyway saturn diff 12 13"""
    db = ctx.db
    diff = db.diff_runs(run_id1, run_id2)
    run1 = db.get_run(run_id1)
    run2 = db.get_run(run_id2)

    if run1 and run2:
        console.print(f"\n[bold]Saturn Diff[/bold] #{run_id1} vs #{run_id2}")
        console.print(f"  [dim]#{run_id1}:[/dim] {run1.command_line[:60]}")
        console.print(f"  [dim]#{run_id2}:[/dim] {run2.command_line[:60]}\n")

    from rich.syntax import Syntax
    if "No differences" in diff:
        console.print(f"[green]{diff}[/green]")
    else:
        console.print(Syntax(diff, "diff", theme="monokai"))


@saturn_group.command("redo")
@click.argument("run_id", type=int)
@click.option("--dry-run", is_flag=True, default=False)
@pass_ctx
def saturn_redo(ctx, run_id, dry_run):
    """Re-execute a previous run.\n\nExample: milkyway saturn redo 42"""
    import subprocess, time, hashlib
    db = ctx.db
    run = db.get_run(run_id)
    if not run:
        console.print(f"[red]Run #{run_id} not found[/red]")
        return

    console.print(f"\n[bold]Replaying run #{run_id}[/bold]")
    console.print(f"  Command: [dim]{run.command_line}[/dim]")
    console.print(f"  Original: exit={run.exit_code}, hash={run.output_hash or 'N/A'}\n")

    if dry_run:
        console.print("[yellow]--dry-run: not executing[/yellow]")
        return

    start = time.monotonic()
    result = subprocess.run(run.command_line, shell=True, capture_output=True, text=True)
    duration = time.monotonic() - start

    console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr, style="dim red")

    new_hash = hashlib.sha256(result.stdout.encode()).hexdigest()[:16]
    if new_hash == run.output_hash:
        console.print(f"\n[bold green]Output matches original (hash: {new_hash})[/bold green]")
    else:
        console.print(f"\n[yellow]Output differs (was: {run.output_hash}, now: {new_hash})[/yellow]")
    console.print(f"[dim]{duration:.1f}s  exit={result.returncode}[/dim]")


@saturn_group.command("status")
@pass_ctx
def saturn_status(ctx):
    """Show context and statistics.\n\nExample: milkyway saturn status"""
    db = ctx.db
    stats = db.get_stats()

    console.print(Panel(
        f"[bold]Directory:[/bold]  {Path.cwd()}\n"
        f"[bold]Challenge:[/bold]  {ctx.challenge or '[dim]none[/dim]'}\n"
        f"[bold]Session:[/bold]    {db.get_current_session() or '[dim]none[/dim]'}",
        title="[bold cyan]Saturn Status[/bold cyan]",
    ))

    table = Table(show_header=False)
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total runs", str(stats["total_runs"]))
    table.add_row("[green]Successful[/green]", str(stats["successful_runs"]))
    table.add_row("[red]Failed[/red]", str(stats["failed_runs"]))
    table.add_row("Challenges", str(stats["challenges"]))
    console.print(table)

    if stats["by_planet"]:
        console.print("\n[bold]By Planet:[/bold]")
        for planet, count in stats["by_planet"].items():
            bar = "█" * min(count, 30)
            console.print(f"  {planet:<12} {bar} {count}")


@saturn_group.command("inspect")
@click.argument("run_id", type=int)
@pass_ctx
def saturn_inspect(ctx, run_id):
    """Show full details and output of a run.\n\nExample: milkyway saturn inspect 42"""
    db = ctx.db
    run = db.get_run(run_id)
    if not run:
        console.print(f"[red]Run #{run_id} not found[/red]")
        return

    console.print(Panel(
        f"[bold]Planet:[/bold]   [cyan]{run.planet}[/cyan]\n"
        f"[bold]Action:[/bold]   {run.action}\n"
        f"[bold]Time:[/bold]     {run.timestamp_str}\n"
        f"[bold]Exit:[/bold]     {'[green]0 (success)[/green]' if run.success else f'[red]{run.exit_code}[/red]'}\n"
        f"[bold]Hash:[/bold]     [dim]{run.output_hash or 'N/A'}[/dim]\n"
        f"[bold]Command:[/bold]\n  [dim]{run.command_line}[/dim]",
        title=f"[bold cyan]Saturn Run #{run_id}[/bold cyan]",
    ))

    output = db.get_run_output(run)
    if output:
        console.print(f"\n[bold]Output:[/bold] [dim]({len(output)} chars)[/dim]")
        console.print(output[:2000])
        if len(output) > 2000:
            console.print(f"[dim]... full output: {run.output_file}[/dim]")


@saturn_group.command("annotate")
@click.argument("run_id", type=int)
@click.argument("text")
@pass_ctx
def saturn_annotate(ctx, run_id, text):
    """Add note to a run.\n\nExample: milkyway saturn annotate 42 'Found admin at /admin'"""
    db = ctx.db
    if not db.get_run(run_id):
        console.print(f"[red]Run #{run_id} not found[/red]")
        return
    db.annotate_run(run_id, text)
    console.print(f"[green]Annotated run #{run_id}[/green]")


@saturn_group.command("export")
@click.argument("session_id")
@click.option("--output", "-o", default=None)
@pass_ctx
def saturn_export(ctx, session_id, output):
    """Export session as Markdown write-up.\n\nExample: milkyway saturn export abc12345 -o writeup.md"""
    md = ctx.db.export_session(session_id)
    if output:
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"[green]Written to {output}[/green]")
    else:
        from rich.markdown import Markdown as RichMarkdown
        console.print(RichMarkdown(md))


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("challenge", short_help="Challenge management (new, list, note, cd, delete)")
@pass_ctx
def challenge_group(ctx: MilkyWayContext):
    """Challenge Manager - Organize your CTF work"""
    pass


@challenge_group.command("new")
@click.argument("name")
@click.option("--category", "-c", default="misc", show_default=True,
              type=click.Choice(ChallengeManager.CATEGORIES))
@click.option("--url", "-u", default=None)
@click.option("--tag", "-t", multiple=True)
@click.option("--description", "-d", default="")
@pass_ctx
def challenge_new(ctx, name, category, url, tag, description):
    """Create a new challenge workspace.\n\nExample: milkyway challenge new pico_web1 --category web"""
    try:
        ch = ctx.cm.new(name, category, url, list(tag), description)
        console.print(f"\n[bold green]Created challenge '[cyan]{ch.name}[/cyan]'[/bold green]")
        console.print(f"  Category: [cyan]{ch.category}[/cyan]")
        console.print(f"  Folder:   {ch.folder_path}")
        console.print(f"  URL:      {ch.url or 'N/A'}")
        console.print(f"\n  [dim]cd {ch.folder_path}[/dim]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


@challenge_group.command("list")
@click.option("--category", "-c", default=None)
@pass_ctx
def challenge_list(ctx, category):
    """List all challenges.\n\nExample: milkyway challenge list --category web"""
    challenges = ctx.cm.list_all(category=category)
    if not challenges:
        console.print("[dim]No challenges yet.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="bold cyan")
    table.add_column("Category", width=10)
    table.add_column("Created", width=12)
    table.add_column("Tags")
    table.add_column("URL")

    for ch in challenges:
        table.add_row(
            ch.name, ch.category,
            ch.created.strftime("%Y-%m-%d"),
            ", ".join(ch.tags) or "—",
            (ch.url[:50] + "..." if ch.url and len(ch.url) > 50 else ch.url) or "—",
        )

    console.print(f"\n[bold]Challenges[/bold] [dim]({len(challenges)})[/dim]\n")
    console.print(table)


@challenge_group.command("note")
@click.argument("name")
@click.argument("text")
@pass_ctx
def challenge_note(ctx, name, text):
    """Add a note.\n\nExample: milkyway challenge note pico_web1 'Found /admin endpoint'"""
    try:
        ctx.cm.add_note(name, text)
        console.print(f"[green]Note added to '{name}'[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


@challenge_group.command("cd")
@click.argument("name")
@pass_ctx
def challenge_cd(ctx, name):
    """Print challenge folder path.\n\nExample: cd $(milkyway challenge cd pico_web1)"""
    path = ctx.cm.cd_path(name)
    if path:
        click.echo(path)
    else:
        console.print(f"[red]Challenge '{name}' not found[/red]", err=True)
        sys.exit(1)


@challenge_group.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, default=False)
@pass_ctx
def challenge_delete(ctx, name, yes):
    """Delete a challenge.\n\nExample: milkyway challenge delete old_challenge --yes"""
    ch = ctx.cm.get(name)
    if not ch:
        console.print(f"[red]Challenge '{name}' not found[/red]")
        return
    if not yes and not click.confirm(f"Delete '{name}' at {ch.folder_path}?"):
        console.print("[dim]Aborted.[/dim]")
        return
    if ctx.cm.delete(name, confirm=True):
        console.print(f"[green]Deleted '{name}'[/green]")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG & TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group("config", short_help="Configuration management")
@pass_ctx
def config_group(ctx: MilkyWayContext):
    """MilkyWay configuration."""
    pass


@config_group.command("show")
@pass_ctx
def config_show(ctx):
    """Show current config."""
    import yaml
    console.print(Panel(yaml.dump(config.all_config(), default_flow_style=False),
                       title="[bold]MilkyWay Config[/bold]"))


@config_group.command("set")
@click.argument("key")
@click.argument("value")
@pass_ctx
def config_set(ctx, key, value):
    """Set a config value.\n\nExample: milkyway config set pluto.backend ollama"""
    config.set_key(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")


@cli.command("tools")
@pass_ctx
def tools_check(ctx):
    """Check availability of all wrapped tools."""
    from milkyway.cli.planets.mercury import Mercury
    from milkyway.cli.planets.venus import Venus
    from milkyway.cli.planets.earth import Earth
    from milkyway.cli.planets.mars import Mars
    from milkyway.cli.planets.jupiter import Jupiter
    from milkyway.cli.planets.neptune import Neptune
    from milkyway.core.runner import check_tool

    planets = [
        ("Mercury (Web)", Mercury.TOOLS),
        ("Venus (Crypto)", Venus.TOOLS),
        ("Earth (Forensics)", Earth.TOOLS),
        ("Mars (Rev)", Mars.TOOLS),
        ("Jupiter (Pwn)", Jupiter.TOOLS),
        ("Neptune (Cloud)", Neptune.TOOLS),
    ]

    console.print("\n[bold]Tool Availability[/bold]\n")
    total_found = total_tools = 0

    for planet_name, tools in planets:
        console.print(f"[bold]{planet_name}[/bold]")
        for tool in tools:
            found = check_tool(tool)
            total_tools += 1
            total_found += found
            status = "[green]found[/green]" if found else "[red]missing[/red]"
            console.print(f"  {tool:<20} {status}")
        console.print()

    console.print(f"[bold]{total_found}/{total_tools} tools available[/bold]")
    if total_found < total_tools:
        console.print("\n[dim]Tip: docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway[/dim]")


if __name__ == "__main__":
    cli()
