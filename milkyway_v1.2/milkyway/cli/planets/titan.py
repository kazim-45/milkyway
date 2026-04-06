"""
🪐 Titan — Password Attacks & Wordlist Planet
Wraps: hydra, medusa, crunch, cewl, cupp, hashcat modes, john modes
"""

from __future__ import annotations

import itertools
import string
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

TITAN_BANNER = "[bold yellow]🪐 Titan[/bold yellow] [dim]— Password Attacks[/dim]"


class Titan(Planet):
    NAME = "titan"
    SYMBOL = "🪐"
    DESCRIPTION = "Password Attacks — brute-force, wordlist generation, spray"
    TOOLS = ["hydra", "medusa", "crunch", "cewl", "cupp", "hashcat", "john"]

    # ── brute ─────────────────────────────────────────────────────────────────

    def brute(
        self,
        target: str,
        service: str = "ssh",
        username: Optional[str] = None,
        user_list: Optional[str] = None,
        wordlist: Optional[str] = None,
        port: Optional[int] = None,
        threads: int = 4,
    ) -> RunResult:
        """Brute-force login with Hydra."""
        if not check_tool("hydra"):
            console.print("[red]hydra not found. Install: apt install hydra[/red]")
            return RunResult("", 1, "", "hydra not found", 0.0)

        from milkyway.core.config import default_wordlist
        wl = wordlist or default_wordlist()

        args = ["hydra", "-t", str(threads)]
        if username:
            args += ["-l", username]
        elif user_list:
            args += ["-L", user_list]
        else:
            args += ["-l", "admin"]

        args += ["-P", wl]
        if port:
            args += ["-s", str(port)]
        args += [target, service]

        cmd = " ".join(args)
        console.print(Panel(
            f"[bold yellow]Brute Force[/bold yellow] {service}://{target}",
            title=TITAN_BANNER,
        ))
        console.print(f"[dim]Wordlist: {wl}  Threads: {threads}[/dim]\n")

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("brute", cmd, {"target": target, "service": service}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── spray ─────────────────────────────────────────────────────────────────

    def spray(
        self,
        target: str,
        service: str = "ssh",
        password: str = "Password123",
        user_list: Optional[str] = None,
    ) -> RunResult:
        """Password spray — one password, many usernames."""
        if not check_tool("hydra"):
            console.print("[red]hydra not found.[/red]")
            return RunResult("", 1, "", "hydra not found", 0.0)

        ul = user_list or "/usr/share/wordlists/seclists/Usernames/top-usernames-shortlist.txt"
        args = ["hydra", "-L", ul, "-p", password, "-t", "4", target, service]
        cmd = " ".join(args)

        console.print(Panel(
            f"[bold yellow]Password Spray[/bold yellow] {service}://{target}",
            title=TITAN_BANNER,
        ))
        console.print(f"[dim]Password: {password}[/dim]\n")

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("spray", cmd, {"target": target, "password": password}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── wordlist ──────────────────────────────────────────────────────────────

    def wordlist(
        self,
        output: str = "wordlist.txt",
        min_len: int = 6,
        max_len: int = 8,
        charset: str = "alnum",
        prefix: str = "",
        suffix: str = "",
    ) -> RunResult:
        """Generate a custom wordlist with crunch or Python."""
        console.print(Panel(
            f"[bold yellow]Wordlist Generation[/bold yellow]",
            title=TITAN_BANNER,
        ))

        CHARSETS = {
            "alpha":    string.ascii_lowercase,
            "ALPHA":    string.ascii_uppercase,
            "alnum":    string.ascii_lowercase + string.digits,
            "ALNUM":    string.ascii_letters + string.digits,
            "digits":   string.digits,
            "special":  string.ascii_letters + string.digits + "!@#$%^&*",
            "hex":      "0123456789abcdef",
        }

        cs = CHARSETS.get(charset, charset)  # Allow custom charset string

        if check_tool("crunch"):
            args = ["crunch", str(min_len), str(max_len), cs, "-o", output]
            if prefix:
                args += ["-t", f"{prefix}@@@"]
            console.print(f"[dim]Using crunch → {output}[/dim]")
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        else:
            # Python fallback — only safe for small ranges
            est_count = sum(len(cs) ** l for l in range(min_len, min(max_len + 1, min_len + 2)))
            if est_count > 1_000_000:
                console.print(f"[yellow]Warning: estimated {est_count:,} words. This may take a while.[/yellow]")

            count = 0
            with open(output, "w") as f:
                for length in range(min_len, max_len + 1):
                    for combo in itertools.product(cs, repeat=length):
                        word = prefix + "".join(combo) + suffix
                        f.write(word + "\n")
                        count += 1
                        if count % 100_000 == 0:
                            console.print(f"[dim]Generated {count:,} words...[/dim]")
                        if count >= 5_000_000:
                            console.print("[yellow]Limit reached (5M). Stopping.[/yellow]")
                            break
                    else:
                        continue
                    break

            console.print(f"[green]✓ Generated {count:,} words → {output}[/green]")
            result = RunResult(f"titan wordlist", 0, f"{count} words", "", 0.0)

        rid = self._record("wordlist", f"titan wordlist -o {output}", {"output": output}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── cewl ──────────────────────────────────────────────────────────────────

    def cewl(self, url: str, depth: int = 2, min_word: int = 5, output: str = "cewl.txt") -> RunResult:
        """Spider a website and generate a wordlist from its content."""
        if not check_tool("cewl"):
            console.print("[yellow]cewl not found. Using Python spider...[/yellow]")
            return self._python_cewl(url, output, min_word)

        args = ["cewl", url, "-d", str(depth), "-m", str(min_word), "-w", output]
        console.print(Panel(f"[bold yellow]CeWL Spider[/bold yellow] {url}", title=TITAN_BANNER))
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("cewl", " ".join(args), {"url": url}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    def _python_cewl(self, url: str, output: str, min_word: int) -> RunResult:
        """Simple Python page scraper for wordlist generation."""
        try:
            import urllib.request, re
            with urllib.request.urlopen(url, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            words = re.findall(r'\b[a-zA-Z]{' + str(min_word) + r',}\b', html)
            words = sorted(set(w.lower() for w in words))
            Path(output).write_text("\n".join(words))
            console.print(f"[green]✓ {len(words)} words → {output}[/green]")
            result = RunResult("", 0, f"{len(words)} words", "", 0.0)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            result = RunResult("", 1, "", str(e), 0.0)
        self._record("cewl", f"titan cewl {url}", {"url": url}, result)
        return result

    # ── analyze ───────────────────────────────────────────────────────────────

    def analyze(self, wordlist_path: str) -> RunResult:
        """Analyze a wordlist — length distribution, patterns, stats."""
        path = Path(wordlist_path)
        if not path.exists():
            console.print(f"[red]File not found: {wordlist_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        console.print(Panel(f"[bold yellow]Wordlist Analysis[/bold yellow] {wordlist_path}", title=TITAN_BANNER))

        words = path.read_text(errors="ignore").splitlines()
        total = len(words)
        lengths = {}
        charsets = {"digits_only": 0, "alpha_only": 0, "mixed": 0, "special": 0}

        for w in words:
            l = len(w)
            lengths[l] = lengths.get(l, 0) + 1
            if w.isdigit():
                charsets["digits_only"] += 1
            elif w.isalpha():
                charsets["alpha_only"] += 1
            elif any(c in string.punctuation for c in w):
                charsets["special"] += 1
            else:
                charsets["mixed"] += 1

        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Stat", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Total words", f"{total:,}")
        table.add_row("Avg length", f"{sum(len(w) for w in words)/max(total,1):.1f}")
        table.add_row("Min length", str(min((len(w) for w in words), default=0)))
        table.add_row("Max length", str(max((len(w) for w in words), default=0)))
        table.add_row("Digits only", f"{charsets['digits_only']:,}")
        table.add_row("Alpha only",  f"{charsets['alpha_only']:,}")
        table.add_row("Mixed",       f"{charsets['mixed']:,}")
        table.add_row("Has special", f"{charsets['special']:,}")
        console.print(table)

        # Top 5 most common lengths
        console.print("\n[bold]Top lengths:[/bold]")
        for length, count in sorted(lengths.items(), key=lambda x: -x[1])[:5]:
            bar = "█" * min(40, count * 40 // total)
            console.print(f"  {length:>3} chars  {bar} {count:,}")

        result = RunResult(f"titan analyze {wordlist_path}", 0, str(total), "", 0.0)
        self._record("analyze", f"titan analyze {wordlist_path}", {"file": wordlist_path}, result)
        return result

    # ── mutate ────────────────────────────────────────────────────────────────

    def mutate(self, wordlist_path: str, output: str = "mutated.txt", rules: str = "common") -> RunResult:
        """Apply common password mutation rules to a wordlist."""
        path = Path(wordlist_path)
        if not path.exists():
            console.print(f"[red]File not found: {wordlist_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        console.print(Panel(f"[bold yellow]Password Mutation[/bold yellow] {wordlist_path}", title=TITAN_BANNER))

        words = path.read_text(errors="ignore").splitlines()
        mutated = set()

        for w in words:
            if not w:
                continue
            # Original
            mutated.add(w)
            # Capitalise first
            mutated.add(w.capitalize())
            # ALL CAPS
            mutated.add(w.upper())
            # Common suffixes
            for suffix in ["1", "123", "!", "2024", "2025", "@", "#1", "01", "12"]:
                mutated.add(w + suffix)
                mutated.add(w.capitalize() + suffix)
            # Leet speak
            leet = w.replace("a","@").replace("e","3").replace("i","1").replace("o","0").replace("s","$")
            mutated.add(leet)
            mutated.add(leet.capitalize())

        Path(output).write_text("\n".join(sorted(mutated)))
        console.print(f"[green]✓ {len(mutated):,} mutations → {output}[/green]")
        console.print(f"[dim]Original: {len(words):,}  After mutation: {len(mutated):,}  "
                      f"({len(mutated)/max(len(words),1):.1f}x)[/dim]")

        result = RunResult(f"titan mutate {wordlist_path}", 0, str(len(mutated)), "", 0.0)
        self._record("mutate", f"titan mutate {wordlist_path}", {"file": wordlist_path}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
