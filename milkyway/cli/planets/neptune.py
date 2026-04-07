"""
♆ Neptune — Cloud & Misc (pure Python core)
"""
from __future__ import annotations
import base64, json, urllib.parse
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool
console = Console(); C = "blue"

class Neptune(Planet):
    NAME="neptune"; SYMBOL="♆"; DESCRIPTION="Cloud & Misc — JWT, cloud enum, URL tools"
    TOOLS=["aws","kubectl"]

    def jwt(self,token:str,secret:Optional[str]=None,crack:bool=False)->RunResult:
        console.print(Panel(f"[bold {C}]♆ JWT Analyze[/bold {C}]",border_style=C))
        parts=token.strip().split(".")
        if len(parts)!=3:
            console.print("[red]Invalid JWT (need 3 parts)[/red]"); return RunResult("",1,"","Invalid",0.0)
        def decode_part(p):
            missing=4-len(p)%4
            if missing!=4: p+="="*missing
            try: return json.loads(base64.urlsafe_b64decode(p))
            except: return {"raw":p}
        header=decode_part(parts[0]); payload=decode_part(parts[1])
        table=Table(show_header=False,border_style="dim")
        table.add_column("Key",style=C,width=16); table.add_column("Value")
        table.add_row("Algorithm", str(header.get("alg","?")))
        table.add_row("Type",      str(header.get("typ","?")))
        for k,v in payload.items(): table.add_row(str(k),str(v)[:80])
        console.print(table)
        alg=header.get("alg","").lower()
        issues=[]
        if alg=="none": issues.append("🚨 alg=none — signature not verified!")
        if alg.startswith("hs") and secret: issues.append(f"🔑 Verify with secret: {secret}")
        if issues:
            console.print("\n[bold yellow]⚠ Issues:[/bold yellow]")
            for i in issues: console.print(f"  {i}")
        out=json.dumps({"header":header,"payload":payload,"issues":issues},indent=2)
        result=RunResult("neptune jwt",0,out,"",0.0)
        self._record("jwt","neptune jwt",{"token":token[:20]+"..."},result); return result

    def cloud(self,provider:str="aws",command:str="whoami")->RunResult:
        console.print(Panel(f"[bold {C}]♆ Cloud [{provider.upper()}][/bold {C}]",border_style=C))
        CMDS={"aws":{"whoami":["aws","sts","get-caller-identity"],"buckets":["aws","s3","ls"],
                     "ec2":["aws","ec2","describe-instances"],"iam":["aws","iam","list-users"]},
              "k8s":{"pods":["kubectl","get","pods"],"ns":["kubectl","get","namespaces"]}}
        if not check_tool(provider if provider!="k8s" else "kubectl"):
            console.print(f"  [yellow]{provider} CLI not found — install it separately[/yellow]")
            return RunResult("",1,"Tool not found","",0.0)
        args=CMDS.get(provider,{}).get(command,[provider]+command.split())
        result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
        self._record("cloud"," ".join(args),{"provider":provider,"command":command},result); return result

    def url(self,target:str,action:str="info")->RunResult:
        console.print(Panel(f"[bold {C}]♆ URL [{action}][/bold {C}]",border_style=C))
        if action=="decode": out=urllib.parse.unquote(target); console.print(f"  [bold green]{out}[/bold green]")
        elif action=="encode": out=urllib.parse.quote(target); console.print(f"  [bold green]{out}[/bold green]")
        else:
            p=urllib.parse.urlparse(target); params=urllib.parse.parse_qs(p.query)
            table=Table(show_header=False,border_style="dim")
            table.add_column("Key",style=C,width=14); table.add_column("Value")
            table.add_row("Scheme",p.scheme); table.add_row("Host",p.netloc)
            table.add_row("Path",p.path); table.add_row("Query",p.query)
            for k,v in params.items(): table.add_row(f"  {k}",", ".join(v))
            console.print(table); out=str(dict(scheme=p.scheme,host=p.netloc,path=p.path))
        result=RunResult("neptune url",0,out,"",0.0)
        self._record("url",f"neptune url {action}",{"target":target},result); return result

    def get_commands(self)->List[click.Command]: return []
