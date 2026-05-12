# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoderVPS is a Coder-based VPS development environment being refactored from a monolithic shell-driven system into a pluginized Python generator with GitHub-built images and isolated workspace runtimes. The repo currently contains the **legacy** system; the refactor design and implementation plan are in `docs/superpowers/`.

## Branch Model

- **`master`** — source code: Python generator (`codervps/`), config (`config/`), Dockerfile (`docker/`), runtime shell modules (`runtime/`), tests, workflows.
- **`generated`** — publishable output: rendered Terraform JSON, catalogs, extension lists, runtime files. The VPS consumes this branch; it does not run the generator.

## Legacy Architecture (current state)

- `cdev` — monolithic Bash management script (~1160 lines). Handles Docker Compose, template patching, local image builds, extension management, NGINX, and diagnostics. **Being refactored into a thin VPS helper.**
- `templates/devbox/` — Coder template: `Dockerfile`, `main.tf`, `startup.sh`. The Dockerfile builds a multi-language devbox image with build-arg-gated toolchains (Rust, C/C++, Go, Python). `main.tf` uses Coder parameters for image profile, language versions, memory. `startup.sh` configures code-server, language runtimes, and extension installation.
- `extensions/extensions/` — VS Code extension lists by profile: `core.txt`, `rust.txt`, `cpp.txt`, `go.txt`, `python.txt`.
- `docker-compose.yml` — Coder + PostgreSQL deployment. Domain: `code.549304.xyz`.
- `pyproject.toml` — uv project, Python 3.13, placeholder `main.py`. Will become the generator package.

## Refactor Target Architecture

See `docs/superpowers/specs/2026-05-12-codervps-refactor-design.md` (design) and `docs/superpowers/plans/2026-05-12-codervps-refactor.md` (13-task implementation plan).

Key changes:
- **Python generator** (`codervps/` package) with CLI: `codervps refresh-catalog`, `render-generated`, `build-matrix`, `validate`.
- **Plugin system** — `ToolchainPlugin` protocol with `discover()`, `coder_parameters()`, `runtime_plan()` for Python, Rust, Go, C/C++.
- **TOML config** — `config/toolchains.toml` and `config/extensions.toml` replace hardcoded versions.
- **Generated `main.tf.json`** — Terraform JSON syntax, fully generated from structured data. No more hand-edited `main.tf`.
- **Runtime action model** — structured actions (download, extract_tar, run, verify_command, etc.) with idempotency, workspace isolation, and atomic downloads. All toolchain data lives under `/workspace/.cdev/`.
- **GitHub Actions** — monthly/manual workflow builds images to GHCR, publishes `generated` branch. No local image builds on VPS.
- **Thin `cdev`** — only VPS operations: info, doctor, ps, logs, restart, push-template, sync-generated, check-generated, check-images, list-workspace-volumes.

## Commands

```bash
# Python (after refactor)
uv sync                          # install dependencies
uv run pytest -q                 # run all tests
uv run pytest tests/test_foo.py  # run single test file
uv run ruff check codervps tests # lint
uv run ruff format --check codervps tests  # format check
uv run codervps --version        # CLI version
uv run codervps refresh-catalog --output build/toolchains.json
uv run codervps render-generated --catalog build/toolchains.json --output build/generated
uv run codervps build-matrix --catalog build/toolchains.json --format github-output

# Legacy (current)
sudo cdev doctor                 # full health check
sudo cdev up                    # start Coder stack
sudo cdev ps                    # show services
sudo cdev logs [service]        # tail logs
sudo cdev patch-runtime         # patch main.tf + startup.sh + plugin dirs
sudo cdev rebuild-devbox        # build devbox image locally
CODER_SESSION_TOKEN='...' sudo cdev push-template  # push template to Coder

# Static checks for runtime shell
shellcheck runtime/startup.sh runtime/lib/actions.sh runtime/plugins/*.sh
```

## Bash Execution Rule (MANDATORY)

**NEVER chain multiple commands with `&&` or `;` in a single Bash tool call.** Each Bash call must execute exactly ONE command. After each command, you MUST read the output/feedback before proceeding to the next command. No exceptions.

- WRONG: `uv sync && uv run pytest -q && uv run ruff check codervps tests`
- RIGHT: Run `uv sync`, read output, then run `uv run pytest -q`, read output, then run `uv run ruff check codervps tests`

This rule applies to ALL Bash tool calls — both in the main conversation and in subagent prompts. Subagent prompts must include this constraint explicitly.

---

## Git Workflow — Complete Protocol (MANDATORY)

This section defines the EXACT git operations for the entire development process. No step may be skipped, abbreviated, or modified.

### Git Safety Rules

1. **NEVER update git config** (no `git config` commands).
2. **NEVER run destructive commands** (`push --force`, `reset --hard`, `checkout .`, `restore .`, `clean -f`, `branch -D`) without explicit user request — EXCEPT when deleting task branches during cleanup (see Cleanup section).
3. **NEVER skip hooks** (`--no-verify`, `--no-gpg-sign`) unless user explicitly requests it.
4. **NEVER force push to master/main** — warn user if they request it.
5. **ALWAYS create NEW commits** rather than amending.
6. **ALWAYS stage specific files** (`git add <specific-files>`) — never `git add -A` or `git add .` which can include secrets or binaries.
7. **ALWAYS use `/bin/rm`** for file deletion, not plain `rm`.

### Git State Tracking

After EVERY git operation, the coordinating agent (main conversation) MUST:
1. Run `git status --short` to verify working tree state
2. Run `git branch --show-current` to confirm current branch
3. Run `git log --oneline -3` to verify commit history

### Branch Creation (Before Each Round)

Before starting a round, create 5 branches from master:

```bash
# Step 1: Ensure we are on master
git checkout master

# Step 2: Verify master is clean (no uncommitted changes)
git status --short

# Step 3: Create 5 branches from master (one command each)
git branch task{N}-r{R}-agent1 master
git branch task{N}-r{R}-agent2 master
git branch task{N}-r{R}-agent3 master
git branch task{N}-r{R}-agent4 master
git branch task{N}-r{R}-agent5 master

# Step 4: Verify all branches created and point to same master commit
git log --oneline -1 task{N}-r{R}-agent1 task{N}-r{R}-agent2 task{N}-r{R}-agent3 task{N}-r{R}-agent4 task{N}-r{R}-agent5
```

### Dev Agent Lifecycle (Per Agent)

**Before launching the agent**, the coordinating agent MUST:
1. Verify master is checked out: `git checkout master`
2. Verify the agent's branch exists: `git branch --contains task{N}-r{R}-agent{A}`

**The agent's internal workflow** (included verbatim in every dev agent prompt):

```
CRITICAL FIRST STEP: Run `git checkout task{N}-r{R}-agent{A}` before doing anything else.

Bash Execution Rule: ONE command per Bash call, never chain with && or ;.

Workflow:
1. `git checkout task{N}-r{R}-agent{A}` — switch to your branch
2. `git log --oneline -3` — verify your starting point
3. Read existing files on the branch
4. Implement the task (write/edit code using Write/Edit tools)
5. `uv sync` — single command, read output
6. `uv run pytest tests/test_foo.py -q` — single command, all must pass
7. `uv run ruff check codervps tests` — single command, must be clean
8. `uv run ruff format --check codervps tests` — single command, must pass
9. `git add <specific-file-1> <specific-file-2> ...` — stage ONLY changed files by name
10. `git commit -m "feat: <task description>"` — commit
11. `git log --oneline -3` — verify your commit is the latest on this branch
12. Report: branch name, commit hash, files changed, test count passed
```

**After the agent completes**, the coordinating agent MUST:
1. `git checkout master` — switch back to master
2. `git log task{N}-r{R}-agent{A} --oneline -3` — verify the agent's commit exists on the branch
3. `git diff master..task{N}-r{R}-agent{A} --stat` — check what files the agent changed
4. Confirm the agent created exactly one new commit beyond master
5. Save a brief summary to memory (see Memory Recall section)

### Review Agent Lifecycle (Per Agent)

**Before launching the reviewer**, the coordinating agent MUST:
1. Verify master is checked out: `git checkout master`

**The reviewer's internal workflow** (included verbatim in every review agent prompt):

```
CRITICAL FIRST STEP: Run `git checkout task{N}-r{R}-agent{A}` before doing anything else.

Bash Execution Rule: ONE command per Bash call, never chain with && or ;.

Workflow:
1. `git checkout task{N}-r{R}-agent{A}` — switch to the branch being reviewed
2. `git log --oneline -3` — verify branch state
3. Read ALL source files on the branch (using Read tool)
4. `uv run pytest tests/ -q` — run all tests
5. `uv run ruff check codervps tests` — lint check
6. `uv run ruff format --check codervps tests` — format check
7. Inspect code quality, spec compliance, test coverage, edge cases
8. Output a STRUCTURED REVIEW containing:
   - Spec compliance (list each requirement, pass/fail)
   - Code quality assessment (strengths, issues)
   - Critical issues (must fix)
   - Important issues (should fix)
   - Suggestions (nice to have)
   - Test quality assessment
   - Comparison to previous round (if applicable)
9. Do NOT make commits — review is read-only
10. `git checkout master` — switch back to master when done
```

**After the reviewer completes**, the coordinating agent MUST:
1. `git checkout master`
2. Save the review findings to memory for synthesis (see Memory Recall section)

### Between Rounds (Feedback Synthesis)

After ALL 5 dev agents AND ALL 5 review agents complete a round:

1. Synthesize all 5 reviews into one document
2. Identify the BEST patterns across all 5 branches
3. Identify the PROBLEMS to avoid across all 5 branches
4. Save this synthesis to memory
5. The NEXT round's dev agents receive the synthesis in their prompts

### Round 5 Final Merge

After Round 5's review phase completes:

1. Run 5 analysis agents — one per branch: `git checkout task{N}-r5-agent{A} && read files && output structured evaluation`
2. Select the single BEST branch based on: test count, code quality, spec compliance, review consensus
3. Announce which branch was selected and why
4. Merge to master:
   ```bash
   git checkout master
   git merge task{N}-r5-agent{X} --no-edit
   ```
5. If merge conflicts:
   ```bash
   # Accept agent's version for conflicting files
   git checkout --theirs <conflicting-file>
   git add <conflicting-file>
   git commit -m "merge: <task description> (Task N - Round 5 converged)"
   ```
6. Verify on master:
   ```bash
   uv run pytest tests/ -q
   uv run ruff check codervps tests
   ```
7. Delete ALL task branches:
   ```bash
   git branch | grep task{N} | xargs git branch -D
   ```
8. Update memory: mark task as COMPLETED

### Cleanup

After a task is fully complete (Round 5 merged):

```bash
# Make sure we are on master
git checkout master

# Delete all branches for this task
git branch | grep "task{N}-" | while read branch; do git branch -D "$branch"; done
```

---

## Multi-Agent Execution Protocol (MANDATORY)

### Task Structure

There are 7 merged tasks (Task A through G). Each task combines 2 original plan tasks. Each task requires exactly **5 rounds**. Each round requires exactly **5 dev agents + 5 review agents**. All agents are **serial** (one at a time, foreground only).

### Merged Task Map

| Task | Original Tasks | Content |
|------|---------------|---------|
| Task A | T1+T2 | CLI Skeleton + Models/Config |
| Task B | T3+T4 | Plugin API + Catalog Refresh |
| Task C | T5+T6 | Terraform JSON + Runtime Shell |
| Task D | T7+T8 | Extensions + Dockerfile Matrix |
| Task E | T9+T10 | Generated Tree + GitHub Actions |
| Task F | T11+T12 | Thin cdev + Docs |
| Task G | T13 | Full Validation |

### Branch Naming Convention

```
task{A}-r{R}-agent{N}     # Dev agents: N=1..5
task{A}-r{R}-review{N}    # Review agents: N=1..5
```

Examples: `taskA-r1-agent1`, `taskA-r3-review4`

### Complete Round Execution Checklist

For each task (A through G), for each round (1 through 5):

#### Phase 0: Setup
- [ ] `git checkout master`
- [ ] `git status --short` (must be clean)
- [ ] Create 5 branches: `git branch task{A}-r{R}-agent{1..5} master`
- [ ] Verify branches: `git log --oneline -1 task{A}-r{R}-agent{1..5}`

#### Phase A: Dev Agents (1→2→3→4→5, serial, foreground)
- [ ] Launch Agent 1: prompt includes `git checkout task{A}-r{R}-agent1`, task spec, round feedback
- [ ] Wait for completion. Verify: `git log task{A}-r{R}-agent1 --oneline -2`
- [ ] `git checkout master`
- [ ] Save agent result to memory
- [ ] Launch Agent 2: prompt includes `git checkout task{A}-r{R}-agent2`, task spec, round feedback
- [ ] Wait for completion. Verify: `git log task{A}-r{R}-agent2 --oneline -2`
- [ ] `git checkout master`
- [ ] Save agent result to memory
- [ ] Launch Agent 3: ... (repeat through Agent 5)
- [ ] `git checkout master`

#### Phase B: Review Agents (1→2→3→4→5, serial, foreground)
- [ ] Launch Review Agent 1: prompt includes `git checkout task{A}-r{R}-agent1`, review criteria
- [ ] Wait for completion. Save review to memory.
- [ ] `git checkout master`
- [ ] Launch Review Agent 2: prompt includes `git checkout task{A}-r{R}-agent2`, review criteria
- [ ] Wait for completion. Save review to memory.
- [ ] ... (repeat through Review Agent 5)
- [ ] `git checkout master`

#### Phase C: Synthesis
- [ ] Compile all 5 reviews into a single synthesis document
- [ ] Identify best patterns and problems to avoid
- [ ] Save to memory (this feeds into next round's dev agent prompts)
- [ ] If this is Round 5: proceed to Final Merge
- [ ] Otherwise: increment R, go to Phase 0

#### Final Merge (Round 5 only)
- [ ] Run 5 analysis agents (one per branch)
- [ ] Select BEST branch
- [ ] `git checkout master && git merge task{A}-r5-agent{X} --no-edit`
- [ ] Verify: `uv run pytest tests/ -q`
- [ ] Delete all task{A} branches
- [ ] Mark task COMPLETED in memory and task list

---

## Memory Recall Protocol (MANDATORY)

### When to Save Memory

After EVERY agent (dev or review) completes, the coordinating agent MUST save a brief memory entry recording:
1. Which agent ran (task, round, agent number)
2. Branch name
3. Commit hash
4. Key result (tests passed, lint status, review verdict)
5. Notable findings or issues

### Memory File Structure

Memory files live at `/home/hp/.claude/projects/-home-hp-Projects-OpenSource-CoderVPS/memory/`.

**After each dev agent:** save to `memory/task{A}-r{R}-agent{N}.md`:
```
---
name: task{A}-r{R}-agent{N}-result
description: Dev agent {N} round {R} task {A} result
type: project
---
Branch: task{A}-r{R}-agent{N}
Commit: <hash>
Tests: N passed
Approach: <brief description of unique approach>
Issues: <any problems noted>
```

**After each review agent:** save to `memory/task{A}-r{R}-review{N}.md`:
```
---
name: task{A}-r{R}-review{N}-result
description: Review agent {N} round {R} task {A} result
type: project
---
Branch reviewed: task{A}-r{R}-agent{N}
Verdict: PASS/FAIL
Critical issues: <list>
Important issues: <list>
Best patterns: <list>
```

**After each round synthesis:** save to `memory/task{A}-r{R}-synthesis.md`:
```
---
name: task{A}-r{R}-synthesis
description: Round {R} task {A} synthesis of all 5 reviews
type: project
---
Best patterns to adopt:
- pattern 1
- pattern 2

Problems to avoid:
- problem 1
- problem 2

Agent rankings for this round:
1. agent N (reason)
2. ...
```

### When to Recall Memory

Before launching each new round's dev agents, the coordinating agent MUST:
1. Read the previous round's synthesis file
2. Read ALL 5 review files from the previous round
3. Incorporate findings into the dev agent prompts

### When NOT to Save to Memory

- Do NOT save code patterns, conventions, or file paths (derivable from code)
- Do NOT save git history or diffs (use git log/diff)
- Do NOT save anything already in CLAUDE.md
- Do NOT save ephemeral task details (current conversation context)

---

## Dev Agent Prompt Template

Every dev agent prompt MUST follow this template:

```
You are Dev Agent {N} of 5 for Task {A} Round {R}.

## CRITICAL FIRST STEP
Run `git checkout task{A}-r{R}-agent{N}` before doing anything else.

## Bash Execution Rule (MANDATORY)
NEVER chain multiple commands with `&&` or `;`. Each Bash call = exactly ONE command.

## Context
[Round {R} feedback synthesis goes here]

## Required Spec
[Task specification from the plan goes here]

## Verification (each a SINGLE Bash command, in order):
1. `git checkout task{A}-r{R}-agent{N}`
2. `git log --oneline -3`
3. [Read existing files]
4. [Write implementation]
5. `uv sync`
6. `uv run pytest tests/test_foo.py -q`
7. `uv run ruff check codervps tests`
8. `uv run ruff format --check codervps tests`
9. `git add <files>`
10. `git commit -m "feat: <description>"`
11. `git log --oneline -3`

## After Completion
Report: branch name, commit hash, files changed, test count, unique approach.

All paths relative to /home/hp/Projects/OpenSource/CoderVPS.
```

## Review Agent Prompt Template

Every review agent prompt MUST follow this template:

```
You are Review Agent {N} of 5 for Task {A} Round {R}.

## CRITICAL FIRST STEP
Run `git checkout task{A}-r{R}-agent{N}` before doing anything else.

## Bash Execution Rule (MANDATORY)
NEVER chain multiple commands with `&&` or `;`. Each Bash call = exactly ONE command.

## Review Task
Review branch `task{A}-r{R}-agent{N}`.

## Instructions:
1. `git checkout task{A}-r{R}-agent{N}`
2. `git log --oneline -3`
3. Read ALL source files on the branch
4. `uv run pytest tests/ -q`
5. `uv run ruff check codervps tests`
6. `uv run ruff format --check codervps tests`
7. Output STRUCTURED REVIEW:
   - Spec compliance (each requirement, pass/fail)
   - Code quality (strengths, issues with severity)
   - Test quality (coverage, gaps, organization)
   - Bugs found
   - Best patterns to adopt
   - Problems to avoid
8. Do NOT make commits — read-only review
9. `git checkout master`

All paths relative to /home/hp/Projects/OpenSource/CoderVPS.
```

---

## Serial Execution Rule (MANDATORY)

- **NEVER launch multiple Agent tool calls in the same message.**
- **NEVER use `run_in_background: true` with Agent tool calls.**
- Each agent runs in **foreground**. Wait for completion before launching the next.
- Between agents: `git checkout master`, verify state, save memory, then launch next.

---

## No Worktree Parallelism

Never use `isolation: "worktree"` with `run_in_background: true`. Agents write files using absolute paths and will corrupt each other's work if run in parallel.

---

## Critical Constraints

- **Workspace isolation**: All runtime toolchain data, caches, and downloads must live under `/workspace/.cdev/`. Never write to `/opt/cde/cache` or shared paths. Each workspace gets its own Docker volume.
- **No shared caches across workspaces**: Do not share persistent volumes, toolchain installs, or compiler caches between workspaces.
- **Immutable workspace parameters**: Language and version selections are immutable after workspace creation. Startup must verify selection hash before installing tools.
- **No host Docker socket in v1**: Do not mount `/var/run/docker.sock` into workspaces.
- **No `docker volume prune` / `docker system prune --volumes`**: These destroy Coder-managed workspace volumes that appear unused when workspaces are stopped.
- **Download integrity**: All downloads must verify checksums (Node SHASUMS256, Go metadata, sccache release checksums). Use `*.part` files with atomic rename after verification.
- **Generated branch atomicity**: `images.json` is written only after all image builds succeed. The `generated` branch is updated with `--force-with-lease`, never plain `--force`. Date tags are immutable — the workflow must fail if a tag already exists in GHCR.
- **Deletion safety on VPS**: Use `/bin/rm` for file deletion (safe-rm entry point). Never use plain `rm`, `find -delete`, `git clean`, or `docker volume prune` as normal operations.
- **Terraform `ignore_changes = all`** on persistent volumes, but no `prevent_destroy` — normal Coder workspace deletion must be able to remove volumes.

## Refactor Workflow

When implementing the refactor, follow the design doc and implementation plan in `docs/superpowers/`. Read the relevant documentation before changing code — do not implement from memory when a plan or design document exists. Keep commits small and intentional; commit documentation, plans, and code changes separately.
