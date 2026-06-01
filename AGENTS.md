# Repository Instructions

## Coding Preferences

- Always write simpler code. Do not consider too many edge cases unless the user asks for them.
- Follow the "let it crash" principle: do not catch non-business exceptions, and do not add non-business null checks.
- Do not add dependency-install boilerplate.
- Do not wrap imports in `try`/`except ImportError` only to print setup or `pip install` instructions.
- Do not print messages about missing packages or how to install them unless the user explicitly asks for that behavior.
- Assume the developer will manage local environment and dependencies.
- Prefer failing normally over adding defensive setup guidance around imports.
- Treat user-authored changes as intentional. If code differs from a previous AI edit, do not change it back unless the user explicitly asks for that reversal.

## Review guidelines

- Don't log PII.

## Scope

- These rules apply across the whole repository unless a more specific nested `AGENTS.md` overrides them.
<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->
