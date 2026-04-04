"""
♃ Jupiter — Binary Exploitation Planet
Wraps: pwntools helpers, checksec, gdb automation, ROPgadget
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

JUPITER_BANNER = "[bold yellow]♃ Jupiter[/bold yellow] [dim]— Binary Exploitation[/dim]"


EXPLOIT_TEMPLATE = '''#!/usr/bin/env python3
"""
Exploit for: {name}
Binary:      {binary}
Author:      MilkyWay (kazim-45)
"""

from pwn import *

# ── Context ───────────────────────────────────────────────────────────────────
context.binary = "{binary}"
context.arch = "{arch}"
context.log_level = "info"

# ── Target ────────────────────────────────────────────────────────────────────
HOST = "{host}"
PORT = {port}

elf = ELF("{binary}", checksec=False)
# rop = ROP(elf)                    # Uncomment for ROP chains
# libc = ELF("libc.so.6")          # Uncomment for ret2libc

def conn():
    if args.REMOTE:
        return remote(HOST, PORT)
    return process("{binary}")

def main():
    r = conn()

    # ── Exploit ──────────────────────────────────────────────────────────────
    # TODO: Build your payload here
    payload = b""

    r.sendline(payload)
    r.interactive()

if __name__ == "__main__":
    main()
'''


class Jupiter(Planet):
    NAME = "jupiter"
    SYMBOL = "♃"
    DESCRIPTION = "Binary exploitation — checksec, ROP, exploit templates"
    TOOLS = ["checksec", "gdb", "ROPgadget", "ropper"]

    # ── checksec ──────────────────────────────────────────────────────────────

    def checksec(self, file_path: str) -> RunResult:
        """Check binary security properties."""
        console.print(Panel(f"[bold yellow]Checksec[/bold yellow] {file_path}", title=JUPITER_BANNER))

        if check_tool("checksec"):
            args = ["checksec", "--file", file_path, "--output", "text"]
            result = self.runner.run(args)
            console.print(result.stdout)
        else:
            # Pure Python fallback via readelf
            result = self._checksec_python(file_path)

        self._record("checksec", f"jupiter checksec {file_path}", {"file": file_path}, result)
        return result

    def _checksec_python(self, file_path: str) -> RunResult:
        """Python-based checksec approximation."""
        path = Path(file_path)
        if not path.exists():
            return RunResult("", 1, "", "File not found", 0.0)

        raw = path.read_bytes()
        properties = {}

        # NX bit — check PT_GNU_STACK
        properties["NX"] = b"GNU_STACK" in raw or (raw[0:4] == b"\x7fELF" and self._check_nx(raw))

        # PIE — check ELF type (ET_DYN = 3)
        if len(raw) > 18:
            et = int.from_bytes(raw[16:18], "little")
            properties["PIE"] = et == 3

        # RELRO — check for GNU_RELRO segment
        properties["RELRO"] = b"GNU_RELRO" in raw

        # Stack canary — check __stack_chk_fail
        properties["Canary"] = b"__stack_chk_fail" in raw

        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Protection")
        table.add_column("Status")
        for prop, enabled in properties.items():
            status = "[bold green]Enabled[/bold green]" if enabled else "[bold red]Disabled[/bold red]"
            table.add_row(prop, status)
        console.print(table)

        out = "\n".join(f"{k}: {'Enabled' if v else 'Disabled'}" for k, v in properties.items())
        return RunResult(f"jupiter checksec {file_path}", 0, out, "", 0.0)

    def _check_nx(self, raw: bytes) -> bool:
        # Very basic: look for GNU_STACK flags
        return b"\x06\x00\x00\x00" in raw[:1024]  # PF_RW without PF_X

    # ── rop ───────────────────────────────────────────────────────────────────

    def rop(self, file_path: str, search: Optional[str] = None) -> RunResult:
        """Find ROP gadgets."""
        tool = None
        if check_tool("ROPgadget"):
            tool = "ROPgadget"
        elif check_tool("ropper"):
            tool = "ropper"

        if not tool:
            console.print("[red]Neither ROPgadget nor ropper found.[/red]")
            console.print("[dim]Install: pip install ROPgadget  OR  pip install ropper[/dim]")
            return RunResult("", 1, "", "Tool not found", 0.0)

        console.print(Panel(f"[bold yellow]ROP Gadgets[/bold yellow] {file_path}", title=JUPITER_BANNER))

        if tool == "ROPgadget":
            args = ["ROPgadget", "--binary", file_path]
            if search:
                args += ["--re", search]
        else:
            args = ["ropper", "-f", file_path]
            if search:
                args += ["-s", search]

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("rop", " ".join(args), {"file": file_path, "search": search}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── template ──────────────────────────────────────────────────────────────

    def template(
        self,
        binary: str,
        name: Optional[str] = None,
        host: str = "localhost",
        port: int = 4444,
        output: Optional[str] = None,
    ) -> RunResult:
        """Generate a pwntools exploit template."""
        arch = "amd64"  # Default; could detect from readelf

        # Try to detect arch from binary
        if check_tool("file"):
            r = self.runner.run(["file", binary])
            if "x86-64" in r.stdout or "x86_64" in r.stdout:
                arch = "amd64"
            elif "i386" in r.stdout or "80386" in r.stdout:
                arch = "i386"
            elif "ARM" in r.stdout:
                arch = "arm"
            elif "AArch64" in r.stdout:
                arch = "aarch64"

        challenge_name = name or Path(binary).stem
        code = EXPLOIT_TEMPLATE.format(
            name=challenge_name,
            binary=binary,
            arch=arch,
            host=host,
            port=port,
        )

        outfile = output or f"exploit_{challenge_name}.py"
        Path(outfile).write_text(code, encoding="utf-8")
        Path(outfile).chmod(0o755)

        console.print(Panel(f"[bold yellow]Exploit Template Generated[/bold yellow]", title=JUPITER_BANNER))
        console.print(f"[green]✓[/green] Written to [bold]{outfile}[/bold]")
        console.print(f"[dim]Architecture detected: {arch}[/dim]")
        console.print(f"\n[dim]Edit {outfile} and run:[/dim]")
        console.print(f"  [bold]python3 {outfile}[/bold]          [dim]← local[/dim]")
        console.print(f"  [bold]python3 {outfile} REMOTE[/bold]   [dim]← remote ({host}:{port})[/dim]")

        syn = Syntax(code, "python", theme="monokai")
        console.print(syn)

        result = RunResult(f"jupiter template {binary}", 0, code, "", 0.0)
        self._record("template", f"jupiter template {binary}", {"binary": binary, "arch": arch}, result)
        return result

    # ── cyclic ────────────────────────────────────────────────────────────────

    def cyclic(self, length: int = 100, find: Optional[str] = None) -> RunResult:
        """Generate or search De Bruijn cyclic patterns (like pwntools cyclic)."""
        # De Bruijn sequence generator
        def debruijn(k: int, n: int):
            alphabet = "abcdefghijklmnopqrstuvwxyz"[:k]
            a = [0] * k * n
            sequence = []
            def db(t, p):
                if t > n:
                    if n % p == 0:
                        sequence.extend(a[1:p + 1])
                else:
                    a[t] = a[t - p]
                    db(t + 1, p)
                    for j in range(a[t - p] + 1, k):
                        a[t] = j
                        db(t + 1, t)
            db(1, 1)
            return "".join(alphabet[i] for i in sequence)

        pattern = debruijn(26, 4)[:length]

        console.print(Panel(f"[bold yellow]Cyclic Pattern[/bold yellow]", title=JUPITER_BANNER))

        if find:
            # Find offset of pattern
            if find in pattern:
                offset = pattern.index(find)
                console.print(f"[green]Found '{find}' at offset: {offset}[/green]")
                result = RunResult("", 0, str(offset), "", 0.0)
            else:
                console.print(f"[red]'{find}' not found in pattern of length {length}[/red]")
                result = RunResult("", 1, "", "Not found", 0.0)
        else:
            console.print(f"[cyan]{pattern}[/cyan]")
            console.print(f"\n[dim]Length: {len(pattern)} bytes[/dim]")
            result = RunResult(f"jupiter cyclic {length}", 0, pattern, "", 0.0)

        self._record("cyclic", f"jupiter cyclic {length}", {"length": length, "find": find}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
