"""♅ Uranus — Mobile/IoT (pure Python APK parsing, tools optional)"""
from __future__ import annotations
import re, zipfile
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool
console = Console(); C = "bright_blue"

DANGEROUS_PERMS = {"READ_CONTACTS","WRITE_CONTACTS","READ_CALL_LOG","CAMERA",
                   "RECORD_AUDIO","ACCESS_FINE_LOCATION","READ_SMS","SEND_SMS",
                   "READ_EXTERNAL_STORAGE","WRITE_EXTERNAL_STORAGE","READ_PHONE_STATE"}

class Uranus(Planet):
    NAME="uranus"; SYMBOL="♅"; DESCRIPTION="Mobile/IoT — APK analysis, instrumentation, ADB"
    TOOLS=["apktool","jadx","frida","objection","adb","aapt"]

    def decompile(self,apk_path:str,output_dir:Optional[str]=None,tool:str="apktool")->RunResult:
        console.print(Panel(f"[bold {C}]♅ Decompile[/bold {C}] {apk_path}",border_style=C))
        out=output_dir or f"{Path(apk_path).stem}_decompiled"
        for t,args_fn in [("jadx",lambda:["jadx","-d",out,apk_path]),
                           ("apktool",lambda:["apktool","d",apk_path,"-o",out,"-f"])]:
            if check_tool(t):
                result=self.runner.run(args_fn(),streaming=True,on_line=lambda l:console.print(l))
                self._record("decompile"," ".join(args_fn()),{"apk":apk_path},result); return result
        console.print("  [yellow]apktool/jadx not found — using Python APK parser[/yellow]\n")
        return self.info(apk_path)

    def info(self,apk_path:str)->RunResult:
        console.print(Panel(f"[bold {C}]♅ APK Info[/bold {C}] {apk_path}",border_style=C))
        if check_tool("aapt"):
            result=self.runner.run(["aapt","dump","badging",apk_path])
            for line in result.stdout.splitlines():
                if any(k in line for k in ["package","sdkVersion","application-label","activity"]):
                    console.print(f"  [cyan]{line}[/cyan]")
            self._record("info",f"uranus info {apk_path}",{"apk":apk_path},result); return result
        # Python ZIP reader
        try:
            with zipfile.ZipFile(apk_path) as z:
                names=z.namelist()
                table=Table(show_header=True,header_style=f"bold {C}",border_style="dim")
                table.add_column("File",style="white"); table.add_column("Size",width=10)
                for n in sorted(names)[:60]:
                    info=z.getinfo(n)
                    table.add_row(n,str(info.file_size))
                console.print(table)
                console.print(f"\n  [dim]{len(names)} files in APK[/dim]")
            result=RunResult(f"uranus info {apk_path}",0,f"{len(names)} files","",0.0)
        except Exception as e:
            console.print(f"  [red]{e}[/red]"); result=RunResult("",1,str(e),"",0.0)
        self._record("info",f"uranus info {apk_path}",{"apk":apk_path},result); return result

    def permissions(self,apk_path:str)->RunResult:
        console.print(Panel(f"[bold {C}]♅ Permissions[/bold {C}] {apk_path}",border_style=C))
        perms=[]
        try:
            with zipfile.ZipFile(apk_path) as z:
                if "AndroidManifest.xml" in z.namelist():
                    raw=z.read("AndroidManifest.xml")
                    found=re.findall(rb'android\.permission\.(\w+)',raw)
                    perms=[p.decode() for p in found]
        except Exception as e:
            if check_tool("aapt"):
                r=self.runner.run(["aapt","dump","permissions",apk_path])
                perms=re.findall(r"android\.permission\.(\w+)",r.stdout)
            else:
                console.print(f"  [red]{e}[/red]")
        table=Table(show_header=True,header_style=f"bold {C}",border_style="dim")
        table.add_column("Permission"); table.add_column("Risk",width=12)
        for p in sorted(set(perms)):
            risk="[bold red]DANGEROUS[/bold red]" if p in DANGEROUS_PERMS else "[dim]Normal[/dim]"
            table.add_row(f"android.permission.{p}",risk)
        console.print(table)
        out="\n".join(f"android.permission.{p}" for p in perms)
        result=RunResult(f"uranus permissions {apk_path}",0,out,"",0.0)
        self._record("permissions",f"uranus permissions {apk_path}",{"apk":apk_path},result); return result

    def strings(self,apk_path:str,grep:Optional[str]=None)->RunResult:
        console.print(Panel(f"[bold {C}]♅ APK Strings[/bold {C}] {apk_path}",border_style=C))
        INTERESTING=["password","secret","key","token","api","flag","http","firebase","aws"]
        found=[]
        try:
            with zipfile.ZipFile(apk_path) as z:
                for name in z.namelist():
                    if name.endswith((".dex",".xml",".json","properties")):
                        try:
                            raw=z.read(name)
                            strings=re.findall(rb'[\x20-\x7e]{6,}',raw)
                            for s in strings:
                                s_str=s.decode("ascii",errors="ignore")
                                if grep:
                                    if re.search(grep,s_str,re.IGNORECASE): found.append((name,s_str))
                                elif any(k in s_str.lower() for k in INTERESTING):
                                    found.append((name,s_str))
                        except: pass
        except Exception as e:
            console.print(f"  [red]{e}[/red]")
        table=Table(show_header=True,header_style=f"bold {C}",border_style="dim")
        table.add_column("File",style="dim",width=25); table.add_column("String",style="bold yellow")
        for fname,s in found[:80]: table.add_row(fname.split("/")[-1],s[:80])
        console.print(table)
        out="\n".join(f"{f}: {s}" for f,s in found)
        result=RunResult(f"uranus strings {apk_path}",0,out,"",0.0)
        self._record("strings",f"uranus strings {apk_path}",{"apk":apk_path},result); return result

    def instrument(self,target:str,script:Optional[str]=None,mode:str="frida")->RunResult:
        console.print(Panel(f"[bold {C}]♅ Instrument[/bold {C}] {target}",border_style=C))
        tool="objection" if mode=="objection" else "frida"
        if not check_tool(tool):
            console.print(f"  [yellow]{tool} not installed — install: pip install {tool}-tools[/yellow]")
            return RunResult("",1,"Tool not found","",0.0)
        args=(["objection","--gadget",target,"explore"] if mode=="objection"
              else (["frida","-U","-l",script,target] if script else ["frida","-U",target]))
        result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
        self._record("instrument"," ".join(args),{"target":target},result); return result

    def adb(self,command:str)->RunResult:
        import shlex
        console.print(Panel(f"[bold {C}]♅ ADB[/bold {C}] {command}",border_style=C))
        if not check_tool("adb"):
            console.print("  [yellow]adb not found — install Android SDK platform-tools[/yellow]")
            return RunResult("",1,"adb not found","",0.0)
        args=["adb"]+shlex.split(command)
        result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
        self._record("adb"," ".join(args),{"command":command},result); return result

    def ssl_bypass(self,package:str)->RunResult:
        console.print(Panel(f"[bold {C}]♅ SSL Bypass[/bold {C}] {package}",border_style=C))
        if check_tool("objection"):
            args=["objection","--gadget",package,"run","android sslpinning disable"]
            result=self.runner.run(args,streaming=True,on_line=lambda l:console.print(l))
        else:
            console.print("  [yellow]objection not installed — install: pip install objection[/yellow]")
            result=RunResult("",1,"objection not found","",0.0)
        self._record("ssl_bypass",f"uranus ssl-bypass {package}",{"package":package},result); return result

    def get_commands(self)->List[click.Command]: return []
