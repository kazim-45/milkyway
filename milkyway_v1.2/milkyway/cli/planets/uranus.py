"""
♅ Uranus — Mobile / IoT Security Planet
Wraps: apktool, jadx, frida, objection, adb, apksigner, aapt, dex2jar
"""

from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

URANUS_BANNER = "[bold blue]♅ Uranus[/bold blue] [dim]— Mobile / IoT[/dim]"


class Uranus(Planet):
    NAME = "uranus"
    SYMBOL = "♅"
    DESCRIPTION = "Mobile / IoT — APK analysis, dynamic instrumentation, ADB"
    TOOLS = ["apktool", "jadx", "frida", "objection", "adb", "aapt", "dex2jar", "apksigner"]

    # ── decompile ─────────────────────────────────────────────────────────────

    def decompile(self, apk_path: str, output_dir: Optional[str] = None, tool: str = "apktool") -> RunResult:
        """Decompile an APK with apktool or jadx."""
        path = Path(apk_path)
        if not path.exists():
            console.print(f"[red]File not found: {apk_path}[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        out = output_dir or f"{path.stem}_decompiled"
        console.print(Panel(f"[bold blue]Decompiling APK[/bold blue] {apk_path}", title=URANUS_BANNER))

        if tool == "jadx":
            if not check_tool("jadx"):
                console.print("[yellow]jadx not found. Trying apktool...[/yellow]")
                tool = "apktool"
            else:
                args = ["jadx", "-d", out, apk_path]
                console.print(f"[dim]Using jadx → {out}[/dim]\n")
                result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
                rid = self._record("decompile", " ".join(args), {"apk": apk_path, "tool": "jadx"}, result)
                if rid:
                    console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
                return result

        if not check_tool("apktool"):
            console.print("[red]apktool not found. Install: https://apktool.org/docs/install[/red]")
            return RunResult("", 1, "", "apktool not found", 0.0)

        args = ["apktool", "d", apk_path, "-o", out, "-f"]
        console.print(f"[dim]Using apktool → {out}[/dim]\n")
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("decompile", " ".join(args), {"apk": apk_path, "tool": "apktool"}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── info ──────────────────────────────────────────────────────────────────

    def info(self, apk_path: str) -> RunResult:
        """Show APK metadata with aapt / apktool."""
        console.print(Panel(f"[bold blue]APK Info[/bold blue] {apk_path}", title=URANUS_BANNER))
        all_out = []

        if check_tool("aapt"):
            args = ["aapt", "dump", "badging", apk_path]
            result = self.runner.run(args)
            # Extract key lines
            for line in result.stdout.splitlines():
                if any(k in line for k in ["package", "sdkVersion", "application-label",
                                           "uses-permission", "activity"]):
                    console.print(f"  [cyan]{line}[/cyan]")
            all_out.append(result.stdout)
        elif check_tool("apktool"):
            args = ["apktool", "dump", "badging", apk_path]
            result = self.runner.run(args)
            console.print(result.stdout[:2000])
            all_out.append(result.stdout)
        else:
            # Pure Python: read AndroidManifest from ZIP
            self._parse_apk_zip(apk_path)

        combined = "\n".join(all_out)
        result = RunResult(f"uranus info {apk_path}", 0, combined, "", 0.0)
        self._record("info", f"uranus info {apk_path}", {"apk": apk_path}, result)
        return result

    def _parse_apk_zip(self, apk_path: str) -> None:
        """Fallback: list APK contents as a ZIP."""
        try:
            import zipfile
            with zipfile.ZipFile(apk_path) as z:
                names = z.namelist()
                console.print(f"\n[bold]APK contents ({len(names)} files):[/bold]")
                for name in sorted(names)[:50]:
                    console.print(f"  [dim]{name}[/dim]")
                if len(names) > 50:
                    console.print(f"  [dim]... and {len(names)-50} more[/dim]")
        except Exception as e:
            console.print(f"[red]Cannot read APK: {e}[/red]")

    # ── permissions ───────────────────────────────────────────────────────────

    def permissions(self, apk_path: str) -> RunResult:
        """List permissions declared in the APK."""
        console.print(Panel(f"[bold blue]APK Permissions[/bold blue] {apk_path}", title=URANUS_BANNER))

        DANGEROUS_PERMS = {
            "READ_CONTACTS", "WRITE_CONTACTS", "READ_CALL_LOG", "WRITE_CALL_LOG",
            "READ_SMS", "RECEIVE_SMS", "SEND_SMS", "CAMERA", "RECORD_AUDIO",
            "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "READ_EXTERNAL_STORAGE",
            "WRITE_EXTERNAL_STORAGE", "READ_PHONE_STATE", "CALL_PHONE",
        }

        all_perms = []

        if check_tool("aapt"):
            result = self.runner.run(["aapt", "dump", "permissions", apk_path])
            for line in result.stdout.splitlines():
                if "uses-permission" in line or "permission" in line.lower():
                    perm = line.strip()
                    all_perms.append(perm)
        else:
            try:
                import zipfile, re
                with zipfile.ZipFile(apk_path) as z:
                    if "AndroidManifest.xml" in z.namelist():
                        raw = z.read("AndroidManifest.xml")
                        perms = re.findall(rb'android\.permission\.(\w+)', raw)
                        all_perms = [f"android.permission.{p.decode()}" for p in perms]
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Permission", style="white")
        table.add_column("Risk", width=12)
        for perm in sorted(set(all_perms)):
            perm_name = perm.split(".")[-1].split("'")[0].strip()
            risk = "[bold red]DANGEROUS[/bold red]" if perm_name in DANGEROUS_PERMS else "[dim]Normal[/dim]"
            table.add_row(perm, risk)
        console.print(table)

        out = "\n".join(all_perms)
        result = RunResult(f"uranus permissions {apk_path}", 0, out, "", 0.0)
        self._record("permissions", f"uranus permissions {apk_path}", {"apk": apk_path}, result)
        return result

    # ── instrument ────────────────────────────────────────────────────────────

    def instrument(self, target: str, script: Optional[str] = None, mode: str = "frida") -> RunResult:
        """Dynamic instrumentation with Frida or Objection."""
        console.print(Panel(f"[bold blue]Instrumentation[/bold blue] {target}", title=URANUS_BANNER))

        if mode == "objection":
            if not check_tool("objection"):
                console.print("[red]objection not found. Install: pip install objection[/red]")
                return RunResult("", 1, "", "Not found", 0.0)
            args = ["objection", "--gadget", target, "explore"]
        else:
            if not check_tool("frida"):
                console.print("[red]frida not found. Install: pip install frida-tools[/red]")
                return RunResult("", 1, "", "Not found", 0.0)
            args = ["frida", "-U", target]
            if script:
                args += ["-l", script]

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("instrument", " ".join(args), {"target": target, "mode": mode}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── adb ───────────────────────────────────────────────────────────────────

    def adb(self, command: str) -> RunResult:
        """Run ADB commands against a connected device."""
        if not check_tool("adb"):
            console.print("[red]adb not found. Install Android SDK platform-tools.[/red]")
            return RunResult("", 1, "", "Not found", 0.0)

        console.print(Panel(f"[bold blue]ADB[/bold blue] {command}", title=URANUS_BANNER))
        args = ["adb"] + shlex.split(command)
        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("adb", " ".join(args), {"command": command}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    # ── strings ───────────────────────────────────────────────────────────────

    def strings(self, apk_path: str, grep: Optional[str] = None) -> RunResult:
        """Extract strings from DEX/APK — great for finding hardcoded secrets."""
        console.print(Panel(f"[bold blue]APK Strings[/bold blue] {apk_path}", title=URANUS_BANNER))

        found = []
        INTERESTING = ["password", "secret", "key", "token", "api", "flag", "ctf",
                       "http", "https", "jdbc", "sqlite", "firebase", "aws"]
        try:
            import zipfile, re
            with zipfile.ZipFile(apk_path) as z:
                for name in z.namelist():
                    if name.endswith((".dex", ".xml", ".json", "properties")):
                        try:
                            raw = z.read(name)
                            # Extract printable ASCII strings ≥ 6 chars
                            strings = re.findall(rb'[\x20-\x7e]{6,}', raw)
                            for s in strings:
                                s_str = s.decode("ascii", errors="ignore")
                                if grep:
                                    import re as re2
                                    if re2.search(grep, s_str, re2.IGNORECASE):
                                        found.append((name, s_str))
                                elif any(kw in s_str.lower() for kw in INTERESTING):
                                    found.append((name, s_str))
                        except Exception:
                            pass
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return RunResult("", 1, "", str(e), 0.0)

        if found:
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("File", style="dim", width=30)
            table.add_column("String", style="bold yellow")
            for fname, s in found[:100]:
                table.add_row(fname.split("/")[-1], s[:80])
            console.print(table)
            if len(found) > 100:
                console.print(f"[dim]... and {len(found)-100} more[/dim]")
        else:
            console.print("[dim]No interesting strings found.[/dim]")

        out = "\n".join(f"{f}: {s}" for f, s in found)
        result = RunResult(f"uranus strings {apk_path}", 0, out, "", 0.0)
        self._record("strings", f"uranus strings {apk_path}", {"apk": apk_path, "grep": grep}, result)
        return result

    # ── ssl-bypass ────────────────────────────────────────────────────────────

    def ssl_bypass(self, package: str) -> RunResult:
        """Attempt SSL pinning bypass with Frida/Objection."""
        console.print(Panel(f"[bold blue]SSL Pinning Bypass[/bold blue] {package}", title=URANUS_BANNER))

        if check_tool("objection"):
            console.print("[dim]Using objection SSL bypass...[/dim]")
            args = ["objection", "--gadget", package, "run",
                    "android sslpinning disable"]
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        elif check_tool("frida"):
            # Write a quick Frida script
            script_content = """
Java.perform(function() {
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    var TrustManager = Java.registerClass({
        name: 'com.milkyway.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    SSLContext.init.overload('[Ljavax.net.ssl.KeyManager;',
        '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation =
        function(km, tm, sr) {
            this.init.call(this, km, [TrustManager.$new()], sr);
        };
    console.log('[MilkyWay] SSL pinning disabled');
});
"""
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(script_content)
                script_path = f.name
            args = ["frida", "-U", "-l", script_path, package]
            result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        else:
            console.print("[red]Neither frida nor objection found.[/red]")
            return RunResult("", 1, "", "Tool not found", 0.0)

        rid = self._record("ssl_bypass", f"uranus ssl-bypass {package}", {"package": package}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn #{rid}[/dim]")
        return result

    def get_commands(self) -> List[click.Command]:
        return []
