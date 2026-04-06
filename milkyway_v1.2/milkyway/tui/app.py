"""
MilkyWay TUI — Textual-based terminal user interface.
A full-screen interactive dashboard for CTF work.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from rich.text import Text

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
    from textual.reactive import reactive
    from textual.screen import Screen
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        ListItem,
        ListView,
        Log,
        Markdown,
        ProgressBar,
        RichLog,
        Static,
        TabbedContent,
        TabPane,
        TextArea,
    )
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from milkyway.core.db import Challenge, Run, SaturnDB
from milkyway.core.challenge_manager import ChallengeManager


# ─── Screens ──────────────────────────────────────────────────────────────────

if TEXTUAL_AVAILABLE:

    class PlanetCard(Static):
        """Displays a planet in the dashboard."""

        DEFAULT_CSS = """
        PlanetCard {
            border: solid $accent;
            padding: 1 2;
            margin: 0 1;
            height: 7;
            width: 1fr;
        }
        PlanetCard:hover {
            border: double $primary;
            background: $surface;
        }
        PlanetCard .name {
            text-style: bold;
            color: $primary;
        }
        PlanetCard .desc {
            color: $text-muted;
        }
        """

        def __init__(self, symbol: str, name: str, desc: str, status: str = "stable") -> None:
            super().__init__()
            self.symbol = symbol
            self.planet_name = name
            self.desc = desc
            self.status = status

        def compose(self) -> ComposeResult:
            status_color = {
                "stable": "green",
                "beta": "yellow",
                "alpha": "orange",
                "planned": "red",
            }.get(self.status, "white")
            yield Static(f"{self.symbol} [bold]{self.planet_name.capitalize()}[/bold]  [{status_color}]{self.status}[/{status_color}]", classes="name")
            yield Static(self.desc, classes="desc")


    class DashboardScreen(Screen):
        """Main dashboard — planet overview + recent runs."""

        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("r", "refresh", "Refresh"),
            Binding("l", "goto_log", "Saturn Log"),
            Binding("c", "goto_challenges", "Challenges"),
            Binding("?", "help", "Help"),
        ]

        DEFAULT_CSS = """
        DashboardScreen {
            background: $background;
        }
        #header-bar {
            height: 3;
            background: $surface;
            padding: 0 2;
        }
        #planet-grid {
            height: auto;
            layout: grid;
            grid-size: 3;
            grid-gutter: 1;
            padding: 1;
        }
        #recent-runs {
            height: 1fr;
            border: solid $accent;
            padding: 1;
            margin: 0 1;
        }
        #stats-bar {
            height: 3;
            background: $surface;
            padding: 0 2;
            layout: horizontal;
        }
        """

        def __init__(self, db: SaturnDB, cm: ChallengeManager) -> None:
            super().__init__()
            self.db = db
            self.cm = cm

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)

            yield Static(
                "  🌌 [bold cyan]MilkyWay[/bold cyan] [dim]— The Galactic CTF Orchestrator[/dim]  "
                " [dim]v1.0.0 by kazim-45[/dim]",
                id="header-bar"
            )

            planets = [
                ("☿", "mercury", "Web Security", "stable"),
                ("♀", "venus", "Cryptography", "stable"),
                ("♁", "earth", "Forensics", "stable"),
                ("♂", "mars", "Reverse Eng.", "beta"),
                ("♃", "jupiter", "Binary Exploit", "beta"),
                ("♆", "neptune", "Cloud & Misc", "beta"),
                ("♇", "pluto", "AI Assistant", "alpha"),
                ("🪐", "saturn", "Version Control", "stable"),
            ]

            with Container(id="planet-grid"):
                for symbol, name, desc, status in planets:
                    yield PlanetCard(symbol, name, desc, status)

            yield Static("\n[bold]📡 Recent Saturn Runs[/bold]", markup=True)

            with ScrollableContainer(id="recent-runs"):
                runs = self.db.get_runs(limit=15)
                if runs:
                    table = DataTable()
                    table.add_columns("ID", "Time", "Planet", "Action", "Command", "Exit")
                    for run in runs:
                        exit_str = "[green]✓[/green]" if run.exit_code == 0 else "[red]✗[/red]"
                        table.add_row(
                            str(run.id),
                            run.timestamp.strftime("%H:%M:%S"),
                            run.planet,
                            run.action,
                            run.command_line[:50] + "..." if len(run.command_line) > 50 else run.command_line,
                            exit_str,
                        )
                    yield table
                else:
                    yield Static("[dim]No runs recorded yet. Start hacking! 🚀[/dim]")

            # Stats bar
            stats = self.db.get_stats()
            yield Static(
                f"  Runs: [cyan]{stats['total_runs']}[/cyan]  "
                f"✅ {stats['successful_runs']}  "
                f"❌ {stats['failed_runs']}  "
                f"Challenges: [cyan]{stats['challenges']}[/cyan]",
                id="stats-bar"
            )

            yield Footer()

        def action_quit(self) -> None:
            self.app.exit()

        def action_refresh(self) -> None:
            self.refresh()

        def action_goto_log(self) -> None:
            self.app.push_screen(SaturnLogScreen(self.db))

        def action_goto_challenges(self) -> None:
            self.app.push_screen(ChallengesScreen(self.db, self.cm))


    class SaturnLogScreen(Screen):
        """Saturn run log browser."""

        BINDINGS = [
            Binding("escape,q", "back", "Back"),
            Binding("d", "diff_mode", "Diff"),
            Binding("enter", "inspect", "Inspect"),
        ]

        DEFAULT_CSS = """
        SaturnLogScreen {
            background: $background;
        }
        #log-table {
            height: 1fr;
            border: solid $primary;
            padding: 1;
        }
        """

        def __init__(self, db: SaturnDB) -> None:
            super().__init__()
            self.db = db

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static("[bold]🪐 Saturn Version Control Log[/bold]\n", markup=True)

            runs = self.db.get_runs(limit=50)
            table = DataTable(id="log-table")
            table.add_columns("ID", "Timestamp", "Planet", "Action", "Command", "Exit", "Hash")

            for run in runs:
                style = "bold green" if run.exit_code == 0 else "red"
                table.add_row(
                    str(run.id),
                    run.timestamp_str,
                    f"[cyan]{run.planet}[/cyan]",
                    run.action,
                    run.command_line[:60] + "..." if len(run.command_line) > 60 else run.command_line,
                    "[green]0[/green]" if run.exit_code == 0 else f"[red]{run.exit_code}[/red]",
                    run.output_hash or "—",
                )
            yield table
            yield Footer()

        def action_back(self) -> None:
            self.app.pop_screen()


    class ChallengesScreen(Screen):
        """Challenge management screen."""

        BINDINGS = [
            Binding("escape,q", "back", "Back"),
            Binding("n", "new_challenge", "New"),
        ]

        def __init__(self, db: SaturnDB, cm: ChallengeManager) -> None:
            super().__init__()
            self.db = db
            self.cm = cm

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static("[bold]🏆 Challenges[/bold]\n", markup=True)

            challenges = self.cm.list_all()
            if challenges:
                table = DataTable()
                table.add_columns("Name", "Category", "Created", "Tags", "Notes")
                for ch in challenges:
                    table.add_row(
                        f"[bold]{ch.name}[/bold]",
                        f"[cyan]{ch.category}[/cyan]",
                        ch.created.strftime("%Y-%m-%d"),
                        ", ".join(ch.tags) or "—",
                        (ch.notes[:40] + "...") if len(ch.notes) > 40 else ch.notes or "—",
                    )
                yield table
            else:
                yield Static(
                    "[dim]No challenges yet.\n\n"
                    "Create one with:\n"
                    "  milkyway challenge new my_challenge --category web[/dim]"
                )
            yield Footer()

        def action_back(self) -> None:
            self.app.pop_screen()


    class MilkyWayApp(App):
        """The main MilkyWay TUI application."""

        TITLE = "🌌 MilkyWay CTF Orchestrator"
        SUB_TITLE = "The Galactic CTF Toolkit"
        CSS_PATH = None

        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit", priority=True),
            Binding("ctrl+l", "toggle_log", "Log"),
            Binding("d", "toggle_dark", "Toggle dark mode"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.db = SaturnDB()
            self.cm = ChallengeManager(self.db)

        def on_mount(self) -> None:
            self.push_screen(DashboardScreen(self.db, self.cm))

        def action_toggle_dark(self) -> None:
            self.dark = not self.dark


def launch_tui() -> None:
    """Launch the MilkyWay TUI."""
    if not TEXTUAL_AVAILABLE:
        from rich.console import Console
        console = Console()
        console.print("[yellow]Textual not installed. Install it with:[/yellow]")
        console.print("  pip install textual")
        console.print("\n[dim]Falling back to text menu...[/dim]\n")
        _text_menu()
        return

    app = MilkyWayApp()
    app.run()


def _text_menu() -> None:
    """Simple text-based menu fallback when Textual isn't available."""
    from rich.console import Console
    from rich.table import Table
    console = Console()

    console.print("""
[bold cyan]🌌 MilkyWay — The Galactic CTF Orchestrator[/bold cyan]
[dim]v1.0.0 by kazim-45[/dim]

[bold]Available Planets:[/bold]
  [cyan]☿ mercury[/cyan]   Web Security (fuzz, sql, request, headers, extract)
  [magenta]♀ venus[/magenta]     Cryptography (identify, hash, crack, encode, decode, xor, factor)
  [green]♁ earth[/green]     Forensics (info, carve, strings, hexdump, steg, pcap)
  [red]♂ mars[/red]       Reverse Engineering (disassemble, info, symbols, trace, r2)
  [yellow]♃ jupiter[/yellow]   Binary Exploitation (checksec, rop, template, cyclic)
  [blue]♆ neptune[/blue]    Cloud & Misc (jwt, cloud, url)
  [purple]♇ pluto[/purple]     AI Assistant (suggest, analyze, cheatsheet)
  [white]🪐 saturn[/white]    Version Control (log, diff, redo, status, export)

[bold]Challenge Management:[/bold]
  milkyway challenge new <name> --category <cat>
  milkyway challenge list
  milkyway challenge note <name> "<text>"

[bold]Quick Start:[/bold]
  milkyway mercury fuzz http://target.com/FUZZ
  milkyway venus identify '<hash>'
  milkyway earth strings ./suspicious_file
  milkyway pluto suggest "I found a weird file with no extension"
  milkyway saturn log
""")
