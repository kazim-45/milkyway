"""♇ Pluto — AI Assistant (keyword engine + Ollama/OpenAI)"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult
console = Console(); C = "purple"

SYSTEM_PROMPT = """You are Pluto, the AI assistant inside MilkyWay CTF Toolkit.
MilkyWay planets:
- mercury (web): fuzz, sql, headers, extract, scan
- venus (crypto): identify, hash, crack, encode, decode, xor, factor, rsa
- earth (forensics): info, carve, strings, hexdump, steg, pcap
- mars (rev eng): disassemble, info, symbols, trace, r2
- jupiter (pwn): checksec, rop, template, cyclic
- neptune (cloud): jwt, cloud, url
- uranus (mobile): decompile, permissions, instrument, strings, ssl-bypass
- vulcan (network): portscan, quickscan, whois, dns, subdomain, banner
- titan (passwords): brute, spray, wordlist, cewl, analyze, mutate
- saturn (version ctrl): log, diff, redo, status, export

Suggest the right planet+command. Be concise, practical. Use code blocks."""

KEYWORD_KB = {
    "base64":("venus","decode","venus decode '<string>' --enc base64"),
    "hex":("venus","decode","venus decode '<string>' --enc hex"),
    "hash":("venus","identify","venus identify '<hash>'"),
    "md5":("venus","identify","venus identify '<hash>'"),
    "sha":("venus","identify","venus identify '<hash>'"),
    "crack":("venus","crack","venus crack '<hash>'"),
    "rsa":("venus","rsa","venus rsa --n '<n>' --e '<e>' --c '<ciphertext>'"),
    "xor":("venus","xor","venus xor '<hex>' '<key>'"),
    "fuzz":("mercury","fuzz","mercury fuzz http://target.com/FUZZ"),
    "directory":("mercury","fuzz","mercury fuzz http://target.com/FUZZ"),
    "sql":("mercury","sql","mercury sql 'http://target.com/page?id=1'"),
    "injection":("mercury","sql","mercury sql 'http://target.com/page?id=1'"),
    "http":("mercury","request","mercury request http://target.com"),
    "login":("mercury","request","mercury request http://target.com/login --method POST --data '...'"),
    "binary":("mars","info","mars info ./binary"),
    "elf":("mars","disassemble","mars disassemble ./binary"),
    "reverse":("mars","disassemble","mars disassemble ./binary"),
    "exploit":("jupiter","checksec","jupiter checksec ./binary"),
    "buffer":("jupiter","template","jupiter template ./binary"),
    "rop":("jupiter","rop","jupiter rop ./binary"),
    "cyclic":("jupiter","cyclic","jupiter cyclic 200"),
    "strings":("earth","strings","earth strings ./file --grep flag"),
    "file":("earth","info","earth info ./file"),
    "image":("earth","info","earth info ./image.png"),
    "png":("earth","steg","earth steg ./image.png"),
    "jpg":("earth","steg","earth steg ./image.jpg"),
    "pcap":("earth","pcap","earth pcap ./capture.pcap"),
    "network":("earth","pcap","earth pcap ./capture.pcap"),
    "steg":("earth","steg","earth steg ./image.jpg"),
    "steganography":("earth","steg","earth steg ./image.jpg"),
    "jwt":("neptune","jwt","neptune jwt 'eyJ...'"),
    "token":("neptune","jwt","neptune jwt 'eyJ...'"),
    "apk":("uranus","decompile","uranus decompile ./app.apk"),
    "android":("uranus","permissions","uranus permissions ./app.apk"),
    "port":("vulcan","quickscan","vulcan quickscan 10.10.10.10"),
    "scan":("vulcan","portscan","vulcan portscan 10.10.10.10"),
    "nmap":("vulcan","portscan","vulcan portscan 10.10.10.10 --ports 1-65535"),
    "subdomain":("vulcan","subdomain","vulcan subdomain example.com"),
    "dns":("vulcan","dns","vulcan dns example.com --type A"),
    "whois":("vulcan","whois","vulcan whois example.com"),
    "password":("titan","brute","titan brute 10.10.10.10 ssh -l admin"),
    "brute":("titan","brute","titan brute 10.10.10.10 ssh -l admin -w rockyou.txt"),
    "wordlist":("titan","wordlist","titan wordlist --charset alnum --min 6 --max 8"),
}

CHEATSHEETS = {
    "web": """# ☿ Mercury — Web Cheatsheet
```bash
mw> mercury fuzz http://target.com/FUZZ              # dir brute-force
mw> mercury fuzz http://target.com/FUZZ -e .php,.html # with extensions
mw> mercury sql 'http://target.com/page?id=1'         # SQLi scan
mw> mercury request http://target.com/api -X POST -d '{"user":"admin"}'
mw> mercury headers http://target.com                # security headers
mw> mercury extract response.html --type comments    # extract HTML comments
mw> mercury scan http://target.com                   # vuln scan
```""",
    "crypto": """# ♀ Venus — Crypto Cheatsheet
```bash
mw> venus identify '5f4dcc3b5aa765d61d8327deb882cf99'   # what hash is this?
mw> venus decode 'aGVsbG8=' --enc base64                 # base64 decode
mw> venus decode '68656c6c6f' --enc hex                  # hex decode
mw> venus encode 'hello' --enc rot13                     # ROT13
mw> venus hash 'password' --algo sha256                  # compute hash
mw> venus crack '5f4d...' -w rockyou.txt                 # crack hash
mw> venus xor '48656c6c6f' 'K'                          # XOR with key
mw> venus factor 3233                                    # factor n (RSA)
mw> venus rsa --n 3233 --e 17 --c 2790                  # full RSA attack
```""",
    "forensics": """# ♁ Earth — Forensics Cheatsheet
```bash
mw> earth info ./suspicious_file     # type, hashes, magic
mw> earth strings ./binary --grep flag  # hunt for flags
mw> earth hexdump ./file -l 512      # hex dump
mw> earth carve ./firmware.bin       # extract embedded files
mw> earth steg ./image.jpg           # LSB steg extraction
mw> earth pcap ./capture.pcap        # parse PCAP
```""",
    "network": """# 🌋 Vulcan — Network Cheatsheet
```bash
mw> vulcan quickscan 10.10.10.10          # fast top-100 ports
mw> vulcan portscan 10.10.10.10 -p 1-65535  # full scan
mw> vulcan dns example.com --type MX      # MX records
mw> vulcan subdomain example.com          # brute-force subdomains
mw> vulcan whois example.com              # WHOIS info
mw> vulcan banner 10.10.10.10 22          # grab banner
```""",
    "passwords": """# 🪐 Titan — Password Cheatsheet
```bash
mw> titan brute 10.10.10.10 ssh -l admin  # SSH brute
mw> titan spray 10.10.10.10 ssh -p 'Summer2024!'  # spray
mw> titan wordlist --charset digits --min 4 --max 4 -o pins.txt
mw> titan mutate names.txt -o mutations.txt
mw> titan cewl http://target.com -o custom.txt
mw> titan analyze rockyou.txt
```""",
}

class Pluto(Planet):
    NAME="pluto"; SYMBOL="♇"; DESCRIPTION="AI Assistant — tool suggestions, analysis, cheatsheets"
    TOOLS=[]

    def suggest(self,description:str,model:Optional[str]=None)->RunResult:
        console.print(Panel(f"[bold {C}]♇ Pluto Thinking…[/bold {C}]",border_style=C))
        response=self._try_ai(description,model) or self._keyword_suggest(description)
        console.print(Markdown(response))
        result=RunResult("pluto suggest",0,response,"",0.0)
        self._record("suggest",f"pluto suggest '{description[:40]}'",{"description":description},result)
        return result

    def analyze(self,file_path:str)->RunResult:
        if not Path(file_path).exists():
            console.print(f"[red]Not found: {file_path}[/red]"); return RunResult("",1,"","",0.0)
        info=self._gather_file_info(file_path)
        return self.suggest(f"I have a file: {file_path}\n\n{info}")

    def _gather_file_info(self,file_path:str)->str:
        import re, hashlib
        path=Path(file_path); raw=path.read_bytes()
        info=[f"Size: {len(raw)} bytes"]
        from milkyway.core.runner import check_tool
        if check_tool("file"):
            from milkyway.core.runner import Runner
            r=Runner().run(["file",file_path])
            info.append(f"Type: {r.stdout.strip()}")
        info.append(f"Magic: {raw[:16].hex(' ')}")
        strings=[m.group().decode("ascii") for m in re.finditer(rb'[\x20-\x7e]{6,}',raw[:4096])]
        interesting=[s for s in strings if any(k in s.lower() for k in ["flag","ctf","password","key"])]
        if interesting: info.append(f"Interesting strings: {', '.join(interesting[:5])}")
        return "\n".join(info)

    def _try_ai(self,description:str,model:Optional[str]=None)->Optional[str]:
        from milkyway.core import config as cfg
        backend=cfg.get("pluto.backend","none")
        if backend=="ollama":
            return self._ollama(description,model or cfg.get("pluto.model","mistral"))
        elif backend=="openai":
            return self._openai(description,model)
        return None

    def _ollama(self,description:str,model:str)->Optional[str]:
        import urllib.request
        try:
            payload=json.dumps({"model":model,"prompt":f"{SYSTEM_PROMPT}\n\nSituation:\n{description}","stream":False}).encode()
            req=urllib.request.Request("http://localhost:11434/api/generate",data=payload,headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=30) as resp:
                return json.loads(resp.read()).get("response","")
        except: return None

    def _openai(self,description:str,model:Optional[str])->Optional[str]:
        from milkyway.core import config as cfg
        key=cfg.get("pluto.openai_api_key","")
        if not key: return None
        try:
            payload=json.dumps({"model":model or "gpt-4o-mini","messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":description}],"max_tokens":600}).encode()
            req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=payload,
                headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},method="POST")
            with urllib.request.urlopen(req,timeout=20) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"]
        except: return None

    def _keyword_suggest(self,description:str)->str:
        desc=description.lower()
        matches=[(planet,action,cmd,kw) for kw,(planet,action,cmd) in KEYWORD_KB.items() if kw in desc]
        if not matches:
            return "## ♇ Pluto\n\nNo keyword matched. Try:\n```bash\nmw> earth info ./file\nmw> venus identify '<string>'\nmw> vulcan quickscan <ip>\n```"
        seen=set(); lines=["## ♇ Pluto Suggestion\n"]
        for planet,action,cmd,kw in matches:
            if planet not in seen:
                seen.add(planet); lines.append(f"### {planet.capitalize()} → `{action}` *(keyword: {kw})*")
                lines.append(f"\n```bash\nmw> {cmd}\n```\n")
        lines+=["---","*Enable Ollama for smarter AI: `mw> config set pluto.backend ollama`*"]
        return "\n".join(lines)

    def cheatsheet(self,topic:str)->RunResult:
        sheet=CHEATSHEETS.get(topic.lower())
        if not sheet:
            console.print(f"[yellow]Topics: {', '.join(CHEATSHEETS)}[/yellow]")
            return RunResult("",1,"","",0.0)
        console.print(Markdown(sheet))
        result=RunResult("pluto cheatsheet",0,sheet,"",0.0)
        self._record("cheatsheet",f"pluto cheatsheet {topic}",{"topic":topic},result); return result

    def get_commands(self)->List[click.Command]: return []
