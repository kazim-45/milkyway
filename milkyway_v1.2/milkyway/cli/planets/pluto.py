"""
♇ Pluto — Intelligent Assistant Planet
AI-powered tool suggestions, challenge analysis, and hint generation.
Backend: Ollama (local) or OpenAI API (optional)
"""

from __future__ import annotations

import json
from typing import List, Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult

console = Console()

PLUTO_BANNER = "[bold purple]♇ Pluto[/bold purple] [dim]— Intelligent Assistant[/dim]"

SYSTEM_PROMPT = """You are Pluto, the intelligent assistant built into MilkyWay CTF Toolkit.
MilkyWay organizes security tools into "planets":
- Mercury (☿): Web security — ffuf, sqlmap, curl, nuclei
- Venus (♀): Cryptography — hashcat, openssl, encoding/decoding
- Earth (♁): Forensics — binwalk, strings, steghide, tshark
- Mars (♂): Reverse Engineering — objdump, r2, ltrace, strace
- Jupiter (♃): Binary Exploitation — pwntools, checksec, ROPgadget
- Uranus (♅): Mobile/IoT — apktool, frida, jadx
- Neptune (♆): Cloud/Misc — aws-cli, jwt_tool, kubectl
- Saturn (🪐): Version control — log, diff, redo

When given a challenge description or situation, suggest:
1. Which planet(s) to use
2. The specific milkyway command(s) to run
3. WHY you're suggesting this approach
4. What to look for in the output

Be concise, practical, and educational. Format your response as Markdown.
Always include actual milkyway CLI commands in code blocks.
If it's a beginner, also explain the underlying concept briefly.
"""

TOOL_KB = {
    "base64": ("venus", "decode", "milkyway venus decode '<string>' --enc base64"),
    "hex": ("venus", "decode", "milkyway venus decode '<string>' --enc hex"),
    "md5": ("venus", "identify", "milkyway venus identify '<hash>'"),
    "sha": ("venus", "identify", "milkyway venus identify '<hash>'"),
    "hash": ("venus", "identify", "milkyway venus identify '<hash>'"),
    "crack": ("venus", "crack", "milkyway venus crack '<hash>' -w /path/to/wordlist.txt"),
    "fuzz": ("mercury", "fuzz", "milkyway mercury fuzz http://target.com/FUZZ"),
    "directory": ("mercury", "fuzz", "milkyway mercury fuzz http://target.com/FUZZ"),
    "sql": ("mercury", "sql", "milkyway mercury sql 'http://target.com/page?id=1'"),
    "injection": ("mercury", "sql", "milkyway mercury sql 'http://target.com/page?id=1'"),
    "login": ("mercury", "request", "milkyway mercury request http://target.com/login --method POST --data 'user=admin&pass=test'"),
    "binary": ("mars", "info", "milkyway mars info ./binary"),
    "elf": ("mars", "disassemble", "milkyway mars disassemble ./binary"),
    "reverse": ("mars", "disassemble", "milkyway mars disassemble ./binary"),
    "exploit": ("jupiter", "checksec", "milkyway jupiter checksec ./binary"),
    "buffer overflow": ("jupiter", "template", "milkyway jupiter template ./binary"),
    "rop": ("jupiter", "rop", "milkyway jupiter rop ./binary"),
    "strings": ("earth", "strings", "milkyway earth strings ./file"),
    "hidden": ("earth", "strings", "milkyway earth strings ./file --grep flag"),
    "image": ("earth", "info", "milkyway earth info ./image.png"),
    "png": ("earth", "carve", "milkyway earth carve ./image.png"),
    "jpg": ("earth", "steg_extract", "milkyway earth steg ./image.jpg"),
    "pcap": ("earth", "pcap", "milkyway earth pcap ./capture.pcap"),
    "network": ("earth", "pcap", "milkyway earth pcap ./capture.pcap -f 'http'"),
    "steg": ("earth", "steg_extract", "milkyway earth steg ./image.jpg"),
    "jwt": ("neptune", "token", "milkyway neptune jwt '<token>'"),
    "token": ("neptune", "token", "milkyway neptune jwt '<token>'"),
    "rsa": ("venus", "factor", "milkyway venus factor '<n>'"),
    "xor": ("venus", "xor", "milkyway venus xor '<data>' --key '<key>'"),
    "apk": ("uranus", "decompile", "milkyway uranus decompile ./app.apk"),
    "android": ("uranus", "decompile", "milkyway uranus decompile ./app.apk"),
}


class Pluto(Planet):
    NAME = "pluto"
    SYMBOL = "♇"
    DESCRIPTION = "AI-powered tool suggestions and challenge analysis"
    TOOLS = []

    def suggest(self, description: str, model: Optional[str] = None) -> RunResult:
        """Suggest MilkyWay tools based on challenge description."""
        console.print(Panel(f"[bold purple]Pluto Thinking...[/bold purple]", title=PLUTO_BANNER))

        # Try AI backends
        response = self._try_ai(description, model)

        if response:
            console.print(Markdown(response))
        else:
            # Fallback: keyword-based suggestion
            response = self._keyword_suggest(description)
            console.print(Markdown(response))

        result = RunResult(f"pluto suggest", 0, response, "", 0.0)
        self._record("suggest", f"pluto suggest '{description[:50]}'", {"description": description}, result)
        return result

    def analyze(self, file_path: str) -> RunResult:
        """Analyze a file and suggest next steps."""
        import os
        if not os.path.exists(file_path):
            console.print(f"[red]File not found: {file_path}[/red]")
            return RunResult("", 1, "", "File not found", 0.0)

        # Gather basic info about the file
        file_info = self._gather_file_info(file_path)
        description = f"I have a file: {file_path}\n\nFile info:\n{file_info}"

        console.print(Panel(f"[bold purple]Analyzing[/bold purple] {file_path}", title=PLUTO_BANNER))
        return self.suggest(description)

    def _gather_file_info(self, file_path: str) -> str:
        from pathlib import Path
        from milkyway.core.runner import check_tool, Runner
        r = Runner()
        info = []

        p = Path(file_path)
        info.append(f"Size: {p.stat().st_size} bytes")

        if check_tool("file"):
            result = r.run(["file", file_path])
            info.append(f"Type: {result.stdout.strip()}")

        # First few bytes
        raw = p.read_bytes()[:16]
        info.append(f"Magic: {raw.hex(' ')}")

        # Quick strings
        if check_tool("strings"):
            result = r.run(["strings", "-n", "6", file_path])
            interesting = [s for s in result.stdout.splitlines() if
                          any(kw in s.lower() for kw in ["flag", "ctf", "password", "secret", "key"])]
            if interesting:
                info.append(f"Interesting strings: {', '.join(interesting[:5])}")

        return "\n".join(info)

    def _try_ai(self, description: str, model: Optional[str] = None) -> Optional[str]:
        """Try Ollama then OpenAI."""
        from milkyway.core import config

        backend = config.get("pluto.backend", "none")

        if backend == "ollama":
            return self._try_ollama(description, model or config.get("pluto.model", "mistral"))
        elif backend == "openai":
            return self._try_openai(description, model)

        return None

    def _try_ollama(self, description: str, model: str = "mistral") -> Optional[str]:
        try:
            import urllib.request
            payload = json.dumps({
                "model": model,
                "prompt": f"{SYSTEM_PROMPT}\n\nChallenge/Situation:\n{description}",
                "stream": False,
            }).encode()
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("response", "")
        except Exception as e:
            console.print(f"[dim]Ollama unavailable ({e}), using built-in suggestions.[/dim]")
            return None

    def _try_openai(self, description: str, model: Optional[str] = None) -> Optional[str]:
        try:
            from milkyway.core import config
            api_key = config.get("pluto.openai_api_key", "")
            if not api_key:
                return None

            import urllib.request
            payload = json.dumps({
                "model": model or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": description},
                ],
                "max_tokens": 500,
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def _keyword_suggest(self, description: str) -> str:
        """Rule-based fallback when no AI backend is available."""
        desc_lower = description.lower()
        matches = []

        for keyword, (planet, action, command) in TOOL_KB.items():
            if keyword in desc_lower:
                matches.append((planet, action, command, keyword))

        if not matches:
            return """## Pluto Suggestion

I couldn't identify a specific tool for this. Here are some general starting points:

**Unknown file?**
```bash
milkyway earth info ./file
milkyway earth strings ./file
```

**Web challenge?**
```bash
milkyway mercury fuzz http://target.com/FUZZ
milkyway mercury headers http://target.com
```

**Crypto challenge?**
```bash
milkyway venus identify '<hash_or_string>'
```

**Tip**: Be more specific about what you found or what the challenge says!
Run `milkyway --help` to see all available commands.
"""

        seen_planets = set()
        lines = ["## ♇ Pluto Suggestion\n"]

        for planet, action, command, keyword in matches:
            if planet not in seen_planets:
                seen_planets.add(planet)
                lines.append(f"### {planet.capitalize()} — detected keyword: `{keyword}`")
                lines.append(f"\n```bash\n{command}\n```\n")

        lines.append("\n---")
        lines.append("*Tip: Enable Ollama for smarter AI-powered suggestions:*")
        lines.append("```bash\n# Install Ollama: https://ollama.ai\nollama pull mistral\nmilkyway config set pluto.backend ollama\n```")

        return "\n".join(lines)

    def cheatsheet(self, topic: str) -> RunResult:
        """Show a quick cheatsheet for common CTF techniques."""
        sheets = {
            "web": """# Web Security Cheatsheet
## Directory Fuzzing
```bash
milkyway mercury fuzz http://target.com/FUZZ -w common.txt
milkyway mercury fuzz http://target.com/FUZZ -e .php,.html,.txt
```
## SQL Injection
```bash
milkyway mercury sql 'http://target.com/page?id=1'
milkyway mercury sql 'http://target.com/login' --data 'user=admin&pass=test'
```
## Request Inspection
```bash
milkyway mercury request http://target.com
milkyway mercury headers http://target.com
```
""",
            "crypto": """# Cryptography Cheatsheet
## Identify hash
```bash
milkyway venus identify '<hash>'
```
## Encode/Decode
```bash
milkyway venus decode '<text>' --enc base64
milkyway venus decode '<text>' --enc hex
milkyway venus encode '<text>' --enc rot13
```
## XOR
```bash
milkyway venus xor '<hex_data>' --key '<key>'
```
## Factor RSA n
```bash
milkyway venus factor '<large_number>'
```
""",
            "forensics": """# Forensics Cheatsheet
## File recon
```bash
milkyway earth info ./suspicious_file
milkyway earth strings ./file --grep flag
milkyway earth hexdump ./file
```
## Extract embedded files
```bash
milkyway earth carve ./file
```
## Steganography
```bash
milkyway earth steg ./image.jpg
milkyway earth steg ./image.jpg --password 'secret'
```
## PCAP Analysis
```bash
milkyway earth pcap ./capture.pcap
milkyway earth pcap ./capture.pcap -f 'http'
```
""",
        }

        sheet = sheets.get(topic.lower())
        if not sheet:
            topics = ", ".join(sheets.keys())
            console.print(f"[yellow]Unknown topic '{topic}'. Available: {topics}[/yellow]")
            result = RunResult("", 1, "", "Unknown topic", 0.0)
        else:
            console.print(Markdown(sheet))
            result = RunResult(f"pluto cheatsheet {topic}", 0, sheet, "", 0.0)

        self._record("cheatsheet", f"pluto cheatsheet {topic}", {"topic": topic}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
