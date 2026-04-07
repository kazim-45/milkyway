"""
♂ Mars — Reverse Engineering Planet
Uses capstone for disassembly (pip install capstone) — no objdump required.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()
BANNER = "[bold red]♂ Mars[/bold red] [dim]— Reverse Engineering[/dim]"


def _detect_arch(raw: bytes):
    """Return (arch_str, bits) from ELF header."""
    if len(raw) < 20 or raw[:4] != b"\x7fELF":
        return "x86", 32
    bits  = 64 if raw[4] == 2 else 32
    mach  = struct.unpack_from("<H", raw, 18)[0]
    archs = {0x3e: "x86", 0x28: "arm", 0xb7: "arm64", 0xf3: "riscv",
             0x02: "sparc", 0x08: "mips", 0x14: "powerpc"}
    return archs.get(mach, "x86"), bits


class Mars(Planet):
    NAME = "mars"; SYMBOL = "♂"
    DESCRIPTION = "Reverse Engineering — disassembly, symbols, trace"
    TOOLS = ["objdump","readelf","nm","strace","ltrace","r2"]

    def disassemble(self, file_path: str, section: str = ".text", syntax: str = "intel") -> RunResult:
        console.print(Panel(f"[bold red]Disassembly[/bold red] {file_path}", title=BANNER))

        if check_tool("objdump"):
            args = ["objdump", f"-M{syntax}", "-d", file_path]
            if section: args += ["--section", section]
            res = self.runner.run(args)
            syn = Syntax(res.stdout[:5000], "asm", theme="monokai")
            console.print(syn)
            if len(res.stdout) > 5000: console.print(f"[dim]… truncated[/dim]")
            rid = self._record("disassemble", " ".join(args), {"file": file_path}, res)
            if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
            return res

        # Pure-Python disassembly via capstone
        console.print("[dim]objdump not found — using capstone disassembler[/dim]\n")
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        raw = path.read_bytes()
        arch_name, bits = _detect_arch(raw)

        # Extract .text section from ELF
        code = raw
        if raw[:4] == b"\x7fELF":
            code = self._extract_elf_text(raw) or raw[:4096]

        try:
            import capstone as cs
            arch_map = {
                "x86":    (cs.CS_ARCH_X86, cs.CS_MODE_64 if bits == 64 else cs.CS_MODE_32),
                "arm":    (cs.CS_ARCH_ARM,   cs.CS_MODE_ARM),
                "arm64":  (cs.CS_ARCH_ARM64, cs.CS_MODE_ARM),
                "mips":   (cs.CS_ARCH_MIPS,  cs.CS_MODE_MIPS32),
            }
            arch_cs, mode_cs = arch_map.get(arch_name, (cs.CS_ARCH_X86, cs.CS_MODE_64))
            md = cs.Csh(arch_cs, mode_cs)
            if syntax == "att":
                md.syntax = cs.CS_OPT_SYNTAX_ATT
            lines = []
            for insn in md.disasm(code[:2048], 0x1000):
                lines.append(f"  0x{insn.address:08x}:  {insn.mnemonic:<10} {insn.op_str}")
                console.print(f"  [dim]0x{insn.address:08x}:[/dim]  [bold green]{insn.mnemonic:<10}[/bold green] [white]{insn.op_str}[/white]")
            out = "\n".join(lines)
        except ImportError:
            console.print("[yellow]capstone not installed. Install: pip install capstone[/yellow]")
            console.print("[dim]Showing raw hex instead:[/dim]\n")
            # Fallback: hex dump of code section
            lines = []
            for i in range(0, min(256, len(code)), 16):
                chunk = code[i:i+16]
                hex_p = " ".join(f"{b:02x}" for b in chunk)
                lines.append(f"  0x{i:04x}: {hex_p}")
                console.print(f"  [dim]0x{i:04x}:[/dim] [green]{hex_p}[/green]")
            out = "\n".join(lines)

        res = RunResult(f"mars disassemble {file_path}", 0, out, "", 0.0)
        rid = self._record("disassemble", f"mars disassemble {file_path}", {"file": file_path}, res)
        if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return res

    def _extract_elf_text(self, raw: bytes) -> Optional[bytes]:
        """Extract .text section bytes from ELF."""
        try:
            if raw[4] == 2:  # 64-bit
                e_shoff = struct.unpack_from("<Q", raw, 40)[0]
                e_shentsize = struct.unpack_from("<H", raw, 58)[0]
                e_shnum = struct.unpack_from("<H", raw, 60)[0]
                e_shstrndx = struct.unpack_from("<H", raw, 62)[0]
                # Get string table
                str_sh_off = e_shoff + e_shstrndx * e_shentsize
                str_offset = struct.unpack_from("<Q", raw, str_sh_off + 24)[0]
                str_size   = struct.unpack_from("<Q", raw, str_sh_off + 32)[0]
                strtab = raw[str_offset:str_offset + str_size]
                for i in range(e_shnum):
                    sh_off = e_shoff + i * e_shentsize
                    name_off = struct.unpack_from("<I", raw, sh_off)[0]
                    sec_off  = struct.unpack_from("<Q", raw, sh_off + 24)[0]
                    sec_size = struct.unpack_from("<Q", raw, sh_off + 32)[0]
                    name_end = strtab.find(b"\x00", name_off)
                    name = strtab[name_off:name_end].decode(errors="ignore")
                    if name == ".text":
                        return raw[sec_off:sec_off + sec_size]
        except Exception:
            pass
        return None

    def info(self, file_path: str) -> RunResult:
        console.print(Panel(f"[bold red]Binary Info[/bold red] {file_path}", title=BANNER))
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]Not found: {file_path}[/red]")
            return RunResult("", 1, "", "", 0.0)

        raw = path.read_bytes()
        out_lines = []

        if check_tool("readelf"):
            res = self.runner.run(["readelf", "-h", file_path])
            for line in res.stdout.splitlines()[:20]: console.print(f"  {line}")
            out_lines.append(res.stdout)
        else:
            arch, bits = _detect_arch(raw)
            console.print(f"  [cyan]Architecture:[/cyan]  {arch}  ({bits}-bit)")
            console.print(f"  [cyan]File type:   [/cyan]  {'ELF' if raw[:4]==b'\\x7fELF' else 'Unknown'}")
            console.print(f"  [cyan]Size:        [/cyan]  {len(raw):,} bytes")

        # Security check — pure Python
        console.print("\n[bold]Security properties:[/bold]")
        sec = {
            "NX":     b"GNU_STACK" in raw or (len(raw)>18 and raw[4] in (1,2)),
            "PIE":    len(raw)>18 and struct.unpack_from("<H",raw,16)[0] == 3,
            "RELRO":  b"GNU_RELRO" in raw,
            "Canary": b"__stack_chk_fail" in raw,
            "Fortify":b"_chk" in raw,
        }
        for prop, enabled in sec.items():
            color = "green" if enabled else "red"
            console.print(f"  [{color}]{'✓' if enabled else '✗'}[/{color}]  {prop}:  {'[bold green]Enabled[/bold green]' if enabled else '[bold red]Disabled[/bold red]'}")

        out = "\n".join(out_lines) + "\n" + "\n".join(f"{k}: {'on' if v else 'off'}" for k,v in sec.items())
        res = RunResult(f"mars info {file_path}", 0, out, "", 0.0)
        self._record("info", f"mars info {file_path}", {"file": file_path}, res)
        return res

    def symbols(self, file_path: str, demangle: bool = True) -> RunResult:
        console.print(Panel(f"[bold red]Symbols[/bold red] {file_path}", title=BANNER))

        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]Not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        raw = path.read_bytes()

        # Try nm — if it fails (bad ELF, etc.) fall through to Python scanner
        nm_success = False
        if check_tool("nm"):
            args = ["nm", "-C" if demangle else "", "--defined-only", file_path]
            args = [a for a in args if a]
            res  = self.runner.run(args)
            if res.exit_code == 0 and res.stdout.strip():
                nm_success = True
                for line in res.stdout.splitlines()[:100]:
                    parts = line.split(None, 2)
                    if len(parts) >= 3:
                        addr, stype, name = parts
                        col = "green" if stype in "tT" else "cyan" if stype in "dD" else "yellow"
                        console.print(f"  [{col}]{stype}[/{col}] [dim]{addr}[/dim] {name}")
                    else:
                        console.print(f"  {line}")

        if not nm_success:
            # Pure-Python: extract printable identifier-like strings
            console.print("[dim]Scanning binary for symbol-like strings…[/dim]\n")
            syms = re.findall(rb'[\x20-\x7e]{5,}', raw)
            seen = set()
            shown = 0
            for s in syms:
                s_str = s.decode("ascii", errors="ignore").strip()
                if s_str in seen: continue
                seen.add(s_str)
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{3,}$', s_str) and shown < 80:
                    console.print(f"  [cyan]{s_str}[/cyan]")
                    shown += 1
            res = RunResult(f"mars symbols {file_path}", 0, "\n".join(seen), "", 0.0)

        self._record("symbols", f"mars symbols {file_path}", {"file": file_path}, res)
        return res

    def trace(self, file_path: str, mode: str = "syscall", args_str: str = "") -> RunResult:
        console.print(Panel(f"[bold red]{mode.capitalize()} Trace[/bold red] {file_path}", title=BANNER))
        tool = "strace" if mode == "syscall" else "ltrace"
        if check_tool(tool):
            import shlex as _sl
            cmd_args = [tool, file_path] + (_sl.split(args_str) if args_str else [])
            res = self.runner.run(cmd_args, streaming=True, on_line=lambda l: console.print(f"[dim]{l}[/dim]"))
        else:
            console.print(f"[yellow]{tool} not found. Install: apt install {tool}[/yellow]")
            console.print("[dim]To run the binary manually:[/dim]")
            console.print(f"  [cyan]{tool} {file_path}[/cyan]")
            res = RunResult("", 1, "", f"{tool} not found", 0.0)
        self._record("trace", f"mars trace {file_path}", {"file": file_path, "mode": mode}, res)
        return res

    def r2(self, file_path: str, command: str = "aaa;pdf @main") -> RunResult:
        console.print(Panel(f"[bold red]Radare2[/bold red] — {command}", title=BANNER))
        if check_tool("r2"):
            args = ["r2", "-q", "-c", command, file_path]
            res  = self.runner.run(args)
            syn  = Syntax(res.stdout[:3000], "asm", theme="monokai")
            console.print(syn)
        else:
            console.print("[yellow]radare2 not found. Install: https://rada.re/n/[/yellow]")
            console.print("[dim]Alternative: mw mars disassemble for capstone-based disassembly[/dim]")
            res = RunResult("", 1, "", "r2 not found", 0.0)
        self._record("r2", f"mars r2 {file_path}", {"file": file_path, "cmd": command}, res)
        return res

    def get_commands(self) -> List[click.Command]:
        return []
