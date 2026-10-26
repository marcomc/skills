#!/usr/bin/env python3
"""Mine AGENTS.md files and produce draft template updates."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


INSTRUCTION_FILE_PATTERNS = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".github/instructions/*.instructions.md",
)

PRIVATE_PATTERNS = [
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[0-1]))(?:\.\d{1,3}){2,3}\b"),
    re.compile(r"(?i)\b(?:token|secret|password|cookie|api[_-]?key)\b\s*[:=]"),
]

KEYWORDS = (
    "must",
    "always",
    "never",
    "prefer",
    "run ",
    "validate",
    "test",
    "lint",
    "secret",
    "deploy",
    "release",
    "readme",
    "changelog",
    "shellcheck",
    "markdownlint",
)
LEARNING_UPSTREAM_DIR = ".work/learning-upstream"
OUT_OF_SYNC_DIR = ".work/out-of-sync"
LEARNED_RULES_HEADING = "## Learned Rules"


def load_manifest(template_repo: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML is required to read templates.yml")
    return yaml.safe_load((template_repo / "templates.yml").read_text(encoding="utf-8"))


def installed_repo_config() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "config" / "template_repo_path.txt"
        if candidate.exists():
            configured = Path(candidate.read_text(encoding="utf-8").strip()).expanduser()
            if (configured / "templates.yml").exists():
                return configured
    return None


def default_template_repo() -> Path:
    env_path = os.environ.get("AGENTS_TEMPLATE_REPO")
    if env_path:
        return Path(env_path).expanduser().resolve()

    configured = installed_repo_config()
    if configured:
        return configured.resolve()

    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (candidate / "templates.yml").exists() and (candidate / "templates").is_dir():
            return candidate.resolve()

    raise SystemExit(
        "Could not find agents-file-templates-and-skills. Pass --template-repo or set AGENTS_TEMPLATE_REPO."
    )


def is_ignored(path: Path, ignored: set[str]) -> bool:
    return any(part in ignored for part in path.parts)


def agents_depth(root: Path, instruction_path: Path) -> int:
    project = project_root_for_instruction(instruction_path)
    rel_parent = project.relative_to(root)
    return len(rel_parent.parts)


def is_instruction_file(root: Path, path: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(rel, f"**/{pattern}") or fnmatch.fnmatch(rel, pattern) for pattern in INSTRUCTION_FILE_PATTERNS)


def project_root_for_instruction(path: Path) -> Path:
    if path.name == "copilot-instructions.md" and path.parent.name == ".github":
        return path.parent.parent
    if path.name.endswith(".instructions.md") and path.parent.parent.name == ".github":
        return path.parent.parent.parent
    return path.parent


def instruction_kind(path: Path) -> str:
    if path.name == "AGENTS.md":
        return "agents"
    if path.name == "CLAUDE.md":
        return "claude"
    if path.name == "GEMINI.md":
        return "gemini"
    if path.name == "copilot-instructions.md":
        return "copilot-repository"
    if path.name.endswith(".instructions.md"):
        return "copilot-path-specific"
    return "unknown"


def instruction_agent(path: Path, text: str = "", agent_global_paths: dict[str, str] | None = None) -> str:
    kind = instruction_kind(path)
    if kind in {"claude", "gemini"}:
        return kind
    if kind.startswith("copilot-"):
        return "copilot"
    if kind == "agents" and agent_global_paths:
        standard_path = agent_global_paths.get("standard")
        for agent, global_path in agent_global_paths.items():
            if global_path != standard_path and f"Follow `{global_path}`" in text:
                return agent
    return "standard"


def nested_instruction_dirs(current_path: Path) -> set[str]:
    if current_path.name == ".github":
        return {"instructions"}
    return {".github"}


def find_agents(roots: list[Path], max_depth: int, ignored: set[str]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            rel = current_path.relative_to(root)
            if is_ignored(rel, ignored):
                dirs[:] = []
                continue
            depth = 0 if rel == Path(".") else len(rel.parts)
            if depth >= max_depth:
                allowed = nested_instruction_dirs(current_path)
                dirs[:] = [item for item in dirs if item not in ignored and item in allowed]
            else:
                dirs[:] = [item for item in dirs if item not in ignored]
            for name in files:
                candidate = current_path / name
                if is_instruction_file(root, candidate) and agents_depth(root, candidate) <= max_depth:
                    found.append(candidate)
    return sorted(set(found))


def project_files(project: Path, ignored: set[str]) -> list[str]:
    files: list[str] = []
    for root, dirs, names in os.walk(project):
        dirs[:] = [d for d in dirs if d not in ignored]
        for name in names:
            files.append((Path(root) / name).relative_to(project).as_posix())
    return files


def glob_matches(pattern: str, files: list[str]) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return any(path == prefix or path.startswith(f"{prefix}/") for path in files)
    return any(fnmatch.fnmatch(path, pattern) for path in files)


def classify(project: Path, agents_text: str, manifest: dict) -> tuple[list[str], list[str]]:
    ignored = set(manifest.get("scan_defaults", {}).get("ignored_dirs", []))
    files = project_files(project, ignored)
    text = agents_text.lower()
    detected: list[str] = []
    evidence: list[str] = []
    for item in manifest.get("project_types", []):
        detector = item.get("detect", {})
        file_hits = [pattern for pattern in detector.get("file_globs", []) if glob_matches(pattern, files)]
        marker_hits = [marker for marker in detector.get("content_markers", []) if marker.lower() in text]
        if file_hits or marker_hits:
            detected.append(item["id"])
            evidence.append(f"{item['id']}: files={file_hits[:3]} markers={marker_hits[:3]}")
    return detected, evidence


def privacy_notes(text: str) -> list[str]:
    notes = []
    for pattern in PRIVATE_PATTERNS:
        if pattern.search(text):
            notes.append("contains private or secret-shaped material; review before reuse")
            break
    return notes


def reusable_categories(text: str) -> list[str]:
    lowered = text.lower()
    categories = []
    checks = {
        "validation": ["lint", "test", "validate", "markdownlint", "shellcheck"],
        "release": ["release", "changelog", "tag"],
        "secrets": ["secret", "token", "password", "no_log"],
        "containers": ["docker", "container", "compose"],
        "docs": ["readme", "documentation", "table of contents"],
        "deployment": ["deploy", "production"],
    }
    for name, markers in checks.items():
        if any(marker in lowered for marker in markers):
            categories.append(name)
    return categories


def redact(line: str) -> str:
    line = re.sub(r"/Users/[A-Za-z0-9._-]+", "${HOME}", line)
    line = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "${EMAIL}", line)
    line = re.sub(r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "${PRIVATE_IP}", line)
    line = re.sub(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "${PRIVATE_IP}", line)
    return line


def candidate_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("|") or len(line) > 220:
            continue
        lowered = line.lower()
        if any(keyword in lowered for keyword in KEYWORDS):
            lines.append(redact(line))
    return lines


def write_matrix(template_repo: Path, agents_files: list[Path], roots: list[Path], manifest: dict) -> list[dict]:
    records = []
    for agents_path in agents_files:
        project = project_root_for_instruction(agents_path)
        text = agents_path.read_text(encoding="utf-8", errors="ignore")
        detected, evidence = classify(project, text, manifest)
        root = next((item for item in roots if agents_path.is_relative_to(item)), roots[0])
        records.append(
            {
                "project_path": str(project),
                "agents_path": str(agents_path),
                "instruction_kind": instruction_kind(agents_path),
                "relative_depth": agents_depth(root, agents_path),
                "detected_types": detected,
                "evidence": evidence,
                "reusable_instruction_categories": reusable_categories(text),
                "privacy_risk_notes": privacy_notes(text),
                "candidate_templates": detected or ["generic-development"],
            }
        )

    matrix_dir = template_repo / ".work" / "matrix"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    (matrix_dir / "projects.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

    summary = ["# Agents Matrix Summary", "", f"- Generated: {date.today().isoformat()}", f"- Files: {len(records)}", ""]
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        for type_id in record["candidate_templates"]:
            counts[type_id] += 1
    summary.append("## Candidate Template Counts")
    summary.append("")
    for type_id, count in sorted(counts.items()):
        summary.append(f"- `{type_id}`: {count}")
    summary.append("")
    (matrix_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")
    return records


def draft_for_template(template_repo: Path, records: list[dict], template: str) -> Path:
    draft_dir = template_repo / ".work" / "drafts" / template
    draft_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[str] = []
    for record in records:
        if template not in record["candidate_templates"]:
            continue
        text = Path(record["agents_path"]).read_text(encoding="utf-8", errors="ignore")
        candidates.extend(candidate_lines(text))

    unique = []
    for line in candidates:
        if line not in unique:
            unique.append(line)

    draft = [
        f"# Draft: {template}",
        "",
        "This ignored draft contains mined candidate rules. Review and sanitize",
        "before editing curated templates.",
        "",
        "## Candidate Rules",
        "",
    ]
    draft.extend(f"- {line.lstrip('- ')}" for line in unique[:80])
    draft.append("")
    path = draft_dir / "draft.md"
    path.write_text("\n".join(draft), encoding="utf-8")
    return path


def clean_field(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for raw in text.splitlines():
        if raw.startswith("## "):
            current = raw.removeprefix("## ").strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(raw)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def bullet_values(section_text: str) -> list[str]:
    values: list[str] = []
    for raw in section_text.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        value = clean_field(line.removeprefix("- "))
        if value and value != "none-recorded":
            values.append(value)
    return values


def parse_learning_upstream_draft(path: Path) -> dict[str, str]:
    record = {
        "path": str(path),
        "lesson_family": path.stem,
        "proposed_template": "not-recorded",
        "review_status": "not-recorded",
        "privacy_verdict": "not-recorded",
        "recurrence_check": "not-recorded",
        "candidate_rule": "",
        "prevention_targets": "",
        "detection_targets": "",
        "refresh_triggers": "",
    }
    text = path.read_text(encoding="utf-8", errors="ignore")
    for raw in text.splitlines():
        line = raw.strip()
        fields = {
            "- Lesson family:": "lesson_family",
            "- Proposed template:": "proposed_template",
            "- Review status:": "review_status",
            "- Privacy verdict:": "privacy_verdict",
            "- Recurrence check:": "recurrence_check",
        }
        for prefix, key in fields.items():
            if line.startswith(prefix):
                record[key] = clean_field(line.removeprefix(prefix))
    sections = parse_markdown_sections(text)
    record["candidate_rule"] = sections.get("Candidate Rule", "").strip()
    record["prevention_targets"] = ", ".join(bullet_values(sections.get("Prevention Targets", "")))
    record["detection_targets"] = ", ".join(bullet_values(sections.get("Detection Targets", "")))
    record["refresh_triggers"] = ", ".join(bullet_values(sections.get("Refresh Triggers", "")))
    return record


def normalize_rule(text: str) -> str:
    lowered = text.lower().replace("`", "")
    lowered = re.sub(r"[-_/]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    lowered = re.sub(r"[^a-z0-9 ]+", "", lowered)
    return lowered


def template_path_for_id(template_repo: Path, manifest: dict, template_id: str) -> Path:
    for item in manifest.get("project_types", []):
        if item.get("id") == template_id:
            return template_repo / item["path"]
    if manifest.get("global_template", {}).get("id") == template_id:
        return template_repo / manifest["global_template"]["path"]
    raise SystemExit(f"Unknown template id in learning draft: {template_id}")


def append_learned_rule(template_text: str, candidate_rule: str) -> tuple[str, str]:
    normalized_candidate = normalize_rule(candidate_rule)
    existing_rules = [
        normalize_rule(line.strip().removeprefix("- "))
        for line in template_text.splitlines()
        if line.strip().startswith("- ")
    ]
    if normalized_candidate in existing_rules:
        return template_text, "already-present"

    bullet = candidate_rule.strip()
    if not bullet.startswith("- "):
        bullet = f"- {bullet}"

    if LEARNED_RULES_HEADING in template_text:
        lines = template_text.rstrip().splitlines()
        for idx, line in enumerate(lines):
            if line.strip() != LEARNED_RULES_HEADING:
                continue
            insert_at = idx + 1
            if insert_at < len(lines) and not lines[insert_at].strip():
                insert_at += 1
            lines.insert(insert_at, bullet)
            return "\n".join(lines) + "\n", "updated"
        return template_text, "already-present"

    updated = template_text.rstrip() + f"\n\n{LEARNED_RULES_HEADING}\n\n{bullet}\n"
    return updated, "updated"


def apply_learning_upstream_draft(
    template_repo: Path,
    manifest: dict,
    draft_path: Path,
    *,
    apply: bool,
) -> dict[str, str]:
    draft = parse_learning_upstream_draft(draft_path)
    candidate_rule = draft["candidate_rule"].strip()
    if not candidate_rule:
        raise SystemExit(f"Learning draft is missing Candidate Rule: {draft_path}")
    if privacy_notes(candidate_rule):
        raise SystemExit(f"Learning draft candidate rule needs privacy review: {draft_path}")
    if draft["privacy_verdict"] != "clean":
        raise SystemExit(f"Learning draft privacy verdict is not clean: {draft_path}")
    if draft["review_status"] != "approved":
        raise SystemExit(f"Learning draft is not approved: {draft_path}")

    template_path = template_path_for_id(template_repo, manifest, draft["proposed_template"])
    original = template_path.read_text(encoding="utf-8")
    updated, action = append_learned_rule(original, candidate_rule)
    if apply and updated != original:
        template_path.write_text(updated, encoding="utf-8")
    return {
        "action": action if apply else f"would-{action}",
        "draft": str(draft_path),
        "template": str(template_path),
        "lesson_family": draft["lesson_family"],
        "proposed_template": draft["proposed_template"],
        "refresh_triggers": draft["refresh_triggers"],
    }


def write_learning_upstream_summary(template_repo: Path) -> Path:
    draft_dir = template_repo / LEARNING_UPSTREAM_DIR
    draft_dir.mkdir(parents=True, exist_ok=True)
    drafts = [path for path in sorted(draft_dir.glob("*.md")) if path.name != "summary.md"]
    records = [parse_learning_upstream_draft(path) for path in drafts]

    by_template: dict[str, int] = defaultdict(int)
    by_status: dict[str, int] = defaultdict(int)
    by_privacy: dict[str, int] = defaultdict(int)
    by_recurrence: dict[str, int] = defaultdict(int)
    for record in records:
        by_template[record["proposed_template"]] += 1
        by_status[record["review_status"]] += 1
        by_privacy[record["privacy_verdict"]] += 1
        by_recurrence[record["recurrence_check"]] += 1

    summary = [
        "# Learning Upstream Summary",
        "",
        f"- Generated: {date.today().isoformat()}",
        f"- Draft files: {len(records)}",
        "",
        "## Proposed Templates",
        "",
    ]
    summary.extend(f"- `{key}`: {count}" for key, count in sorted(by_template.items()))
    if not by_template:
        summary.append("- `none`: 0")
    summary.extend(["", "## Review Status", ""])
    summary.extend(f"- `{key}`: {count}" for key, count in sorted(by_status.items()))
    if not by_status:
        summary.append("- `none`: 0")
    summary.extend(["", "## Privacy Verdict", ""])
    summary.extend(f"- `{key}`: {count}" for key, count in sorted(by_privacy.items()))
    if not by_privacy:
        summary.append("- `none`: 0")
    summary.extend(["", "## Recurrence", ""])
    summary.extend(f"- `{key}`: {count}" for key, count in sorted(by_recurrence.items()))
    if not by_recurrence:
        summary.append("- `none`: 0")
    summary.extend(["", "## Drafts", ""])
    for record in records:
        summary.append(
            f"- `{record['lesson_family']}` -> `{record['proposed_template']}` "
            f"({record['review_status']}, {record['privacy_verdict']})"
        )
    if not records:
        summary.append("- No draft files found.")
    summary.append("")

    path = draft_dir / "summary.md"
    path.write_text("\n".join(summary), encoding="utf-8")
    return path


def load_init_helper():
    helper = Path(__file__).resolve().parents[2] / "init-agents-file" / "scripts" / "init_agents_file.py"
    if not helper.is_file():
        raise SystemExit(
            "The out-of-sync report requires the companion init-agents-file skill. "
            "Install both skills under the same skills directory, then retry."
        )
    spec = importlib.util.spec_from_file_location("init_agents_file_helper", helper)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load init-agents-file helper: {helper}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_out_of_sync_report(
    template_repo: Path,
    roots: list[Path],
    max_depth: int,
    ignored: set[str],
) -> Path:
    init_helper = load_init_helper()
    candidates = []
    for path in find_agents(roots, max_depth, ignored):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if init_helper.GENERATED_MARKER in text:
            candidates.append((path, text))
    records = []
    for instruction_path, text in candidates:
        project = project_root_for_instruction(instruction_path)
        output_name = instruction_path.relative_to(project).as_posix()
        agent = instruction_agent(instruction_path, text, init_helper.AGENT_GLOBAL_PATHS)
        record = init_helper.check_output(
            project,
            template_repo,
            [],
            [],
            agent,
            output_name,
        )
        record["instruction_budget"] = init_helper.budget_report(
            project,
            template_repo,
            [],
            agent,
            output_name,
        )
        records.append(record)

    report_dir = template_repo / OUT_OF_SYNC_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "projects.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

    counts: dict[str, int] = defaultdict(int)
    budget_counts: dict[str, int] = defaultdict(int)
    for record in records:
        counts[str(record["status"])] += 1
        budget = record.get("instruction_budget", {})
        if isinstance(budget, dict):
            budget_counts[str(budget.get("status", "unknown"))] += 1

    summary = [
        "# Out Of Sync Summary",
        "",
        f"- Generated: {date.today().isoformat()}",
        f"- Generated project files checked: {len(records)}",
        "",
        "## Status Counts",
        "",
    ]
    if counts:
        summary.extend(f"- `{status}`: {count}" for status, count in sorted(counts.items()))
    else:
        summary.append("- `none`: 0")
    summary.extend(["", "## Instruction Budget", ""])
    if budget_counts:
        summary.extend(f"- `{status}`: {count}" for status, count in sorted(budget_counts.items()))
    else:
        summary.append("- `none`: 0")
    summary.extend(["", "## Projects", ""])
    for record in records:
        types = ", ".join(f"`{item}`" for item in record.get("template_types", [])) or "`none`"
        budget = record.get("instruction_budget", {})
        budget_status = budget.get("status", "unknown") if isinstance(budget, dict) else "unknown"
        summary.append(f"- `{record['status']}` `{budget_status}` {record['output']} ({types})")
    if not records:
        summary.append("- No generated project files found.")
    summary.append("")

    path = report_dir / "summary.md"
    path.write_text("\n".join(summary), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-repo", default=None)
    parser.add_argument("--scan-root", action="append", default=[])
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--template", default="")
    parser.add_argument("--current-project", default="")
    parser.add_argument("--learning-upstream-summary", action="store_true")
    parser.add_argument("--out-of-sync-report", action="store_true")
    parser.add_argument("--apply-learning-draft", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    template_repo = Path(args.template_repo).expanduser().resolve() if args.template_repo else default_template_repo()
    if args.apply_learning_draft:
        manifest = load_manifest(template_repo)
        result = apply_learning_upstream_draft(
            template_repo,
            manifest,
            args.apply_learning_draft.expanduser().resolve(),
            apply=args.apply,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"{result['action']} {result['template']}")
        return 0

    if args.learning_upstream_summary and not args.scan_root and not args.current_project and not args.template:
        path = write_learning_upstream_summary(template_repo)
        print(f"Wrote {path}")
        return 0

    manifest = load_manifest(template_repo)
    ignored = set(manifest.get("scan_defaults", {}).get("ignored_dirs", []))
    max_depth = args.max_depth or int(manifest.get("scan_defaults", {}).get("max_depth", 2))

    if args.out_of_sync_report and not args.current_project and not args.template:
        roots = [Path(item).expanduser().resolve() for item in args.scan_root] or [Path.cwd()]
        path = write_out_of_sync_report(template_repo, roots, max_depth, ignored)
        print(f"Wrote {path}")
        return 0

    if args.current_project:
        current_project = Path(args.current_project).expanduser().resolve()
        candidates = [
            current_project / "AGENTS.md",
            current_project / "CLAUDE.md",
            current_project / "GEMINI.md",
            current_project / ".github" / "copilot-instructions.md",
        ]
        candidates.extend((current_project / ".github" / "instructions").glob("*.instructions.md"))
        agents_files = [path for path in candidates if path.exists()]
        roots = [current_project]
    else:
        roots = [Path(item).expanduser().resolve() for item in args.scan_root] or [Path.cwd()]
        agents_files = find_agents(roots, max_depth, ignored)

    records = write_matrix(template_repo, agents_files, roots, manifest)
    print(f"Wrote matrix for {len(records)} AGENTS.md files.")

    if args.template:
        path = draft_for_template(template_repo, records, args.template)
        print(f"Wrote {path}")

    if args.learning_upstream_summary:
        path = write_learning_upstream_summary(template_repo)
        print(f"Wrote {path}")

    if args.out_of_sync_report:
        path = write_out_of_sync_report(template_repo, roots, max_depth, ignored)
        print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
