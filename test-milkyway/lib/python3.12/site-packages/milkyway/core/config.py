"""
Config — User configuration for MilkyWay (~/.milkyway/config.yaml).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml


DEFAULT_CONFIG = {
    "challenges_dir": str(Path.home() / "milkyway-challenges"),
    "default_wordlist": "/usr/share/wordlists/dirb/common.txt",
    "timeout": 300,
    "verbose": False,
    "theme": "dark",
    "pluto": {
        "backend": "ollama",         # "ollama" | "openai" | "none"
        "model": "mistral",
        "openai_api_key": "",
    },
    "team": {
        "username": "me",
        "git_url": "",
    },
}

_CONFIG_PATH = Path.home() / ".milkyway" / "config.yaml"
_config_cache: Optional[dict] = None


def _load() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            loaded = yaml.safe_load(f) or {}
        # Deep merge with defaults
        merged = _deep_merge(DEFAULT_CONFIG, loaded)
    else:
        merged = DEFAULT_CONFIG.copy()
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _save(merged)

    _config_cache = merged
    return merged


def _save(cfg: dict) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def get(key: str, default: Any = None) -> Any:
    """Get a config value by dot-notation key (e.g. 'pluto.backend')."""
    cfg = _load()
    parts = key.split(".")
    val = cfg
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return default
    return val if val is not None else default


def set_key(key: str, value: Any) -> None:
    """Set a config value and persist."""
    global _config_cache
    cfg = _load()
    parts = key.split(".")
    target = cfg
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value
    _config_cache = cfg
    _save(cfg)


def challenges_dir() -> Path:
    p = Path(get("challenges_dir"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def default_wordlist() -> str:
    wl = get("default_wordlist")
    if wl and Path(wl).exists():
        return wl
    # Try common fallbacks
    fallbacks = [
        "/usr/share/wordlists/dirb/common.txt",
        "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
        "/opt/homebrew/share/wordlists/dirb/common.txt",
    ]
    for fb in fallbacks:
        if Path(fb).exists():
            return fb
    # Use bundled minimal wordlist
    bundled = Path(__file__).parent.parent / "data" / "wordlists" / "common.txt"
    return str(bundled)


def all_config() -> dict:
    return _load()
