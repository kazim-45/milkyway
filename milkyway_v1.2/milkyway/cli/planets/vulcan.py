"""
🌋 Vulcan — Network Recon & OSINT Planet
Wraps: nmap, whois, dig, traceroute, nslookup, theHarvester, shodan-cli
"""

from __future__ import annotations

import json
import re
import socket
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

VULCAN_BANNER = "[bold bright_red]🌋 Vulcan[/bold bright_red] [dim]— Network Recon & OSINT[/dim]"


class Vulcan(Planet):
    NAME = "vulcan"
    SYMBOL = "🌋"
    DESCRIPTION = "Network Recon & OSINT — nmap, whois, DNS, port scanning"
    TOOLS = ["nmap", "whois", "dig", "nslookup", "traceroute", "nc", "masscan"]

    # ── portscan ──────────────────────────────────────────────────────────────

    def portscan(
        self,
        target: str,
        ports: str = "1-1000",
        speed: int = 3,
        service_detection: bool = True,
        os_detection: bool = False,
        script: Optional[str] = None,
        output: Optional[str] = None,
    ) -> RunResult:
        """Port scan with nmap."""
        if not check_tool("nmap"):
            console.print("[red]nmap not found. Install: apt install nmap[/red]")
            return RunResult("", 1, "", "nmap not found", 0.0)

        args = ["nmap", f"-T{speed}", "-p", ports, target]
        if service_detection:
            args.append("-sV")
        if os_detection:
            args += ["-O", "--osscan-guess"]
        if script:
            args += [f"--script={script}"]
        if output:
            args += ["-oN", output]

        cmd = " ".join(args)
        console.print(Panel(f"[bold bright_red]Port Scan[/bold bright_red] {target}", title=VULCAN_BANNER))
        console.print(f"[dim]Ports: {ports}  Speed: T{speed}  Services: {service_detection}[/dim]\n")

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("portscan", cmd, {"target": target, "ports": ports}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── quickscan ─────────────────────────────────────────────────────────────

    def quickscan(self, target: str) -> RunResult:
        """Fast top-100 port scan."""
        if not check_tool("nmap"):
            return self._python_portscan(target)

        args = ["nmap", "-T4", "--top-ports", "100", "-sV", target]
        console.print(Panel(f"[bold bright_red]Quick Scan[/bold bright_red] {target}", title=VULCAN_BANNER))
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("quickscan", " ".join(args), {"target": target}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    def _python_portscan(self, target: str) -> RunResult:
        """Pure-Python fallback port scanner (top 30 ports)."""
        import concurrent.futures

        TOP_PORTS = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
                     993, 995, 1723, 3306, 3389, 5900, 8080, 8443, 8888]

        console.print(Panel(f"[bold bright_red]Quick Scan (Python)[/bold bright_red] {target}", title=VULCAN_BANNER))
        console.print("[dim]nmap not found — using built-in scanner[/dim]\n")

        results = []

        def check_port(port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                r = s.connect_ex((target, port))
                s.close()
                return port, r == 0
            except Exception:
                return port, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futures = {ex.submit(check_port, p): p for p in TOP_PORTS}
            for f in concurrent.futures.as_completed(futures):
                port, open_ = f.result()
                if open_:
                    results.append(port)
                    console.print(f"  [green]OPEN[/green]  {target}:{port}")

        if not results:
            console.print("[dim]No open ports found in top-30 list.[/dim]")

        out = "\n".join(f"{target}:{p} OPEN" for p in sorted(results))
        result = RunResult(f"vulcan quickscan {target}", 0, out, "", 0.0)
        self._record("quickscan", f"vulcan quickscan {target}", {"target": target}, result)
        return result

    # ── whois ─────────────────────────────────────────────────────────────────

    def whois(self, target: str) -> RunResult:
        """WHOIS lookup for domain or IP."""
        console.print(Panel(f"[bold bright_red]WHOIS[/bold bright_red] {target}", title=VULCAN_BANNER))

        if check_tool("whois"):
            args = ["whois", target]
            result = self.runner.run(args)
            # Extract key lines
            interesting = []
            for line in result.stdout.splitlines():
                if any(k in line.lower() for k in [
                    "registrar", "creation", "expiry", "expiration", "registrant",
                    "name server", "updated", "status", "org", "country", "netrange",
                ]):
                    console.print(f"  [cyan]{line}[/cyan]")
                    interesting.append(line)
            if not interesting:
                console.print(result.stdout[:2000])
        else:
            # Python fallback using socket WHOIS
            result = self._python_whois(target)

        rid = self._record("whois", f"vulcan whois {target}", {"target": target}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    def _python_whois(self, target: str) -> RunResult:
        """Simple Python WHOIS via socket."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(("whois.iana.org", 43))
            s.sendall(f"{target}\r\n".encode())
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            s.close()
            out = response.decode("utf-8", errors="replace")
            console.print(out[:2000])
            return RunResult(f"vulcan whois {target}", 0, out, "", 0.0)
        except Exception as e:
            console.print(f"[red]WHOIS failed: {e}[/red]")
            return RunResult("", 1, "", str(e), 0.0)

    # ── dns ───────────────────────────────────────────────────────────────────

    def dns(self, target: str, record_type: str = "ANY") -> RunResult:
        """DNS lookup / zone walk."""
        console.print(Panel(f"[bold bright_red]DNS Lookup[/bold bright_red] {target}", title=VULCAN_BANNER))

        if check_tool("dig"):
            args = ["dig", f"+short", record_type, target]
            result = self.runner.run(args)
            console.print(result.stdout or "[dim]No records found.[/dim]")
        elif check_tool("nslookup"):
            args = ["nslookup", "-type=" + record_type, target]
            result = self.runner.run(args)
            console.print(result.stdout)
        else:
            # Python socket fallback
            try:
                addrs = socket.getaddrinfo(target, None)
                out = "\n".join(set(a[4][0] for a in addrs))
                console.print(f"[green]{out}[/green]")
                result = RunResult(f"vulcan dns {target}", 0, out, "", 0.0)
            except Exception as e:
                console.print(f"[red]DNS failed: {e}[/red]")
                result = RunResult("", 1, "", str(e), 0.0)

        rid = self._record("dns", f"vulcan dns {target}", {"target": target, "type": record_type}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── subdomain ─────────────────────────────────────────────────────────────

    def subdomain(self, domain: str, wordlist: Optional[str] = None) -> RunResult:
        """Brute-force subdomains via DNS resolution."""
        console.print(Panel(f"[bold bright_red]Subdomain Enum[/bold bright_red] {domain}", title=VULCAN_BANNER))

        # Build wordlist
        if wordlist and Path(wordlist).exists():
            words = Path(wordlist).read_text().splitlines()
        else:
            words = [
                "www", "mail", "ftp", "admin", "test", "dev", "staging", "api",
                "blog", "shop", "beta", "vpn", "remote", "portal", "cdn", "static",
                "m", "mobile", "app", "ns1", "ns2", "smtp", "pop", "imap",
            ]

        found = []
        for word in words:
            subdomain = f"{word}.{domain}"
            try:
                ip = socket.gethostbyname(subdomain)
                found.append((subdomain, ip))
                console.print(f"  [bold green]FOUND[/bold green]  {subdomain:<40} → {ip}")
            except socket.gaierror:
                pass

        if not found:
            console.print("[dim]No subdomains resolved.[/dim]")

        out = "\n".join(f"{s} {ip}" for s, ip in found)
        result = RunResult(f"vulcan subdomain {domain}", 0, out, "", 0.0)
        self._record("subdomain", f"vulcan subdomain {domain}", {"domain": domain}, result)
        return result

    # ── banner ────────────────────────────────────────────────────────────────

    def banner(self, host: str, port: int) -> RunResult:
        """Grab service banner from a port."""
        console.print(Panel(f"[bold bright_red]Banner Grab[/bold bright_red] {host}:{port}", title=VULCAN_BANNER))

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = s.recv(1024).decode("utf-8", errors="replace")
            s.close()
            console.print(f"[bold cyan]Banner:[/bold cyan]\n{banner}")
            result = RunResult(f"vulcan banner {host} {port}", 0, banner, "", 0.0)
        except Exception as e:
            console.print(f"[red]Banner grab failed: {e}[/red]")
            result = RunResult("", 1, "", str(e), 0.0)

        self._record("banner", f"vulcan banner {host} {port}", {"host": host, "port": port}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
