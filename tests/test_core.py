"""
Tests for MilkyWay core components.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from milkyway.core.db import SaturnDB
from milkyway.core.runner import RunResult, check_tool, Runner
from milkyway.core.challenge_manager import ChallengeManager


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SaturnDB for testing."""
    db_path = tmp_path / "test.db"
    return SaturnDB(db_path)


@pytest.fixture
def tmp_cm(tmp_path, tmp_db):
    """Create a ChallengeManager with temp dirs."""
    import milkyway.core.config as cfg
    # Override challenges dir to temp
    original = cfg.get("challenges_dir")
    cfg.set_key("challenges_dir", str(tmp_path / "challenges"))
    cm = ChallengeManager(tmp_db)
    yield cm
    cfg.set_key("challenges_dir", original)


# ─── Saturn DB Tests ──────────────────────────────────────────────────────────

class TestSaturnDB:

    def test_init_creates_schema(self, tmp_db):
        """DB should initialize with all required tables."""
        with tmp_db._conn() as conn:
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        assert "runs" in tables
        assert "challenges" in tables
        assert "sessions" in tables
        assert "annotations" in tables

    def test_record_run_returns_id(self, tmp_db):
        """record_run should return a positive integer ID."""
        rid = tmp_db.record_run(
            planet="mercury",
            action="fuzz",
            command_line="milkyway mercury fuzz http://target.com/FUZZ",
            parameters={"url": "http://target.com/FUZZ"},
            exit_code=0,
            output="Found: /admin\n",
        )
        assert isinstance(rid, int)
        assert rid > 0

    def test_get_run_roundtrip(self, tmp_db):
        """Records should be retrievable with all fields intact."""
        rid = tmp_db.record_run(
            planet="venus",
            action="identify",
            command_line="venus identify abc123",
            parameters={"hash": "abc123"},
            exit_code=0,
            output="MD5 detected",
        )
        run = tmp_db.get_run(rid)
        assert run is not None
        assert run.planet == "venus"
        assert run.action == "identify"
        assert run.exit_code == 0
        assert run.success is True

    def test_get_runs_filtering(self, tmp_db):
        """get_runs should support planet and search filters."""
        tmp_db.record_run("mercury", "fuzz", "fuzz http://a.com", {}, 0)
        tmp_db.record_run("venus", "hash", "hash hello", {}, 0)
        tmp_db.record_run("mercury", "sql", "sql http://b.com", {}, 1)

        mercury_runs = tmp_db.get_runs(planet="mercury")
        assert len(mercury_runs) == 2
        assert all(r.planet == "mercury" for r in mercury_runs)

        failed = [r for r in tmp_db.get_runs() if r.exit_code != 0]
        assert len(failed) == 1

    def test_create_and_get_challenge(self, tmp_db, tmp_path):
        """Challenge creation and retrieval should work."""
        folder = str(tmp_path / "test_challenge")
        Path(folder).mkdir()

        cid = tmp_db.create_challenge(
            name="test_web",
            category="web",
            folder_path=folder,
            url="http://example.com",
            tags=["beginner", "sql"],
        )
        ch = tmp_db.get_challenge_by_id(cid)
        assert ch is not None
        assert ch.name == "test_web"
        assert ch.category == "web"
        assert "beginner" in ch.tags

    def test_challenge_unique_name(self, tmp_db, tmp_path):
        """Duplicate challenge names should raise an error."""
        folder = str(tmp_path / "dup")
        Path(folder).mkdir()
        tmp_db.create_challenge("dup_test", "misc", folder)
        with pytest.raises(Exception):  # SQLite UNIQUE constraint
            tmp_db.create_challenge("dup_test", "web", folder)

    def test_stats(self, tmp_db):
        """Stats should aggregate correctly."""
        tmp_db.record_run("mercury", "fuzz", "cmd1", {}, 0)
        tmp_db.record_run("mercury", "sql", "cmd2", {}, 0)
        tmp_db.record_run("venus", "hash", "cmd3", {}, 1)

        stats = tmp_db.get_stats()
        assert stats["total_runs"] == 3
        assert stats["successful_runs"] == 2
        assert stats["failed_runs"] == 1
        assert "mercury" in stats["by_planet"]
        assert stats["by_planet"]["mercury"] == 2

    def test_annotate_run(self, tmp_db):
        """Annotations should be stored without error."""
        rid = tmp_db.record_run("earth", "strings", "strings ./file", {}, 0)
        tmp_db.annotate_run(rid, "Found suspicious string at offset 0x42")
        # No exception = pass

    def test_list_challenges(self, tmp_db, tmp_path):
        """list_challenges should support category filter."""
        for i, cat in enumerate(["web", "web", "crypto"]):
            folder = str(tmp_path / f"ch{i}")
            Path(folder).mkdir()
            tmp_db.create_challenge(f"challenge_{i}", cat, folder)

        all_ch = tmp_db.list_challenges()
        assert len(all_ch) == 3

        web_ch = tmp_db.list_challenges(category="web")
        assert len(web_ch) == 2


# ─── Runner Tests ─────────────────────────────────────────────────────────────

class TestRunner:

    def test_run_echo(self):
        """Basic command execution should work."""
        r = Runner()
        result = r.run(["echo", "hello milkyway"])
        assert result.exit_code == 0
        assert "hello milkyway" in result.stdout
        assert result.success is True

    def test_run_nonzero_exit(self):
        """Non-zero exit codes should be captured."""
        r = Runner()
        result = r.run(["false"])
        assert result.exit_code != 0
        assert result.success is False

    def test_run_captures_stderr(self):
        """Stderr should be captured separately."""
        r = Runner()
        result = r.run(["ls", "/nonexistent_path_xyz"])
        assert result.exit_code != 0
        assert result.stderr or result.stdout  # error in one of them

    def test_timeout(self):
        """Commands that exceed timeout should be marked timed_out."""
        r = Runner(timeout=1)
        result = r.run(["sleep", "10"])
        assert result.timed_out is True

    def test_check_tool_existing(self):
        """check_tool should return True for 'echo'."""
        assert check_tool("echo") is True

    def test_check_tool_missing(self):
        """check_tool should return False for nonexistent tool."""
        assert check_tool("this_tool_does_not_exist_xyz") is False


# ─── Challenge Manager Tests ──────────────────────────────────────────────────

class TestChallengeManager:

    def test_create_challenge_folder(self, tmp_cm, tmp_path):
        """new() should create the challenge folder structure."""
        ch = tmp_cm.new("test_challenge", "web", url="http://example.com")
        assert ch is not None
        assert Path(ch.folder_path).exists()
        assert (Path(ch.folder_path) / ".milkyway").exists()
        assert (Path(ch.folder_path) / "files").exists()
        assert (Path(ch.folder_path) / "solutions").exists()
        assert (Path(ch.folder_path) / "notes.md").exists()
        assert (Path(ch.folder_path) / "README.md").exists()

    def test_create_challenge_db_entry(self, tmp_cm):
        """new() should register in the DB."""
        ch = tmp_cm.new("db_test", "crypto")
        assert tmp_cm.get("db_test") is not None
        assert ch.category == "crypto"

    def test_duplicate_name_raises(self, tmp_cm):
        """Creating duplicate challenge should raise ValueError."""
        tmp_cm.new("unique_name", "misc")
        with pytest.raises(ValueError, match="already exists"):
            tmp_cm.new("unique_name", "web")

    def test_invalid_name_raises(self, tmp_cm):
        """Invalid characters in name should raise ValueError."""
        with pytest.raises(ValueError):
            tmp_cm.new("bad name with spaces!", "web")

    def test_add_note(self, tmp_cm):
        """Notes should be appended to notes.md."""
        tmp_cm.new("note_test", "web")
        tmp_cm.add_note("note_test", "Found XSS at /search")
        ch = tmp_cm.get("note_test")
        notes_file = Path(ch.folder_path) / "notes.md"
        content = notes_file.read_text()
        assert "Found XSS at /search" in content

    def test_list_challenges(self, tmp_cm):
        """list_all should return all challenges, filterable by category."""
        tmp_cm.new("web1", "web")
        tmp_cm.new("web2", "web")
        tmp_cm.new("crypto1", "crypto")

        all_ch = tmp_cm.list_all()
        assert len(all_ch) == 3

        web_ch = tmp_cm.list_all(category="web")
        assert len(web_ch) == 2
        assert all(c.category == "web" for c in web_ch)

    def test_cd_path(self, tmp_cm):
        """cd_path should return the folder path string."""
        ch = tmp_cm.new("cd_test", "misc")
        path = tmp_cm.cd_path("cd_test")
        assert path == ch.folder_path

    def test_delete_challenge(self, tmp_cm):
        """delete() with confirm=True should remove folder and DB entry."""
        tmp_cm.new("to_delete", "misc")
        assert tmp_cm.get("to_delete") is not None

        result = tmp_cm.delete("to_delete", confirm=True)
        assert result is True
        assert tmp_cm.get("to_delete") is None


# ─── Venus (Crypto) Tests ─────────────────────────────────────────────────────

class TestVenusPure:
    """Tests for pure-Python crypto operations (no external tools needed)."""

    def test_identify_md5(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        result = v.identify("d8578edf8458ce06fbc5bb76a58c5ca4")
        assert result.exit_code == 0
        assert "MD5" in result.stdout

    def test_identify_sha256(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        result = v.identify("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert "SHA-256" in result.stdout

    def test_hash_md5(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        result = v.hash("hello", "md5")
        assert "5d41402abc4b2a76b9719d911017c592" in result.stdout

    def test_encode_base64(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        result = v.encode("hello world", "base64")
        assert "aGVsbG8gd29ybGQ=" in result.stdout

    def test_decode_base64(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        result = v.decode("aGVsbG8gd29ybGQ=", "base64")
        assert "hello world" in result.stdout

    def test_encode_decode_roundtrip(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        original = "CTF{test_flag_123}"
        for enc in ["base64", "hex", "rot13"]:
            encoded = v.encode(original, enc)
            decoded = v.decode(encoded.stdout.strip(), enc)
            assert original in decoded.stdout

    def test_xor(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        # XOR with self should give zeros
        result = v.xor("deadbeef", "key", "hex")
        assert result.exit_code == 0

    def test_factor_small(self, tmp_db):
        from milkyway.cli.planets.venus import Venus
        v = Venus(db=tmp_db, record=False)
        result = v.factor("12")
        assert result.exit_code == 0


# ─── Earth (Forensics) Tests ──────────────────────────────────────────────────

class TestEarthPure:
    """Tests for pure-Python forensics operations."""

    def test_info_existing_file(self, tmp_db, tmp_path):
        from milkyway.cli.planets.earth import Earth
        e = Earth(db=tmp_db, record=False)
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Hello, CTF! This is a test file.")
        result = e.info(str(test_file))
        assert result.exit_code == 0

    def test_info_missing_file(self, tmp_db):
        from milkyway.cli.planets.earth import Earth
        e = Earth(db=tmp_db, record=False)
        result = e.info("/nonexistent/path/file.bin")
        assert result.exit_code == 1

    def test_hexdump_python_fallback(self, tmp_db, tmp_path):
        from milkyway.cli.planets.earth import Earth
        e = Earth(db=tmp_db, record=False)
        test_file = tmp_path / "hex_test.bin"
        test_file.write_bytes(bytes(range(64)))
        result = e.hexdump(str(test_file), length=64)
        assert result.exit_code == 0

    def test_strings_with_grep(self, tmp_db, tmp_path):
        from milkyway.cli.planets.earth import Earth
        e = Earth(db=tmp_db, record=False)
        test_file = tmp_path / "strings_test.txt"
        test_file.write_text("garbage\x00\x00CTF{hidden_flag}\x00\x00more_garbage")
        result = e.strings(str(test_file), min_len=4, grep="CTF")
        assert result.exit_code == 0


# ─── Jupiter Tests ────────────────────────────────────────────────────────────

class TestJupiterPure:

    def test_cyclic_generate(self, tmp_db):
        from milkyway.cli.planets.jupiter import Jupiter
        j = Jupiter(db=tmp_db, record=False)
        result = j.cyclic(length=100)
        assert result.exit_code == 0
        assert len(result.stdout) >= 100

    def test_cyclic_find(self, tmp_db):
        from milkyway.cli.planets.jupiter import Jupiter
        j = Jupiter(db=tmp_db, record=False)
        # Generate then find
        gen = j.cyclic(length=200)
        pattern = gen.stdout.strip()
        if len(pattern) >= 4:
            sub = pattern[8:12]
            find_result = j.cyclic(length=200, find=sub)
            assert find_result.exit_code == 0


# ─── Neptune Tests ────────────────────────────────────────────────────────────

class TestNeptunePure:

    def test_jwt_decode_valid(self, tmp_db):
        from milkyway.cli.planets.neptune import Neptune
        n = Neptune(db=tmp_db, record=False)
        # This is a real (non-secret) example JWT
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = n.jwt(token)
        assert result.exit_code == 0
        assert "HS256" in result.stdout

    def test_jwt_invalid_format(self, tmp_db):
        from milkyway.cli.planets.neptune import Neptune
        n = Neptune(db=tmp_db, record=False)
        result = n.jwt("not.a.valid.jwt.token.with.too.many.parts")
        assert result.exit_code == 1

    def test_url_info(self, tmp_db):
        from milkyway.cli.planets.neptune import Neptune
        n = Neptune(db=tmp_db, record=False)
        result = n.url("http://example.com/path?id=1&name=test", "info")
        assert result.exit_code == 0

    def test_url_encode_decode(self, tmp_db):
        from milkyway.cli.planets.neptune import Neptune
        n = Neptune(db=tmp_db, record=False)
        original = "hello world & <test>"
        encoded = n.url(original, "encode")
        decoded = n.url(encoded.stdout.strip(), "decode")
        assert original in decoded.stdout
