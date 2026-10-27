---
name: speckit-kanban-sync
description: Sync a newly generated `tasks.md` (from /speckit.tasks) into `TODO.kanban` Backlog with correct labels and Portable Kanban-safe schema. Use after each new specs session to create backlog cards from tasks.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Speckit Kanban Sync

## Overview

Creates or updates Backlog cards in `TODO.kanban` based on `tasks.md`, applying
project labeling rules and keeping the Portable Kanban schema valid.

## Inputs

- `tasks.md` path (typically `specs/00x-*/tasks.md`)
- `TODO.kanban` path (repo root)

## Workflow

1. Parse `tasks.md` for task lines `- [ ] T### ...` or `- [x] T### ...`.
2. For each task, create a Backlog card in `TODO.kanban` unless it already exists.
3. Card title: **use the full task line text** (the line after `T###`), not a shortened summary.
4. Card description: optional; only add when extra context is required.
5. Add labels:
   - Always add the spec task label in `spec00x-T###` format.
   - Add component labels based on keywords (Samba, Home Assistant, Pi-hole,
     Cloudflared, Cockpit, Docs, Workspace, Prod, Dev, Ansible).
   - Add group labels when provided (e.g., `group-1-...`).
6. If a label doesn’t exist, create it with an unused color.

## Portable Kanban Schema Rules (Do Not Break)

- All `id` fields must be UUIDs.
- Comments must be `{ id, comment }` (no `content` field).
- Preserve list IDs and keep `listId` matching the list.
- Do not alter list definitions beyond adding cards/labels.

## Rules Recap

- Older specs should already have the correct `spec00x-T###` labels. Only add if missing.
- When a task is started, move its card to **Doing**; when finished, move it to **Done**.
