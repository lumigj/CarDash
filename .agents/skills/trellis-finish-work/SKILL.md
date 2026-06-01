---
name: trellis-finish-work
description: "Wrap up the current session: verify quality gate passed, remind user to commit, archive completed tasks, and record session progress to the developer journal. Use when done coding and ready to end the session."
---

# Finish Work

Wrap up the current session: archive the active task (and any other completed-but-unarchived tasks the user wants to clean up) and record the session journal. Code commits are NOT done here — those happen in workflow Phase 3.4 before you invoke this command.

This project requires fresh user approval before every commit. Do not rely on script auto-commits during finish-work. Use `--no-commit` for archive and journal commands, then present a bookkeeping commit plan and wait for the user to approve it before running `git commit`.

## Step 1: Survey current state

```bash
python3 ./.trellis/scripts/get_context.py --mode record
```

This prints:

- **My active tasks** — review whether any besides the current one are actually done (code merged, AC met) and should be archived this round.
- **Git status** — quick visual on what's dirty.
- **Recent commits** — you'll need their hashes in Step 4 for `--commit`.

If `--mode record` surfaces other completed tasks not tied to the current session, surface them to the user with a one-shot confirmation: "These N tasks look done — archive them too in this round? [y/N]". Default is no; the current active task is always archived in Step 3 regardless.

## Step 2: Sanity check — classify dirty paths

Run:

```bash
git status --porcelain
```

Filter out paths under `.trellis/workspace/` and `.trellis/tasks/` — those are managed by `add_session.py` and `task.py archive` auto-commits and will appear dirty as part of this skill's own work.

For each remaining dirty path, decide whether it belongs to **the current task** or to **other parallel work** (e.g., another terminal window editing the same repo). Heuristics:

- Paths referenced in the current task's `prd.md` / `implement.jsonl` / `check.jsonl` → current task
- Paths in code areas matching the task's stated scope, or that you remember editing this session → current task
- Paths in unrelated areas you have no recollection of touching this session → other parallel work

Then route:

- **Any remaining path looks like current-task work** — bail out with:
  > "Working tree has uncommitted code changes from this task: `<list>`. Return to workflow Phase 3.4 to commit them before running ``finish-work` (Trellis command)`."

  Do NOT run `git commit` here. Do NOT prompt the user to commit. The user goes back to Phase 3.4 and the AI drives the batched commit there.
- **All remaining paths look unrelated** (other parallel-window work) — report them once and continue to Step 3:
  > "FYI, dirty files outside this task's scope — leaving them for the other window: `<list>`."
- **Genuinely unsure** — ask the user once: "Are `<list>` this task's work I forgot to commit, or another window's? (commit / ignore)" — then route per their answer.

## Step 3: Archive task(s) Without Committing

```bash
python3 ./.trellis/scripts/task.py archive <task-name> --no-commit
```

At minimum: the current active task (if any). Plus any extra tasks the user confirmed in Step 1. Always pass `--no-commit` so the script moves task files but does not create a git commit.

If there is no active task and the user did not confirm any cleanup archives, skip this step.

## Step 4: Record session journal Without Committing

```bash
python3 ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary" \
  --no-commit
```

Use the work-commit hashes produced in Phase 3.4 (visible in Step 1's `Recent commits` list, or via `git log --oneline`) for `--commit`. Do not include archive or journal bookkeeping commit hashes. Always pass `--no-commit` so the script writes journal files but does not create a git commit.

## Step 5: Ask Before Bookkeeping Commits

Inspect dirty state:

```bash
git status --porcelain
git log --oneline -5
```

Draft a bookkeeping commit plan for the Trellis files created by Steps 3 and 4. Keep archive and journal commits separate:

```text
Proposed Trellis finish-work commits (in order):
  1. chore(task): archive <task-name>
     - .trellis/tasks/archive/<year-month>/<task-name>/
     - .trellis/tasks/<task-name>/ (deleted)
  2. chore: record journal
     - .trellis/workspace/<developer>/journal-N.md
     - .trellis/workspace/index.md

Reply 'ok' / '行' to execute. Reply with edits, or 'manual' / '我自己来' to leave these files uncommitted.
```

Only after the user explicitly approves this exact plan, run `git add` / `git rm --cached` / `git commit` as needed for each commit in order. Do not amend. Do not push.

If the user rejects or chooses manual mode, stop and leave the dirty Trellis files for the user to commit or discard. Do not attempt a second plan unless the user explicitly asks.

Final git log order after approval: `<work commits from 3.4>` → `chore(task): archive ...` (one or more) → `chore: record journal`.
