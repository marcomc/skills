#!/usr/bin/env bash
set -euo pipefail

root="$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || pwd)"
output_mode="list"

usage() {
  cat <<'USAGE'
Usage: collect-context.sh [--block]

Options:
  --block   Print a ready-to-paste Markdown block grouped by core/referenced files
  --help    Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --block)
      output_mode="block"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

collect_files() {
  local file
  rg --files -g 'AGENTS.md' "${root}" 2>/dev/null || true

  for file in README.md TODO.md CHANGELOG.md; do
    if [[ -f "${root}/${file}" ]]; then
      printf '%s\n' "${root}/${file}"
    fi
  done

  if [[ -d "${root}/specs" ]]; then
    rg --files "${root}/specs" 2>/dev/null || true
  fi

  rg --files \
    -g '*Summary*.md' \
    -g '*Journey*.md' \
    -g 'Status*.md' \
    -g 'Progress*.md' \
    -g 'Roadmap*.md' \
    -g 'Backlog*.md' \
    "${root}" 2>/dev/null || true
}

extract_references() {
  local files=()
  while IFS= read -r line; do
    [[ -n "${line}" ]] && files+=("${line}")
  done

  if [[ ${#files[@]} -eq 0 ]]; then
    return 0
  fi

  rg -o --no-filename "[A-Za-z0-9._/-]+\.(md|yml|yaml|sh|py|json|toml|txt)" "${files[@]}" 2>/dev/null || true
  rg -o --no-filename "\]\([^)]*\)" "${files[@]}" 2>/dev/null | \
    sed -E 's/^\]\(([^)]+)\)$/\1/' | \
    sed -E 's/[?#].*$//' | \
    grep -vE '^(https?://|mailto:)' || true
}

resolve_paths() {
  local path
  while IFS= read -r path; do
    [[ -z "${path}" ]] && continue
    if [[ "${path}" = /* ]]; then
      [[ -f "${path}" ]] && printf '%s\n' "${path}"
      continue
    fi
    if [[ -f "${root}/${path}" ]]; then
      printf '%s\n' "${root}/${path}"
      continue
    fi
  done
}

primary_files_raw="$(collect_files | sort -u)"
mapfile -t primary_files <<< "${primary_files_raw}"

referenced_files_raw=""
if [[ ${#primary_files[@]} -gt 0 ]]; then
  referenced_files_raw="$(printf '%s\n' "${primary_files[@]}" | extract_references | resolve_paths | sort -u)"
fi
mapfile -t referenced_files <<< "${referenced_files_raw}"

if [[ "${output_mode}" == "block" ]]; then
  printf '## Context files\n\n'
  printf '### Core\n'
  if [[ ${#primary_files[@]} -eq 0 ]]; then
    printf '_No core files found._\n'
  else
    for path in "${primary_files[@]}"; do
      [[ -n "${path}" ]] && printf -- "- \`%s\`\n" "${path}"
    done
  fi
  printf '\n### Referenced\n'
  if [[ ${#referenced_files[@]} -eq 0 ]]; then
    printf '_No referenced files found._\n'
  else
    declare -A primary_set=()
    for path in "${primary_files[@]}"; do
      [[ -n "${path}" ]] && primary_set["${path}"]=1
    done
    for path in "${referenced_files[@]}"; do
      [[ -n "${path}" && -z "${primary_set["${path}"]+x}" ]] && printf -- "- \`%s\`\n" "${path}"
    done
  fi
  exit 0
fi

printf '%s\n' "${primary_files[@]}"
printf '%s\n' "${referenced_files[@]}"
