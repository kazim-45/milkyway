"""
♃ Jupiter — Binary Exploitation Planet
pwntools used when available; pure-Python fallbacks for everything.
"""
from __future__ import annotations

import struct
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
BANNER = "[bold yellow]♃ Jupiter[/bold yellow] [dim]— Binary Exploitation[/dim]"

EXPLOIT_TEMPLATE = '''#!/usr/bin/env python3
"""Exploit for: {name}  |  Binary: {binary}  |  MilkyWay v2"""

from pwn import *

context.binary = "{binary}"
context.arch   = "{arch}"
context.log_level = "info"

HOST, PORT = "{host}", {port}
elf = ELF("{binary}", checksec=False)
# rop  = ROP(elf)
# libc = ELF("libc.so.6")

def conn():
    return remote(HOST, PORT) if args.REMOTE else process("{binary}")

def main():
    r = conn()
    # ── Build payload ──────────────────────────────────
    payload = b""
    # payload  = b"A" * offset
    # payload += p64(elf.sym["win"])
    r.sendline(payload)
    r.interactive()

if __name__ == "__main__":
    main()
'''


class Jupiter(Planet):
    NAME = "jupiter"; SYMBOL = "♃"
    DESCRIPTION = "Binary exploitation — checksec, ROP, cyclic, exploit templates"
    TOOLS = ["gdb","checksec","ROPgadget","ropper"]

    def checksec(self, file_path: str) -> RunResult:
        console.print(Panel(f"[bold yellow]Checksec[/bold yellow] {file_path}", title=BANNER))

        if check_tool("checksec"):
            args = ["checksec", "--file", file_path, "--output", "text"]
            res  = self.runner.run(args)
            console.print(res.stdout)
            self._record("checksec", " ".join(args), {"file": file_path}, res)
            return res

        # Try pwntools
        try:
            from pwn import ELF
            elf = ELF(file_path, checksec=False)
            props = {
                "NX":         elf.nx,
                "PIE":        elf.pie,
                "RELRO":      elf.relro or "None",
                "Canary":     elf.canary,
                "ASLR":       True,  # kernel setting, always note it
                "Fortify":    elf.fortify,
            }
            t = Table(show_header=True, header_style="bold yellow")
            t.add_column("Protection", style="cyan")
            t.add_column("Status")
            for k, v in props.items():
                if v is True:
                    t.add_row(k, "[bold green]Enabled[/bold green]")
                elif v is False:
                    t.add_row(k, "[bold red]Disabled[/bold red]")
                else:
                    t.add_row(k, f"[yellow]{v}[/yellow]")
            console.print(t)
            out = "\n".join(f"{k}: {v}" for k, v in props.items())
            res = RunResult(f"jupiter checksec {file_path}", 0, out, "", 0.0)
            self._record("checksec", f"jupiter checksec {file_path}", {"file": file_path}, res)
            return res
        except ImportError:
            pass

        # Pure-Python ELF header parsing
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)
        raw = path.read_bytes()
        props = {
            "NX":      not (b"GNU_STACK" in raw and b"\x07" in raw[raw.find(b"GNU_STACK"):raw.find(b"GNU_STACK")+40] if b"GNU_STACK" in raw else False),
            "PIE":     len(raw) > 18 and struct.unpack_from("<H", raw, 16)[0] == 3,
            "RELRO":   b"GNU_RELRO" in raw,
            "Canary":  b"__stack_chk_fail" in raw,
            "Fortify": b"_chk\x00" in raw,
        }
        t = Table(show_header=True, header_style="bold yellow")
        t.add_column("Protection", style="cyan")
        t.add_column("Status")
        for k, v in props.items():
            color = "green" if v else "red"
            t.add_row(k, f"[bold {color}]{'Enabled' if v else 'Disabled'}[/bold {color}]")
        console.print(t)
        out = "\n".join(f"{k}: {'on' if v else 'off'}" for k, v in props.items())
        res = RunResult(f"jupiter checksec {file_path}", 0, out, "", 0.0)
        self._record("checksec", f"jupiter checksec {file_path}", {"file": file_path}, res)
        return res

    def rop(self, file_path: str, search: Optional[str] = None) -> RunResult:
        console.print(Panel(f"[bold yellow]ROP Gadgets[/bold yellow] {file_path}", title=BANNER))

        for tool in ("ROPgadget", "ropper"):
            if check_tool(tool):
                if tool == "ROPgadget":
                    args = ["ROPgadget", "--binary", file_path]
                    if search: args += ["--re", search]
                else:
                    args = ["ropper", "-f", file_path]
                    if search: args += ["-s", search]
                res = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
                rid = self._record("rop", " ".join(args), {"file": file_path, "search": search}, res)
                if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
                return res

        # Pure-Python capstone gadget finder
        console.print("[dim]ROPgadget/ropper not found — using built-in gadget scanner[/dim]\n")
        try:
            import capstone as cs
            path = Path(file_path)
            if not path.exists():
                console.print(f"[red]Not found: {file_path}[/red]")
                return RunResult("", 1, "", "", 0.0)
            raw = path.read_bytes()[:16384]  # scan first 16KB
            md  = cs.Csh(cs.CS_ARCH_X86, cs.CS_MODE_64)
            gadgets = []
            # Find ret instructions and work backwards
            import re
            for ret_offset in (m.start() for m in re.finditer(b"\xc3|\xc2..", raw)):
                for back in range(1, 9):
                    if ret_offset - back < 0: continue
                    chunk = raw[ret_offset - back:ret_offset + 1]
                    insns = list(md.disasm(chunk, 0x1000 + ret_offset - back))
                    if insns:
                        asm = " ; ".join(f"{i.mnemonic} {i.op_str}".strip() for i in insns)
                        addr = 0x1000 + ret_offset - back
                        if search is None or search in asm:
                            gadgets.append((addr, asm))
                            if len(gadgets) <= 50:
                                console.print(f"  [dim]0x{addr:08x}:[/dim]  [yellow]{asm}[/yellow]")
            console.print(f"\n[dim]{len(gadgets)} gadgets found (first 50 shown)[/dim]")
            out = "\n".join(f"0x{a:08x}: {g}" for a,g in gadgets)
        except ImportError:
            console.print("[yellow]capstone not installed: pip install capstone[/yellow]")
            console.print("[yellow]ROPgadget not installed: pip install ROPgadget[/yellow]")
            out = ""; res = RunResult("", 1, "", "no tool", 0.0)
        else:
            res = RunResult(f"jupiter rop {file_path}", 0, out, "", 0.0)
        self._record("rop", f"jupiter rop {file_path}", {"file": file_path, "search": search}, res)
        return res

    def template(self, binary: str, name: Optional[str] = None, host: str = "localhost",
                 port: int = 4444, output: Optional[str] = None) -> RunResult:
        # Detect arch
        arch = "amd64"
        path = Path(binary)
        if path.exists():
            raw = path.read_bytes()
            if len(raw) > 20 and raw[:4] == b"\x7fELF":
                mach = struct.unpack_from("<H", raw, 18)[0]
                arch = {0x3e:"amd64",0x28:"arm",0xb7:"aarch64",0x03:"i386"}.get(mach,"amd64")
            elif check_tool("file"):
                r = self.runner.run(["file", binary])
                if "x86-64" in r.stdout: arch = "amd64"
                elif "i386"  in r.stdout: arch = "i386"
                elif "ARM"   in r.stdout: arch = "arm"
                elif "AArch64" in r.stdout: arch = "aarch64"

        cname  = name or path.stem
        code   = EXPLOIT_TEMPLATE.format(name=cname, binary=binary, arch=arch, host=host, port=port)
        outfile= output or f"exploit_{cname}.py"
        Path(outfile).write_text(code)
        Path(outfile).chmod(0o755)

        console.print(Panel(f"[bold yellow]Exploit Template[/bold yellow] generated", title=BANNER))
        console.print(f"[green]✓[/green] Written → [bold]{outfile}[/bold]  (arch={arch})")
        console.print(f"\n[dim]Run local :[/dim]  python3 {outfile}")
        console.print(f"[dim]Run remote:[/dim]  python3 {outfile} REMOTE")
        syn = Syntax(code, "python", theme="monokai")
        console.print(syn)

        res = RunResult(f"jupiter template {binary}", 0, code, "", 0.0)
        self._record("template", f"jupiter template {binary}", {"binary": binary, "arch": arch}, res)
        return res

    def cyclic(self, length: int = 100, find: Optional[str] = None) -> RunResult:
        # Try pwntools first
        try:
            from pwn import cyclic as pwn_cyclic, cyclic_find
            if find:
                offset = cyclic_find(find)
                console.print(Panel(f"[bold yellow]Cyclic Find[/bold yellow]", title=BANNER))
                console.print(f"  '{find}' → offset [bold green]{offset}[/bold green]")
                res = RunResult("jupiter cyclic", 0, str(offset), "", 0.0)
            else:
                pattern = pwn_cyclic(length).decode()
                console.print(Panel(f"[bold yellow]Cyclic Pattern[/bold yellow] (length={length})", title=BANNER))
                console.print(f"[cyan]{pattern}[/cyan]")
                res = RunResult("jupiter cyclic", 0, pattern, "", 0.0)
            self._record("cyclic", f"jupiter cyclic {length}", {"length": length, "find": find}, res)
            return res
        except ImportError:
            pass

        # Pure-Python De Bruijn generator
        def debruijn(k: int, n: int) -> str:
            alpha = "abcdefghijklmnopqrstuvwxyz"[:k]
            a = [0] * k * n; seq = []
            def db(t, p):
                if t > n:
                    if n % p == 0: seq.extend(a[1:p+1])
                else:
                    a[t] = a[t-p]
                    db(t+1, p)
                    for j in range(a[t-p]+1, k):
                        a[t] = j; db(t+1, t)
            db(1, 1)
            return "".join(alpha[i] for i in seq)

        pattern = debruijn(26, 4)[:length]
        console.print(Panel(f"[bold yellow]Cyclic Pattern[/bold yellow] (length={length})", title=BANNER))

        if find:
            if find in pattern:
                offset = pattern.index(find)
                console.print(f"  '{find}' → offset [bold green]{offset}[/bold green]")
                res = RunResult("jupiter cyclic", 0, str(offset), "", 0.0)
            else:
                console.print(f"  [red]'{find}' not found in pattern of length {length}[/red]")
                res = RunResult("", 1, "", "Not found", 0.0)
        else:
            console.print(f"[cyan]{pattern}[/cyan]")
            console.print(f"\n[dim]Length: {len(pattern)} bytes[/dim]")
            res = RunResult("jupiter cyclic", 0, pattern, "", 0.0)

        self._record("cyclic", f"jupiter cyclic {length}", {"length": length, "find": find}, res)
        return res

    def get_commands(self) -> List[click.Command]:
        return []
