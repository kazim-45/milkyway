"""
MilkyWay CLI — Root command group.
Entry points: `milkyway`, `mw`
Planet shorthand: `mw mercury fuzz` OR `mw venus decode` etc.
No args → interactive mw> shell.
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


# ─── Shared context ───────────────────────────────────────────────────────────

class MWContext:
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


pass_ctx = click.make_pass_decorator(MWContext)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"], "max_content_width": 100}


# ─── Root group ───────────────────────────────────────────────────────────────

@click.group(
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS,
    epilog=(
        "\b\n"
        "  Quick start:\n"
        "    mw                                  →  interactive shell (mw> prompt)\n"
        "    mw mercury fuzz http://t.com/FUZZ   →  directory brute-force\n"
        "    mw venus identify '<hash>'          →  identify hash type\n"
        "    mw pluto suggest 'found base64'     →  get AI tool suggestion\n"
        "    mw saturn log                       →  view full run history\n"
    ),
)
@click.version_option(__version__, "-V", "--version",
                      message="MilkyWay %(version)s | The Galactic CTF Orchestrator")
@click.option("--verbose",   "-v", is_flag=True,  help="Verbose output")
@click.option("--no-record",       is_flag=True,  help="Don't record to Saturn")
@click.option("--challenge", "-C", default=None,  help="Associate run with challenge")
@click.option("--timeout",         default=300, show_default=True, help="Tool timeout (s)")
@click.pass_context
def cli(ctx, verbose, no_record, challenge, timeout):
    """🌌  MilkyWay — The Galactic CTF Orchestrator

    \b
    Planets:
      mercury   ☿  Web Security      fuzz · sql · request · headers · extract · scan
      venus     ♀  Cryptography      identify · hash · crack · encode · decode · xor · factor
      earth     ♁  Forensics         info · carve · strings · hexdump · steg · pcap
      mars      ♂  Reverse Eng.      disassemble · info · symbols · trace · r2
      jupiter   ♃  Binary Exploit    checksec · rop · template · cyclic
      neptune   ♆  Cloud & Misc      jwt · cloud · url
      pluto     ♇  AI Assistant      suggest · analyze · cheatsheet
      saturn    🪐  Version Control   log · diff · redo · status · annotate · export
      challenge 🏆  Workspaces        new · list · note · cd · delete

    \b
    Run `mw` with no arguments to enter the interactive mw> shell.
    """
    ctx.ensure_object(dict)
    ctx.obj = MWContext(
        verbose=verbose,
        record=not no_record,
        challenge=challenge,
        timeout=timeout,
    )
    if ctx.invoked_subcommand is None:
        from milkyway.shell import run_shell
        run_shell()


# ══════════════════════════════════════════════════════════════════════════════
#  ☿  MERCURY — Web Security
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="☿  Web Security  (fuzz · sql · request · headers · extract · scan)")
@pass_ctx
def mercury(ctx): """☿  Mercury — Web Security"""  # noqa: E704


@mercury.command("fuzz")
@click.argument("url")
@click.option("--wordlist",   "-w", default=None)
@click.option("--method",     "-X", default="GET")
@click.option("--extensions", "-e", default="",         help="e.g. .php,.html")
@click.option("--status-codes","-sc",default="200,301,302,403", show_default=True)
@click.option("--threads",    "-t", default=40,          show_default=True)
@click.option("--rate",             default=0,           help="Rate limit req/s (0=off)")
@click.option("--recursion",  "-r", is_flag=True)
@click.option("--output",     "-o", default=None,        help="JSON output file")
@click.option("--extra",            default="",          help="Extra ffuf flags")
@pass_ctx
def mercury_fuzz(ctx, url, wordlist, method, extensions, status_codes,
                 threads, rate, recursion, output, extra):
    """Directory/file fuzzing with ffuf.

    \b
    Examples:
      mw> mercury fuzz http://target.com/FUZZ
      mw> mercury fuzz http://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt
      mw> mercury fuzz http://target.com/FUZZ -e .php,.html -t 80
      mw> mercury fuzz http://api.target.com/v1/FUZZ -sc 200,201,401
    """
    from milkyway.cli.planets.mercury import Mercury
    try:
        ctx.make_planet(Mercury).fuzz(
            url, wordlist, method, extensions, status_codes, threads, rate, recursion, output, extra)
    except Exception as e:
        console.print(f"\n  [bold red][!][/bold red] {e}\n"); sys.exit(1)


@mercury.command("sql")
@click.argument("url")
@click.option("--data",      "-d", default=None)
@click.option("--technique",       default="BEUSTQ")
@click.option("--level",           default=1, type=int, show_default=True)
@click.option("--risk",            default=1, type=int, show_default=True)
@click.option("--dbs",             is_flag=True,  help="Enumerate databases")
@click.option("--dump",            is_flag=True,  help="Dump tables")
@click.option("--extra",           default="",    help="Extra sqlmap flags")
@pass_ctx
def mercury_sql(ctx, url, data, technique, level, risk, dbs, dump, extra):
    """SQL injection scanning with sqlmap.

    \b
    Examples:
      mw> mercury sql 'http://target.com/page?id=1'
      mw> mercury sql 'http://target.com/login' --data 'user=admin&pass=test'
      mw> mercury sql 'http://target.com/page?id=1' --dbs
    """
    from milkyway.cli.planets.mercury import Mercury
    try:
        ctx.make_planet(Mercury).sql(url, data, technique, level, risk, dbs, dump, extra_args=extra)
    except Exception as e:
        console.print(f"\n  [bold red][!][/bold red] {e}\n")


@mercury.command("request")
@click.argument("url")
@click.option("--method",     "-X", default="GET")
@click.option("--data",       "-d", default=None)
@click.option("--header",     "-H", "headers", multiple=True)
@click.option("--cookie",     "-b", default=None)
@click.option("--no-redirect",      is_flag=True)
@click.option("--output",     "-o", default=None)
@click.option("--verbose",    "-v", is_flag=True)
@pass_ctx
def mercury_request(ctx, url, method, data, headers, cookie, no_redirect, output, verbose):
    """Craft HTTP requests with curl.

    \b
    Examples:
      mw> mercury request http://target.com
      mw> mercury request http://target.com/api --method POST --data '{"user":"admin"}'
      mw> mercury request http://target.com -H 'Authorization: Bearer TOKEN'
    """
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).request(url, method, data, list(headers), cookie, not no_redirect, output, verbose)


@mercury.command("headers")
@click.argument("url")
@pass_ctx
def mercury_headers(ctx, url):
    """Inspect HTTP response headers.

    \b
    Examples:
      mw> mercury headers http://target.com
    """
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).headers(url)


@mercury.command("extract")
@click.argument("file")
@click.option("--type", "extract_type", default="links",
              type=click.Choice(["links","forms","cookies","comments","emails"]))
@pass_ctx
def mercury_extract(ctx, file, extract_type):
    """Extract data from HTML files.

    \b
    Examples:
      mw> mercury extract response.html --type links
      mw> mercury extract response.html --type comments
    """
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).extract(file, extract_type)


@mercury.command("scan")
@click.argument("url")
@click.option("--templates", "-t", default=None)
@pass_ctx
def mercury_scan(ctx, url, templates):
    """Template-based vulnerability scan with nuclei.

    \b
    Examples:
      mw> mercury scan http://target.com
    """
    from milkyway.cli.planets.mercury import Mercury
    ctx.make_planet(Mercury).scan(url, templates)


# ══════════════════════════════════════════════════════════════════════════════
#  ♀  VENUS — Cryptography
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="♀  Cryptography  (identify · hash · crack · encode · decode · xor · factor)")
@pass_ctx
def venus(ctx): """♀  Venus — Cryptography"""  # noqa: E704


@venus.command("identify")
@click.argument("hash_str")
@pass_ctx
def venus_identify(ctx, hash_str):
    """Identify hash type from a string.

    \b
    Examples:
      mw> venus identify '5f4dcc3b5aa765d61d8327deb882cf99'
      mw> venus identify 'aGVsbG8gd29ybGQ='
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).identify(hash_str)


@venus.command("hash")
@click.argument("text")
@click.option("--algo","-a", default="md5",
              type=click.Choice(["md5","sha1","sha256","sha512","sha224","sha384"]))
@pass_ctx
def venus_hash(ctx, text, algo):
    """Compute hash of text.

    \b
    Examples:
      mw> venus hash 'password123'
      mw> venus hash 'hello' --algo sha256
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).hash(text, algo)


@venus.command("crack")
@click.argument("hash_str")
@click.option("--wordlist","-w", default=None)
@click.option("--type","hash_type", default=None, type=int)
@pass_ctx
def venus_crack(ctx, hash_str, wordlist, hash_type):
    """Crack a hash with hashcat or john.

    \b
    Examples:
      mw> venus crack '5f4dcc3b5aa765d61d8327deb882cf99'
      mw> venus crack '<hash>' -w /usr/share/wordlists/rockyou.txt
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).crack(hash_str, wordlist, hash_type)


@venus.command("encode")
@click.argument("text")
@click.option("--enc","-e", default="base64",
              type=click.Choice(["base64","base32","hex","url","rot13","binary"]))
@pass_ctx
def venus_encode(ctx, text, enc):
    """Encode text.

    \b
    Examples:
      mw> venus encode 'hello world'
      mw> venus encode 'hello' --enc hex
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).encode(text, enc)


@venus.command("decode")
@click.argument("text")
@click.option("--enc","-e", default="base64",
              type=click.Choice(["base64","base32","hex","url","rot13","binary"]))
@pass_ctx
def venus_decode(ctx, text, enc):
    """Decode text.

    \b
    Examples:
      mw> venus decode 'aGVsbG8gd29ybGQ='
      mw> venus decode '68656c6c6f' --enc hex
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).decode(text, enc)


@venus.command("xor")
@click.argument("data")
@click.argument("key")
@click.option("--format","fmt", default="hex", type=click.Choice(["hex","base64","text"]))
@pass_ctx
def venus_xor(ctx, data, key, fmt):
    """XOR data with a key.

    \b
    Examples:
      mw> venus xor '48656c6c6f' 'K'
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).xor(data, key, fmt)


@venus.command("factor")
@click.argument("number")
@pass_ctx
def venus_factor(ctx, number):
    """Factor a number (RSA challenges).

    \b
    Examples:
      mw> venus factor 3233
    """
    from milkyway.cli.planets.venus import Venus
    ctx.make_planet(Venus).factor(number)


# ══════════════════════════════════════════════════════════════════════════════
#  ♁  EARTH — Forensics
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="♁  Forensics  (info · carve · strings · hexdump · steg · pcap)")
@pass_ctx
def earth(ctx): """♁  Earth — Forensics"""  # noqa: E704


@earth.command("info")
@click.argument("file")
@pass_ctx
def earth_info(ctx, file):
    """File type, hashes, EXIF metadata.

    \b
    Examples:
      mw> earth info ./suspicious_file
    """
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).info(file)


@earth.command("carve")
@click.argument("file")
@click.option("--output-dir","-o", default=None)
@pass_ctx
def earth_carve(ctx, file, output_dir):
    """Extract embedded files with binwalk.

    \b
    Examples:
      mw> earth carve ./firmware.bin
    """
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).carve(file, output_dir)


@earth.command("strings")
@click.argument("file")
@click.option("--min-len","-n", default=4, show_default=True)
@click.option("--grep",   "-g", default=None)
@pass_ctx
def earth_strings(ctx, file, min_len, grep):
    """Extract strings (flags are highlighted).

    \b
    Examples:
      mw> earth strings ./binary --grep flag
    """
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).strings(file, min_len, grep)


@earth.command("hexdump")
@click.argument("file")
@click.option("--length","-l", default=256, show_default=True)
@click.option("--offset","-s", default=0,   show_default=True)
@pass_ctx
def earth_hexdump(ctx, file, length, offset):
    """Hex dump of a file.

    \b
    Examples:
      mw> earth hexdump ./file -l 512
    """
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).hexdump(file, length, offset)


@earth.command("steg")
@click.argument("file")
@click.option("--password","-p", default=None)
@click.option("--output",  "-o", default="steg_output.txt")
@pass_ctx
def earth_steg(ctx, file, password, output):
    """Steganography extraction with steghide.

    \b
    Examples:
      mw> earth steg ./image.jpg
      mw> earth steg ./image.jpg --password secret
    """
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).steg_extract(file, password, output)


@earth.command("pcap")
@click.argument("file")
@click.option("--filter","-f","display_filter", default="")
@click.option("--follow",     default=None, type=click.Choice(["tcp","udp","http"]))
@pass_ctx
def earth_pcap(ctx, file, display_filter, follow):
    """Analyse PCAP files with tshark.

    \b
    Examples:
      mw> earth pcap ./capture.pcap -f 'http'
    """
    from milkyway.cli.planets.earth import Earth
    ctx.make_planet(Earth).pcap(file, display_filter, follow)


# ══════════════════════════════════════════════════════════════════════════════
#  ♂  MARS — Reverse Engineering
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="♂  Reverse Engineering  (disassemble · info · symbols · trace · r2)")
@pass_ctx
def mars(ctx): """♂  Mars — Reverse Engineering"""  # noqa: E704


@mars.command("disassemble")
@click.argument("file")
@click.option("--section", default=".text")
@click.option("--syntax",  default="intel", type=click.Choice(["intel","att"]))
@pass_ctx
def mars_disassemble(ctx, file, section, syntax):
    """Disassemble a binary (objdump).

    \b
    Examples:
      mw> mars disassemble ./binary
    """
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).disassemble(file, section, syntax)


@mars.command("info")
@click.argument("file")
@pass_ctx
def mars_info(ctx, file):
    """ELF/PE headers and security flags.

    \b
    Examples:
      mw> mars info ./binary
    """
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).info(file)


@mars.command("symbols")
@click.argument("file")
@click.option("--no-demangle", is_flag=True)
@pass_ctx
def mars_symbols(ctx, file, no_demangle):
    """List symbols in a binary (nm).

    \b
    Examples:
      mw> mars symbols ./binary
    """
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).symbols(file, not no_demangle)


@mars.command("trace")
@click.argument("file")
@click.option("--mode", default="syscall", type=click.Choice(["syscall","library"]))
@click.option("--args","args_str", default="")
@pass_ctx
def mars_trace(ctx, file, mode, args_str):
    """Trace syscalls or library calls.

    \b
    Examples:
      mw> mars trace ./binary --mode library
    """
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).trace(file, mode, args_str)


@mars.command("r2")
@click.argument("file")
@click.option("--cmd", default="aaa;pdf @main")
@pass_ctx
def mars_r2(ctx, file, cmd):
    """Batch radare2.

    \b
    Examples:
      mw> mars r2 ./binary --cmd 'afl'
    """
    from milkyway.cli.planets.mars import Mars
    ctx.make_planet(Mars).r2(file, cmd)


# ══════════════════════════════════════════════════════════════════════════════
#  ♃  JUPITER — Binary Exploitation
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="♃  Binary Exploitation  (checksec · rop · template · cyclic)")
@pass_ctx
def jupiter(ctx): """♃  Jupiter — Binary Exploitation"""  # noqa: E704


@jupiter.command("checksec")
@click.argument("file")
@pass_ctx
def jupiter_checksec(ctx, file):
    """Check binary security mitigations.

    \b
    Examples:
      mw> jupiter checksec ./binary
    """
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).checksec(file)


@jupiter.command("rop")
@click.argument("file")
@click.option("--search","-s", default=None)
@pass_ctx
def jupiter_rop(ctx, file, search):
    """Find ROP gadgets (ROPgadget / ropper).

    \b
    Examples:
      mw> jupiter rop ./binary
      mw> jupiter rop ./binary --search 'pop rdi'
    """
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).rop(file, search)


@jupiter.command("template")
@click.argument("binary")
@click.option("--name",  "-n", default=None)
@click.option("--host",        default="localhost")
@click.option("--port",        default=4444, type=int)
@click.option("--output","-o", default=None)
@pass_ctx
def jupiter_template(ctx, binary, name, host, port, output):
    """Generate pwntools exploit template.

    \b
    Examples:
      mw> jupiter template ./binary --host ctf.io --port 1337
    """
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).template(binary, name, host, port, output)


@jupiter.command("cyclic")
@click.argument("length", type=int, default=100)
@click.option("--find","-f", default=None)
@pass_ctx
def jupiter_cyclic(ctx, length, find):
    """Generate or search De Bruijn cyclic patterns.

    \b
    Examples:
      mw> jupiter cyclic 200
      mw> jupiter cyclic 200 --find 'aaab'
    """
    from milkyway.cli.planets.jupiter import Jupiter
    ctx.make_planet(Jupiter).cyclic(length, find)


# ══════════════════════════════════════════════════════════════════════════════
#  ♆  NEPTUNE — Cloud & Misc
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="♆  Cloud & Misc  (jwt · cloud · url)")
@pass_ctx
def neptune(ctx): """♆  Neptune — Cloud & Misc"""  # noqa: E704


@neptune.command("jwt")
@click.argument("token")
@click.option("--secret","-s", default=None)
@click.option("--crack", "-c", is_flag=True)
@pass_ctx
def neptune_jwt(ctx, token, secret, crack):
    """Decode and audit JWT tokens.

    \b
    Examples:
      mw> neptune jwt 'eyJ...'
    """
    from milkyway.cli.planets.neptune import Neptune
    ctx.make_planet(Neptune).jwt(token, secret, crack)


@neptune.command("cloud")
@click.option("--provider","-p", default="aws", type=click.Choice(["aws","k8s"]))
@click.option("--cmd","command", default="whoami")
@pass_ctx
def neptune_cloud(ctx, provider, command):
    """Cloud enumeration (AWS / Kubernetes).

    \b
    Examples:
      mw> neptune cloud --provider aws --cmd whoami
    """
    from milkyway.cli.planets.neptune import Neptune
    ctx.make_planet(Neptune).cloud(provider, command)


@neptune.command("url")
@click.argument("target")
@click.option("--action","-a", default="info", type=click.Choice(["info","decode","encode"]))
@pass_ctx
def neptune_url(ctx, target, action):
    """URL parse / decode / encode.

    \b
    Examples:
      mw> neptune url 'http://target.com/page?id=1'
      mw> neptune url 'hello%20world' --action decode
    """
    from milkyway.cli.planets.neptune import Neptune
    ctx.make_planet(Neptune).url(target, action)


# ══════════════════════════════════════════════════════════════════════════════
#  ♇  PLUTO — AI Assistant
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="♇  AI Assistant  (suggest · analyze · cheatsheet)")
@pass_ctx
def pluto(ctx): """♇  Pluto — AI Assistant"""  # noqa: E704


@pluto.command("suggest")
@click.argument("description")
@click.option("--model", default=None)
@pass_ctx
def pluto_suggest(ctx, description, model):
    """Get AI-powered tool suggestions.

    \b
    Examples:
      mw> pluto suggest "I found a weird file with no extension"
      mw> pluto suggest "Hash: 5f4dcc3b5aa765d61d8327deb882cf99"
    """
    from milkyway.cli.planets.pluto import Pluto
    ctx.make_planet(Pluto).suggest(description, model)


@pluto.command("analyze")
@click.argument("file")
@pass_ctx
def pluto_analyze(ctx, file):
    """Analyze a file and suggest next steps.

    \b
    Examples:
      mw> pluto analyze ./suspicious_file
    """
    from milkyway.cli.planets.pluto import Pluto
    ctx.make_planet(Pluto).analyze(file)


@pluto.command("cheatsheet")
@click.argument("topic", type=click.Choice(["web","crypto","forensics"]))
@pass_ctx
def pluto_cheatsheet(ctx, topic):
    """Quick reference cheatsheet.

    \b
    Examples:
      mw> pluto cheatsheet web
    """
    from milkyway.cli.planets.pluto import Pluto
    ctx.make_planet(Pluto).cheatsheet(topic)


# ══════════════════════════════════════════════════════════════════════════════
#  🪐  SATURN — Version Control
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="🪐  Version Control  (log · diff · redo · status · annotate · export)")
@pass_ctx
def saturn(ctx): """🪐  Saturn — Version Control"""  # noqa: E704


@saturn.command("log")
@click.option("--limit",    "-n", default=20, show_default=True)
@click.option("--challenge","-C", default=None)
@click.option("--planet",   "-p", default=None)
@click.option("--search",   "-s", default=None)
@click.option("--json","as_json", is_flag=True)
@pass_ctx
def saturn_log(ctx, limit, challenge, planet, search, as_json):
    """Show recent run history.

    \b
    Examples:
      mw> saturn log
      mw> saturn log --limit 50 --planet mercury
      mw> saturn log --challenge pico_web1
    """
    import json as _json

    challenge_id = None
    if challenge:
        ch = ctx.db.get_challenge(challenge)
        if ch:
            challenge_id = ch.id

    runs = ctx.db.get_runs(limit=limit, challenge_id=challenge_id, planet=planet, search=search)

    if as_json:
        console.print(_json.dumps([r.to_dict() for r in runs], indent=2))
        return

    if not runs:
        console.print("\n  [dim][*] No runs yet. Start hacking![/dim]\n")
        return

    table = Table(
        title=f"\n  🪐  Saturn Log  [dim]({len(runs)} runs)[/dim]",
        header_style="bold cyan", border_style="dim cyan", show_lines=False,
    )
    table.add_column("ID",    style="dim",   width=5)
    table.add_column("Time",  style="white", width=19)
    table.add_column("Planet",style="cyan",  width=10)
    table.add_column("Action",               width=13)
    table.add_column("Command")
    table.add_column("Exit",                 width=5)

    for run in runs:
        es = "green" if run.exit_code == 0 else "red"
        cmd = run.command_line[:65] + "…" if len(run.command_line) > 65 else run.command_line
        table.add_row(str(run.id), run.timestamp_str, run.planet, run.action,
                      cmd, f"[{es}]{run.exit_code}[/{es}]")

    console.print(table)
    console.print(f"  [dim]Tip: --limit N · --search '<text>' · --planet <name>[/dim]\n")


@saturn.command("diff")
@click.argument("run_id1", type=int)
@click.argument("run_id2", type=int)
@pass_ctx
def saturn_diff(ctx, run_id1, run_id2):
    """Compare output of two runs.

    \b
    Examples:
      mw> saturn diff 12 13
    """
    result = ctx.db.diff_runs(run_id1, run_id2)
    if result.strip():
        from rich.syntax import Syntax
        console.print(Syntax(result, "diff", theme="monokai"))
    else:
        console.print("\n  [green][*] No differences.[/green]\n")


@saturn.command("redo")
@click.argument("run_id", type=int)
@click.option("--dry-run", is_flag=True)
@pass_ctx
def saturn_redo(ctx, run_id, dry_run):
    """Re-execute a previous run.

    \b
    Examples:
      mw> saturn redo 42
    """
    run = ctx.db.get_run(run_id)
    if not run:
        console.print(f"\n  [red][!] Run #{run_id} not found.[/red]\n"); sys.exit(1)

    console.print(Panel(
        f"[bold]Replaying Run #{run_id}[/bold]\n"
        f"Planet  : {run.planet}\nAction  : {run.action}\n"
        f"Command : [cyan]{run.command_line}[/cyan]",
        title="🪐 Saturn Redo", border_style="cyan",
    ))
    if dry_run:
        console.print("  [yellow][*] Dry run — not executing.[/yellow]\n"); return

    import subprocess
    result = subprocess.run(run.command_line, shell=True, cwd=run.working_dir or None)
    console.print(f"\n  [dim][*] Redo complete (exit={result.returncode})[/dim]\n")


@saturn.command("status")
@pass_ctx
def saturn_status(ctx):
    """Current context, stats, DB path.

    \b
    Examples:
      mw> saturn status
    """
    stats = ctx.db.get_stats()
    ch = ctx.cm.get_current_challenge()
    session = ctx.db.get_current_session()

    table = Table(title="\n  🪐  Saturn Status", show_header=False, border_style="cyan")
    table.add_column("Key",   style="bold cyan", width=22)
    table.add_column("Value")
    table.add_row("Current Challenge", ch.name if ch else "[dim]none[/dim]")
    table.add_row("Active Session",    session or "[dim]none[/dim]")
    table.add_row("Total Runs",        str(stats["total_runs"]))
    table.add_row("Successful",        f"[green]{stats['successful_runs']}[/green]")
    table.add_row("Failed",            f"[red]{stats['failed_runs']}[/red]")
    table.add_row("Challenges",        str(stats["challenges"]))
    table.add_row("DB",                str(ctx.db.db_path))
    if stats["by_planet"]:
        top = list(stats["by_planet"].items())[:4]
        table.add_row("Top Planets", "  ".join(f"{p}({n})" for p, n in top))
    console.print(table); console.print()


@saturn.command("annotate")
@click.argument("run_id", type=int)
@click.argument("text")
@pass_ctx
def saturn_annotate(ctx, run_id, text):
    """Add a note to a run.

    \b
    Examples:
      mw> saturn annotate 42 "Got the flag here!"
    """
    ctx.db.annotate_run(run_id, text)
    console.print(f"\n  [green][+] Annotated run #{run_id}[/green]\n")


@saturn.command("export")
@click.argument("session_id")
@click.option("--output","-o", default=None)
@pass_ctx
def saturn_export(ctx, session_id, output):
    """Export session as markdown write-up.

    \b
    Examples:
      mw> saturn export abc12345 -o writeup.md
    """
    md = ctx.db.export_session(session_id)
    if output:
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"\n  [green][+] Exported to {output}[/green]\n")
    else:
        from rich.markdown import Markdown as RichMD
        console.print(RichMD(md))


@saturn.command("clear")
@click.option("--confirm", is_flag=True)
@pass_ctx
def saturn_clear(ctx, confirm):
    """Clear run history (DESTRUCTIVE).

    \b
    Examples:
      mw> saturn clear --confirm
    """
    if not confirm:
        console.print("\n  [yellow][!] Add --confirm to clear history.[/yellow]\n"); return
    import sqlite3
    with sqlite3.connect(str(ctx.db.db_path)) as conn:
        conn.execute("DELETE FROM runs"); conn.execute("DELETE FROM annotations")
    console.print("\n  [green][+] Saturn log cleared.[/green]\n")


# ══════════════════════════════════════════════════════════════════════════════
#  🏆  CHALLENGE — Workspace Manager
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="🏆  Challenge Manager  (new · list · note · cd · delete)")
@pass_ctx
def challenge(ctx): """🏆  Challenge Manager"""  # noqa: E704


@challenge.command("new")
@click.argument("name")
@click.option("--category","-c", default="misc",
              type=click.Choice(ChallengeManager.CATEGORIES))
@click.option("--url",     "-u", default=None)
@click.option("--tags",    "-t", default="")
@click.option("--description","-d", default="")
@pass_ctx
def challenge_new(ctx, name, category, url, tags, description):
    """Create a challenge workspace.

    \b
    Examples:
      mw> challenge new pico_web1 --category web
      mw> challenge new htb_rev1 -c rev --url https://app.hackthebox.com/...
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        ch = ctx.cm.new(name, category, url, tag_list, description)
        console.print(Panel(
            f"[bold green][+] Challenge created![/bold green]\n\n"
            f"Name     : [bold]{ch.name}[/bold]\n"
            f"Category : [cyan]{ch.category}[/cyan]\n"
            f"Path     : {ch.folder_path}\n"
            f"URL      : {url or 'N/A'}\n\n"
            f"[dim]$ cd {ch.folder_path}[/dim]\n"
            f"[dim]mw> challenge note {name} 'your observations here'[/dim]",
            title="🏆 New Challenge", border_style="green",
        ))
    except ValueError as e:
        console.print(f"\n  [red][!] {e}[/red]\n"); sys.exit(1)


@challenge.command("list")
@click.option("--category","-c", default=None)
@pass_ctx
def challenge_list(ctx, category):
    """List all challenges.

    \b
    Examples:
      mw> challenge list
      mw> challenge list --category web
    """
    challenges = ctx.cm.list_all(category)
    if not challenges:
        console.print("\n  [dim][*] No challenges yet. Use: challenge new <n>[/dim]\n"); return

    table = Table(
        title=f"\n  🏆  Challenges  [dim]({len(challenges)} total)[/dim]",
        header_style="bold yellow", border_style="dim yellow",
    )
    table.add_column("Name",     style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Created",  style="dim")
    table.add_column("Tags")
    table.add_column("Notes")
    for ch in challenges:
        table.add_row(ch.name, ch.category, ch.created.strftime("%Y-%m-%d"),
                      ", ".join(ch.tags) or "—",
                      (ch.notes[:35]+"…") if len(ch.notes) > 35 else ch.notes or "—")
    console.print(table); console.print()


@challenge.command("note")
@click.argument("name")
@click.argument("text")
@pass_ctx
def challenge_note(ctx, name, text):
    """Add a timestamped note to a challenge.

    \b
    Examples:
      mw> challenge note pico_web1 "Found SQL injection at /login"
    """
    try:
        ctx.cm.add_note(name, text)
        console.print(f"\n  [green][+] Note added to '{name}'[/green]\n")
    except ValueError as e:
        console.print(f"\n  [red][!] {e}[/red]\n")


@challenge.command("cd")
@click.argument("name")
@pass_ctx
def challenge_cd(ctx, name):
    """Print path (use: cd $(mw challenge cd <n>))."""
    path = ctx.cm.cd_path(name)
    if path:
        click.echo(path)
    else:
        console.print(f"\n  [red][!] Challenge '{name}' not found.[/red]\n"); sys.exit(1)


@challenge.command("delete")
@click.argument("name")
@click.option("--confirm", is_flag=True)
@pass_ctx
def challenge_delete(ctx, name, confirm):
    """Delete a challenge and its folder.

    \b
    Examples:
      mw> challenge delete pico_web1 --confirm
    """
    if not confirm:
        console.print(f"\n  [yellow][!] Add --confirm to delete '{name}'.[/yellow]\n"); return
    ok = ctx.cm.delete(name, confirm=True)
    if ok:
        console.print(f"\n  [green][+] Challenge '{name}' deleted.[/green]\n")
    else:
        console.print(f"\n  [red][!] Challenge '{name}' not found.[/red]\n")


# ══════════════════════════════════════════════════════════════════════════════
#  ⏱  SESSION
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(short_help="⏱  Session Management  (start · end)")
@pass_ctx
def session(ctx): """⏱  Session Management"""  # noqa: E704


@session.command("start")
@click.argument("name")
@click.option("--challenge","-C", default=None)
@pass_ctx
def session_start(ctx, name, challenge):
    """Start a named work session."""
    cid = None
    if challenge:
        ch = ctx.db.get_challenge(challenge)
        if ch: cid = ch.id
    sid = ctx.db.start_session(name, cid)
    console.print(f"\n  [green][+] Session '[bold]{name}[/bold]' started  (id: {sid})[/green]")
    console.print(f"\n  [dim]export MILKYWAY_SESSION={sid}[/dim]\n")


@session.command("end")
@click.argument("session_id")
@pass_ctx
def session_end(ctx, session_id):
    """End a session."""
    ctx.db.end_session(session_id)
    console.print(f"\n  [green][+] Session {session_id} ended.[/green]\n")


# ══════════════════════════════════════════════════════════════════════════════
#  ⚙  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

@cli.group(name="config", short_help="⚙  Configuration  (show · get · set)")
def config_cmd(): """⚙  Configuration"""  # noqa: E704


@config_cmd.command("show")
def config_show():
    """Show all configuration values."""
    import yaml as _yaml
    from milkyway.core import config as cfg
    from rich.syntax import Syntax
    data = cfg.all_config()
    if data.get("pluto", {}).get("openai_api_key"):
        data["pluto"]["openai_api_key"] = "****"
    console.print(Syntax(_yaml.dump(data, default_flow_style=False), "yaml", theme="monokai"))


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value."""
    from milkyway.core import config as cfg
    cfg.set_key(key, value)
    console.print(f"\n  [green][+] {key} = {value}[/green]\n")


@config_cmd.command("get")
@click.argument("key")
def config_get(key):
    """Get a configuration value."""
    from milkyway.core import config as cfg
    val = cfg.get(key)
    console.print(str(val) if val is not None else "[dim]not set[/dim]")


# ══════════════════════════════════════════════════════════════════════════════
#  STANDALONE COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@cli.command("tools")
@click.option("--install", is_flag=True)
def tools_check(install):
    """Check external tool availability.

    \b
    Examples:
      mw> tools
      mw> tools --install
    """
    from milkyway.core.runner import check_tool

    TOOL_META = [
        ("ffuf",      "mercury",  "go install github.com/ffuf/ffuf@latest"),
        ("sqlmap",    "mercury",  "pip install sqlmap  OR  apt install sqlmap"),
        ("nuclei",    "mercury",  "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"),
        ("curl",      "mercury",  "apt install curl"),
        ("hashcat",   "venus",    "apt install hashcat"),
        ("john",      "venus",    "apt install john"),
        ("openssl",   "venus",    "apt install openssl"),
        ("binwalk",   "earth",    "pip install binwalk  OR  apt install binwalk"),
        ("strings",   "earth",    "apt install binutils"),
        ("file",      "earth",    "pre-installed"),
        ("exiftool",  "earth",    "apt install exiftool"),
        ("tshark",    "earth",    "apt install tshark"),
        ("steghide",  "earth",    "apt install steghide"),
        ("objdump",   "mars",     "apt install binutils"),
        ("readelf",   "mars",     "apt install binutils"),
        ("strace",    "mars",     "apt install strace"),
        ("ltrace",    "mars",     "apt install ltrace"),
        ("r2",        "mars",     "https://rada.re/n/"),
        ("gdb",       "jupiter",  "apt install gdb"),
        ("checksec",  "jupiter",  "apt install checksec"),
        ("ROPgadget", "jupiter",  "pip install ROPgadget"),
        ("ropper",    "jupiter",  "pip install ropper"),
        ("aws",       "neptune",  "pip install awscli"),
    ]

    table = Table(
        title="\n  🛠  Tool Availability",
        header_style="bold cyan", border_style="dim cyan", show_lines=False,
    )
    table.add_column("Tool",   style="white", width=12)
    table.add_column("Planet", style="cyan",  width=10)
    table.add_column("Status",               width=14)
    if install:
        table.add_column("Install")

    found = 0
    for tool, planet, hint in TOOL_META:
        ok = check_tool(tool)
        if ok: found += 1
        status = "[bold green]✓  found[/bold green]" if ok else "[red]✗  missing[/red]"
        row = [tool, planet, status]
        if install:
            row.append(hint if not ok else "")
        table.add_row(*row)

    console.print(table)
    console.print(f"\n  [dim]{found}/{len(TOOL_META)} tools found.[/dim]\n")


@cli.command("tui")
def tui_cmd():
    """Launch the graphical TUI dashboard (Textual)."""
    from milkyway.tui.app import launch_tui
    launch_tui()


if __name__ == "__main__":
    cli()
