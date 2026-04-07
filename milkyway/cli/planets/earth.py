"""
♁ Earth — Forensics Planet
Pure-Python implementations. External tools used when available.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()
BANNER = "[bold green]♁ Earth[/bold green] [dim]— Forensics[/dim]"

MAGIC_DB = {
    b"\x89PNG": "PNG image",        b"\xff\xd8\xff": "JPEG image",
    b"GIF8":    "GIF image",        b"BM": "BMP image",
    b"PK\x03\x04": "ZIP archive",   b"Rar!": "RAR archive",
    b"\x1f\x8b": "Gzip",           b"BZh": "Bzip2",
    b"\x7fELF": "ELF binary",      b"MZ": "Windows PE",
    b"%PDF":    "PDF document",     b"SQLite format 3": "SQLite DB",
    b"-----BEGIN": "PEM cert/key", b"<?php": "PHP source",
    b"<html":   "HTML",            b"#!/": "Shell script",
}

def _magic(raw: bytes) -> str:
    for sig, label in MAGIC_DB.items():
        if raw[:len(sig)] == sig:
            return label
    try:
        import magic as pm
        return pm.from_buffer(raw)
    except Exception:
        pass
    return "Unknown/Binary"


class Earth(Planet):
    NAME = "earth"; SYMBOL = "♁"
    DESCRIPTION = "Forensics — file analysis, carving, strings, steg, PCAP"
    TOOLS = ["binwalk","strings","file","exiftool","tshark","steghide","xxd"]

    def info(self, file_path: str) -> RunResult:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)
        raw   = path.read_bytes()
        magic = _magic(raw)
        md5   = hashlib.md5(raw).hexdigest()
        sha256= hashlib.sha256(raw).hexdigest()
        console.print(Panel(f"[bold green]File Info[/bold green] {file_path}", title=BANNER))
        t = Table(show_header=True, header_style="bold green")
        t.add_column("Property", style="cyan", width=14)
        t.add_column("Value")
        t.add_row("Type",   f"[bold]{magic}[/bold]")
        t.add_row("Size",   f"{len(raw):,} bytes")
        t.add_row("Magic",  raw[:16].hex(" "))
        t.add_row("MD5",    md5)
        t.add_row("SHA256", sha256)
        console.print(t)
        if check_tool("exiftool"):
            r = self.runner.run(["exiftool", file_path])
            for line in r.stdout.strip().splitlines()[:15]:
                console.print(f"  {line}")
        try:
            from PIL import Image
            if "image" in magic.lower():
                img = Image.open(file_path)
                console.print(f"\n[cyan]Image:[/cyan] {img.size[0]}×{img.size[1]} px  mode={img.mode}")
        except Exception:
            pass
        out = f"type={magic}\nsize={len(raw)}\nmd5={md5}\nsha256={sha256}"
        res = RunResult(f"earth info {file_path}", 0, out, "", 0.0)
        self._record("info", f"earth info {file_path}", {"file": file_path}, res)
        return res

    def carve(self, file_path: str, output_dir: Optional[str] = None) -> RunResult:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)
        console.print(Panel(f"[bold green]Carving[/bold green] {file_path}", title=BANNER))
        if check_tool("binwalk"):
            out_d = output_dir or f"{file_path}_extracted"
            args  = ["binwalk", "--extract", "--directory", out_d, file_path]
            res   = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
            rid   = self._record("carve", " ".join(args), {"file": file_path}, res)
            if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
            return res
        # Pure-Python carving
        console.print("[dim]binwalk not found — using built-in carver[/dim]\n")
        raw   = path.read_bytes()
        out_d = Path(output_dir or f"{file_path}_extracted")
        out_d.mkdir(parents=True, exist_ok=True)
        SIGS = [
            (b"\x89PNG\r\n\x1a\n", b"IEND\xaeB`\x82", ".png"),
            (b"\xff\xd8\xff",      b"\xff\xd9",        ".jpg"),
            (b"GIF8",              b"\x00;",            ".gif"),
            (b"PK\x03\x04",       b"PK\x05\x06",      ".zip"),
            (b"%PDF",              b"%%EOF",            ".pdf"),
        ]
        found = []
        for start, end, ext in SIGS:
            pos = 0
            while True:
                idx = raw.find(start, pos)
                if idx == -1: break
                end_idx = raw.find(end, idx + len(start))
                if end_idx == -1: pos = idx + 1; continue
                chunk = raw[idx:end_idx + len(end)]
                fname = out_d / f"carved_{idx:08x}{ext}"
                fname.write_bytes(chunk)
                found.append(str(fname))
                console.print(f"  [green]Carved[/green]  {fname.name}  ({len(chunk):,} bytes)")
                pos = idx + 1
        if not found: console.print("[dim]No embedded files found.[/dim]")
        else: console.print(f"\n[green]{len(found)} files extracted → {out_d}[/green]")
        res = RunResult(f"earth carve {file_path}", 0, "\n".join(found), "", 0.0)
        self._record("carve", f"earth carve {file_path}", {"file": file_path}, res)
        return res

    def strings(self, file_path: str, min_len: int = 4, grep: Optional[str] = None) -> RunResult:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)
        console.print(Panel(f"[bold green]Strings[/bold green] {file_path}", title=BANNER))
        if check_tool("strings"):
            res   = self.runner.run(["strings", "-n", str(min_len), file_path])
            lines = res.stdout.splitlines()
        else:
            raw   = path.read_bytes()
            pat   = re.compile(rb'[\x20-\x7e]{' + str(min_len).encode() + rb',}')
            lines = [m.group().decode("ascii", errors="ignore") for m in pat.finditer(raw)]
        if grep:
            lines = [l for l in lines if re.search(grep, l, re.I)]
            console.print(f"[dim]Filter: '{grep}' → {len(lines)} matches[/dim]\n")
        FLAG = re.compile(r'flag|ctf|password|secret|key|token|api', re.I)
        for line in lines[:500]:
            if FLAG.search(line):
                console.print(f"  [bold yellow]★ {line}[/bold yellow]")
            else:
                console.print(f"  {line}")
        if len(lines) > 500:
            console.print(f"\n[dim]… {len(lines)-500} more strings[/dim]")
        res = RunResult(f"earth strings {file_path}", 0, "\n".join(lines), "", 0.0)
        rid = self._record("strings", f"earth strings {file_path}", {"file": file_path, "grep": grep}, res)
        if rid: console.print(f"[dim]📡 Saturn #{rid}[/dim]")
        return res

    def hexdump(self, file_path: str, length: int = 256, offset: int = 0) -> RunResult:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)
        console.print(Panel(f"[bold green]Hex Dump[/bold green] {file_path}", title=BANNER))
        if check_tool("xxd"):
            res = self.runner.run(["xxd", "-l", str(length), "-s", str(offset), file_path])
            console.print(res.stdout)
        else:
            raw  = path.read_bytes()[offset:offset + length]
            lines = []
            for i in range(0, len(raw), 16):
                chunk = raw[i:i+16]
                hex_p = " ".join(f"{b:02x}" for b in chunk)
                asc_p = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                console.print(f"[dim]{offset+i:08x}:[/dim] [green]{hex_p:<48}[/green]  [cyan]{asc_p}[/cyan]")
                lines.append(f"{offset+i:08x}: {hex_p:<48}  {asc_p}")
            res = RunResult(f"earth hexdump {file_path}", 0, "\n".join(lines), "", 0.0)
        self._record("hexdump", f"earth hexdump {file_path}", {"file": file_path, "length": length}, res)
        return res

    def steg_extract(self, file_path: str, password: Optional[str] = None, output: str = "steg_output.txt") -> RunResult:
        console.print(Panel(f"[bold green]Steganography[/bold green] {file_path}", title=BANNER))
        if check_tool("steghide"):
            args = ["steghide", "extract", "-sf", file_path, "-p", password or "", "-f", "-xf", output]
            res  = self.runner.run(args)
            self._print_result(res)
        else:
            console.print("[dim]steghide not found — scanning for hidden data[/dim]\n")
            path = Path(file_path)
            if not path.exists():
                return RunResult("", 1, "", "Not found", 0.0)
            raw = path.read_bytes()
            # JPEG appended data
            if raw[:3] == b"\xff\xd8\xff":
                eof = raw.rfind(b"\xff\xd9")
                if eof != -1 and eof + 2 < len(raw):
                    extra = raw[eof + 2:]
                    console.print(f"[yellow]{len(extra)} bytes after JPEG EOF:[/yellow]")
                    for s in re.findall(rb'[\x20-\x7e]{4,}', extra):
                        console.print(f"  [green]{s.decode(errors='ignore')}[/green]")
            # PNG appended
            elif raw[:4] == b"\x89PNG":
                iend = raw.rfind(b"IEND\xaeB`\x82")
                if iend != -1 and iend + 8 < len(raw):
                    extra = raw[iend + 8:]
                    console.print(f"[yellow]{len(extra)} bytes after PNG IEND:[/yellow]")
                    for s in re.findall(rb'[\x20-\x7e]{4,}', extra):
                        console.print(f"  [green]{s.decode(errors='ignore')}[/green]")
            res = RunResult(f"earth steg {file_path}", 0, "", "", 0.0)
        self._record("steg_extract", f"earth steg {file_path}", {"file": file_path}, res)
        return res

    def pcap(self, file_path: str, display_filter: str = "", follow: Optional[str] = None) -> RunResult:
        console.print(Panel(f"[bold green]PCAP Analysis[/bold green] {file_path}", title=BANNER))
        if check_tool("tshark"):
            if follow:
                args = ["tshark", "-r", file_path, "-z", f"follow,{follow},ascii,0"]
            else:
                args = ["tshark", "-r", file_path, "-T", "fields",
                        "-e", "frame.number", "-e", "ip.src", "-e", "ip.dst",
                        "-e", "_ws.col.Protocol", "-e", "_ws.col.Info", "-E", "separator=|"]
                if display_filter: args += ["-Y", display_filter]
            res = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
            rid = self._record("pcap", " ".join(args), {"file": file_path}, res)
            if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
            return res
        # Pure-Python minimal PCAP
        console.print("[dim]tshark not found — basic PCAP reader[/dim]\n")
        try:
            path = Path(file_path)
            raw  = path.read_bytes()
            if len(raw) < 24: raise ValueError("Too short")
            magic = struct.unpack_from("<I", raw, 0)[0]
            if magic not in (0xa1b2c3d4, 0xd4c3b2a1):
                raise ValueError("Not PCAP")
            pkts = []; pos = 24
            while pos + 16 <= len(raw):
                _, _, incl, orig = struct.unpack_from("<IIII", raw, pos)
                pos += 16
                if pos + incl > len(raw): break
                data = raw[pos:pos + incl]
                pkts.append((orig, data)); pos += incl
            t = Table(show_header=True, header_style="bold green")
            t.add_column("#",  width=5)
            t.add_column("Len",width=7)
            t.add_column("Preview",width=60)
            for i, (length, data) in enumerate(pkts[:50], 1):
                prev = re.sub(rb'[^\x20-\x7e]', b'.', data[:50]).decode()
                t.add_row(str(i), str(length), prev)
            console.print(t)
            console.print(f"[dim]{len(pkts)} packets total[/dim]")
        except Exception as e:
            console.print(f"[red]Cannot read PCAP: {e}[/red]")
            console.print("[dim]Install tshark: apt install tshark[/dim]")
        res = RunResult(f"earth pcap {file_path}", 0, "", "", 0.0)
        self._record("pcap", f"earth pcap {file_path}", {"file": file_path}, res)
        return res

    def get_commands(self) -> List[click.Command]:
        return []
