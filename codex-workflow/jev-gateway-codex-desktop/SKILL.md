---
name: jev-gateway-codex-desktop
description: Install or repair Jev Gateway and configure Codex Desktop to route through it while preserving the existing ChatGPT login. Use when setting up Jev with the Codex desktop app on this or another computer.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Jev Gateway with Codex Desktop

Install Jev Gateway, connect its Jev decision calls to OpenRouter, and optionally route the local Codex CLI and ChatGPT/Codex Desktop through the same local gateway.

## Credentials and billing boundaries

- Never ask for, read, print, copy, or place an API key in a command, chat, transcript, or skill file. Start `jev-codex --setup` in a user-visible interactive terminal and let the user enter the key at the hidden prompt.
- The Jev key is only for Jev decisions through OpenRouter. Codex's existing login authenticates requests to the configured LLM upstream.
- Before configuring Codex Desktop, check `jev-codex --status`. For a ChatGPT login, the upstream must be `https://chatgpt.com/backend-api/codex`. Stop if it points to `https://api.openai.com/v1` or another unexpected endpoint; do not silently route subscription traffic to API billing.
- Local status and gateway logs do not prove account billing. Explain that only the provider/account usage page can confirm charges.
- A running gateway or successful CLI request does not prove Desktop uses it. Require a new tool-using task in Codex Desktop after a full app restart and a new metadata-only gateway log event before claiming Desktop routing works.

## Install and set up Jev

1. Check the host OS, Codex Desktop/CLI presence, Node.js (`>=22.15`), npm, and Python (`>=3.11`, for `tomllib`). On macOS, check whether Homebrew currently has a maintained `jev-gateway` formula or cask; install with Homebrew if one exists. Otherwise, and on other systems, verify `npm view jev-gateway version repository.url engines dist.integrity --json` points to the public `vinilana/jev-gateway` repository and supports the installed Node version, then install with `npm install --global jev-gateway`.
2. Start `jev-codex --setup` in a visible interactive terminal. Select OpenRouter and let the user type the key into the hidden prompt. The wizard validates and stores it in `~/.jev-gateway/.env` with private permissions. Never inspect that file's contents.
3. Run `jev-codex --start` and `jev-codex --status`. Confirm `Jev via OpenRouter`, the expected ChatGPT upstream, and the local bind address `127.0.0.1:8790`. If any check differs, stop before changing Codex Desktop configuration.

The OpenRouter CLI is optional. Its credit-balance and analytics commands may require a Management API key; do not substitute or reveal the Jev API key to check account administration endpoints.

## Configure Codex Desktop

Use the included `scripts/configure_codex_desktop.py` to add the local provider to the user-level Codex configuration. It creates a timestamped backup, preserves the current model and unrelated settings, validates TOML, and refuses to replace an unrelated custom provider or a conflicting Jev provider entry.

```sh
python3 /path/to/jev-gateway-codex-desktop/scripts/configure_codex_desktop.py --apply
```

The script resolves `CODEX_HOME` when set, otherwise `~/.codex`. Review its reported backup path. The resulting Codex Desktop provider uses `http://127.0.0.1:8790/v1`, the Responses API, and Codex's existing OpenAI/ChatGPT authentication. Do not add an OpenAI API key to this setup.

If the user does not want to change the Desktop default provider, stop after installation and setup; `codex --profile jev` can test the CLI profile, but it does not by itself connect Desktop.

## Test Desktop routing

1. Fully quit and reopen Codex Desktop so it reloads `config.toml`.
2. In the Desktop app, start a fresh local Codex task that must invoke a harmless local tool, such as printing a fixed marker in a temporary directory. A plain text response without a tool may not trigger a Jev decision.
3. Check `jev-codex --status` and inspect only event metadata from `~/.jev-gateway/codex.log` (timestamp, status, routing mode, tool name, Jev latency). Do not dump request or response bodies. Confirm a new HTTP 200 event with a Jev decision after the test task began.
4. If no new event appears, report Desktop routing as unverified and troubleshoot the app's loaded config/restart. Do not count previous CLI events as Desktop proof.

Keep claims separate:

- `--status` confirms the gateway is up and shows its configured upstream.
- A `codex exec --profile jev` request verifies the CLI path only.
- Only a fresh tool-using Desktop task followed by a new gateway event verifies Desktop routing.

## Roll back

Use the exact backup path reported by the configurator, then fully restart Codex Desktop:

```sh
python3 /path/to/jev-gateway-codex-desktop/scripts/configure_codex_desktop.py --rollback /path/to/config.toml.pre-jev-<timestamp>.bak
```

This restores only the Codex configuration file. It does not delete the gateway, its OpenRouter key, or logs. Stop the gateway separately with `jev-codex --stop` only if the user asks to stop it.

## Use on another computer

Install this skill under `$CODEX_HOME/skills/jev-gateway-codex-desktop` (or `~/.codex/skills/jev-gateway-codex-desktop` when `CODEX_HOME` is unset), then follow the setup for that computer from the beginning. The configuration helper is portable and resolves `CODEX_HOME` or that system's user home; it does not contain this Mac's absolute paths. Re-check OS, package availability, Node, Python, Codex authentication, and gateway status; never copy the old computer's API key or `~/.codex/auth.json`.

The bundled `skill-installer` installs skills from GitHub repository paths, not arbitrary local folders. If this skill is later published in a GitHub repository, install it on another computer with the helper from the preinstalled `skill-installer`, passing that repository and this skill's relative path. Otherwise copy the skill directory securely into the destination skills folder.
