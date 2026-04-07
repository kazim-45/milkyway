"""
♀ Venus — Cryptography Planet
All operations implemented in pure Python.
pycryptodome, sympy, gmpy2 used when available for speed/extra features.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import itertools
import math
import struct
import time
import urllib.parse
import urllib.request
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()
BANNER = "[bold magenta]♀ Venus[/bold magenta] [dim]— Cryptography[/dim]"


class Venus(Planet):
    NAME = "venus"
    SYMBOL = "♀"
    DESCRIPTION = "Cryptography — hashing, encoding, cracking, factoring"
    TOOLS = ["hashcat", "john", "openssl"]

    # ── identify ──────────────────────────────────────────────────────────────

    def identify(self, hash_str: str) -> RunResult:
        h = hash_str.strip()
        length = len(h)
        is_hex = all(c in "0123456789abcdefABCDEF" for c in h)

        candidates = []

        # Hex-length matches
        HEX_MAP = {
            32:  ["MD5", "MD4", "NTLM", "LM"],
            40:  ["SHA-1", "MySQL4.1+", "SHA1-CRYPT"],
            56:  ["SHA-224", "Keccak-224"],
            64:  ["SHA-256", "SHA3-256", "Blake2-256", "RIPEMD-256"],
            96:  ["SHA-384", "SHA3-384"],
            128: ["SHA-512", "SHA3-512", "Blake2b-512", "Whirlpool"],
        }
        if is_hex and length in HEX_MAP:
            candidates.extend(HEX_MAP[length])

        # Prefix patterns
        if h.startswith("$2"):   candidates.append("bcrypt")
        if h.startswith("$6$"):  candidates.append("SHA-512crypt (Linux shadow)")
        if h.startswith("$5$"):  candidates.append("SHA-256crypt (Linux shadow)")
        if h.startswith("$1$"):  candidates.append("MD5crypt (Linux shadow)")
        if h.startswith("$apr1$"): candidates.append("md5apr1 (Apache)")
        if h.startswith("$y$"):  candidates.append("yescrypt")
        if re.match(r"^[A-Z2-7]+=*$", h): candidates.append("Base32")
        if re.match(r"^[A-Za-z0-9+/]+=*$", h) and len(h) % 4 == 0:
            candidates.append("Base64")
        if all(c in "01 " for c in h.replace(" ","")): candidates.append("Binary string")
        if all(c in "0123456789" for c in h) and len(h) in [6, 8, 10]:
            candidates.append("Numeric OTP / PIN")

        # Online lookup (optional)
        online_result = self._online_lookup(h) if is_hex and length == 32 else None

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property")
        table.add_column("Value")
        table.add_row("Input",    f"[cyan]{h[:80]}{'…' if len(h) > 80 else ''}[/cyan]")
        table.add_row("Length",   str(length))
        table.add_row("Hex chars","✅" if is_hex else "❌")

        for algo in candidates:
            table.add_row("[green]Possible type[/green]", f"[bold green]{algo}[/bold green]")
        if not candidates:
            table.add_row("[yellow]Type[/yellow]", "[yellow]Unknown — check manually[/yellow]")
        if online_result:
            table.add_row("[bold red]CRACKED[/bold red]", f"[bold red]{online_result}[/bold red]")

        console.print(Panel(f"[bold magenta]Hash Identification[/bold magenta]", title=BANNER))
        console.print(table)

        out = "\n".join(candidates) + (f"\nCRACKED: {online_result}" if online_result else "")
        result = RunResult(f"venus identify", 0, out, "", 0.0)
        self._record("identify", f"venus identify {h[:20]}", {"hash": h}, result)
        return result

    def _online_lookup(self, h: str) -> Optional[str]:
        """Try free hash lookup APIs."""
        apis = [
            f"https://md5decrypt.net/Api/api.php?hash={h}&hash_type=md5&email=api@mw.ctf&code=api_mw",
        ]
        for api in apis:
            try:
                with urllib.request.urlopen(api, timeout=5) as resp:
                    text = resp.read().decode().strip()
                    if text and text not in ("INVALID_HASH", "NOT_FOUND", ""):
                        return text
            except Exception:
                pass
        return None

    # ── hash ──────────────────────────────────────────────────────────────────

    def hash(self, text: str, algorithm: str = "md5") -> RunResult:
        algos = {
            "md5":    hashlib.md5,
            "sha1":   hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
            "sha224": hashlib.sha224,
            "sha384": hashlib.sha384,
        }
        if algorithm not in algos:
            console.print(f"[red]Unknown: {algorithm}[/red]")
            return RunResult("", 1, "", "", 0.0)

        h = algos[algorithm](text.encode()).hexdigest()
        console.print(Panel(f"[bold magenta]{algorithm.upper()} Hash[/bold magenta]", title=BANNER))
        console.print(f"Input  : [dim]{text}[/dim]")
        console.print(f"Hash   : [bold green]{h}[/bold green]")

        # Also show all common hashes at once
        all_hashes = {k: v(text.encode()).hexdigest() for k, v in algos.items()}
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Algorithm")
        table.add_column("Hash")
        for k, v in all_hashes.items():
            style = "bold green" if k == algorithm else "dim"
            table.add_row(k, f"[{style}]{v}[/{style}]")
        console.print(table)

        result = RunResult(f"venus hash", 0, h, "", 0.0)
        self._record("hash", f"venus hash --algo {algorithm}", {"text": text, "algo": algorithm}, result)
        return result

    # ── crack ─────────────────────────────────────────────────────────────────

    def crack(self, hash_str: str, wordlist: Optional[str] = None, hash_type: Optional[int] = None) -> RunResult:
        console.print(Panel(f"[bold red]Hash Cracking[/bold red]", title=BANNER))

        # Try hashcat
        if check_tool("hashcat") and wordlist:
            from milkyway.core.config import default_wordlist
            wl = wordlist or default_wordlist()
            args = ["hashcat", hash_str, wl, "--quiet"]
            if hash_type is not None: args += ["-m", str(hash_type)]
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
            self._record("crack", " ".join(args), {"hash": hash_str}, result)
            return result

        # Try john
        if check_tool("john"):
            import tempfile, os
            with tempfile.NamedTemporaryFile("w", suffix=".hash", delete=False) as f:
                f.write(hash_str + "\n"); fname = f.name
            args = ["john", fname]
            if wordlist: args += [f"--wordlist={wordlist}"]
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
            os.unlink(fname)
            self._record("crack", " ".join(args), {"hash": hash_str}, result)
            return result

        # Pure-Python cracker
        console.print("[dim]hashcat/john not found — using built-in Python cracker[/dim]\n")
        from milkyway.core.config import default_wordlist
        wl_path = wordlist or default_wordlist()

        try:
            words = Path(wl_path).read_text(errors="ignore").splitlines()
        except Exception:
            words = ["password", "123456", "admin", "letmein", "qwerty",
                     "welcome", "monkey", "dragon", "master", "hello"]

        h_lower = hash_str.strip().lower()
        hl = len(h_lower)

        def _try(word: str) -> Optional[str]:
            w = word.strip()
            if not w: return None
            checks = [
                hashlib.md5(w.encode()).hexdigest(),
                hashlib.sha1(w.encode()).hexdigest(),
                hashlib.sha256(w.encode()).hexdigest(),
                hashlib.sha512(w.encode()).hexdigest(),
            ]
            if h_lower in checks:
                return w
            return None

        cracked = None
        checked = 0
        for word in words[:500_000]:
            checked += 1
            r = _try(word)
            if r:
                cracked = r
                break
            if checked % 10000 == 0:
                console.print(f"[dim]Tried {checked:,} words…[/dim]")

        if cracked:
            console.print(f"\n[bold green]✓ CRACKED: {hash_str[:20]}… → [bold]{cracked}[/bold][/bold green]")
        else:
            console.print(f"\n[yellow]Not found in {checked:,} words. Try a larger wordlist or hashcat.[/yellow]")

        out = f"cracked: {cracked}" if cracked else "not found"
        result = RunResult("venus crack", 0 if cracked else 1, out, "", 0.0)
        self._record("crack", f"venus crack {hash_str[:20]}", {"hash": hash_str, "wordlist": wl_path}, result)
        return result

    # ── encode ────────────────────────────────────────────────────────────────

    def encode(self, text: str, encoding: str = "base64") -> RunResult:
        result_str = self._do_encode(text, encoding)
        console.print(Panel(f"[bold magenta]{encoding.upper()} Encode[/bold magenta]", title=BANNER))
        console.print(f"Input  : [dim]{text[:80]}[/dim]")
        console.print(f"Output : [bold green]{result_str[:200]}[/bold green]")
        result = RunResult("venus encode", 0, result_str, "", 0.0)
        self._record("encode", f"venus encode --enc {encoding}", {"text": text, "encoding": encoding}, result)
        return result

    def _do_encode(self, text: str, encoding: str) -> str:
        import codecs
        try:
            if encoding == "base64":   return base64.b64encode(text.encode()).decode()
            if encoding == "base32":   return base64.b32encode(text.encode()).decode()
            if encoding == "base16":   return text.encode().hex().upper()
            if encoding == "hex":      return text.encode().hex()
            if encoding == "url":      return urllib.parse.quote(text)
            if encoding == "rot13":    return codecs.encode(text, "rot_13")
            if encoding == "binary":   return " ".join(f"{ord(c):08b}" for c in text)
            if encoding == "morse":    return self._to_morse(text)
            if encoding == "html":     return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
        except Exception as e:
            return f"Error: {e}"
        return f"Unknown encoding: {encoding}"

    def _to_morse(self, text: str) -> str:
        MORSE = {"A":".-","B":"-...","C":"-.-.","D":"-..","E":".","F":"..-.","G":"--.","H":"....","I":"..","J":".---","K":"-.-","L":".-..","M":"--","N":"-.","O":"---","P":".--.","Q":"--.-","R":".-.","S":"...","T":"-","U":"..-","V":"...-","W":".--","X":"-..-","Y":"-.--","Z":"--..","0":"-----","1":".----","2":"..---","3":"...--","4":"....-","5":".....","6":"-....","7":"--...","8":"---..","9":"----."}
        return " ".join(MORSE.get(c.upper(), "?") for c in text if c != " ")

    # ── decode ────────────────────────────────────────────────────────────────

    def decode(self, text: str, encoding: str = "base64") -> RunResult:
        result_str = self._do_decode(text, encoding)
        console.print(Panel(f"[bold magenta]{encoding.upper()} Decode[/bold magenta]", title=BANNER))
        console.print(f"Input  : [dim]{text[:80]}[/dim]")
        console.print(f"Output : [bold green]{result_str[:200]}[/bold green]")
        result = RunResult("venus decode", 0, result_str, "", 0.0)
        self._record("decode", f"venus decode --enc {encoding}", {"text": text, "encoding": encoding}, result)
        return result

    def _do_decode(self, text: str, encoding: str) -> str:
        import codecs
        try:
            if encoding == "base64":
                pad = 4 - len(text) % 4
                if pad != 4: text += "=" * pad
                return base64.b64decode(text).decode(errors="replace")
            if encoding == "base32":
                pad = 8 - len(text) % 8
                if pad != 8: text += "=" * pad
                return base64.b32decode(text.upper()).decode(errors="replace")
            if encoding == "hex":      return bytes.fromhex(text).decode(errors="replace")
            if encoding == "url":      return urllib.parse.unquote(text)
            if encoding == "rot13":    return codecs.decode(text, "rot_13")
            if encoding == "binary":   return "".join(chr(int(b,2)) for b in text.split())
        except Exception as e:
            return f"Error: {e}"
        return f"Unknown encoding: {encoding}"

    # ── xor ───────────────────────────────────────────────────────────────────

    def xor(self, data: str, key: str, fmt: str = "hex") -> RunResult:
        try:
            if fmt == "hex":    data_bytes = bytes.fromhex(data)
            elif fmt == "base64": data_bytes = base64.b64decode(data)
            else:               data_bytes = data.encode()

            key_bytes = key.encode()
            result_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data_bytes))
            result_hex  = result_bytes.hex()
            result_text = result_bytes.decode(errors="replace")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return RunResult("", 1, "", str(e), 0.0)

        console.print(Panel(f"[bold magenta]XOR[/bold magenta]  key=[cyan]{key}[/cyan]", title=BANNER))
        console.print(f"Hex  : [bold green]{result_hex[:100]}[/bold green]")
        console.print(f"Text : [bold yellow]{result_text[:100]}[/bold yellow]")

        out = f"hex: {result_hex}\ntext: {result_text}"
        result = RunResult("venus xor", 0, out, "", 0.0)
        self._record("xor", f"venus xor --key {key}", {"data": data[:20], "key": key}, result)
        return result

    # ── factor ────────────────────────────────────────────────────────────────

    def factor(self, number: str) -> RunResult:
        console.print(Panel(f"[bold magenta]Factoring[/bold magenta] {number}", title=BANNER))

        # Try sympy first (much faster for large numbers)
        try:
            from sympy import factorint
            n = int(number)
            factors = factorint(n)
            display = " × ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(factors.items()))
            console.print(f"[green]{number} = {display}[/green]")
            out = display
        except ImportError:
            # Pure-Python trial division
            n = int(number)
            factors = []
            d = 2
            temp = n
            while d * d <= temp:
                while temp % d == 0:
                    factors.append(d)
                    temp //= d
                d += 1
            if temp > 1:
                factors.append(temp)
            display = " × ".join(map(str, factors))
            console.print(f"[green]{number} = {display}[/green]")
            out = display

        # For RSA context: show p and q
        factor_list = []
        try:
            from sympy import factorint
            factor_list = list(factorint(int(number)).keys())
        except Exception:
            pass

        if len(factor_list) == 2:
            p, q = factor_list
            console.print(f"\n[cyan]RSA context:[/cyan]  p = {p}  q = {q}")
            console.print(f"  phi(n) = (p-1)(q-1) = {(p-1)*(q-1)}")

        result = RunResult("venus factor", 0, out, "", 0.0)
        self._record("factor", f"venus factor {number}", {"number": number}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []


import re
from pathlib import Path
