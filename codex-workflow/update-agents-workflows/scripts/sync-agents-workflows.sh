#!/usr/bin/env bash
set -euo pipefail

APPLY=false
AGENTS_PATH=""
LIMIT=25

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=true
      shift
      ;;
    --agents)
      AGENTS_PATH="${2:-}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:-25}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: sync-agents-workflows.sh [--apply] [--agents <AGENTS.md>] [--limit N]" >&2
      exit 1
      ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${REPO_ROOT}"

if [[ -z "${AGENTS_PATH}" ]]; then
  AGENTS_PATH="${REPO_ROOT}/AGENTS.md"
fi

if [[ ! -f "${AGENTS_PATH}" ]]; then
  echo "AGENTS.md not found: ${AGENTS_PATH}" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
CANDIDATES_RAW="${TMP_DIR}/candidates-raw.tsv"
CANDIDATES_DEDUP="${TMP_DIR}/candidates-dedup.tsv"
MISSING="${TMP_DIR}/missing.tsv"
trap 'rm -rf "${TMP_DIR}"' EXIT

touch "${CANDIDATES_RAW}" "${MISSING}"

append_candidate() {
  local cmd="$1" src="$2"
  [[ -z "${cmd}" ]] && return
  printf '%s\t%s\n' "${cmd}" "${src}" >> "${CANDIDATES_RAW}"
}

# 1) Makefile targets as runnable workflows.
if [[ -f Makefile ]]; then
  MAKE_TARGETS_FILE="${TMP_DIR}/make-targets.txt"
  grep -E '^[A-Za-z0-9._-]+:' Makefile | sed -E 's/:.*$/:/' > "${MAKE_TARGETS_FILE}" || true
  while IFS=: read -r target _; do
    [[ -z "${target}" ]] && continue
    [[ "${target}" =~ ^[A-Za-z0-9._-]+$ ]] || continue
    [[ "${target}" == .* ]] && continue
    append_candidate "make ${target}" "Makefile"
  done < "${MAKE_TARGETS_FILE}"
fi

# 2) package.json scripts.
if [[ -f package.json ]] && command -v jq >/dev/null 2>&1; then
  while IFS= read -r script_name; do
    [[ -z "${script_name}" ]] && continue
    append_candidate "npm run ${script_name}" "package.json"
  done < <(jq -r '.scripts // {} | keys[]' package.json 2>/dev/null || true)
fi

# 3) Executable helper scripts under common script folders.
for d in scripts tools bin; do
  [[ -d "${d}" ]] || continue
  FIND_FILE="${TMP_DIR}/find-${d}.txt"
  find "${d}" -type f \( -name '*.sh' -o -name '*.py' -o -name '*.js' -o -name '*.ts' \) -perm -u+x 2>/dev/null > "${FIND_FILE}" || true
  while IFS= read -r file; do
    rel="${file#./}"
    append_candidate "./${rel}" "${rel}"
  done < "${FIND_FILE}"
done

# 4) Inline command snippets from docs/specs/readme.
if [[ -f README.md ]] || [[ -d docs ]] || [[ -d specs ]]; then
  rg -n -o '`[^`]+`' README.md docs specs 2>/dev/null | while IFS= read -r row; do
    file="${row%%:*}"
    rest="${row#*:}"
    line_no="${rest%%:*}"
    snippet="${row#*:*:}"
    cmd="${snippet#\`}"
    cmd="${cmd%\`}"
    [[ -z "${cmd}" ]] && continue
    case "${cmd}" in
      make*|npm*|pnpm*|yarn*|bun*|python*|pytest*|tox*|poetry*|pipenv*|cargo*|go*|node*|docker*|kubectl*|helm*|terraform*|ansible*|uv*|just*|task*|ws*|./*|bash*|sh*)
        append_candidate "${cmd}" "${file}:${line_no}"
        ;;
      *)
        ;;
    esac
  done
fi

# Deduplicate by command; keep first source location.
awk -F '\t' '!seen[$1]++ {print $0}' "${CANDIDATES_RAW}" > "${CANDIDATES_DEDUP}"

# Keep only commands not already mentioned in AGENTS.
while IFS=$'\t' read -r cmd src; do
  [[ -z "${cmd}" ]] && continue
  if rg -qF "${cmd}" "${AGENTS_PATH}"; then
    continue
  fi
  printf '%s\t%s\n' "${cmd}" "${src}" >> "${MISSING}"
done < "${CANDIDATES_DEDUP}"

TOTAL="$(wc -l < "${MISSING}" | tr -d ' ')"
if [[ "${TOTAL}" -eq 0 ]]; then
  echo "No missing workflow commands discovered for AGENTS.md."
  exit 0
fi

head -n "${LIMIT}" "${MISSING}" > "${MISSING}.limited"

if [[ "${APPLY}" != true ]]; then
  echo "Discovered missing AGENTS workflow command candidates (${TOTAL}, showing up to ${LIMIT}):"
  nl -ba "${MISSING}.limited" | sed -E 's/^\s*([0-9]+)\s+([^\t]+)\t(.*)$/\1. \2 (source: \3)/'
  echo
  echo "Run with --apply to update AGENTS.md managed TODO block."
  exit 0
fi

START='<!-- codex:agents-workflow-sync:start -->'
END='<!-- codex:agents-workflow-sync:end -->'
BLOCK_FILE="${TMP_DIR}/block.md"

{
  echo "## Agent Discovered Workflow TODOs"
  echo
  echo "${START}"
  while IFS=$'\t' read -r cmd src; do
    echo "- TODO: verify and document \`${cmd}\` (source: \`${src}\`)."
  done < "${MISSING}.limited"
  echo "${END}"
} > "${BLOCK_FILE}"

if rg -qF "${START}" "${AGENTS_PATH}" && rg -qF "${END}" "${AGENTS_PATH}"; then
  awk -v start="${START}" -v end="${END}" -v block_file="${BLOCK_FILE}" '
    BEGIN {
      while ((getline line < block_file) > 0) block = block line "\n"
      close(block_file)
    }
    $0 == start {
      printf "%s", block
      skip = 1
      next
    }
    $0 == end {
      skip = 0
      next
    }
    !skip { print }
  ' "${AGENTS_PATH}" > "${AGENTS_PATH}.tmp"
  mv "${AGENTS_PATH}.tmp" "${AGENTS_PATH}"
else
  {
    cat "${AGENTS_PATH}"
    echo
    cat "${BLOCK_FILE}"
  } > "${AGENTS_PATH}.tmp"
  mv "${AGENTS_PATH}.tmp" "${AGENTS_PATH}"
fi

echo "Updated ${AGENTS_PATH} with managed TODO workflow block (${LIMIT} max entries)."
