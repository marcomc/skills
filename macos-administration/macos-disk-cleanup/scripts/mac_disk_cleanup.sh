#!/bin/sh

set -eu

usage() {
    cat <<'USAGE'
Usage: mac_disk_cleanup.sh [--dry-run | --apply-safe] [--deep] [--thin-snapshots GIB]

  --dry-run             Inventory only; default mode.
  --apply-safe          Clear rebuildable caches after inventory and per-target activity checks.
  --deep                Traverse the full live Data volume for size rankings.
  --thin-snapshots GIB  Also ask Time Machine to thin local snapshots by GIB.
USAGE
}

user_home=${HOME:?HOME is required}
data_volume=/System/Volumes/Data
mode=dry-run
thin_gib=0
deep_scan=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run)
            mode=dry-run
            shift
            ;;
        --apply-safe)
            mode=apply-safe
            shift
            ;;
        --deep)
            deep_scan=1
            shift
            ;;
        --thin-snapshots)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            thin_gib=$2
            case "${thin_gib}" in
                ''|*[!0-9]*) usage >&2; exit 2 ;;
                *) ;;
            esac
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
done

show_size() {
    target_dir=$1
    [ -e "${target_dir}" ] || return 0
    du -sh "${target_dir}" 2>/dev/null || true
}

report_named_processes() {
    process_name=$1
    pids=$(pgrep -x "${process_name}" 2>/dev/null || true)
    [ -n "${pids}" ] || return 0
    printf 'ACTIVE process=%s pids=%s\n' "${process_name}" "${pids}" >&2
}

report_open_handles() {
    target_path=$1
    open_pids=''
    open_handles_safe=0
    if [ -d "${target_path}" ]; then
        if open_pids=$(lsof -nP -t +D "${target_path}" 2>&1); then
            :
        else
            lsof_status=$?
            if [ "${lsof_status}" -ne 1 ]; then
                printf 'SKIP %s: lsof failed with status %s\n' "${target_path}" "${lsof_status}" >&2
                return 0
            fi
        fi
    else
        if open_pids=$(lsof -nP -t "${target_path}" 2>&1); then
            :
        else
            lsof_status=$?
            if [ "${lsof_status}" -ne 1 ]; then
                printf 'SKIP %s: lsof failed with status %s\n' "${target_path}" "${lsof_status}" >&2
                return 0
            fi
        fi
    fi

    if [ -n "${open_pids}" ] && printf '%s\n' "${open_pids}" | LC_ALL=C grep -qv '^[0-9][0-9]*$'; then
        printf 'SKIP %s: lsof produced diagnostics; activity check is inconclusive\n' "${target_path}" >&2
        return 0
    fi

    if [ -z "${open_pids}" ]; then
        open_handles_safe=1
        return 0
    fi
    printf '%s\n' "${open_pids}" | awk '!seen[$0]++' | while IFS= read -r process_id; do
        process_command=$(ps -p "${process_id}" -o comm= 2>/dev/null || true)
        printf 'ACTIVE handle target=%s pid=%s command=%s\n' "${target_path}" "${process_id}" "${process_command}" >&2
    done
}

owner_process_kind() {
    target_path=$1
    case "${target_path}" in
        "${user_home}/.cache/uv"|"${user_home}/.cache/uv/"*)
            printf '%s\n' uv
            ;;
        "${user_home}/.cache/codex-runtimes"|"${user_home}/.cache/codex-runtimes/"*)
            printf '%s\n' codex
            ;;
        "${user_home}/.npm"|"${user_home}/.npm/"*)
            printf '%s\n' package-manager
            ;;
        "${user_home}/Library/Developer/Xcode/DerivedData"|"${user_home}/Library/Developer/Xcode/DerivedData/"*)
            printf '%s\n' xcode
            ;;
        *)
            printf '%s\n' none
            ;;
    esac
}

preserved_entry_reason() {
    target_path=$1
    case "${target_path}" in
        "${user_home}/.cache/uv"|"${user_home}/.cache/uv/"*)
            printf '%s\n' 'managed by uv; use uv cache prune'
            ;;
        "${user_home}/.cache/codex-runtimes"|"${user_home}/.cache/codex-runtimes/"*)
            printf '%s\n' 'Codex runtime; use the owning updater'
            ;;
        "${user_home}/.cache/whisper"|"${user_home}/.cache/whisper/"*|"${user_home}/.cache/huggingface"|"${user_home}/.cache/huggingface/"*|"${user_home}/.cache/torch"|"${user_home}/.cache/torch/"*|"${user_home}/.cache/transformers"|"${user_home}/.cache/transformers/"*|"${user_home}/.cache/mlx"|"${user_home}/.cache/mlx/"*)
            printf '%s\n' 'model or ML assets; preserve by default'
            ;;
        "${user_home}/.cache/"*-venv|"${user_home}/.cache/"*'-venv/'*|"${user_home}/.cache/venv"|"${user_home}/.cache/venv/"*|"${user_home}/.cache/.venv"|"${user_home}/.cache/.venv/"*)
            printf '%s\n' 'cached virtual environment; preserve by default'
            ;;
        *)
            ;;
    esac
}

report_owner_processes() {
    owner_kind=$1
    case "${owner_kind}" in
        uv)
            report_named_processes uv
            ;;
        codex)
            report_named_processes codex
            report_named_processes ChatGPT
            ;;
        package-manager)
            report_named_processes npm
            report_named_processes pnpm
            report_named_processes yarn
            report_named_processes bun
            ;;
        xcode)
            report_named_processes xcodebuild
            report_named_processes swift
            ;;
        none)
            ;;
        *)
            ;;
    esac
}

has_owner_process() {
    owner_kind=$1
    owner_process_active=0
    case "${owner_kind}" in
        uv)
            if pgrep -x uv >/dev/null 2>&1; then owner_process_active=1; fi
            ;;
        codex)
            if pgrep -x codex >/dev/null 2>&1 || pgrep -x ChatGPT >/dev/null 2>&1; then owner_process_active=1; fi
            ;;
        package-manager)
            if pgrep -x npm >/dev/null 2>&1 || pgrep -x pnpm >/dev/null 2>&1 || pgrep -x yarn >/dev/null 2>&1 || pgrep -x bun >/dev/null 2>&1; then owner_process_active=1; fi
            ;;
        xcode)
            if pgrep -x xcodebuild >/dev/null 2>&1 || pgrep -x swift >/dev/null 2>&1; then owner_process_active=1; fi
            ;;
        none)
            ;;
        *)
            ;;
    esac
    return 0
}

check_clear_preflight() {
    target_path=$1
    owner_kind=$2
    clear_preflight_safe=0
    if ! command -v lsof >/dev/null 2>&1; then
        printf 'SKIP %s: lsof is unavailable; cannot perform activity check\n' "${target_path}" >&2
        return 0
    fi
    report_owner_processes "${owner_kind}"
    has_owner_process "${owner_kind}"
    if [ "${owner_process_active}" -eq 1 ]; then
        printf 'SKIP %s: owning process is active\n' "${target_path}" >&2
        return 0
    fi
    report_open_handles "${target_path}"
    if [ "${open_handles_safe}" -eq 1 ]; then
        clear_preflight_safe=1
    fi
    return 0
}

clear_entry() {
    target_path=$1
    [ -e "${target_path}" ] || [ -L "${target_path}" ] || return 0
    preserve_reason=$(preserved_entry_reason "${target_path}")
    if [ -n "${preserve_reason}" ]; then
        printf 'PRESERVE %s: %s\n' "${target_path}" "${preserve_reason}"
        return 0
    fi
    owner_kind=$(owner_process_kind "${target_path}")
    check_clear_preflight "${target_path}" "${owner_kind}"
    if [ "${clear_preflight_safe}" -eq 1 ]; then
        printf 'CLEAN %s\n' "${target_path}"
        rm -rf -- "${target_path}"
    else
        printf 'PRESERVE %s\n' "${target_path}"
    fi
}

clear_children() {
    parent_dir=$1
    [ -d "${parent_dir}" ] || return 0
    for child_path in "${parent_dir}"/* "${parent_dir}"/.[!.]* "${parent_dir}"/..?*; do
        clear_entry "${child_path}"
    done
}

printf '%s\n' '== live filesystem =='
df -h "${data_volume}"
printf '%s\n' '== APFS snapshots =='
if command -v diskutil >/dev/null 2>&1; then
    diskutil apfs listSnapshots "${data_volume}" 2>&1 || true
fi
if command -v tmutil >/dev/null 2>&1; then
    tmutil listlocalsnapshotdates / 2>&1 || true
fi

if [ "${deep_scan}" -eq 1 ]; then
    printf '%s\n' '== largest live Data-volume directories =='
    du -x -d 1 -h "${data_volume}" 2>/dev/null | sort -hr | head -25 || true
    printf '%s\n' '== largest user-home directories =='
    du -x -d 2 -h "${user_home}" 2>/dev/null | sort -hr | head -40 || true
else
    printf '%s\n' '== deep size ranking =='
    printf '%s\n' 'SKIP: pass --deep to traverse the full live Data volume'
fi

printf '%s\n' '== package-manager caches =='
show_size "${user_home}/.npm/_cacache"
if [ "${deep_scan}" -eq 1 ]; then
    show_size "${user_home}/.cache"
else
    printf '%s\n' 'User cache totals: pass --deep for recursive sizes'
fi

printf '%s\n' '== rebuildable cache candidates =='
if [ "${deep_scan}" -eq 1 ]; then
    show_size "${user_home}/Library/Caches"
    show_size "${user_home}/Library/Developer/Xcode/DerivedData"
else
    printf '%s\n' 'Cache totals: pass --deep for recursive sizes'
fi
if [ "${deep_scan}" -eq 1 ]; then
    container_cache_count=0
    for cache_dir in "${user_home}/Library/Containers"/*/Data/Library/Caches; do
        if [ -d "${cache_dir}" ]; then container_cache_count=$((container_cache_count + 1)); fi
    done
    group_cache_count=0
    for cache_dir in "${user_home}/Library/Group Containers"/*/Library/Caches; do
        if [ -d "${cache_dir}" ]; then group_cache_count=$((group_cache_count + 1)); fi
    done
    printf 'Sandbox cache directories: %s\n' "${container_cache_count}"
    printf 'Shared cache directories: %s\n' "${group_cache_count}"
else
    printf '%s\n' 'Sandbox/shared cache enumeration: deferred until --deep or --apply-safe'
fi

printf '%s\n' '== relevant active processes =='
for process_name in npm pnpm yarn bun uv codex ChatGPT xcodebuild swift backupd mobilebackupd; do
    report_named_processes "${process_name}"
done

if [ "${mode}" = apply-safe ]; then
    printf '%s\n' '== applying rebuildable cleanup =='
    cache_cleanup_allowed=1
    npm_available=0
    uv_available=0

    if command -v npm >/dev/null 2>&1; then
        npm_available=1
        if npm_cache_dir=$(npm config get cache 2>/dev/null) && [ -n "${npm_cache_dir}" ]; then
            if [ "${npm_cache_dir}" != "${user_home}/.npm" ]; then
                printf 'SKIP cache cleanup: npm cache resolves to custom path %s; only %s is supported\n' \
                    "${npm_cache_dir}" "${user_home}/.npm" >&2
                cache_cleanup_allowed=0
            fi
        else
            printf '%s\n' 'SKIP cache cleanup: could not resolve npm cache location' >&2
            cache_cleanup_allowed=0
        fi
    fi

    if command -v uv >/dev/null 2>&1; then
        uv_available=1
        if uv_cache_dir=$(uv cache dir 2>/dev/null) && [ -n "${uv_cache_dir}" ]; then
            if [ "${uv_cache_dir}" != "${user_home}/.cache/uv" ]; then
                printf 'SKIP cache cleanup: uv cache resolves to custom path %s; only %s is supported\n' \
                    "${uv_cache_dir}" "${user_home}/.cache/uv" >&2
                cache_cleanup_allowed=0
            fi
        else
            printf '%s\n' 'SKIP cache cleanup: could not resolve uv cache location' >&2
            cache_cleanup_allowed=0
        fi
    fi

    if [ "${cache_cleanup_allowed}" -eq 1 ]; then
        if [ "${npm_available}" -eq 1 ]; then
            check_clear_preflight "${user_home}/.npm" package-manager
            if [ "${clear_preflight_safe}" -eq 1 ]; then
                npm cache clean --force
                npm cache verify
            else
                printf '%s\n' 'PRESERVE NPM cache'
            fi
        fi

        if [ "${uv_available}" -eq 1 ]; then
            check_clear_preflight "${user_home}/.cache/uv" uv
            if [ "${clear_preflight_safe}" -eq 1 ]; then
                uv cache prune
            else
                printf '%s\n' 'PRESERVE uv cache'
            fi
        fi

        clear_children "${user_home}/.cache"
        clear_children "${user_home}/Library/Caches"
        clear_children "${user_home}/Library/Developer/Xcode/DerivedData"
        for cache_dir in "${user_home}/Library/Containers"/*/Data/Library/Caches \
            "${user_home}/Library/Group Containers"/*/Library/Caches; do
            clear_children "${cache_dir}"
        done
    else
        printf '%s\n' 'PRESERVE caches: package-manager cache discovery was custom or inconclusive' >&2
    fi
fi

if [ "${thin_gib}" -gt 0 ]; then
    if ! command -v tmutil >/dev/null 2>&1; then
        printf '%s\n' 'SKIP snapshots: tmutil is unavailable' >&2
    elif pgrep -x backupd >/dev/null 2>&1 || pgrep -x mobilebackupd >/dev/null 2>&1; then
        report_named_processes backupd
        report_named_processes mobilebackupd
        printf '%s\n' 'SKIP snapshots: Time Machine service is active' >&2
    else
        thin_bytes=$((thin_gib * 1073741824))
        printf 'THIN local Time Machine snapshots: %s GiB requested\n' "${thin_gib}"
        tmutil thinlocalsnapshots / "${thin_bytes}" 4 || true
    fi
fi

printf '%s\n' '== final filesystem state =='
df -h "${data_volume}"
exit 0
