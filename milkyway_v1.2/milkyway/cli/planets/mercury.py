"""
☿ Mercury — Web Security Planet
Wraps: ffuf, sqlmap, curl, nuclei, httpx, whatweb
"""

from __future__ import annotations

import shlex
import urllib.parse
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, ToolNotFoundError, check_tool

console = Console()

MERCURY_BANNER = "[bold cyan]☿ Mercury[/bold cyan] [dim]— Web Security[/dim]"


class Mercury(Planet):
    NAME = "mercury"
    SYMBOL = "☿"
    DESCRIPTION = "Web security — fuzzing, injection, request crafting"
    TOOLS = ["ffuf", "sqlmap", "curl", "nuclei", "httpx", "whatweb", "nikto"]

    # ── fuzz ──────────────────────────────────────────────────────────────────

    def fuzz(
        self,
        url: str,
        wordlist: Optional[str],
        method: str = "GET",
        extensions: str = "",
        status_codes: str = "200,301,302,403",
        threads: int = 40,
        rate: int = 0,
        recursion: bool = False,
        output: Optional[str] = None,
        extra_args: str = "",
    ) -> RunResult:
        if not check_tool("ffuf"):
            raise ToolNotFoundError("ffuf", "Install: go install github.com/ffuf/ffuf@latest")

        from milkyway.core.config import default_wordlist
        wl = wordlist or default_wordlist()

        args = [
            "ffuf",
            "-u", url,
            "-w", wl,
            "-mc", status_codes,
            "-t", str(threads),
            "-c",           # Colorize (suppressed in capture mode but helpful for streaming)
        ]
        if method != "GET":
            args += ["-X", method]
        if extensions:
            args += ["-e", extensions]
        if rate > 0:
            args += ["-rate", str(rate)]
        if recursion:
            args += ["-recursion", "-recursion-depth", "2"]
        if output:
            args += ["-o", output, "-of", "json"]
        if extra_args:
            args += shlex.split(extra_args)

        cmd = " ".join(args)
        console.print(Panel(f"[bold green]Fuzzing[/bold green] {url}", title=MERCURY_BANNER))
        console.print(f"[dim]Wordlist:[/dim] {wl}")
        console.print(f"[dim]Threads:[/dim] {threads} | [dim]Status codes:[/dim] {status_codes}\n")

        lines_seen = []
        def on_line(line: str):
            lines_seen.append(line)
            if line.strip():
                console.print(line)

        result = self.runner.run(args, on_line=on_line, spinner_text="Fuzzing...")
        rid = self._record("fuzz", cmd, {"url": url, "wordlist": wl}, result)
        console.print(f"\n[dim]Found {sum(1 for l in lines_seen if 'Status:' in l)} results[/dim]")
        if rid:
            console.print(f"[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── sql ───────────────────────────────────────────────────────────────────

    def sql(
        self,
        url: str,
        data: Optional[str],
        technique: str = "BEUSTQ",
        level: int = 1,
        risk: int = 1,
        dbs: bool = False,
        dump: bool = False,
        batch: bool = True,
        extra_args: str = "",
    ) -> RunResult:
        if not check_tool("sqlmap"):
            raise ToolNotFoundError("sqlmap", "Install: pip install sqlmap  OR  apt install sqlmap")

        args = [
            "sqlmap",
            "-u", url,
            f"--technique={technique}",
            f"--level={level}",
            f"--risk={risk}",
        ]
        if data:
            args += ["--data", data]
        if dbs:
            args.append("--dbs")
        if dump:
            args.append("--dump")
        if batch:
            args.append("--batch")
        if extra_args:
            args += shlex.split(extra_args)

        cmd = " ".join(args)
        console.print(Panel(f"[bold red]SQL Injection Scan[/bold red] {url}", title=MERCURY_BANNER))

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("sql", cmd, {"url": url, "data": data}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── request ───────────────────────────────────────────────────────────────

    def request(
        self,
        url: str,
        method: str = "GET",
        data: Optional[str] = None,
        headers: Optional[List[str]] = None,
        cookies: Optional[str] = None,
        follow_redirects: bool = True,
        output_file: Optional[str] = None,
        verbose: bool = False,
    ) -> RunResult:
        args = ["curl", "-s", "-X", method, url]

        if follow_redirects:
            args.append("-L")
        if verbose:
            args.append("-v")
        if data:
            args += ["--data", data]
        for hdr in (headers or []):
            args += ["-H", hdr]
        if cookies:
            args += ["-b", cookies]
        if output_file:
            args += ["-o", output_file]

        args += ["-w", "\n\n[Status: %{http_code}] [Size: %{size_download}b] [Time: %{time_total}s]"]

        cmd = " ".join(args)
        console.print(Panel(f"[bold blue]HTTP {method}[/bold blue] {url}", title=MERCURY_BANNER))

        result = self.runner.run(args)
        self._print_result(result)
        rid = self._record("request", cmd, {"url": url, "method": method}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── extract ───────────────────────────────────────────────────────────────

    def extract(self, file_path: str, extract_type: str = "links") -> RunResult:
        """Extract links, forms, cookies, or comments from HTML."""
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult(file_path, 1, "", "File not found", 0.0)

        content = path.read_text(encoding="utf-8", errors="replace")

        import re
        results = []

        if extract_type == "links":
            patterns = [r'href=["\']([^"\']+)["\']', r'src=["\']([^"\']+)["\']', r'action=["\']([^"\']+)["\']']
            for pat in patterns:
                results.extend(re.findall(pat, content, re.IGNORECASE))
            results = sorted(set(results))
            label = "Links/Sources/Actions"

        elif extract_type == "forms":
            form_blocks = re.findall(r'<form[^>]*>.*?</form>', content, re.DOTALL | re.IGNORECASE)
            results = form_blocks
            label = "Forms"

        elif extract_type == "cookies":
            results = re.findall(r'Set-Cookie:\s*([^\r\n]+)', content, re.IGNORECASE)
            label = "Cookies"

        elif extract_type == "comments":
            results = re.findall(r'<!--(.*?)-->', content, re.DOTALL)
            results = [r.strip() for r in results if r.strip()]
            label = "HTML Comments"

        elif extract_type == "emails":
            results = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
            results = sorted(set(results))
            label = "Emails"

        else:
            results = []
            label = extract_type

        output = f"=== {label} ===\n" + "\n".join(results)
        console.print(Panel(f"[bold yellow]Extracting {label}[/bold yellow] from {file_path}", title=MERCURY_BANNER))
        for r in results:
            console.print(f"  [green]→[/green] {r[:120]}")

        fake_result = RunResult(f"extract {file_path} --type {extract_type}", 0, output, "", 0.0)
        rid = self._record("extract", f"mercury extract {file_path} --type {extract_type}", {"file": file_path, "type": extract_type}, fake_result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return fake_result

    # ── scan ──────────────────────────────────────────────────────────────────

    def scan(self, url: str, templates: Optional[str] = None) -> RunResult:
        """Run nuclei template scan."""
        if not check_tool("nuclei"):
            raise ToolNotFoundError("nuclei", "Install: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")

        args = ["nuclei", "-u", url, "-nc"]
        if templates:
            args += ["-t", templates]

        cmd = " ".join(args)
        console.print(Panel(f"[bold magenta]Nuclei Scan[/bold magenta] {url}", title=MERCURY_BANNER))

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("scan", cmd, {"url": url, "templates": templates}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── headers ───────────────────────────────────────────────────────────────

    def headers(self, url: str) -> RunResult:
        """Inspect HTTP headers of a URL."""
        args = ["curl", "-s", "-I", url, "-L"]
        result = self.runner.run(args)
        console.print(Panel(f"[bold cyan]Headers[/bold cyan] {url}", title=MERCURY_BANNER))

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Header", style="cyan", width=30)
        table.add_column("Value")
        for line in result.stdout.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                table.add_row(k.strip(), v.strip())
        console.print(table)

        rid = self._record("headers", f"mercury headers {url}", {"url": url}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []   # Commands are registered directly via Click groups in main.py
