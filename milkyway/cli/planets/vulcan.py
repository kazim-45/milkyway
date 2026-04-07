"""🌋 Vulcan — Network Recon & OSINT (pure Python, nmap optional)"""
from __future__ import annotations
import concurrent.futures, socket, ssl, struct, time, urllib.request
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool
console = Console(); C = "bright_red"

TOP_PORTS=[21,22,23,25,53,80,110,111,135,139,143,389,443,445,465,587,
           993,995,1433,1723,3306,3389,5432,5900,6379,8080,8443,8888,27017]
PORT_SERVICES={21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
               110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",3306:"MySQL",
               3389:"RDP",5432:"PostgreSQL",5900:"VNC",6379:"Redis",
               8080:"HTTP-Alt",8443:"HTTPS-Alt",27017:"MongoDB"}

def _tcp_connect(host,port,timeout=1.0):
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.settimeout(timeout)
        r=s.connect_ex((host,port)); s.close()
        return r==0
    except: return False

def _grab_banner(host,port,timeout=3):
    try:
        s=socket.socket(); s.settimeout(timeout)
        s.connect((host,port))
        if port==443:
            ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
            s=ctx.wrap_socket(s,server_hostname=host)
        s.send(b"HEAD / HTTP/1.0\r\nHost: "+host.encode()+b"\r\n\r\n")
        banner=s.recv(512).decode("utf-8",errors="replace").strip()
        s.close(); return banner.splitlines()[0] if banner else ""
    except: return ""

class Vulcan(Planet):
    NAME="vulcan"; SYMBOL="🌋"; DESCRIPTION="Network Recon & OSINT — port scan, WHOIS, DNS"
    TOOLS=["nmap","whois","dig","nslookup"]

    def portscan(self,target:str,ports:str="1-1000",speed:int=3,service_detection:bool=True,
                 os_detect:bool=False,script:Optional[str]=None,output:Optional[str]=None)->RunResult:
        console.print(Panel(f"[bold {C}]🌋 Port Scan[/bold {C}] {target}",border_style=C))
        if check_tool("nmap"):
            args=["nmap",f"-T{speed}","-p",ports,target]
            if service_detection: args.append("-sV")
            if os_detect: args+=["-O","--osscan-guess"]
            if script: args+=[f"--script={script}"]
            if output: args+=["-oN",output]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
            self._record("portscan"," ".join(args),{"target":target},result); return result
        return self._py_scan(target,ports,service_detection)

    def quickscan(self,target:str)->RunResult:
        console.print(Panel(f"[bold {C}]🌋 Quick Scan[/bold {C}] {target}",border_style=C))
        if check_tool("nmap"):
            args=["nmap","-T4","--top-ports","100","-sV",target]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
            self._record("quickscan"," ".join(args),{"target":target},result); return result
        return self._py_scan(target,"top",True)

    def _py_scan(self,target:str,ports_spec:str,service_detect:bool)->RunResult:
        console.print(f"  [dim]nmap not found — Python port scanner[/dim]\n")
        if ports_spec=="top": ports=TOP_PORTS
        elif "-" in ports_spec:
            start,end=[int(x) for x in ports_spec.split("-")]; ports=list(range(start,min(end+1,65536)))
        else: ports=[int(p.strip()) for p in ports_spec.split(",")]
        table=Table(show_header=True,header_style=f"bold {C}",border_style="dim")
        table.add_column("Port",width=8); table.add_column("Service",width=14)
        table.add_column("State",width=10); table.add_column("Banner")
        found=[]
        def probe(port):
            open_=_tcp_connect(target,port,timeout=0.8)
            return port,open_
        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as ex:
            for port,open_ in sorted(ex.map(probe,ports)):
                if open_:
                    svc=PORT_SERVICES.get(port,"")
                    banner=_grab_banner(target,port) if service_detect else ""
                    table.add_row(str(port),svc,"[bold green]OPEN[/bold green]",banner[:50])
                    found.append(port)
        console.print(table)
        console.print(f"\n  [dim]{len(found)} open ports found[/dim]")
        out="\n".join(f"{p} OPEN {PORT_SERVICES.get(p,'')}" for p in found)
        result=RunResult(f"vulcan scan {target}",0,out,"",0.0)
        self._record("portscan",f"vulcan portscan {target}",{"target":target},result); return result

    def whois(self,target:str)->RunResult:
        console.print(Panel(f"[bold {C}]🌋 WHOIS[/bold {C}] {target}",border_style=C))
        if check_tool("whois"):
            result=self.runner.run(["whois",target])
            for line in result.stdout.splitlines():
                if any(k in line.lower() for k in ["registrar","creation","expiry","name server","org","country"]):
                    console.print(f"  [cyan]{line}[/cyan]")
            self._record("whois",f"vulcan whois {target}",{"target":target},result); return result
        # Socket WHOIS
        try:
            s=socket.socket(); s.settimeout(8); s.connect(("whois.iana.org",43))
            s.sendall(f"{target}\r\n".encode()); raw=b""
            while True:
                d=s.recv(4096)
                if not d: break
                raw+=d
            s.close()
            out=raw.decode("utf-8",errors="replace")
            console.print(out[:2000])
        except Exception as e:
            out=str(e); console.print(f"  [red]{e}[/red]")
        result=RunResult(f"vulcan whois {target}",0,out,"",0.0)
        self._record("whois",f"vulcan whois {target}",{"target":target},result); return result

    def dns(self,target:str,record_type:str="A")->RunResult:
        console.print(Panel(f"[bold {C}]🌋 DNS [{record_type}][/bold {C}] {target}",border_style=C))
        if check_tool("dig"):
            result=self.runner.run(["dig","+short",record_type,target])
            console.print(result.stdout or "[dim]No records[/dim]")
            self._record("dns",f"vulcan dns {target}",{"target":target},result); return result
        # stdlib fallback
        try:
            addrs=socket.getaddrinfo(target,None)
            results=sorted(set(a[4][0] for a in addrs))
            for ip in results: console.print(f"  [bold green]{ip}[/bold green]")
            out="\n".join(results)
        except Exception as e:
            out=str(e); console.print(f"  [red]{e}[/red]")
        result=RunResult(f"vulcan dns {target}",0,out,"",0.0)
        self._record("dns",f"vulcan dns {target}",{"target":target,"type":record_type},result); return result

    def subdomain(self,domain:str,wordlist:Optional[str]=None)->RunResult:
        console.print(Panel(f"[bold {C}]🌋 Subdomain Enum[/bold {C}] {domain}",border_style=C))
        words=Path(wordlist).read_text().splitlines() if wordlist and Path(wordlist).exists() else \
              ["www","mail","ftp","admin","test","dev","staging","api","blog","shop","vpn","remote",
               "portal","cdn","static","m","mobile","app","ns1","ns2","smtp","pop","imap","beta"]
        found=[]
        def probe(word):
            sub=f"{word}.{domain}"
            try: ip=socket.gethostbyname(sub); return sub,ip
            except: return sub,None
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            for sub,ip in ex.map(probe,words):
                if ip:
                    found.append((sub,ip))
                    console.print(f"  [bold green]FOUND[/bold green]  {sub:<40} → {ip}")
        if not found: console.print("  [dim]No subdomains resolved[/dim]")
        out="\n".join(f"{s} {ip}" for s,ip in found)
        result=RunResult(f"vulcan subdomain {domain}",0,out,"",0.0)
        self._record("subdomain",f"vulcan subdomain {domain}",{"domain":domain},result); return result

    def banner(self,host:str,port:int)->RunResult:
        console.print(Panel(f"[bold {C}]🌋 Banner Grab[/bold {C}] {host}:{port}",border_style=C))
        b=_grab_banner(host,port)
        console.print(f"  [bold cyan]{b or '(no banner)'}[/bold cyan]")
        result=RunResult(f"vulcan banner {host} {port}",0,b,"",0.0)
        self._record("banner",f"vulcan banner {host} {port}",{"host":host,"port":port},result); return result

    def get_commands(self)->List[click.Command]: return []
