#!/usr/bin/env python3
"""Generate a project AGENTS.md from reusable template overlays."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


BEGIN_LOCAL = "<!-- BEGIN PROJECT LOCAL -->"
END_LOCAL = "<!-- END PROJECT LOCAL -->"
GENERATED_MARKER = "<!-- generated-by: agents-file-templates-and-skills/init-agents-file -->"
GENERATED_DATE_PATTERN = re.compile(r"<!-- generated-date: .*? -->")
TEMPLATE_MARKER_PATTERN = re.compile(r"<!-- BEGIN TEMPLATE: (?P<type>[^>]+) -->")
TEMPLATE_SECTION_PATTERN = re.compile(
    r"<!-- BEGIN TEMPLATE: (?P<type>[^>]+) -->\n(?P<body>.*?)\n<!-- END TEMPLATE: (?P=type) -->",
    re.DOTALL,
)
PLACEHOLDER_TOKEN_PATTERN = re.compile(r"\$\{(?P<key>[A-Za-z_][A-Za-z0-9_]*)\}")
PROJECT_DESCRIPTION_PATTERN = re.compile(r"^- Description:\s*(?P<value>.+)$", re.MULTILINE)
PROJECT_NAME_PATTERN = re.compile(r"^- Project: `(?P<value>.*?)`$", re.MULTILINE)
GLOBAL_POLICY_PATH_PATTERN = re.compile(
    r"^Follow `(?P<value>.*?)` for canonical user-wide policy\.$", re.MULTILINE
)
DERIVED_PLACEHOLDERS = {"GENERATED_DATE", "PROJECT_NAME"}
RECOVERABLE_BASE_PLACEHOLDERS = {
    "GLOBAL_AGENTS_PATH",
    "PROJECT_DESCRIPTION",
    "PROJECT_NAME",
}
DEFAULT_BUDGET_WARNING_WORDS = 1_200

AGENT_OUTPUTS = {
    "standard": "AGENTS.md",
    "openai": "AGENTS.md",
    "codex": "AGENTS.md",
    "opencode": "AGENTS.md",
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
    "copilot": ".github/copilot-instructions.md",
}

AGENT_GLOBAL_PATHS = {
    "standard": "${HOME}/AGENTS.md",
    "openai": "${HOME}/AGENTS.md",
    "codex": "${HOME}/AGENTS.md",
    "opencode": "${HOME}/.config/opencode/AGENTS.md",
    "claude": "${HOME}/.claude/CLAUDE.md",
    "gemini": "${HOME}/.gemini/GEMINI.md",
    "copilot": "GitHub Copilot personal or organization custom instructions",
}


def load_manifest(template_repo: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML is required to read templates.yml")
    manifest_path = template_repo / "templates.yml"
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def iter_project_files(project: Path, ignored_dirs: set[str]) -> list[str]:
    paths: list[str] = []
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        root_path = Path(root)
        for name in files:
            rel = (root_path / name).relative_to(project).as_posix()
            paths.append(rel)
    return paths


def glob_matches(pattern: str, files: list[str]) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return any(path == prefix or path.startswith(f"{prefix}/") for path in files)
    return any(fnmatch.fnmatch(path, pattern) for path in files)


def detect_types(project: Path, manifest: dict) -> list[str]:
    ignored = set(manifest.get("scan_defaults", {}).get("ignored_dirs", []))
    files = iter_project_files(project, ignored)
    content = ""
    agents = project / "AGENTS.md"
    readme = project / "README.md"
    for candidate in (agents, readme):
        if candidate.exists():
            content += "\n" + candidate.read_text(encoding="utf-8", errors="ignore").lower()

    detected: list[str] = []
    for item in manifest.get("project_types", []):
        detector = item.get("detect", {})
        file_hit = any(glob_matches(pattern, files) for pattern in detector.get("file_globs", []))
        content_hit = any(marker.lower() in content for marker in detector.get("content_markers", []))
        if file_hit or content_hit:
            detected.append(item["id"])
    return detected


def strip_title(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return markdown.strip()


def existing_local_section(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        rf"{re.escape(BEGIN_LOCAL)}(?P<body>.*?){re.escape(END_LOCAL)}",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group("body").strip() if match else ""


def placeholder_values(project: Path, pairs: list[str], agent: str) -> dict[str, str]:
    values = {
        "HOME": "${HOME}",
        "USER_NAME": os.environ.get("USER", ""),
        "USER_WORKSPACE_ROOT": "${HOME}",
        "GLOBAL_AGENTS_PATH": AGENT_GLOBAL_PATHS.get(agent, AGENT_GLOBAL_PATHS["standard"]),
        "MARKDOWNLINT_CONFIG": "${HOME}/.markdownlint.json",
        "OBSIDIAN_VAULT_PATH": "${OBSIDIAN_VAULT_PATH}",
        "PRIMARY_DOMAIN": "${PRIMARY_DOMAIN}",
        "AUTHORIZED_WORK_CONTEXT": "${AUTHORIZED_WORK_CONTEXT}",
        "PROJECT_NAME": project.name,
        "PROJECT_DESCRIPTION": "${PROJECT_DESCRIPTION}",
        "GENERATED_DATE": date.today().isoformat(),
    }
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"Invalid --set value, expected KEY=VALUE: {pair}")
        key, value = pair.split("=", 1)
        values[key] = value
    return values


def replace_placeholders(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("${" + key + "}", value)
    return text


def template_map(manifest: dict) -> dict[str, str]:
    return {item["id"]: item["path"] for item in manifest.get("project_types", [])}


def render(project: Path, template_repo: Path, forced_types: list[str], pairs: list[str], agent: str, output_name: str) -> str:
    manifest = load_manifest(template_repo)
    detected = forced_types or detect_types(project, manifest)
    always = manifest.get("merge", {}).get("always_include", [])
    ordered = []
    for item in [*always, *detected]:
        if item not in ordered:
            ordered.append(item)

    paths = template_map(manifest)
    values = placeholder_values(project, pairs, agent)
    output = [
        f"# {output_name} Instructions",
        "",
        "<!-- generated-by: agents-file-templates-and-skills/init-agents-file -->",
        f"<!-- generated-date: {values['GENERATED_DATE']} -->",
        "",
        f"Follow `{values['GLOBAL_AGENTS_PATH']}` for canonical user-wide policy.",
        "",
        "## Project Context",
        "",
        f"- Project: `{values['PROJECT_NAME']}`",
        f"- Description: {values['PROJECT_DESCRIPTION']}",
        "",
        "## Project-Type Overlays",
        "",
    ]

    for type_id in ordered:
        rel_path = paths.get(type_id)
        if not rel_path:
            continue
        template_path = template_repo / rel_path
        body = strip_title(template_path.read_text(encoding="utf-8"))
        body = replace_placeholders(body, values)
        output.extend(
            [
                f"<!-- BEGIN TEMPLATE: {type_id} -->",
                f"### {type_id.replace('-', ' ').title()}",
                "",
                body,
                "",
                f"<!-- END TEMPLATE: {type_id} -->",
                "",
            ]
        )

    local = existing_local_section(project / output_name)
    output.extend(
        [
            "## Project Local Rules",
            "",
            BEGIN_LOCAL,
            local,
            END_LOCAL,
            "",
        ]
    )
    return "\n".join(output).replace("\n\n\n", "\n\n")


def generated_types(text: str) -> list[str]:
    types: list[str] = []
    for match in TEMPLATE_MARKER_PATTERN.finditer(text):
        type_id = match.group("type").strip()
        if type_id and type_id not in types:
            types.append(type_id)
    return types


def normalize_generated(text: str) -> str:
    return GENERATED_DATE_PATTERN.sub("<!-- generated-date: CHECK -->", text).strip()


def placeholder_pattern(rendered: str, sentinels: dict[str, str]) -> str:
    reverse = {value: key for key, value in sentinels.items()}
    sentinel_re = re.compile("|".join(re.escape(value) for value in sentinels.values()))
    parts: list[str] = []
    seen: set[str] = set()
    cursor = 0
    for match in sentinel_re.finditer(rendered):
        parts.append(re.escape(rendered[cursor : match.start()]))
        key = reverse[match.group(0)]
        group = f"placeholder_{key}"
        if key in seen:
            parts.append(f"(?P={group})")
        else:
            parts.append(f"(?P<{group}>.*?)")
            seen.add(key)
        cursor = match.end()
    parts.append(re.escape(rendered[cursor:]))
    return "".join(parts)


def recover_render_pairs(
    project: Path,
    template_repo: Path,
    selected: list[str],
    agent: str,
    output_name: str,
    current: str,
) -> tuple[list[str], bool]:
    recovered: dict[str, str] = {}
    project_name_match = PROJECT_NAME_PATTERN.search(current)
    project_name = project_name_match.group("value") if project_name_match else None
    description_match = PROJECT_DESCRIPTION_PATTERN.search(current)
    if description_match:
        description = description_match.group("value").strip()
        if description and description != "${PROJECT_DESCRIPTION}":
            recovered["PROJECT_DESCRIPTION"] = description
    global_path_match = GLOBAL_POLICY_PATH_PATTERN.search(current)
    if global_path_match:
        recovered["GLOBAL_AGENTS_PATH"] = global_path_match.group("value")

    keys = sorted(recoverable_placeholder_keys(template_repo, selected))
    sentinels = {key: f"__AGENTS_RENDER_PLACEHOLDER_{key}__" for key in keys}
    sentinel_pairs = [f"{key}={value}" for key, value in sentinels.items()]
    rendered = render(project, template_repo, selected, sentinel_pairs, agent, output_name)
    match = re.fullmatch(
        placeholder_pattern(normalize_generated(rendered), sentinels),
        normalize_generated(current),
        re.DOTALL,
    )
    if not match:
        if project_name is not None:
            recovered["PROJECT_NAME"] = project_name
        return [f"{key}={value}" for key, value in recovered.items()], False
    for key in sentinels:
        if sentinels[key] in rendered:
            recovered[key] = match.group(f"placeholder_{key}")
    return [f"{key}={value}" for key, value in recovered.items()], True


def recoverable_placeholder_keys(template_repo: Path, selected: list[str]) -> set[str]:
    keys = {*RECOVERABLE_BASE_PLACEHOLDERS, *template_placeholder_keys(template_repo, selected)}
    return keys - DERIVED_PLACEHOLDERS


def template_placeholder_keys(template_repo: Path, selected: list[str]) -> set[str]:
    manifest = load_manifest(template_repo)
    paths = template_map(manifest)
    keys: set[str] = set()
    for type_id in selected:
        rel_path = paths.get(type_id)
        if not rel_path:
            continue
        text = (template_repo / rel_path).read_text(encoding="utf-8")
        keys.update(match.group("key") for match in PLACEHOLDER_TOKEN_PATTERN.finditer(text))
    return keys


def unrecovered_placeholders(
    template_repo: Path,
    selected: list[str],
    recovered_pairs: list[str],
    supplied_pairs: list[str],
) -> list[str]:
    """Find reachable placeholder values that are neither recovered nor explicit."""
    template_keys = {
        *RECOVERABLE_BASE_PLACEHOLDERS,
        *template_placeholder_keys(template_repo, selected),
    } - (DERIVED_PLACEHOLDERS - RECOVERABLE_BASE_PLACEHOLDERS)
    recovered = {pair.split("=", 1)[0] for pair in recovered_pairs if "=" in pair}
    supplied = {pair.split("=", 1)[0] for pair in supplied_pairs if "=" in pair}
    return sorted(template_keys - recovered - supplied)


def check_output(
    project: Path,
    template_repo: Path,
    forced_types: list[str],
    pairs: list[str],
    agent: str,
    output_name: str,
) -> dict[str, object]:
    output = project / output_name
    manifest = load_manifest(template_repo)
    detected = forced_types or detect_types(project, manifest)
    if not output.exists():
        return {
            "project": str(project),
            "output": str(output),
            "status": "missing",
            "template_types": detected,
        }

    current = output.read_text(encoding="utf-8", errors="ignore")
    if GENERATED_MARKER not in current:
        return {
            "project": str(project),
            "output": str(output),
            "status": "not-generated",
            "template_types": generated_types(current),
        }

    selected = forced_types or generated_types(current) or detected
    recovered, recovery_complete = recover_render_pairs(
        project, template_repo, selected, agent, output_name, current
    )
    expected = render(project, template_repo, selected, [*recovered, *pairs], agent, output_name)
    status = (
        "current"
        if recovery_complete and normalize_generated(current) == normalize_generated(expected)
        else "out-of-sync"
    )
    return {
        "project": str(project),
        "output": str(output),
        "status": status,
        "template_types": selected,
    }


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'/-]*", text))


def budget_warning_words(template_repo: Path, override: int | None) -> int:
    if override is not None:
        if override < 1:
            raise SystemExit("--budget-warning-words must be at least 1")
        return override
    configured = load_manifest(template_repo).get("instruction_budget", {}).get("root_warning_words")
    if configured is None:
        return DEFAULT_BUDGET_WARNING_WORDS
    if not isinstance(configured, int) or configured < 1:
        raise SystemExit("instruction_budget.root_warning_words must be a positive integer")
    return configured


def budget_report(
    project: Path,
    template_repo: Path,
    forced_types: list[str],
    agent: str,
    output_name: str,
    warning_words: int | None = None,
) -> dict[str, object]:
    output = project / output_name
    threshold = budget_warning_words(template_repo, warning_words)
    if not output.exists():
        return {
            "project": str(project),
            "output": str(output),
            "status": "missing",
            "word_count": 0,
            "warning_words": threshold,
            "local_rules_word_count": 0,
            "template_sections": [],
        }

    current = output.read_text(encoding="utf-8", errors="ignore")
    template_sections = [
        {"template": match.group("type").strip(), "word_count": word_count(match.group("body"))}
        for match in TEMPLATE_SECTION_PATTERN.finditer(current)
    ]
    selected = forced_types or generated_types(current)
    if not selected:
        selected = detect_types(project, load_manifest(template_repo))
    local_words = word_count(existing_local_section(output))
    total_words = word_count(current)
    return {
        "project": str(project),
        "output": str(output),
        "status": "over-budget" if total_words > threshold else "within-budget",
        "word_count": total_words,
        "warning_words": threshold,
        "local_rules_word_count": local_words,
        "template_types": selected,
        "template_sections": template_sections,
    }


def ancestors(path: Path) -> list[Path]:
    resolved = path.expanduser().resolve()
    return [resolved, *resolved.parents]


def installed_repo_config() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "config" / "template_repo_path.txt"
        if candidate.exists():
            configured = Path(candidate.read_text(encoding="utf-8").strip()).expanduser()
            if (configured / "templates.yml").exists():
                return configured
    return None


def default_template_repo(project: Path) -> Path:
    env_path = os.environ.get("AGENTS_TEMPLATE_REPO")
    if env_path:
        return Path(env_path).expanduser()

    configured = installed_repo_config()
    if configured:
        return configured

    search_roots = [*ancestors(Path(__file__).resolve()), *ancestors(project), *ancestors(Path.cwd())]
    for candidate in search_roots:
        if (candidate / "templates.yml").exists() and (candidate / "templates").is_dir():
            return candidate

    for name in ("agents-file-templates-and-skills", "agents-file-templates"):
        candidate = Path.home() / "Development" / name
        if candidate.exists():
            return candidate

    raise SystemExit(
        "Could not find agents-file-templates-and-skills. Pass --template-repo or set AGENTS_TEMPLATE_REPO."
    )


def output_for_agent(agent: str, mode: str, explicit_output: str | None) -> str:
    if explicit_output:
        return explicit_output
    if mode == "specific":
        return AGENT_OUTPUTS.get(agent, AGENT_OUTPUTS["standard"])
    return AGENT_OUTPUTS["standard"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--template-repo", default=None)
    parser.add_argument("--types", default="")
    parser.add_argument("--agent", default="standard", choices=sorted(AGENT_OUTPUTS))
    parser.add_argument("--output-mode", default="standard", choices=["standard", "specific"])
    parser.add_argument("--output", default=None)
    parser.add_argument("--set", dest="sets", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--budget-report", action="store_true")
    parser.add_argument("--budget-warning-words", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    template_repo = Path(args.template_repo).expanduser().resolve() if args.template_repo else default_template_repo(project)
    forced = [item.strip() for item in args.types.split(",") if item.strip()]
    output_name = output_for_agent(args.agent, args.output_mode, args.output)

    if args.check:
        payload = check_output(project, template_repo, forced, args.sets, args.agent, output_name)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"{payload['status']} {payload['output']}")
        return 0 if payload["status"] == "current" else 1

    if args.budget_report:
        payload = budget_report(
            project,
            template_repo,
            forced,
            args.agent,
            output_name,
            args.budget_warning_words,
        )
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(
                f"{payload['status']} {payload['output']}: {payload['word_count']} words "
                f"(warning at {payload['warning_words']})"
            )
        return 0

    output = project / output_name
    selected = forced
    recovered: list[str] = []
    recovery_complete = True
    if output.exists():
        current = output.read_text(encoding="utf-8", errors="ignore")
        if GENERATED_MARKER not in current:
            if args.apply:
                raise SystemExit(
                    f"Refusing to overwrite existing unmarked instruction file: {output}. "
                    "Review or move it, then rerun --apply."
                )
        else:
            if not selected:
                selected = generated_types(current)
            recovered, recovery_complete = recover_render_pairs(
                project, template_repo, selected, args.agent, output_name, current
            )

    if output.exists() and GENERATED_MARKER in current and not recovery_complete:
        unrecovered = unrecovered_placeholders(
            template_repo,
            selected,
            recovered,
            args.sets,
        )
        if args.apply and unrecovered:
            raise SystemExit(
                f"Cannot safely refresh {output}: the generated file no longer matches its current templates, "
                f"and values for placeholders {', '.join(unrecovered)} are missing. No file was changed. "
                "Review and supply each replacement with --set KEY=VALUE, then rerun --apply."
            )
        if not args.apply and unrecovered:
            print(
                f"Warning: prior values for placeholders {', '.join(unrecovered)} may not be recoverable "
                f"for {output}; apply requires explicit --set values.",
                file=sys.stderr,
            )

    content = render(project, template_repo, selected, [*recovered, *args.sets], args.agent, output_name)

    if args.apply:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
