"""Tests for Venus (Cryptography) planet."""

import tempfile
from pathlib import Path

import pytest

from milkyway.core.db import SaturnDB


@pytest.fixture
def venus(tmp_path):
    from milkyway.cli.planets.venus import Venus
    db = SaturnDB(tmp_path / "test.db")
    return Venus(db=db, verbose=False, record=False)


def test_identify_md5(venus):
    result = venus.identify("5f4dcc3b5aa765d61d8327deb882cf99")
    assert result.exit_code == 0
    assert "MD5" in result.output


def test_identify_sha256(venus):
    result = venus.identify("b94f6f125c79e3a5ffaa826f584c10d52ada669e6762051b826b55776d05a8a")
    assert result.exit_code == 0
    assert "SHA-256" in result.output or "SHA3-256" in result.output


def test_identify_sha1(venus):
    result = venus.identify("da39a3ee5e6b4b0d3255bfef95601890afd80709")
    assert "SHA-1" in result.output


def test_identify_base64(venus):
    result = venus.identify("aGVsbG8gd29ybGQ=")
    assert "Base64" in result.output


def test_hash_md5(venus):
    result = venus.hash("password", "md5")
    assert result.exit_code == 0
    assert "5f4dcc3b5aa765d61d8327deb882cf99" in result.output


def test_hash_sha256(venus):
    result = venus.hash("hello", "sha256")
    assert "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" in result.output


def test_encode_base64(venus):
    result = venus.encode("hello world", "base64")
    assert result.exit_code == 0
    assert "aGVsbG8gd29ybGQ=" in result.output


def test_encode_hex(venus):
    result = venus.encode("hello", "hex")
    assert "68656c6c6f" in result.output


def test_encode_rot13(venus):
    result = venus.encode("hello", "rot13")
    assert "uryyb" in result.output


def test_decode_base64(venus):
    result = venus.decode("aGVsbG8gd29ybGQ=", "base64")
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_decode_hex(venus):
    result = venus.decode("68656c6c6f", "hex")
    assert "hello" in result.output


def test_roundtrip_base64(venus):
    original = "CTF{flag_goes_here_1234}"
    encoded = venus.encode(original, "base64")
    import base64
    b64 = base64.b64encode(original.encode()).decode()
    decoded = venus.decode(b64, "base64")
    assert original in decoded.output


def test_xor(venus):
    # XOR with key 'A' (0x41)
    # 'B' (0x42) XOR 'A' (0x41) = 0x03
    result = venus.xor("42", "A", "hex")
    assert result.exit_code == 0


def test_factor_small(venus):
    result = venus.factor("15")
    assert result.exit_code == 0
    # 15 = 3 * 5
    assert "3" in result.output or "5" in result.output


def test_factor_prime(venus):
    result = venus.factor("17")
    assert "17" in result.output
