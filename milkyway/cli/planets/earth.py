"""
♁ Earth — Forensics Planet
Wraps: binwalk, strings, file, exiftool, steghide, tshark, foremost, xxd
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

EARTH_BANNER = "[bold green]♁ Earth[/bold green] [dim]— Forensics[/dim]"


class Earth(Planet):
    NAME = "earth"
    SYMBOL = "♁"
    DESCRIPTION = "Forensics — file analysis, carving, steganography, PCAP"
    TOOLS = ["binwalk", "strings", "file", "exiftool", "xxd", "tshark", "foremost", "steghide"]

    # ── file info ─────────────────────────────────────────────────────────────

    def info(self, file_path: str) -> RunResult:
        """Run multiple recon tools on a file."""
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        console.print(Panel(f"[bold green]File Info[/bold green] {file_path}", title=EARTH_BANNER))

        all_output = []

        # `file` command
        if check_tool("file"):
            result = self.runner.run(["file", file_path])
            console.print(f"[cyan]File type:[/cyan] {result.stdout.strip()}")
            all_output.append(result.stdout)

        # Size
        size = path.stat().st_size
        console.print(f"[cyan]Size:[/cyan] {size:,} bytes ({size / 1024:.1f} KB)")

        # MD5
        import hashlib
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        console.print(f"[cyan]MD5:[/cyan]    {md5}")
        console.print(f"[cyan]SHA256:[/cyan] {sha256}")

        # Magic bytes (first 16 bytes as hex)
        raw = path.read_bytes()[:16]
        magic = raw.hex(" ")
        console.print(f"[cyan]Magic:[/cyan]  {magic}")

        # exiftool if available
        if check_tool("exiftool"):
            result = self.runner.run(["exiftool", file_path])
            if result.stdout.strip():
                console.print("\n[bold]Metadata (exiftool):[/bold]")
                for line in result.stdout.strip().splitlines()[:20]:
                    console.print(f"  {line}")
            all_output.append(result.stdout)

        combined = "\n".join(all_output)
        result = RunResult(f"earth info {file_path}", 0, combined, "", 0.0)
        self._record("info", f"earth info {file_path}", {"file": file_path}, result)
        return result

    # ── carve ─────────────────────────────────────────────────────────────────

    def carve(self, file_path: str, output_dir: Optional[str] = None) -> RunResult:
        """Extract embedded files with binwalk."""
        if not check_tool("binwalk"):
            console.print("[red]binwalk not found. Install: pip install binwalk OR apt install binwalk[/red]")
            return RunResult("", 1, "", "binwalk not found", 0.0)

        out_dir = output_dir or f"{file_path}_extracted"
        args = ["binwalk", "--extract", "--directory", out_dir, file_path]

        console.print(Panel(f"[bold green]Carving[/bold green] {file_path}", title=EARTH_BANNER))
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("carve", " ".join(args), {"file": file_path, "output_dir": out_dir}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── strings ───────────────────────────────────────────────────────────────

    def strings(
        self, file_path: str, min_len: int = 4, grep: Optional[str] = None
    ) -> RunResult:
        """Extract strings from binary/file."""
        args = ["strings", "-n", str(min_len), file_path]
        console.print(Panel(f"[bold green]Strings[/bold green] {file_path}", title=EARTH_BANNER))

        result = self.runner.run(args)
        lines = result.stdout.splitlines()

        if grep:
            import re
            lines = [l for l in lines if re.search(grep, l, re.IGNORECASE)]
            console.print(f"[dim]Grepping for: {grep} → {len(lines)} matches[/dim]\n")

        for line in lines[:200]:
            # Highlight interesting strings
            if any(kw in line.lower() for kw in ["flag", "ctf", "password", "secret", "key", "token"]):
                console.print(f"[bold yellow]★ {line}[/bold yellow]")
            else:
                console.print(f"  {line}")

        if len(lines) > 200:
            console.print(f"\n[dim]... and {len(lines) - 200} more strings[/dim]")

        rid = self._record("strings", " ".join(args), {"file": file_path, "min_len": min_len, "grep": grep}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── hex dump ──────────────────────────────────────────────────────────────

    def hexdump(self, file_path: str, length: int = 256, offset: int = 0) -> RunResult:
        """Show hex dump of file."""
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        console.print(Panel(f"[bold green]Hex Dump[/bold green] {file_path}", title=EARTH_BANNER))

        if check_tool("xxd"):
            args = ["xxd", "-l", str(length), "-s", str(offset), file_path]
            result = self.runner.run(args)
            console.print(result.stdout)
        else:
            # Pure Python fallback
            raw = path.read_bytes()[offset:offset + length]
            lines = []
            for i in range(0, len(raw), 16):
                chunk = raw[i:i + 16]
                hex_part = " ".join(f"{b:02x}" for b in chunk)
                asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                lines.append(f"{offset+i:08x}: {hex_part:<48}  {asc_part}")
            output = "\n".join(lines)
            console.print(output)
            result = RunResult(f"earth hexdump {file_path}", 0, output, "", 0.0)

        self._record("hexdump", f"earth hexdump {file_path}", {"file": file_path, "length": length, "offset": offset}, result)
        return result

    # ── steg ──────────────────────────────────────────────────────────────────

    def steg_extract(self, file_path: str, password: Optional[str] = None, output: str = "steg_output.txt") -> RunResult:
        """Extract hidden data with steghide."""
        if not check_tool("steghide"):
            console.print("[yellow]steghide not found. Try: apt install steghide[/yellow]")
            return RunResult("", 1, "", "steghide not found", 0.0)

        args = ["steghide", "extract", "-sf", file_path, "-p", password or "", "-f", "-xf", output]
        console.print(Panel(f"[bold green]Steg Extract[/bold green] {file_path}", title=EARTH_BANNER))

        result = self.runner.run(args)
        self._print_result(result)
        rid = self._record("steg_extract", " ".join(args), {"file": file_path}, result)
        return result

    # ── pcap ──────────────────────────────────────────────────────────────────

    def pcap(self, file_path: str, display_filter: str = "", follow: Optional[str] = None) -> RunResult:
        """Analyze PCAP files with tshark."""
        if not check_tool("tshark"):
            console.print("[red]tshark not found. Install: apt install tshark[/red]")
            return RunResult("", 1, "", "tshark not found", 0.0)

        console.print(Panel(f"[bold green]PCAP Analysis[/bold green] {file_path}", title=EARTH_BANNER))

        if follow:
            # Follow a stream (tcp/udp/http)
            args = ["tshark", "-r", file_path, "-z", f"follow,{follow},ascii,0"]
        else:
            args = ["tshark", "-r", file_path, "-T", "fields",
                    "-e", "frame.number", "-e", "ip.src", "-e", "ip.dst",
                    "-e", "_ws.col.Protocol", "-e", "_ws.col.Info",
                    "-E", "separator=|"]
            if display_filter:
                args += ["-Y", display_filter]

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("pcap", " ".join(args), {"file": file_path, "filter": display_filter}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    def get_commands(self) -> List[click.Command]:
        return []
