"""
Runner — Safe subprocess execution with timeout, output capture, and Saturn integration.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

console = Console()


@dataclass
class RunResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Combined stdout + stderr."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)

    def __str__(self) -> str:
        return self.output


def check_tool(name: str) -> bool:
    """Return True if `name` is available on PATH."""
    return shutil.which(name) is not None


def require_tool(name: str, install_hint: str = "") -> None:
    """Raise ToolNotFoundError if tool is missing."""
    if not check_tool(name):
        msg = f"Tool '{name}' not found on PATH."
        if install_hint:
            msg += f"\nInstall hint: {install_hint}"
        raise ToolNotFoundError(name, msg)


class ToolNotFoundError(Exception):
    def __init__(self, tool: str, message: str = ""):
        self.tool = tool
        super().__init__(message or f"Tool '{tool}' not found")


class Runner:
    """Execute external tools safely with output capture."""

    DEFAULT_TIMEOUT = 300  # 5 minutes

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose

    def run(
        self,
        args: List[str],
        *,
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
        streaming: bool = False,
        on_line: Optional[Callable[[str], None]] = None,
        spinner_text: str = "Running...",
    ) -> RunResult:
        cmd_str = " ".join(shlex.quote(str(a)) for a in args)

        if self.verbose:
            console.print(f"[dim]$ {cmd_str}[/dim]")

        start = time.monotonic()
        try:
            if streaming or on_line:
                return self._run_streaming(args, cmd_str, cwd, env, on_line, spinner_text, start)
            else:
                return self._run_captured(args, cmd_str, cwd, env, spinner_text, start)
        except FileNotFoundError:
            tool = args[0]
            raise ToolNotFoundError(tool, f"'{tool}' not found. Is it installed?")

    def _run_captured(
        self,
        args: List[str],
        cmd_str: str,
        cwd: Optional[Path],
        env: Optional[dict],
        spinner_text: str,
        start: float,
    ) -> RunResult:
        timed_out = False
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
                env=env,
            )
            duration = time.monotonic() - start
            return RunResult(
                command=cmd_str,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.monotonic() - start
            return RunResult(
                command=cmd_str,
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                duration=duration,
                timed_out=True,
            )

    def _run_streaming(
        self,
        args: List[str],
        cmd_str: str,
        cwd: Optional[Path],
        env: Optional[dict],
        on_line: Optional[Callable[[str], None]],
        spinner_text: str,
        start: float,
    ) -> RunResult:
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=env,
        )

        def read_stdout():
            for line in process.stdout:
                line = line.rstrip("\n")
                stdout_lines.append(line)
                if on_line:
                    on_line(line)

        def read_stderr():
            for line in process.stderr:
                stderr_lines.append(line.rstrip("\n"))

        t1 = threading.Thread(target=read_stdout, daemon=True)
        t2 = threading.Thread(target=read_stderr, daemon=True)
        t1.start()
        t2.start()

        timed_out = False
        try:
            process.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            timed_out = True

        t1.join(timeout=2)
        t2.join(timeout=2)

        duration = time.monotonic() - start
        return RunResult(
            command=cmd_str,
            exit_code=process.returncode or 0,
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
            duration=duration,
            timed_out=timed_out,
        )


# Module-level convenience runner
_default_runner = Runner()


def run(args: List[str], **kwargs) -> RunResult:
    return _default_runner.run(args, **kwargs)
