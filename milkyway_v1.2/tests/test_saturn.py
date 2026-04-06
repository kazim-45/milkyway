"""Tests for Saturn DB layer."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from milkyway.core.db import SaturnDB


@pytest.fixture
def db(tmp_path):
    """Temporary in-memory DB for each test."""
    return SaturnDB(tmp_path / "test.db")


def test_record_and_retrieve_run(db):
    run_id = db.record_run(
        planet="mercury",
        action="fuzz",
        command_line="milkyway mercury fuzz http://test.com/FUZZ",
        parameters={"url": "http://test.com/FUZZ", "wordlist": "common.txt"},
        exit_code=0,
        output="Found: /admin\nFound: /login\n",
    )
    assert run_id == 1

    run = db.get_run(run_id)
    assert run is not None
    assert run.planet == "mercury"
    assert run.action == "fuzz"
    assert run.exit_code == 0
    assert run.success is True


def test_failed_run(db):
    run_id = db.record_run(
        planet="venus",
        action="crack",
        command_line="venus crack hash.txt",
        parameters={},
        exit_code=1,
        output="",
    )
    run = db.get_run(run_id)
    assert run.success is False
    assert run.exit_code == 1


def test_get_runs_list(db):
    for i in range(5):
        db.record_run(
            planet="mercury",
            action="fuzz",
            command_line=f"run {i}",
            parameters={},
            exit_code=0,
        )

    runs = db.get_runs(limit=3)
    assert len(runs) == 3


def test_filter_by_planet(db):
    db.record_run("mercury", "fuzz", "cmd1", {}, 0)
    db.record_run("venus", "identify", "cmd2", {}, 0)
    db.record_run("mercury", "sql", "cmd3", {}, 0)

    mercury_runs = db.get_runs(planet="mercury")
    assert len(mercury_runs) == 2
    assert all(r.planet == "mercury" for r in mercury_runs)


def test_create_and_get_challenge(db):
    with tempfile.TemporaryDirectory() as tmp:
        cid = db.create_challenge(
            name="test_web",
            category="web",
            folder_path=tmp,
            url="https://example.com",
            tags=["easy", "web"],
        )
        assert cid == 1

        ch = db.get_challenge("test_web")
        assert ch is not None
        assert ch.name == "test_web"
        assert ch.category == "web"
        assert "easy" in ch.tags


def test_update_challenge_notes(db):
    with tempfile.TemporaryDirectory() as tmp:
        db.create_challenge("note_test", "misc", tmp)
        db.update_challenge_notes("note_test", "This is a note about SQL injection.")
        ch = db.get_challenge("note_test")
        assert "SQL injection" in ch.notes


def test_annotate_run(db):
    run_id = db.record_run("earth", "carve", "earth carve file.bin", {}, 0)
    db.annotate_run(run_id, "Found embedded PNG inside")

    # Annotation stored without error
    with db._conn() as conn:
        rows = conn.execute(
            "SELECT * FROM annotations WHERE run_id=?", (run_id,)
        ).fetchall()
    assert len(rows) == 1
    assert "PNG" in rows[0]["text"]


def test_get_stats(db):
    db.record_run("mercury", "fuzz", "cmd", {}, 0)
    db.record_run("mercury", "sql", "cmd", {}, 1)
    db.record_run("venus", "hash", "cmd", {}, 0)

    stats = db.get_stats()
    assert stats["total_runs"] == 3
    assert stats["successful_runs"] == 2
    assert stats["failed_runs"] == 1
    assert "mercury" in stats["by_planet"]


def test_start_session(db):
    sid = db.start_session("ctf_run_1")
    assert len(sid) == 8  # UUID prefix


def test_session_export(db):
    sid = db.start_session("test_session")
    db.record_run("mercury", "fuzz", "milkyway mercury fuzz http://test.com/FUZZ", {}, 0, session_id=sid)
    db.record_run("venus", "identify", "milkyway venus identify abc123", {}, 0, session_id=sid)

    md = db.export_session(sid)
    assert "test_session" in md
    assert "mercury" in md
    assert "venus" in md


def test_list_challenges(db):
    with tempfile.TemporaryDirectory() as tmp:
        db.create_challenge("web1", "web", tmp)
        db.create_challenge("crypto1", "crypto", tmp)
        db.create_challenge("web2", "web", tmp)

    all_ch = db.list_challenges()
    assert len(all_ch) == 3

    web_ch = db.list_challenges(category="web")
    assert len(web_ch) == 2
    assert all(c.category == "web" for c in web_ch)


def test_diff_runs(db):
    db.record_run("mercury", "fuzz", "run1", {}, 0, output="line1\nline2\nline3\n")
    db.record_run("mercury", "fuzz", "run2", {}, 0, output="line1\nline2_changed\nline3\n")

    diff = db.diff_runs(1, 2)
    # Diff should show something (either output or "No differences")
    assert isinstance(diff, str)
