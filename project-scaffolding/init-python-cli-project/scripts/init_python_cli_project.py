#!/usr/bin/env python3
"""Generate a new Python CLI project from the shared local template."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import UTC, datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_TEMPLATE_ROOT = Path.home() / "Development" / "templates" / "python-cli-template"
PACKAGE_DIR_PLACEHOLDER = "__PACKAGE_NAME__"
TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
    "",
}


@dataclass(frozen=True)
class TemplateContext:
    project_name: str
    cli_name: str
    package_name: str
    description: str
    python_version: str
    author_name: str
    author_email: str
    config_name: str
    license_id: str
    copyright_year: str
    ruff_target_version: str

    def replacements(self) -> dict[str, str]:
        return {
            "__PROJECT_NAME__": self.project_name,
            "__CLI_NAME__": self.cli_name,
            "__PACKAGE_NAME__": self.package_name,
            "__DESCRIPTION__": self.description,
            "__PYTHON_VERSION__": self.python_version,
            "__AUTHOR_NAME__": self.author_name,
            "__AUTHOR_EMAIL__": self.author_email,
            "__CONFIG_NAME__": self.config_name,
            "__LICENSE_ID__": self.license_id,
            "__COPYRIGHT_YEAR__": self.copyright_year,
            "__RUFF_TARGET_VERSION__": self.ruff_target_version,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new Python CLI project from the shared local template."
    )
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument(
        "--template-root",
        type=Path,
        default=DEFAULT_TEMPLATE_ROOT,
        help="Template directory to copy from.",
    )
    parser.add_argument("--project-name")
    parser.add_argument("--cli-name")
    parser.add_argument("--package-name")
    parser.add_argument("--description")
    parser.add_argument("--python-version", default="3.11")
    parser.add_argument("--author-name")
    parser.add_argument("--author-email")
    parser.add_argument("--config-name")
    parser.add_argument("--license-id", default="MIT")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-git", action="store_true")
    parser.add_argument("--no-sync", action="store_true")
    return parser.parse_args()


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = lowered.strip("-")
    if not lowered:
        raise ValueError("Unable to derive a non-empty CLI name from the provided input.")
    return lowered


def packageify(value: str) -> str:
    package_name = value.replace("-", "_")
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", package_name):
        raise ValueError(f"Invalid package name: {package_name!r}")
    return package_name


def git_config(key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--get", key],
        capture_output=True,
        text=True,
        check=False,
    )
    value = result.stdout.strip()
    return value or None


def build_context(args: argparse.Namespace) -> TemplateContext:
    destination_name = args.destination.name
    project_name = args.project_name or destination_name
    cli_name = args.cli_name or slugify(project_name)
    package_name = args.package_name or packageify(cli_name)
    description = args.description or f"Python CLI for {project_name}"
    author_name = args.author_name or git_config("user.name") or "Your Name"
    author_email = args.author_email or git_config("user.email") or "you@example.com"
    config_name = args.config_name or cli_name
    copyright_year = str(datetime.now(UTC).year)
    python_version_digits = args.python_version.replace(".", "")
    ruff_target_version = f"py{python_version_digits}"

    return TemplateContext(
        project_name=project_name,
        cli_name=cli_name,
        package_name=package_name,
        description=description,
        python_version=args.python_version,
        author_name=author_name,
        author_email=author_email,
        config_name=config_name,
        license_id=args.license_id,
        copyright_year=copyright_year,
        ruff_target_version=ruff_target_version,
    )


def ensure_destination(destination: Path, *, force: bool) -> None:
    if destination.exists():
        if not force and any(destination.iterdir()):
            raise FileExistsError(
                f"Destination {destination} already exists and is not empty. "
                "Pass --force to overwrite."
            )
        if force:
            shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)


def copy_template(template_root: Path, destination: Path) -> None:
    if not template_root.exists():
        raise FileNotFoundError(f"Template root does not exist: {template_root}")
    shutil.copytree(template_root, destination)


def rename_package_dir(destination: Path, package_name: str) -> None:
    source_dir = destination / "src" / PACKAGE_DIR_PLACEHOLDER
    target_dir = destination / "src" / package_name
    source_dir.rename(target_dir)


def should_replace_text(path: Path) -> bool:
    return path.suffix in TEXT_EXTENSIONS or path.name in {
        "Makefile",
        "LICENSE",
        ".python-version",
        ".gitignore",
    }


def replace_placeholders(destination: Path, context: TemplateContext) -> None:
    replacements = context.replacements()
    for path in sorted(destination.rglob("*")):
        if not path.is_file() or not should_replace_text(path):
            continue
        content = path.read_text(encoding="utf-8")
        for source, target in replacements.items():
            content = content.replace(source, target)
        path.write_text(content, encoding="utf-8")


def init_git(destination: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=destination, check=True)


def sync_environment(destination: Path) -> None:
    subprocess.run(["uv", "sync", "--extra", "dev"], cwd=destination, check=True)


def main() -> int:
    args = parse_args()
    context = build_context(args)

    if not args.template_root.exists():
        raise FileNotFoundError(f"Template root not found: {args.template_root}")

    ensure_destination(args.destination, force=args.force)
    copy_template(args.template_root, args.destination)
    rename_package_dir(args.destination, context.package_name)
    replace_placeholders(args.destination, context)

    if not args.no_git:
        init_git(args.destination)

    if not args.no_sync:
        sync_environment(args.destination)

    summary = {
        "destination": str(args.destination),
        "project_name": context.project_name,
        "cli_name": context.cli_name,
        "package_name": context.package_name,
        "config_name": context.config_name,
        "python_version": context.python_version,
    }
    for key, value in summary.items():
        print(f"{key}={value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
