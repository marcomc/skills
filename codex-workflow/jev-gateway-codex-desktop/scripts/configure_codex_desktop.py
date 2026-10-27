#!/usr/bin/env python3
"""Safely add or restore the Jev Gateway provider in the user's Codex config."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import tomllib


PROVIDER_ID = "jev-gateway"
PROVIDER = {
    "name": "jev-gateway",
    "base_url": "http://127.0.0.1:8790/v1",
    "wire_api": "responses",
    "requires_openai_auth": True,
}


class ConfigError(Exception):
    """Raised when a config cannot be safely changed."""


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def parse_config(text: str, label: str) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{label} is not valid TOML: {exc}") from exc


def backup_name(config_path: Path, label: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = config_path.with_name(f"{config_path.name}.{label}-{stamp}.bak")
    suffix = 1
    while candidate.exists():
        candidate = config_path.with_name(
            f"{config_path.name}.{label}-{stamp}-{suffix}.bak"
        )
        suffix += 1
    return candidate


def private_backup(source: Path, destination: Path, default_mode: int = 0o600) -> None:
    mode = stat.S_IMODE(source.stat().st_mode) if source.exists() else default_mode
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    file_descriptor = os.open(destination, flags, mode)
    with os.fdopen(file_descriptor, "wb") as target:
        if source.exists():
            with source.open("rb") as original:
                shutil.copyfileobj(original, target)
    os.chmod(destination, mode)


def atomic_write(destination: Path, content: bytes, mode: int) -> None:
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def provider_block() -> str:
    return (
        f"[model_providers.{PROVIDER_ID}]\n"
        f'name = "{PROVIDER["name"]}"\n'
        f'base_url = "{PROVIDER["base_url"]}"\n'
        f'wire_api = "{PROVIDER["wire_api"]}"\n'
        "requires_openai_auth = true\n"
    )


def configure(config_path: Path) -> int:
    if config_path.is_symlink():
        raise ConfigError(f"Refusing to replace symlink: {config_path}")

    original = config_path.read_text() if config_path.exists() else ""
    parsed = parse_config(original, str(config_path))
    active_provider = parsed.get("model_provider")
    if active_provider not in (None, "openai", PROVIDER_ID):
        raise ConfigError(
            f"Active provider is {active_provider!r}; refusing to replace it. "
            "Review the config and decide whether to switch providers first."
        )

    model_providers = parsed.get("model_providers", {})
    if not isinstance(model_providers, dict):
        raise ConfigError("model_providers is not a TOML table")
    existing_provider = model_providers.get(PROVIDER_ID)
    if existing_provider is not None:
        if not isinstance(existing_provider, dict) or any(
            existing_provider.get(key) != value for key, value in PROVIDER.items()
        ):
            raise ConfigError(
                "A conflicting [model_providers.jev-gateway] already exists; "
                "refusing to overwrite it."
            )

    if active_provider == PROVIDER_ID and existing_provider == PROVIDER:
        print(f"Jev Gateway is already the active provider in {config_path}")
        return 0

    updated = original
    if active_provider is None:
        # Add a root-level key before the first TOML table.
        table_match = re.search(r"(?m)^\s*\[", updated)
        boundary = table_match.start() if table_match else len(updated)
        root = updated[:boundary]
        tail = updated[boundary:]
        if root and not root.endswith("\n"):
            root += "\n"
        updated = root + 'model_provider = "jev-gateway"\n' + tail
    elif active_provider == "openai":
        # Change only the root-level provider value, leaving all other settings intact.
        table_match = re.search(r"(?m)^\s*\[", updated)
        boundary = table_match.start() if table_match else len(updated)
        root = updated[:boundary]
        match = re.search(
            r'(?m)^([ \t]*model_provider[ \t]*=[ \t]*)"openai"([ \t]*(?:#.*)?)$',
            root,
        )
        if not match:
            raise ConfigError(
                "Could not safely locate the root-level model_provider = \"openai\" line."
            )
        replacement = match.group(1) + '"jev-gateway"' + match.group(2)
        updated = root[: match.start()] + replacement + root[match.end() :] + updated[boundary:]

    if existing_provider is None:
        if updated and not updated.endswith("\n"):
            updated += "\n"
        updated += "\n" + provider_block()

    verified = parse_config(updated, "proposed Codex configuration")
    if verified.get("model_provider") != PROVIDER_ID:
        raise ConfigError("Proposed config does not select Jev Gateway")
    if verified.get("model_providers", {}).get(PROVIDER_ID) != PROVIDER:
        raise ConfigError("Proposed Jev Gateway provider does not match expected values")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_name(config_path, "pre-jev")
    private_backup(config_path, backup)
    existing_mode = (
        stat.S_IMODE(config_path.stat().st_mode) if config_path.exists() else 0o600
    )
    atomic_write(config_path, updated.encode(), existing_mode)
    print(f"Configured {config_path}")
    print(f"Backup: {backup}")
    print("Model and unrelated settings were preserved.")
    return 0


def rollback(config_path: Path, backup_path: Path) -> int:
    if not backup_path.is_file() or backup_path.is_symlink():
        raise ConfigError(f"Backup file not found or is a symlink: {backup_path}")
    backup_content = backup_path.read_bytes()
    parse_config(backup_content.decode(), str(backup_path))
    if config_path.is_symlink():
        raise ConfigError(f"Refusing to replace symlink: {config_path}")

    rollback_backup = backup_name(config_path, "pre-rollback")
    private_backup(config_path, rollback_backup)
    mode = stat.S_IMODE(backup_path.stat().st_mode)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(config_path, backup_content, mode)
    print(f"Restored {config_path} from {backup_path}")
    print(f"Pre-rollback config backup: {rollback_backup}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--apply", action="store_true", help="Configure Jev Gateway")
    action.add_argument(
        "--rollback", type=Path, metavar="BACKUP", help="Restore a saved config backup"
    )
    args = parser.parse_args()
    config_path = codex_home() / "config.toml"
    try:
        if args.apply:
            return configure(config_path)
        return rollback(config_path, args.rollback.expanduser())
    except (ConfigError, OSError, UnicodeDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
