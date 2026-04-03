"""
♂ Mars — Reverse Engineering Planet
Wraps: strings, file, objdump, ltrace, strace, radare2, ghidra-headless
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

MARS_BANNER = "[bold red]♂ Mars[/bold red] [dim]— Reverse Engineering[/dim]"


class Mars(Planet):
    NAME = "mars"
    SYMBOL = "♂"
    DESCRIPTION = "Reverse Engineering — disassembly, decompilation, tracing"
    TOOLS = ["objdump", "readelf", "ltrace", "strace", "r2", "ghidra"]

    # ── disassemble ───────────────────────────────────────────────────────────

    def disassemble(self, file_path: str, section: str = ".text", syntax: str = "intel") -> RunResult:
        """Disassemble binary with objdump."""
        if not check_tool("objdump"):
            console.print("[red]objdump not found. Install: binutils[/red]")
            return RunResult("", 1, "", "objdump not found", 0.0)

        args = ["objdump", f"-M{syntax}", "-d", file_path]
        if section:
            args += ["--section", section]

        console.print(Panel(f"[bold red]Disassembly[/bold red] {file_path}", title=MARS_BANNER))
        result = self.runner.run(args)

        # Syntax highlight the output
        if result.stdout:
            syn = Syntax(result.stdout[:4000], "asm", theme="monokai", line_numbers=False)
            console.print(syn)
            if len(result.stdout) > 4000:
                console.print(f"[dim]... truncated ({len(result.stdout):,} chars total)[/dim]")

        rid = self._record("disassemble", " ".join(args), {"file": file_path, "section": section}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── info ──────────────────────────────────────────────────────────────────

    def info(self, file_path: str) -> RunResult:
        """ELF/PE info with readelf/file."""
        console.print(Panel(f"[bold red]Binary Info[/bold red] {file_path}", title=MARS_BANNER))
        all_output = []

        # file
        if check_tool("file"):
            r = self.runner.run(["file", file_path])
            console.print(f"[cyan]Type:[/cyan] {r.stdout.strip()}")
            all_output.append(r.stdout)

        # readelf headers
        if check_tool("readelf"):
            r = self.runner.run(["readelf", "-h", file_path])
            console.print("\n[cyan]ELF Header:[/cyan]")
            for line in r.stdout.splitlines()[:20]:
                console.print(f"  {line}")
            all_output.append(r.stdout)

            # Security features
            r2 = self.runner.run(["readelf", "-d", file_path])
            console.print("\n[cyan]Dynamic section:[/cyan]")
            for line in r2.stdout.splitlines()[:15]:
                console.print(f"  {line}")

        # checksec equivalent
        if check_tool("checksec"):
            r = self.runner.run(["checksec", "--file", file_path])
            console.print("\n[cyan]Security:[/cyan]")
            console.print(r.stdout)
            all_output.append(r.stdout)

        result = RunResult(f"mars info {file_path}", 0, "\n".join(all_output), "", 0.0)
        self._record("info", f"mars info {file_path}", {"file": file_path}, result)
        return result

    # ── symbols ───────────────────────────────────────────────────────────────

    def symbols(self, file_path: str, demangle: bool = True) -> RunResult:
        """List symbols with nm."""
        args = ["nm", "-C" if demangle else "", "--defined-only", file_path]
        args = [a for a in args if a]

        if not check_tool("nm"):
            console.print("[red]nm not found[/red]")
            return RunResult("", 1, "", "", 0.0)

        console.print(Panel(f"[bold red]Symbols[/bold red] {file_path}", title=MARS_BANNER))
        result = self.runner.run(args)

        for line in result.stdout.splitlines()[:100]:
            parts = line.split(None, 2)
            if len(parts) >= 3:
                addr, sym_type, name = parts
                color = "green" if sym_type in "tT" else "cyan" if sym_type in "dD" else "yellow"
                console.print(f"  [{color}]{sym_type}[/{color}] [dim]{addr}[/dim] {name}")
            else:
                console.print(f"  {line}")

        rid = self._record("symbols", " ".join(args), {"file": file_path}, result)
        return result

    # ── trace ─────────────────────────────────────────────────────────────────

    def trace(self, file_path: str, mode: str = "syscall", args_str: str = "") -> RunResult:
        """Trace system calls or library calls."""
        import shlex as _shlex

        if mode == "syscall":
            if not check_tool("strace"):
                console.print("[red]strace not found[/red]")
                return RunResult("", 1, "", "", 0.0)
            cmd_args = ["strace", "-e", "trace=all", file_path]
        else:
            if not check_tool("ltrace"):
                console.print("[red]ltrace not found[/red]")
                return RunResult("", 1, "", "", 0.0)
            cmd_args = ["ltrace", file_path]

        if args_str:
            cmd_args += _shlex.split(args_str)

        console.print(Panel(f"[bold red]{mode.capitalize()} Trace[/bold red] {file_path}", title=MARS_BANNER))
        result = self.runner.run(cmd_args, streaming=True, on_line=lambda l: console.print(f"[dim]{l}[/dim]"))
        rid = self._record("trace", " ".join(cmd_args), {"file": file_path, "mode": mode}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── radare2 ───────────────────────────────────────────────────────────────

    def r2(self, file_path: str, command: str = "aaa;pdf @main") -> RunResult:
        """Run radare2 in batch mode."""
        if not check_tool("r2"):
            console.print("[yellow]radare2 not found. Install: https://rada.re/n/[/yellow]")
            return RunResult("", 1, "", "r2 not found", 0.0)

        args = ["r2", "-q", "-c", command, file_path]
        console.print(Panel(f"[bold red]Radare2[/bold red] — {command}", title=MARS_BANNER))
        result = self.runner.run(args)

        if result.stdout:
            syn = Syntax(result.stdout[:3000], "asm", theme="monokai")
            console.print(syn)

        rid = self._record("r2", " ".join(args), {"file": file_path, "cmd": command}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    def get_commands(self) -> List[click.Command]:
        return []
