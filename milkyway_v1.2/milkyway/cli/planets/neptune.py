"""
♆ Neptune — Cloud & Miscellaneous Planet
Wraps: jwt_tool, aws-cli, kubectl, URL analysis
"""

from __future__ import annotations

import base64
import json
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from milkyway.cli.planets.base import Planet
from milkyway.core.runner import RunResult, check_tool

console = Console()

NEPTUNE_BANNER = "[bold blue]♆ Neptune[/bold blue] [dim]— Cloud & Misc[/dim]"


class Neptune(Planet):
    NAME = "neptune"
    SYMBOL = "♆"
    DESCRIPTION = "Cloud & Misc — JWT analysis, cloud enum, token cracking"
    TOOLS = ["aws", "kubectl", "jwt_tool"]

    # ── JWT ───────────────────────────────────────────────────────────────────

    def jwt(self, token: str, secret: Optional[str] = None, crack: bool = False) -> RunResult:
        """Decode and analyze JWT tokens."""
        console.print(Panel(f"[bold blue]JWT Analysis[/bold blue]", title=NEPTUNE_BANNER))

        parts = token.strip().split(".")
        if len(parts) != 3:
            console.print("[red]Invalid JWT format (expected 3 parts separated by '.')[/red]")
            return RunResult("", 1, "", "Invalid JWT", 0.0)

        def decode_part(part: str) -> dict:
            padding = 4 - len(part) % 4
            if padding != 4:
                part += "=" * padding
            try:
                return json.loads(base64.urlsafe_b64decode(part))
            except Exception:
                return {"raw": part}

        header = decode_part(parts[0])
        payload = decode_part(parts[1])
        signature = parts[2]

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Section")
        table.add_column("Content")

        table.add_row("Algorithm", str(header.get("alg", "unknown")))
        table.add_row("Type", str(header.get("typ", "unknown")))
        console.print(table)

        console.print("\n[bold]Header:[/bold]")
        console.print(Syntax(json.dumps(header, indent=2), "json", theme="monokai"))
        console.print("\n[bold]Payload:[/bold]")
        console.print(Syntax(json.dumps(payload, indent=2), "json", theme="monokai"))
        console.print(f"\n[bold]Signature:[/bold] [dim]{signature[:40]}...[/dim]")

        # Check for vulnerabilities
        alg = header.get("alg", "").lower()
        issues = []
        if alg == "none":
            issues.append("🚨 Algorithm is 'none' — signature not verified!")
        if alg == "hs256" and secret:
            issues.append(f"🔑 Try verifying with secret: {secret}")

        if issues:
            console.print("\n[bold yellow]Potential Issues:[/bold yellow]")
            for issue in issues:
                console.print(f"  {issue}")

        out = json.dumps({"header": header, "payload": payload, "issues": issues}, indent=2)
        result = RunResult(f"neptune jwt", 0, out, "", 0.0)
        self._record("jwt", f"neptune jwt", {"token": token[:20] + "..."}, result)
        return result

    # ── aws enum ──────────────────────────────────────────────────────────────

    def cloud(self, provider: str = "aws", command: str = "whoami") -> RunResult:
        """Cloud enumeration commands."""
        console.print(Panel(f"[bold blue]{provider.upper()} Enumeration[/bold blue]", title=NEPTUNE_BANNER))

        if provider == "aws":
            if not check_tool("aws"):
                console.print("[red]aws-cli not found. Install: pip install awscli[/red]")
                return RunResult("", 1, "", "aws not found", 0.0)

            COMMANDS = {
                "whoami": ["aws", "sts", "get-caller-identity"],
                "buckets": ["aws", "s3", "ls"],
                "ec2": ["aws", "ec2", "describe-instances", "--query",
                        "Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress}"],
                "iam": ["aws", "iam", "list-users"],
                "secrets": ["aws", "secretsmanager", "list-secrets"],
            }
            args = COMMANDS.get(command, ["aws"] + command.split())

        elif provider == "k8s" or provider == "kubectl":
            if not check_tool("kubectl"):
                console.print("[red]kubectl not found[/red]")
                return RunResult("", 1, "", "", 0.0)
            args = ["kubectl"] + command.split()
        else:
            console.print(f"[red]Unknown provider: {provider}[/red]")
            return RunResult("", 1, "", "", 0.0)

        result = self.runner.run(args, streaming=True, on_line=lambda l: console.print(l))
        rid = self._record("cloud", " ".join(args), {"provider": provider, "command": command}, result)
        if rid:
            console.print(f"\n[dim]📡 Saturn recorded run #{rid}[/dim]")
        return result

    # ── url decode ────────────────────────────────────────────────────────────

    def url(self, target: str, action: str = "info") -> RunResult:
        """URL analysis — decode, parse, extract components."""
        import urllib.parse
        console.print(Panel(f"[bold blue]URL Analysis[/bold blue]", title=NEPTUNE_BANNER))

        if action == "decode":
            result_str = urllib.parse.unquote(target)
            console.print(f"Decoded: [bold green]{result_str}[/bold green]")
        elif action == "encode":
            result_str = urllib.parse.quote(target)
            console.print(f"Encoded: [bold green]{result_str}[/bold green]")
        elif action == "info":
            parsed = urllib.parse.urlparse(target)
            params = urllib.parse.parse_qs(parsed.query)

            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Component")
            table.add_column("Value")
            table.add_row("Scheme", parsed.scheme or "N/A")
            table.add_row("Host", parsed.netloc or "N/A")
            table.add_row("Path", parsed.path or "/")
            table.add_row("Query", parsed.query or "")
            table.add_row("Fragment", parsed.fragment or "")
            for k, v in params.items():
                table.add_row(f"  Param: {k}", ", ".join(v))
            console.print(table)
            result_str = str(dict(scheme=parsed.scheme, host=parsed.netloc, path=parsed.path))
        else:
            result_str = "Unknown action"

        result = RunResult(f"neptune url {action}", 0, result_str, "", 0.0)
        self._record("url", f"neptune url {action}", {"target": target, "action": action}, result)
        return result

    def get_commands(self) -> List[click.Command]:
        return []
