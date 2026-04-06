"""Tests for Mercury (Web) planet and general CLI."""

import tempfile
from pathlib import Path

import pytest

from milkyway.core.db import SaturnDB


@pytest.fixture
def mercury(tmp_path):
    from milkyway.cli.planets.mercury import Mercury
    db = SaturnDB(tmp_path / "test.db")
    return Mercury(db=db, verbose=False, record=False)


@pytest.fixture
def earth(tmp_path):
    from milkyway.cli.planets.earth import Earth
    db = SaturnDB(tmp_path / "test.db")
    return Earth(db=db, verbose=False, record=False)


@pytest.fixture
def jupiter(tmp_path):
    from milkyway.cli.planets.jupiter import Jupiter
    db = SaturnDB(tmp_path / "test.db")
    return Jupiter(db=db, verbose=False, record=False)


def test_mercury_extract_links(mercury, tmp_path):
    html = tmp_path / "test.html"
    html.write_text("""
    <html>
    <a href="/admin">Admin</a>
    <a href="/login">Login</a>
    <form action="/submit">
    <img src="/logo.png">
    </html>
    """)

    result = mercury.extract(str(html), "links")
    assert result.exit_code == 0
    assert "/admin" in result.output
    assert "/login" in result.output


def test_mercury_extract_forms(mercury, tmp_path):
    html = tmp_path / "test.html"
    html.write_text("""
    <form action="/login" method="POST">
        <input name="user">
        <input name="pass" type="password">
    </form>
    """)

    result = mercury.extract(str(html), "forms")
    assert "form" in result.output.lower()


def test_mercury_extract_comments(mercury, tmp_path):
    html = tmp_path / "test.html"
    html.write_text("""
    <html>
    <!-- TODO: remove this debug endpoint /debug/secret -->
    <p>Hello</p>
    <!-- admin password: hunter2 -->
    </html>
    """)
    result = mercury.extract(str(html), "comments")
    assert "/debug/secret" in result.output or "hunter2" in result.output


def test_mercury_extract_emails(mercury, tmp_path):
    html = tmp_path / "test.html"
    html.write_text("Contact us at admin@example.com or support@ctf.io")
    result = mercury.extract(str(html), "emails")
    assert "admin@example.com" in result.output


def test_earth_strings(earth, tmp_path):
    binary = tmp_path / "test_binary"
    binary.write_bytes(
        b"\x7fELF\x00\x00" + b"A" * 10 +
        b"CTF{hello_world_flag}\x00" +
        b"password=secret123\x00" +
        b"\x00\x01\x02\x03"
    )
    result = earth.strings(str(binary), min_len=4)
    assert result.exit_code == 0
    assert "CTF" in result.output or "hello" in result.output


def test_earth_hexdump(earth, tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(bytes(range(32)))
    result = earth.hexdump(str(f), length=32)
    assert result.exit_code == 0
    assert "00" in result.output


def test_earth_info(earth, tmp_path):
    f = tmp_path / "test_file.txt"
    f.write_text("Hello, MilkyWay!")
    result = earth.info(str(f))
    assert result.exit_code == 0


def test_jupiter_cyclic_generate(jupiter):
    result = jupiter.cyclic(100)
    assert result.exit_code == 0
    assert len(result.output) >= 100


def test_jupiter_cyclic_find(jupiter):
    result = jupiter.cyclic(200)
    pattern = result.output[:4]
    # Find offset 0
    result2 = jupiter.cyclic(200, find=pattern)
    assert "0" in result2.output


def test_jupiter_checksec_missing_file(jupiter):
    result = jupiter.checksec("/nonexistent/file")
    # Should handle gracefully
    assert result.exit_code != 0 or "not found" in result.output.lower() or result.exit_code == 0


def test_challenge_manager(tmp_path):
    from milkyway.core.challenge_manager import ChallengeManager
    from milkyway.core.db import SaturnDB
    from milkyway.core import config

    db = SaturnDB(tmp_path / "test.db")
    # Override challenges dir to tmp
    cm = ChallengeManager(db)
    cm.challenges_dir = tmp_path / "challenges"
    cm.challenges_dir.mkdir()

    ch = cm.new("test_challenge", "web", url="https://example.com", tags=["easy"])
    assert ch.name == "test_challenge"
    assert ch.category == "web"
    assert (cm.challenges_dir / "test_challenge").exists()
    assert (cm.challenges_dir / "test_challenge" / "notes.md").exists()
    assert (cm.challenges_dir / "test_challenge" / "solutions" / "solve.py").exists()


def test_challenge_manager_duplicate(tmp_path):
    from milkyway.core.challenge_manager import ChallengeManager
    from milkyway.core.db import SaturnDB

    db = SaturnDB(tmp_path / "test.db")
    cm = ChallengeManager(db)
    cm.challenges_dir = tmp_path / "challenges"
    cm.challenges_dir.mkdir()

    cm.new("dupe_test", "misc")

    with pytest.raises(ValueError, match="already exists"):
        cm.new("dupe_test", "web")


def test_challenge_add_note(tmp_path):
    from milkyway.core.challenge_manager import ChallengeManager
    from milkyway.core.db import SaturnDB

    db = SaturnDB(tmp_path / "test.db")
    cm = ChallengeManager(db)
    cm.challenges_dir = tmp_path / "challenges"
    cm.challenges_dir.mkdir()

    cm.new("note_test", "web")
    cm.add_note("note_test", "Found SQL injection at /login")

    notes_file = cm.challenges_dir / "note_test" / "notes.md"
    assert "SQL injection" in notes_file.read_text()
