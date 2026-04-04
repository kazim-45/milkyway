"""
Base Planet — Abstract base for all MilkyWay planets.
Each planet wraps a domain of security tools with a consistent interface.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console

from milkyway.core.db import SaturnDB
from milkyway.core.runner import Runner, RunResult, ToolNotFoundError

console = Console()


class Planet(ABC):
    """Abstract base for MilkyWay planets."""

    NAME: str = ""
    SYMBOL: str = "●"
    DESCRIPTION: str = ""
    TOOLS: List[str] = []

    def __init__(
        self,
        db: Optional[SaturnDB] = None,
        verbose: bool = False,
        record: bool = True,
        challenge: Optional[str] = None,
        timeout: int = 300,
    ):
        self.db = db or SaturnDB()
        self.verbose = verbose
        self.record = record
        self.challenge = challenge
        self.runner = Runner(timeout=timeout, verbose=verbose)

    @property
    def challenge_id(self) -> Optional[int]:
        if not self.challenge:
            return None
        ch = self.db.get_challenge(self.challenge)
        return ch.id if ch else None

    def _record(
        self,
        action: str,
        command_line: str,
        parameters: dict,
        result: RunResult,
    ) -> Optional[int]:
        if not self.record:
            return None
        return self.db.record_run(
            planet=self.NAME,
            action=action,
            command_line=command_line,
            parameters=parameters,
            exit_code=result.exit_code,
            output=result.output,
            challenge_id=self.challenge_id,
            session_id=self.db.get_current_session(),
        )

    def _print_result(self, result: RunResult, run_id: Optional[int] = None) -> None:
        if result.timed_out:
            console.print("[yellow]⏰ Command timed out[/yellow]")
        elif result.success:
            console.print(result.stdout, end="")
            if result.stderr and self.verbose:
                console.print(result.stderr, end="", style="dim")
        else:
            console.print(result.stdout, end="")
            if result.stderr:
                console.print(result.stderr, end="", style="red dim")

        if run_id is not None:
            console.print(
                f"\n[dim]📡 Saturn recorded run #{run_id} "
                f"({result.duration:.1f}s, exit={result.exit_code})[/dim]"
            )

    def check_tools(self) -> dict[str, bool]:
        from milkyway.core.runner import check_tool
        return {t: check_tool(t) for t in self.TOOLS}

    @abstractmethod
    def get_commands(self) -> List[click.Command]:
        """Return all Click commands for this planet."""
        ...
