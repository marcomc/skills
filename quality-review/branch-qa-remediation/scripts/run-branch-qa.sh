#!/usr/bin/env bash
set -euo pipefail

BASE_BRANCH="main"
OUTPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      BASE_BRANCH="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: run-branch-qa.sh [--base <branch>] [--output <report.md>]" >&2
      exit 1
      ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  echo "Not in a git repository." >&2
  exit 1
fi
cd "${REPO_ROOT}"

BASE_REF="${BASE_BRANCH}"
if ! git rev-parse --verify "${BASE_REF}" >/dev/null 2>&1; then
  if git rev-parse --verify "origin/${BASE_BRANCH}" >/dev/null 2>&1; then
    BASE_REF="origin/${BASE_BRANCH}"
  else
    echo "Base branch not found: ${BASE_BRANCH} (or origin/${BASE_BRANCH})" >&2
    exit 1
  fi
fi

MERGE_BASE="$(git merge-base HEAD "${BASE_REF}" 2>/dev/null || true)"
if [[ -z "${MERGE_BASE}" ]]; then
  echo "Could not determine merge-base between HEAD and ${BASE_REF}." >&2
  exit 1
fi

BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
TS="$(date +%Y%m%d-%H%M%S)"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DEFAULT_OUT="${REPO_ROOT}/docs/qa/reports/branch-qa-remediation-${TS}.md"
REPORT_PATH="${OUTPUT_PATH:-${DEFAULT_OUT}}"
mkdir -p "$(dirname "${REPORT_PATH}")"

TMP_DIR="$(mktemp -d)"
FINDINGS_TSV="${TMP_DIR}/findings.tsv"
SORTED_TSV="${TMP_DIR}/findings-sorted.tsv"
CHANGED_FILES_TXT="${TMP_DIR}/changed-files.txt"
trap 'rm -rf "${TMP_DIR}"' EXIT

touch "${FINDINGS_TSV}"

git diff --name-only --diff-filter=ACMRT "${MERGE_BASE}" > "${CHANGED_FILES_TXT}"

add_finding() {
  local severity="$1" file="$2" line="$3" issue="$4" remediation="$5"
  local rank
  case "${severity}" in
    High) rank="1" ;;
    Medium) rank="2" ;;
    Low) rank="3" ;;
    *) rank="3" ;;
  esac
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${rank}" "${severity}" "${file}" "${line}" "${issue}" "${remediation}" >> "${FINDINGS_TSV}"
}

extract_added_lines() {
  local file="$1"
  git diff -U0 "${MERGE_BASE}" -- "${file}" | awk '
    /^@@ / {
      header=$0
      sub(/^.*\+/, "", header)
      sub(/ .*/, "", header)
      split(header, a, ",")
      line=a[1]
      next
    }
    /^\+[^+]/ {
      text=substr($0, 2)
      printf "%s\t%s\n", line, text
      line++
    }
  '
}

while IFS= read -r file; do
  [[ -z "${file}" ]] && continue
  [[ ! -f "${file}" ]] && continue
  [[ "${file}" == docs/qa/reports/* || "${file}" == reports/* ]] && continue

  ADDED_FILE="${TMP_DIR}/added-$(echo "${file}" | tr '/ ' '__').tsv"
  extract_added_lines "${file}" > "${ADDED_FILE}"

  while IFS=$'\t' read -r line text; do
    [[ -z "${line}" ]] && continue

    if [[ "${text}" =~ (password|secret|token|api[_-]?key)[[:space:]]*[:=][[:space:]]*[\"\'][^\"\']{6,}[\"\'] ]]; then
      add_finding "High" "${file}" "${line}" \
        "Potential hardcoded credential in added line" \
        "Move secret to env/vault/secret store and reference via variable lookup."
    fi

    if [[ "${text}" =~ (console\.log\(|debugger;|set[[:space:]]+-x|fmt\.Println\(|print\() ]]; then
      add_finding "Medium" "${file}" "${line}" \
        "Debug/logging statement added" \
        "Remove or gate debug output behind explicit debug flags."
    fi

    if [[ "${file}" =~ \.(sh|bash|py|js|ts|tsx|jsx|go|java|kt|c|cc|cpp|h|hpp|yml|yaml|toml|json)$ ]] && [[ "${text}" =~ ^[[:space:]]*(#|//|/\*|\*|<!--).*(TODO|FIXME|XXX|HACK) ]]; then
      add_finding "Low" "${file}" "${line}" \
        "Placeholder marker added in code" \
        "Convert to a tracked task/card or resolve before merge."
    fi

  done < "${ADDED_FILE}"
done < "${CHANGED_FILES_TXT}"

if command -v shellcheck >/dev/null 2>&1; then
  while IFS= read -r file; do
    [[ -z "${file}" ]] && continue
    [[ ! -f "${file}" ]] && continue
    if [[ "${file}" =~ \.sh$ ]]; then
      while IFS= read -r out_line; do
        [[ -z "${out_line}" ]] && continue
        sc_file="$(printf '%s' "${out_line}" | cut -d: -f1)"
        sc_line="$(printf '%s' "${out_line}" | cut -d: -f2)"
        msg="$(printf '%s' "${out_line}" | cut -d: -f4-)"
        sev="Low"
        if [[ "${msg}" =~ error ]]; then
          sev="High"
        elif [[ "${msg}" =~ warning ]]; then
          sev="Medium"
        fi
        add_finding "${sev}" "${sc_file}" "${sc_line}" \
          "shellcheck finding: ${msg}" \
          "Apply shellcheck suggestion for this line and re-run shellcheck on changed scripts."
      done < <(shellcheck --enable=all -f gcc "${file}" 2>/dev/null || true)
    fi
  done < "${CHANGED_FILES_TXT}"
fi

if [[ -s "${FINDINGS_TSV}" ]]; then
  sort -t $'\t' -k1,1n -k3,3 -k4,4n "${FINDINGS_TSV}" > "${SORTED_TSV}"
else
  : > "${SORTED_TSV}"
fi

TOTAL_FILES="$(wc -l < "${CHANGED_FILES_TXT}" | tr -d ' ')"
TOTAL_FINDINGS="$(wc -l < "${SORTED_TSV}" | tr -d ' ')"
HIGH_COUNT="$(awk -F '\t' '$2=="High"{c++} END{print c+0}' "${SORTED_TSV}")"
MED_COUNT="$(awk -F '\t' '$2=="Medium"{c++} END{print c+0}' "${SORTED_TSV}")"
LOW_COUNT="$(awk -F '\t' '$2=="Low"{c++} END{print c+0}' "${SORTED_TSV}")"

{
  echo "# Branch QA Remediation Report"
  echo
  printf -- "- Branch: \`%s\`\n" "${BRANCH_NAME}"
  printf -- "- Base: \`%s\`\n" "${BASE_REF}"
  printf -- "- Merge Base: \`%s\`\n" "${MERGE_BASE}"
  printf -- "- Generated: \`%s\`\n" "${GENERATED_AT}"
  echo
  echo "## Summary"
  echo
  echo "- Changed files: ${TOTAL_FILES}"
  echo "- Findings: ${TOTAL_FINDINGS} (High: ${HIGH_COUNT}, Medium: ${MED_COUNT}, Low: ${LOW_COUNT})"
  echo
  echo "## Findings"
  echo

  if [[ "${TOTAL_FINDINGS}" -eq 0 ]]; then
    echo "No actionable findings detected in branch changes."
  else
    echo "| Severity | File | Line | Issue | Remediation |"
    echo "|---|---|---:|---|---|"
    while IFS=$'\t' read -r rank severity file line issue remediation; do
      printf "| %s | \`%s\` | %s | %s | %s |\n" "${severity}" "${file}" "${line}" "${issue}" "${remediation}"
    done < "${SORTED_TSV}"
  fi

  echo
  echo "## Remediation Prompt Snippet"
  echo
  echo '```markdown'
  printf 'Apply the following branch QA remediations against current HEAD (base: %s).\n\n' "${BASE_REF}"

  if [[ "${TOTAL_FINDINGS}" -eq 0 ]]; then
    echo "No findings to remediate. Verify with branch QA report and proceed."
  else
    n=0
    while IFS=$'\t' read -r rank severity file line issue remediation; do
      n=$((n + 1))
      printf "%s. [%s] \`%s:%s\`\n" "${n}" "${severity}" "${file}" "${line}"
      printf "   - Issue: %s\n" "${issue}"
      printf "   - Fix: %s\n" "${remediation}"
    done < "${SORTED_TSV}"
    echo
    echo "After applying fixes, rerun:"
    echo "- shellcheck --enable=all on changed .sh files"
    echo "- /Users/mmassari/.codex/skills/branch-qa-remediation/scripts/run-branch-qa.sh --base ${BASE_BRANCH}"
  fi
  echo '```'
} > "${REPORT_PATH}"

echo "${REPORT_PATH}"
