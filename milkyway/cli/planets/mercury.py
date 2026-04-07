"""
☿ Mercury — Web Security Planet
Pure-Python implementations for everything.
External tools (ffuf, sqlmap, nuclei) used when available, never required.
"""
from __future__ import annotations

import re
import shlex
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()
BANNER = "[bold cyan]☿ Mercury[/bold cyan] [dim]— Web Security[/dim]"


class Mercury(Planet):
    NAME = "mercury"
    SYMBOL = "☿"
    DESCRIPTION = "Web security — fuzzing, SQL injection, request crafting"
    TOOLS = ["ffuf", "sqlmap", "curl", "nuclei"]

    # ── fuzz ──────────────────────────────────────────────────────────────────

    def fuzz(self, url: str, wordlist: Optional[str], method: str = "GET",
             extensions: str = "", status_codes: str = "200,301,302,403",
             threads: int = 40, rate: int = 0, recursion: bool = False,
             output: Optional[str] = None, extra_args: str = "") -> RunResult:

        console.print(Panel(f"[bold cyan]Directory Fuzzing[/bold cyan] {url}", title=BANNER))

        # Try ffuf first
        if check_tool("ffuf"):
            from milkyway.core.config import default_wordlist
            wl = wordlist or default_wordlist()
            args = ["ffuf", "-u", url, "-w", wl, "-mc", status_codes,
                    "-t", str(threads), "-c"]
            if method != "GET": args += ["-X", method]
            if extensions: args += ["-e", extensions]
            if output: args += ["-o", output, "-of", "json"]
            if extra_args: args += shlex.split(extra_args)
            cmd = " ".join(args)
            result = self.runner.run(args, streaming=True,
                                     on_line=lambda l: console.print(l))
            rid = self._record("fuzz", cmd, {"url": url}, result)
            if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
            return result

        # ── Pure-Python fallback ───────────────────────────────────────────
        console.print("[dim]ffuf not found — using built-in Python fuzzer[/dim]\n")
        from milkyway.core.config import default_wordlist
        wl_path = wordlist or default_wordlist()

        try:
            words = Path(wl_path).read_text(errors="ignore").splitlines()
        except Exception:
            words = self._builtin_wordlist()

        target_codes = {int(c.strip()) for c in status_codes.split(",") if c.strip().isdigit()}
        exts = [""] + [e if e.startswith(".") else "." + e for e in extensions.split(",") if e.strip()]

        found = []
        import concurrent.futures, urllib.request

        def probe(word_ext):
            word, ext = word_ext
            if not word.strip(): return None
            target = url.replace("FUZZ", word.strip() + ext) if "FUZZ" in url else url.rstrip("/") + "/" + word.strip() + ext
            try:
                req = urllib.request.Request(target, method=method)
                req.add_header("User-Agent", "MilkyWay/2.0 CTF-Scanner")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    code = resp.status
                    size = len(resp.read())
                    if code in target_codes:
                        return (target, code, size)
            except urllib.error.HTTPError as e:
                if e.code in target_codes:
                    return (target, e.code, 0)
            except Exception:
                pass
            return None

        combos = [(w, e) for w in words[:2000] for e in exts]
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(threads, 20)) as ex:
            for res in ex.map(probe, combos):
                if res:
                    target, code, size = res
                    found.append(res)
                    console.print(f"  [bold green]FOUND[/bold green]  [{code}]  {target}  [{size}b]")

        output_str = "\n".join(f"{t} [{c}] [{s}b]" for t, c, s in found)
        console.print(f"\n[dim]Scanned {len(combos)} paths — found {len(found)} results[/dim]")
        result = RunResult(f"mercury fuzz {url}", 0, output_str, "", 0.0)
        rid = self._record("fuzz", f"mercury fuzz {url}", {"url": url, "wordlist": wl_path}, result)
        if rid: console.print(f"[dim]📡 Saturn #{rid}[/dim]")
        return result

    def _builtin_wordlist(self) -> List[str]:
        return [
            "admin", "login", "dashboard", "api", "api/v1", "api/v2",
            "upload", "uploads", "config", ".env", ".git", "backup",
            "backup.zip", "robots.txt", "sitemap.xml", "wp-admin",
            "wp-login.php", "phpmyadmin", "test", "dev", "staging",
            "static", "assets", "css", "js", "img", "images", "files",
            "docs", "flag", "flag.txt", "secret", "password", "private",
            "hidden", "internal", ".htaccess", ".htpasswd", "index.php",
            "index.html", "admin.php", "login.php", "upload.php",
        ]

    # ── sql ───────────────────────────────────────────────────────────────────

    def sql(self, url: str, data: Optional[str] = None, technique: str = "BEUSTQ",
            level: int = 1, risk: int = 1, dbs: bool = False, dump: bool = False,
            extra_args: str = "") -> RunResult:

        console.print(Panel(f"[bold red]SQL Injection[/bold red] {url}", title=BANNER))

        if check_tool("sqlmap"):
            args = ["sqlmap", "-u", url, f"--technique={technique}",
                    f"--level={level}", f"--risk={risk}", "--batch"]
            if data: args += ["--data", data]
            if dbs:  args.append("--dbs")
            if dump: args.append("--dump")
            if extra_args: args += shlex.split(extra_args)
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
            rid = self._record("sql", " ".join(args), {"url": url}, result)
            if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
            return result

        # ── Pure-Python SQLi detection ─────────────────────────────────────
        console.print("[dim]sqlmap not found — using built-in SQLi prober[/dim]\n")
        payloads = [
            ("'",            "syntax error",  "Single-quote error-based"),
            ("' OR '1'='1",  "1=1",           "Boolean-based blind"),
            ("'; SELECT sleep(0)--", "",      "Time-based (safe)"),
            ("' UNION SELECT NULL--", "null", "UNION-based"),
            ("1 AND 1=1",    "",              "Numeric boolean"),
            ("1 AND 1=2",    "",              "Numeric boolean (false)"),
        ]

        vuln_found = []
        for payload, indicator, label in payloads:
            test_url = url + urllib.parse.quote(payload) if "?" not in url else url + urllib.parse.quote(payload)
            try:
                req = urllib.request.Request(test_url)
                req.add_header("User-Agent", "MilkyWay/2.0")
                with urllib.request.urlopen(req, timeout=8) as resp:
                    body = resp.read().decode(errors="ignore").lower()
                    errors = ["sql syntax", "mysql_fetch", "ora-0", "postgresql",
                              "sqlite", "syntax error", "unclosed quotation"]
                    if any(e in body for e in errors):
                        console.print(f"  [bold red]POTENTIAL SQLi[/bold red] [{label}] — SQL error in response")
                        vuln_found.append(label)
                    elif indicator and indicator in body:
                        console.print(f"  [bold yellow]POSSIBLE SQLi[/bold yellow] [{label}] — indicator found")
                        vuln_found.append(label)
                    else:
                        console.print(f"  [dim]clean  [{label}][/dim]")
            except Exception as e:
                console.print(f"  [dim]error  [{label}]: {e}[/dim]")

        summary = f"Found {len(vuln_found)} potential SQLi vectors" if vuln_found else "No obvious SQLi detected"
        console.print(f"\n[{'bold red' if vuln_found else 'dim'}]{summary}[/]")
        console.print("[dim]Tip: install sqlmap for thorough scanning: pip install sqlmap[/dim]")

        out = "\n".join(vuln_found)
        result = RunResult(f"mercury sql {url}", 0 if not vuln_found else 1, out, "", 0.0)
        rid = self._record("sql", f"mercury sql {url}", {"url": url}, result)
        if rid: console.print(f"[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── request ───────────────────────────────────────────────────────────────

    def request(self, url: str, method: str = "GET", data: Optional[str] = None,
                headers: Optional[List[str]] = None, cookies: Optional[str] = None,
                follow_redirects: bool = True, output_file: Optional[str] = None,
                verbose: bool = False) -> RunResult:

        console.print(Panel(f"[bold blue]HTTP {method}[/bold blue] {url}", title=BANNER))

        if check_tool("curl"):
            args = ["curl", "-s", "-X", method, url]
            if follow_redirects: args.append("-L")
            if verbose: args.append("-v")
            if data: args += ["--data", data]
            for h in (headers or []): args += ["-H", h]
            if cookies: args += ["-b", cookies]
            if output_file: args += ["-o", output_file]
            args += ["-w", "\n\n[Status: %{http_code}] [Size: %{size_download}b] [Time: %{time_total}s]"]
            result = self.runner.run(args)
            console.print(result.stdout)
            rid = self._record("request", " ".join(args), {"url": url, "method": method}, result)
            return result

        # Pure-Python HTTP
        try:
            import urllib.request as ureq
            hdr_dict = {}
            for h in (headers or []):
                if ":" in h:
                    k, _, v = h.partition(":")
                    hdr_dict[k.strip()] = v.strip()
            hdr_dict.setdefault("User-Agent", "MilkyWay/2.0")
            if cookies:
                hdr_dict["Cookie"] = cookies

            body = data.encode() if data else None
            req = ureq.Request(url, data=body, headers=hdr_dict, method=method)
            t0 = time.monotonic()
            with ureq.urlopen(req, timeout=15) as resp:
                duration = time.monotonic() - t0
                raw = resp.read()
                status = resp.status
                resp_headers = dict(resp.headers)
                body_text = raw.decode(errors="replace")

            if verbose:
                console.print("[bold cyan]Response Headers:[/bold cyan]")
                for k, v in resp_headers.items():
                    console.print(f"  [cyan]{k}:[/cyan] {v}")
                console.print()
            console.print(body_text[:3000])
            console.print(f"\n[dim][Status: {status}] [Size: {len(raw)}b] [Time: {duration:.3f}s][/dim]")
            if output_file:
                Path(output_file).write_bytes(raw)
                console.print(f"[green]Saved to {output_file}[/green]")

            out = body_text
            result = RunResult(f"mercury request {url}", 0, out, "", duration)
        except Exception as e:
            console.print(f"[red]Request failed: {e}[/red]")
            result = RunResult(f"mercury request {url}", 1, "", str(e), 0.0)

        rid = self._record("request", f"mercury request {url}", {"url": url, "method": method}, result)
        if rid: console.print(f"[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── headers ───────────────────────────────────────────────────────────────

    def headers(self, url: str) -> RunResult:
        console.print(Panel(f"[bold cyan]HTTP Headers[/bold cyan] {url}", title=BANNER))
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "MilkyWay/2.0")
            with urllib.request.urlopen(req, timeout=10) as resp:
                hdrs = dict(resp.headers)
                status = resp.status

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Header", style="cyan", width=35)
            table.add_column("Value")

            security_headers = {"x-frame-options","content-security-policy","strict-transport-security",
                                "x-content-type-options","x-xss-protection","referrer-policy","permissions-policy"}
            missing = []
            for k, v in hdrs.items():
                style = "bold green" if k.lower() in security_headers else "white"
                table.add_row(k, f"[{style}]{v}[/{style}]")
            for sh in security_headers:
                if sh not in {k.lower() for k in hdrs}:
                    missing.append(sh)

            console.print(f"[bold]Status: {status}[/bold]\n")
            console.print(table)
            if missing:
                console.print(f"\n[yellow]⚠ Missing security headers: {', '.join(missing)}[/yellow]")

            out = "\n".join(f"{k}: {v}" for k, v in hdrs.items())
            result = RunResult(f"mercury headers {url}", 0, out, "", 0.0)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            result = RunResult("", 1, "", str(e), 0.0)

        self._record("headers", f"mercury headers {url}", {"url": url}, result)
        return result

    # ── extract ───────────────────────────────────────────────────────────────

    def extract(self, file_path: str, extract_type: str = "links") -> RunResult:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        content = path.read_text(errors="replace")

        # Try beautifulsoup4 if available
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            USE_BS4 = True
        except ImportError:
            USE_BS4 = False

        results = []
        label = extract_type

        if extract_type == "links":
            if USE_BS4:
                results = [a.get("href","") for a in soup.find_all(["a","img","script","form"],
                            attrs={"href":True,"src":True,"action":True})
                           if a.get("href") or a.get("src") or a.get("action")]
                results = sorted(set(filter(None, results)))
            else:
                results = sorted(set(re.findall(r'(?:href|src|action)=["\']([^"\']+)["\']', content, re.I)))

        elif extract_type == "forms":
            if USE_BS4:
                for form in soup.find_all("form"):
                    inputs = [(i.get("name","?"), i.get("type","text")) for i in form.find_all("input")]
                    results.append(f"action={form.get('action','')} method={form.get('method','GET')} inputs={inputs}")
            else:
                results = re.findall(r'<form[^>]*>.*?</form>', content, re.DOTALL|re.I)

        elif extract_type == "comments":
            results = [c.strip() for c in re.findall(r'<!--(.*?)-->', content, re.DOTALL) if c.strip()]

        elif extract_type == "emails":
            results = sorted(set(re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', content)))

        elif extract_type == "cookies":
            results = re.findall(r'Set-Cookie:\s*([^\r\n]+)', content, re.I)

        console.print(Panel(f"[bold yellow]Extracting {label}[/bold yellow] from {file_path}", title=BANNER))
        for r in results:
            console.print(f"  [green]→[/green] {str(r)[:120]}")
        console.print(f"\n[dim]{len(results)} items found[/dim]")

        out = "\n".join(str(r) for r in results)
        result = RunResult(f"mercury extract {file_path} --type {extract_type}", 0, out, "", 0.0)
        self._record("extract", f"mercury extract {file_path}", {"file": file_path, "type": extract_type}, result)
        return result

    # ── scan ──────────────────────────────────────────────────────────────────

    def scan(self, url: str, templates: Optional[str] = None) -> RunResult:
        console.print(Panel(f"[bold magenta]Vulnerability Scan[/bold magenta] {url}", title=BANNER))

        if check_tool("nuclei"):
            args = ["nuclei", "-u", url, "-nc"]
            if templates: args += ["-t", templates]
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
            rid = self._record("scan", " ".join(args), {"url": url}, result)
            if rid: console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
            return result

        # Built-in common vulnerability checks
        console.print("[dim]nuclei not found — running built-in checks[/dim]\n")
        checks = [
            ("/.git/config",      "Git repository exposure"),
            ("/.env",             ".env file exposure"),
            ("/phpinfo.php",      "PHPinfo disclosure"),
            ("/wp-login.php",     "WordPress login"),
            ("/admin",            "Admin panel"),
            ("/.htaccess",        "Apache config exposure"),
            ("/server-status",    "Apache server-status"),
            ("/robots.txt",       "Robots.txt"),
            ("/.well-known/security.txt", "Security.txt"),
        ]
        found = []
        for path, label in checks:
            test_url = url.rstrip("/") + path
            try:
                req = urllib.request.Request(test_url)
                req.add_header("User-Agent", "MilkyWay/2.0")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    code = resp.status
                    if code < 400:
                        console.print(f"  [bold red]FOUND[/bold red]  [{code}]  {label}  → {test_url}")
                        found.append((test_url, code, label))
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    console.print(f"  [yellow]  {e.code}  {label}[/yellow]")
            except Exception:
                pass

        console.print(f"\n[dim]{len(found)} issues found. Install nuclei for full scanning.[/dim]")
        out = "\n".join(f"{u} [{c}] {l}" for u, c, l in found)
        result = RunResult(f"mercury scan {url}", 0, out, "", 0.0)
        self._record("scan", f"mercury scan {url}", {"url": url}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
