---
name: mcpone-install-mcp-server
description: Install or update an MCP server in the local McpOne SQLite database and enable it in Codex Cluster A. Use when a user says to install an MCP server from a URL into McpOne.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# McpOne MCP Server Installer

Use this skill when the user asks for something like: `install skill (<name>) from <url>`.

## Primary usage

Run these commands from the installed skill directory (for example,
`cd ~/.agents/skills/mcpone-install-mcp-server`). Name optional:

```bash
python3 scripts/install_mcp_server.py \
  --url "https://github.com/loopwork/iMCP"
```

- Streamable HTTP server with bearer authentication:

```bash
python3 scripts/install_mcp_server.py \
  --name "Home Assistant" \
  --server-url "http://home.example:8123/api/mcp" \
  --header "Authorization=Bearer TOKEN" \
  --all-active-clusters \
  --sync-json-agent-configs
```

- Name explicit:

```bash
python3 scripts/install_mcp_server.py \
  --name "iMCP" \
  --url "https://github.com/loopwork/iMCP"
```

## How inference works

- Tries to extract install/run command from URL documentation (README/code blocks).
- Falls back to host heuristics:
- `npmjs.com/package/<pkg>` -> `npx -y <pkg>`
- `pypi.org/project/<pkg>` -> `uvx <pkg>`
- `github.com/loopwork/iMCP` -> `/Applications/iMCP.app/Contents/MacOS/imcp-server`
- Auto-generates a stable 6-char ID when `--id` is omitted.
- `--server-url` records a native `STREAMABLE_HTTP` endpoint instead of a
  local command.
- `--all-active-clusters` enables the server for every configured agent's
  active cluster; without it, only `Codex -> Cluster A` is updated.
- `--sync-json-agent-configs` merges a Streamable HTTP server into enabled JSON
  agent configurations. It renders agent-specific HTTP fields, preserves
  unrelated servers, removes only the same McpOne server ID alias, writes
  atomically, and creates a timestamped backup per file. Existing McpOne HTTP
  records are also upgraded to the current agent-specific shape when their old
  typed entry matches the McpOne record, without enabling unrelated agents.
- Codex TOML is intentionally excluded from JSON synchronization. Add its HTTP
  server with `codex mcp add --url ... --bearer-token-env-var ...`; this avoids
  McpOne's unsupported `args` and `headers` fields for Codex HTTP servers.

## Optional overrides

```bash
python3 scripts/install_mcp_server.py \
  --url "https://example.com/docs" \
  --command "npx" \
  --arg "-y" \
  --arg "my-mcp-package" \
  --env "API_KEY=..."
```

## Verification

- Use dry run to inspect inferred values without DB changes:

```bash
python3 scripts/install_mcp_server.py \
  --url "https://github.com/loopwork/iMCP" \
  --dry-run
```

- Restart McpOne after install:

```bash
osascript -e 'tell application "McpOne" to quit' >/dev/null 2>&1 || true
open -a "/Applications/McpOne.app"
```

## Scope and guardrails

- Updates McpOne DB and, only with `--sync-json-agent-configs`, the enabled
  JSON agent configuration files. Does not edit Codex TOML.
- Upserts `ZADDEDSERVER` and enables the server in the selected cluster or all
  active clusters.
- Supports current McpOne JSON agents without hard-coding their paths: Claude,
  Claude CLI, Copilot, Gemini CLI, VS Code, Insiders, and Antigravity are read
  from `ZADDEDAPP`. Unknown JSON agents receive the common typed HTTP shape.
- Uses Gemini CLI's `httpUrl` for Streamable HTTP and Antigravity's `serverUrl`,
  following their [configuration schema](https://geminicli.com/docs/reference/configuration/)
  and [MCP setup docs](https://www.antigravity.google/docs/mcp). Symlinked agent
  config paths are rejected so atomic replacement cannot detach a linked file.
- Creates a timestamped McpOne DB backup before modification.
- The McpOne backup uses SQLite's online backup API, including committed WAL
  data. Config sync preflights every file, rejects symlinked configs and
  unverified same-name entries, then applies all writes with rollback for
  caught I/O or database-commit failures. Backups remain available for manual
  recovery if restoring a config fails. Endpoint credentials and query/fragment
  values are omitted from command output.
- If inference fails, provide `--command` and `--arg` explicitly.
