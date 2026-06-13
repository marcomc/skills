---
name: mcpone-install-mcp-server
description: Install or update an MCP server in the local McpOne SQLite database and enable it in Codex Cluster A. Use when a user says to install an MCP server from a URL into McpOne.
---

# McpOne MCP Server Installer

Use this skill when the user asks for something like: `install skill (<name>) from <url>`.

## Primary usage

- Name optional:

```bash
~/.Codex/skills/mcpone-install-mcp-server/scripts/install_mcp_server.py \
  --url "https://github.com/loopwork/iMCP"
```

- Name explicit:

```bash
~/.Codex/skills/mcpone-install-mcp-server/scripts/install_mcp_server.py \
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

## Optional overrides

```bash
~/.Codex/skills/mcpone-install-mcp-server/scripts/install_mcp_server.py \
  --url "https://example.com/docs" \
  --command "npx" \
  --arg "-y" \
  --arg "my-mcp-package" \
  --env "API_KEY=..."
```

## Verification

- Use dry run to inspect inferred values without DB changes:

```bash
~/.Codex/skills/mcpone-install-mcp-server/scripts/install_mcp_server.py \
  --url "https://github.com/loopwork/iMCP" \
  --dry-run
```

- Restart McpOne after install:

```bash
osascript -e 'tell application "McpOne" to quit' >/dev/null 2>&1 || true
open -a "/Applications/McpOne.app"
```

## Scope and guardrails

- Updates McpOne DB only; does not edit Codex TOML.
- Upserts `ZADDEDSERVER` and enables server in `Codex -> Cluster A`.
- Creates a timestamped McpOne DB backup before modification.
- If inference fails, provide `--command` and `--arg` explicitly.
