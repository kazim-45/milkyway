"""
♀ Venus — Cryptography Planet
Wraps: openssl, hashcat, john, python crypto libs, CyberChef-style operations
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
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

VENUS_BANNER = "[bold magenta]♀ Venus[/bold magenta] [dim]— Cryptography[/dim]"


class Venus(Planet):
    NAME = "venus"
    SYMBOL = "♀"
    DESCRIPTION = "Cryptography — hashing, encoding, decryption, factoring"
    TOOLS = ["openssl", "hashcat", "john", "factor"]

    # ── identify ──────────────────────────────────────────────────────────────

    def identify(self, hash_str: str) -> RunResult:
        """Identify hash type by length and character set."""
        hash_str = hash_str.strip()
        length = len(hash_str)
        is_hex = all(c in "0123456789abcdefABCDEF" for c in hash_str)
        is_b64 = self._is_base64(hash_str)

        identifications = []

        if is_hex:
            HEX_LENGTHS = {
                32: ["MD5", "MD4", "NTLM", "LM"],
                40: ["SHA-1", "SHA1-CRYPT", "MySQL4.1+"],
                56: ["SHA-224", "Keccak-224"],
                64: ["SHA-256", "SHA3-256", "Blake2-256", "RIPEMD-256"],
                96: ["SHA-384", "SHA3-384"],
                128: ["SHA-512", "SHA3-512", "Whirlpool", "Blake2b-512"],
            }
            if length in HEX_LENGTHS:
                identifications.extend(HEX_LENGTHS[length])

        if is_b64 and not is_hex:
            identifications.append("Base64 encoded")

        if hash_str.startswith("$2") and "$" in hash_str[3:]:
            identifications.append("bcrypt")
        if hash_str.startswith("$6$"):
            identifications.append("SHA-512 crypt (Unix shadow)")
        if hash_str.startswith("$5$"):
            identifications.append("SHA-256 crypt (Unix shadow)")
        if hash_str.startswith("$1$"):
            identifications.append("MD5 crypt (Unix shadow)")
        if hash_str.startswith("$apr1$"):
            identifications.append("md5apr1 (Apache)")
        if re.match(r'^[A-Z2-7]+=*$', hash_str):
            identifications.append("Base32 encoded")
        if all(c in "01" for c in hash_str):
            identifications.append("Binary string")

        output = f"Hash: {hash_str}\nLength: {length}\nPossible types:\n"
        console.print(Panel(f"[bold magenta]Hash Identification[/bold magenta]", title=VENUS_BANNER))

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property")
        table.add_column("Value")
        table.add_row("Input", f"[cyan]{hash_str[:80]}{'...' if len(hash_str) > 80 else ''}[/cyan]")
        table.add_row("Length", str(length))
        table.add_row("Hex chars", "✅" if is_hex else "❌")
        table.add_row("Base64 chars", "✅" if is_b64 else "❌")
        for algo in identifications:
            table.add_row("[green]Possible type[/green]", f"[bold green]{algo}[/bold green]")
        if not identifications:
            table.add_row("[yellow]Possible type[/yellow]", "[yellow]Unknown — check manually[/yellow]")
        console.print(table)

        output += "\n".join(identifications) or "Unknown"
        result = RunResult(f"venus identify {hash_str[:20]}...", 0, output, "", 0.0)
        self._record("identify", f"venus identify {hash_str[:20]}", {"hash": hash_str}, result)
        return result

    def _is_base64(self, s: str) -> bool:
        try:
            if len(s) % 4 == 0:
                base64.b64decode(s, validate=True)
                return True
        except Exception:
            pass
        return False

    # ── hash ──────────────────────────────────────────────────────────────────

    def hash(self, text: str, algorithm: str = "md5") -> RunResult:
        """Compute hash of text."""
        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
            "sha224": hashlib.sha224,
            "sha384": hashlib.sha384,
        }
        if algorithm not in algorithms:
            console.print(f"[red]Unknown algorithm: {algorithm}. Choose from: {', '.join(algorithms)}[/red]")
            return RunResult("", 1, "", "Unknown algorithm", 0.0)

        h = algorithms[algorithm](text.encode()).hexdigest()
        console.print(Panel(f"[bold magenta]{algorithm.upper()}[/bold magenta] hash", title=VENUS_BANNER))
        console.print(f"Input:  [dim]{text}[/dim]")
        console.print(f"Hash:   [bold green]{h}[/bold green]")

        result = RunResult(f"venus hash {text[:20]}", 0, h, "", 0.0)
        self._record("hash", f"venus hash --algo {algorithm}", {"text": text, "algo": algorithm}, result)
        return result

    # ── crack ─────────────────────────────────────────────────────────────────

    def crack(self, hash_str: str, wordlist: Optional[str] = None, hash_type: Optional[int] = None) -> RunResult:
        """Crack hash with hashcat."""
        if not check_tool("hashcat"):
            console.print("[yellow]hashcat not found. Trying john...[/yellow]")
            return self._crack_john(hash_str, wordlist)

        from milkyway.core.config import default_wordlist
        wl = wordlist or default_wordlist()

        args = ["hashcat", hash_str, wl, "--quiet"]
        if hash_type is not None:
            args += ["-m", str(hash_type)]

        console.print(Panel(f"[bold red]Hash Cracking[/bold red]", title=VENUS_BANNER))
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("crack", " ".join(args), {"hash": hash_str, "wordlist": wl}, result)
        if rid:
            console.print(f"[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    def _crack_john(self, hash_str: str, wordlist: Optional[str]) -> RunResult:
        if not check_tool("john"):
            console.print("[red]Neither hashcat nor john found.[/red]")
            return RunResult("", 1, "", "Tool not found", 0.0)
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".hash", delete=False) as f:
            f.write(hash_str + "\n")
            hash_file = f.name
        args = ["john", hash_file]
        if wordlist:
            args += [f"--wordlist={wordlist}"]
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        return result

    # ── encode / decode ───────────────────────────────────────────────────────

    def encode(self, text: str, encoding: str = "base64") -> RunResult:
        """Encode text using common encodings."""
        result_str = ""
        try:
            if encoding == "base64":
                result_str = base64.b64encode(text.encode()).decode()
            elif encoding == "base32":
                result_str = base64.b32encode(text.encode()).decode()
            elif encoding == "hex":
                result_str = text.encode().hex()
            elif encoding == "url":
                import urllib.parse
                result_str = urllib.parse.quote(text)
            elif encoding == "rot13":
                import codecs
                result_str = codecs.encode(text, "rot_13")
            elif encoding == "binary":
                result_str = " ".join(format(ord(c), "08b") for c in text)
            else:
                result_str = f"Unknown encoding: {encoding}"
        except Exception as e:
            result_str = f"Error: {e}"

        console.print(Panel(f"[bold magenta]{encoding.upper()} Encode[/bold magenta]", title=VENUS_BANNER))
        console.print(f"Input:  [dim]{text[:80]}[/dim]")
        console.print(f"Output: [bold green]{result_str[:200]}[/bold green]")

        result = RunResult(f"venus encode --enc {encoding}", 0, result_str, "", 0.0)
        self._record("encode", f"venus encode --enc {encoding}", {"text": text, "encoding": encoding}, result)
        return result

    def decode(self, text: str, encoding: str = "base64") -> RunResult:
        """Decode text from common encodings."""
        result_str = ""
        try:
            if encoding == "base64":
                result_str = base64.b64decode(text.encode()).decode(errors="replace")
            elif encoding == "base32":
                result_str = base64.b32decode(text.encode()).decode(errors="replace")
            elif encoding == "hex":
                result_str = bytes.fromhex(text).decode(errors="replace")
            elif encoding == "url":
                import urllib.parse
                result_str = urllib.parse.unquote(text)
            elif encoding == "rot13":
                import codecs
                result_str = codecs.decode(text, "rot_13")
            elif encoding == "binary":
                parts = text.split()
                result_str = "".join(chr(int(b, 2)) for b in parts)
            else:
                result_str = f"Unknown encoding: {encoding}"
        except Exception as e:
            result_str = f"Error decoding: {e}"

        console.print(Panel(f"[bold magenta]{encoding.upper()} Decode[/bold magenta]", title=VENUS_BANNER))
        console.print(f"Input:  [dim]{text[:80]}[/dim]")
        console.print(f"Output: [bold green]{result_str[:200]}[/bold green]")

        result = RunResult(f"venus decode --enc {encoding}", 0, result_str, "", 0.0)
        self._record("decode", f"venus decode --enc {encoding}", {"text": text, "encoding": encoding}, result)
        return result

    # ── factor ────────────────────────────────────────────────────────────────

    def factor(self, number: str) -> RunResult:
        """Factor a number (for RSA challenges)."""
        console.print(Panel(f"[bold magenta]Factoring[/bold magenta] {number}", title=VENUS_BANNER))
        if check_tool("factor"):
            args = ["factor", number]
            result = self.runner.run(args)
            console.print(result.stdout)
        else:
            # Pure Python factoring for smaller numbers
            n = int(number)
            factors = []
            d = 2
            while d * d <= n:
                while n % d == 0:
                    factors.append(d)
                    n //= d
                d += 1
            if n > 1:
                factors.append(n)
            out = f"{number}: " + " ".join(map(str, factors))
            console.print(f"[green]{out}[/green]")
            result = RunResult(f"venus factor {number}", 0, out, "", 0.0)

        self._record("factor", f"venus factor {number}", {"number": number}, result)
        return result

    # ── xor ───────────────────────────────────────────────────────────────────

    def xor(self, data: str, key: str, input_format: str = "hex") -> RunResult:
        """XOR data with key."""
        try:
            if input_format == "hex":
                data_bytes = bytes.fromhex(data)
            elif input_format == "base64":
                data_bytes = base64.b64decode(data)
            else:
                data_bytes = data.encode()

            key_bytes = key.encode()
            result_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data_bytes))
            result_hex = result_bytes.hex()
            result_text = result_bytes.decode(errors="replace")

        except Exception as e:
            result_hex = ""
            result_text = f"Error: {e}"

        console.print(Panel(f"[bold magenta]XOR[/bold magenta]", title=VENUS_BANNER))
        console.print(f"Key: [cyan]{key}[/cyan]")
        console.print(f"Hex:  [bold green]{result_hex[:100]}[/bold green]")
        console.print(f"Text: [bold yellow]{result_text[:100]}[/bold yellow]")

        out = f"hex: {result_hex}\ntext: {result_text}"
        result = RunResult(f"venus xor", 0, out, "", 0.0)
        self._record("xor", f"venus xor --key {key}", {"data": data[:20], "key": key}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
