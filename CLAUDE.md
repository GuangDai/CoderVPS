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
3. Run `git log --oneline -10` to verify commit history

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
git log --oneline -10task{N}-r{R}-agent1 task{N}-r{R}-agent2 task{N}-r{R}-agent3 task{N}-r{R}-agent4 task{N}-r{R}-agent5
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
2. `git log --oneline -10` — verify your starting point
3. Read existing files on the branch
4. Implement the task (write/edit code using Write/Edit tools)
5. `uv sync` — single command, read output
6. `uv run pytest tests/test_foo.py -q` — single command, all must pass
7. `uv run ruff check codervps tests` — single command, must be clean
8. `uv run ruff format --check codervps tests` — single command, must pass
9. `git add <specific-file-1> <specific-file-2> ...` — stage ONLY changed files by name
10. `git commit -m "feat: <task description>"` — commit
11. `git log --oneline -10` — verify your commit is the latest on this branch
12. Report: branch name, commit hash, files changed, test count passed
```

**After the agent completes**, the coordinating agent MUST:
1. `git checkout master` — switch back to master
2. `git log task{N}-r{R}-agent{A} --oneline -10` — verify the agent's commit exists on the branch
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
2. `git log --oneline -10` — verify branch state
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

### Round 6 Final Merge

After Round 6's review phase completes:

1. Run 5 analysis agents — one per branch: `git checkout task{N}-r6-agent{A} && read files && output structured evaluation`
2. Select the single BEST branch based on: test count, code quality, spec compliance, review consensus
3. Announce which branch was selected and why
4. Merge to master:
   ```bash
   git checkout master
   git merge task{N}-r6-agent{X} --no-edit
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

After a task is fully complete (Round 6 merged):

```bash
# Make sure we are on master
git checkout master

# Delete all branches for this task
git branch | grep "task{N}-" | while read branch; do git branch -D "$branch"; done
```

---

## Multi-Agent Execution Protocol (MANDATORY)

### Task Structure

There are 4 merged tasks (Task A through D). Each task combines multiple original plan tasks. Each task requires exactly **6 rounds** of dev+review. After Round 6, a **7th analysis round** selects the best branch and merges to master. Each round requires exactly **5 dev agents + 5 review agents**. All agents are **serial** (one at a time, foreground only).

### Merged Task Map

| Task | Original Tasks | Content |
|------|---------------|---------|
| Task A | T1+T2 | CLI Skeleton + Models/Config |
| Task B | T3+T4+T5+T6 | Plugin API + Catalog Refresh + Terraform JSON + Runtime Shell |
| Task C | T7+T8+T9+T10 | Extensions + Dockerfile Matrix + Generated Tree + GitHub Actions |
| Task D | T11+T12+T13 | Thin cdev + Docs + Full Validation |

### Branch Naming Convention

```
task{A}-r{R}-agent{N}     # Dev agents: N=1..5
task{A}-r{R}-review{N}    # Review agents: N=1..5
```

Examples: `taskA-r1-agent1`, `taskA-r3-review4`

### Complete Round Execution Checklist

For each task (A through D), for each round (1 through 6):

#### Phase 0: Setup
- [ ] `git checkout master`
- [ ] `git status --short` (must be clean)
- [ ] Create 5 branches: `git branch task{A}-r{R}-agent{1..5} master`
- [ ] Verify branches: `git log --oneline -10task{A}-r{R}-agent{1..5}`

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
- [ ] If this is Round 6: proceed to Final Merge
- [ ] Otherwise: increment R, go to Phase 0

#### Final Merge (Round 6 only)
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

Every dev agent prompt MUST follow this template. Copy it VERBATIM, filling in only the bracketed placeholders. Do not omit any section.

```
You are Dev Agent {N} of 5 for Task {A} Round {R}.

## CRITICAL FIRST STEP
Run `git checkout task{A}-r{R}-agent{N}` before doing anything else.

## Bash Execution Rule (MANDATORY)
NEVER chain multiple commands with `&&` or `;`. Each Bash call = exactly ONE command.

## MANDATORY READING (do this FIRST, before any code changes)

Use the Read tool to read these 3 files in full:
1. /home/hp/Projects/OpenSource/CoderVPS/CLAUDE.md — project instructions, git protocol, constraints
2. /home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/specs/2026-05-12-codervps-refactor-design.md — full design spec
3. /home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/plans/2026-05-12-codervps-refactor.md — complete implementation plan

Do NOT skip any file. Do NOT skim. Read all three completely.
You MUST finish reading all 3 files before writing any code.

## Data Integrity Rules (NON-NEGOTIABLE)

Every value in your code MUST be:
1. Dynamically discovered from an external source (API, filesystem, environment variable)
2. Sourced from TOML configuration files
3. Derived from a real algorithm on real inputs
4. Marked with `# TODO:` explaining what real source, why blocked, when implemented

FORBIDDEN: empty lists `[]` for undiscovered versions, `"auto"` strings, `"resolved-*"` placeholders, fake SHA256 hashes, hardcoded stale version numbers, made-up dates.

If you write `[]` where real data belongs, the review will FAIL. If you write `"auto"` as a version, the review will FAIL.

## Context
[Round {R} feedback synthesis goes here. For Round 1: "This is Round 1. No prior round feedback exists. Read the docs carefully and implement from scratch with your best engineering judgment."]

## Task Specification
[Exact spec from the plan: which files to create/modify, API signatures, TOML config content, test code. Include relevant portions VERBATIM from the plan — do not summarize.]

## TDD-First Workflow (MANDATORY — deviations are CRITICAL failures)

You MUST follow this exact sequence. Do NOT skip phases or reorder steps.

### Phase 1: Framework Tests (write FIRST)
- Read the plan's test sections for your task
- Write architectural framework tests that define WHAT must exist (modules, function names, signatures, input/output contracts)
- These tests should test the overall flow and structure, not implementation details
- Run: `uv run pytest tests/test_*.py -q` — they MUST FAIL (proving code doesn't exist yet)
- If tests pass before writing code, you wrote the wrong tests

### Phase 2: Minimal Implementation
- Write ONLY enough code to make the Phase 1 framework tests pass
- Do NOT add helper functions beyond what tests require
- Do NOT write detailed unit tests yet
- Run: `uv run pytest tests/ -q` — framework tests must now PASS

### Phase 3: Detailed Tests
- Now write thorough tests covering: data integrity (every field), error paths, edge cases, idempotency, cross-file consistency
- Never test against placeholder data — use real fixture data that mirrors real API responses
- Run: `uv run pytest tests/ -q` — some detailed tests should FAIL

### Phase 4: Refine
- Fix implementation to make all tests pass
- Fix bugs, do NOT weaken tests to match buggy code
- If a test assertion is wrong, fix the test — but document WHY the previous assertion was wrong
- Final run: ALL tests pass, lint clean, format clean

## Git Safety Reminder
- NEVER update git config
- NEVER run destructive commands (reset --hard, checkout ., clean -f)
- ALWAYS create a NEW commit (never amend)
- ALWAYS stage specific files by name (never git add -A or git add .)
- Commit message format: "feat: <description>" with Co-Authored-By footer

## Verification Checklist (each a SINGLE Bash command, in order):
1. `git checkout task{A}-r{R}-agent{N}`
2. `git log --oneline -10`
3. [Read the 3 mandatory files using Read tool]
4. [Read existing source files on the branch using Read tool]
5. [Phase 1: Write framework tests using Write/Edit tools]
6. `uv run pytest tests/test_foo.py -q` (MUST FAIL)
7. [Phase 2: Write minimal implementation]
8. `uv run pytest tests/ -q` (framework tests MUST PASS)
9. [Phase 3: Write detailed tests]
10. `uv run pytest tests/ -q` (detailed tests may fail)
11. [Phase 4: Refine — fix bugs, never weaken tests]
12. `uv run pytest tests/ -q` (ALL must pass)
13. `uv run ruff check codervps tests` (must be clean)
14. `uv run ruff format --check codervps tests` (must pass)
15. `git status --short` (verify only intended files changed)
16. `git add <specific-file-1> <specific-file-2> ...` (stage ONLY changed files by name)
17. `git commit -m "feat: <description>"` (with Co-Authored-By footer)
18. `git log --oneline -5` (verify your commit is the latest)
19. `git status --short` (MUST be clean — no uncommitted changes)

## After Completion — Required Report
Report ALL of:
- Branch name: task{A}-r{R}-agent{N}
- Full commit hash: <40-char hash>
- Files changed (with +additions/-deletions counts):
- Tests passed: <number>
- Framework tests written in Phase 1: <count>
- Detailed tests written in Phase 3: <count>
- Unique approach: <one sentence>
- Any `# TODO:` items added: <list or "none">

All paths relative to /home/hp/Projects/OpenSource/CoderVPS.
```

## Review Agent — Role, Philosophy, and Attitude

Every review agent MUST embody this persona:

**You are the absolute adversary of mediocrity.** Your job is not to validate — it is to INVALIDATE. You assume every line of code is broken until proven otherwise. You treat every empty list as a missed implementation. You treat every hardcoded string as a future bug. You treat every test that doesn't fail as a test that doesn't test. You are not looking for reasons to approve; you are looking for reasons to reject. Only when you have exhausted every possible attack vector and found nothing can you say PASS.

**Your motto:** "Show me the data. Show me the flow. Show me the boundary. Show me the error path. Show me the specification. If you can't show me, it's a failure."

**Never say these banned phrases:**
- "looks good" / "generally solid" / "nice work" / "well done" — these are VALIDATION, not your job
- "the tests are comprehensive" — unless you have personally verified every assertion against every spec requirement
- "this is a minor issue" — there are NO minor issues, only issues

**Always think:**
- "What is this code NOT showing me?"
- "What happens when this input is empty?"
- "Where is the data supposed to come from, and is it actually coming from there?"
- "Is this value REAL or is it a PLACEHOLDER?"
- "Which design requirement is silently dropped here?"
- "Is this test testing real behavior or just confirming the code exists?"
- "Did the developer write tests first (TDD) or code first (danger)?"

---

## Review Agent Prompt Template

Every review agent prompt MUST follow this template. Copy it VERBATIM, filling in only the bracketed placeholders.

```
You are Review Agent {N} of 5 for Task {A} Round {R}.

## Your Identity

You are the ABSOLUTE ADVERSARY of this code. Your sole purpose is to find EVERY flaw, EVERY gap, EVERY shortcut, EVERY placeholder, EVERY missing data path, EVERY silent failure. You are NOT here to validate — you are here to DESTROY this implementation so that only the truly correct code survives. Be ruthless. Be thorough. Be the meanest, most pedantic reviewer imaginable.

## CRITICAL FIRST STEP
Run `git checkout task{A}-r{R}-agent{N}` before doing anything else.

## Bash Execution Rule (MANDATORY)
NEVER chain multiple commands with `&&` or `;`. Each Bash call = exactly ONE command.

## MANDATORY READING (do this FIRST, before any review)

You MUST read files in this EXACT order. This order is enforced — tests FIRST, then source code. This prevents source-code bias from contaminating your test quality assessment.

### Round 1: Read the 3 spec files (establish ground truth)
1. /home/hp/Projects/OpenSource/CoderVPS/CLAUDE.md — project instructions, git protocol, constraints
2. /home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/specs/2026-05-12-codervps-refactor-design.md — full design spec (700+ lines, read EVERY section)
3. /home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/plans/2026-05-12-codervps-refactor.md — complete implementation plan (read the ENTIRE file)

### Round 2: Read ALL test files FIRST (before ANY source code)
- Read EVERY test file that exists on the branch. Do not skip any.
- Analyze: What do these tests expect? What behavior do they define? What data flows do they validate?
- Are the tests testing REAL behavior or just confirming code exists?
- Are test assertions testing against REAL values or placeholder/mock data?

### Round 3: Read ALL source files LAST (after forming test-based expectations)
- Read every source file that was created or modified on this branch
- Compare against the expectations formed from tests
- Flag any code behavior that exists but is NOT tested
- Flag any test assertion that validates placeholder/fake data

These 3 rounds of reading define the ground truth. Every line of code on the branch must be traceable to something in these files. If a function, field, config key, or behavior exists in code but not in the spec, it is a DEVIATION. If behavior exists in the spec but not in code, it is a GAP. Both are issues.

## Review Task
Review branch `task{A}-r{R}-agent{N}` with maximum adversarial rigor.

## Review Protocol — 16 Mandatory Dimensions

You MUST address EVERY one of these 16 dimensions. No dimension may be skipped. For each dimension, produce specific findings with file:line references. A dimension with "nothing found" is acceptable only after deliberate, documented investigation.

### DIMENSION 0: TDD Discipline (NEW — review this FIRST)
Before reviewing code, determine if the agent followed TDD:
- Check the commit diff: were test files created/modified BEFORE source files? (Look at file creation timestamps in the commit, or analyze the diff order)
- Read ALL test files first (before any source code). Do the tests define clear expected behavior?
- Then read source files. Does the code exist BECAUSE tests demanded it, or does it look like code was written first and tests added after?
- Are there tests that pass trivially (e.g., `assert True`, `assert "foo" in out` without verifying structure)?
- Are there tests that were clearly weakened to match buggy code (e.g., asserting `== []` when spec says versions must be populated)?
- Do tests exist for error paths and edge cases, or only happy paths?
- VERDICT: TDD_COMPLIANT / TDD_SUSPECT / TDD_VIOLATION — with specific evidence

### DIMENSION 1: Complete File Inventory
Run `git diff master..task{A}-r{R}-agent{N} --stat`. List EVERY file created, modified, or deleted. For each file:
- Is it required by the plan? Which task/step?
- Is its location correct per the plan's file structure?
- Is it the right scope for this task, or scope creep from another task?
- What files are MISSING that the plan requires?
- Are there untracked files that should have been committed?

### DIMENSION 2: Placeholder & Dead Code Audit (NEW — review this second, after TDD)
Scan EVERY source file line by line for:
- **Empty collections**: `[]`, `{}`, `set()` where real data should exist
- **Magic strings**: `"auto"`, `"resolved-*"`, `"placeholder"`, `"TBD"`, bare `"TODO"` without colon+explanation
- **Hardcoded versions**: specific version strings like `"3.13"`, `"1.24.9"`, `"19"` that should come from discovery
- **Fake hashes/checksums**: hex strings that aren't real SHA256 values: `"sha-go-1263"`, `"resolved-sccache-release-sha256"`
- **Made-up dates**: hardcoded dates like `20260511` that should be dynamically generated
- **Dead code**: unused imports, functions that are never called, constants that are never referenced (excluding tests), regex patterns that are compiled but never used, parameters that are accepted but never consumed
- **Duplicated constants**: same value defined independently in multiple files

For EACH finding, classify as:
- PLACEHOLDER: value should be real but isn't — CRITICAL if no `# TODO:` with explanation
- DEAD_CODE: exists but never used — IMPORTANT (must be removed)
- DUPLICATE: same value in multiple places — IMPORTANT (single source of truth needed)
- HARDCODED_STALE: real value now but will become wrong — IMPORTANT (needs discovery or `# TODO:`)

### DIMENSION 3: Data Flow — Upstream Sources to Downstream Consumers
For EVERY data object (catalog entries, config values, CLI arguments, TOML sections, JSON fields, build args):
- Where does the data originate? (config file? hardcoded? discovery? user input?)
- Is the origin correct per the design spec? Or is it a placeholder/stub?
- How does the data flow through the code? Trace the ENTIRE chain from source to sink.
- Is EVERY intermediate step present? Are any steps missing?
- Does the data reach ALL its consumers? (template? CLI? workflow? runtime?)
- Is the data TRANSFORMED correctly at each step? Or are there type mismatches / format errors?
- If data is empty `[]` or `{}` or `"auto"` — is there a `# TODO:` with a concrete plan to populate it?

### DIMENSION 4: Completeness — Every Object, Every Field
For EVERY dataclass, function, CLI command, TOML section, and workflow job:
- Are ALL required fields populated? List every field and its source.
- Are there hardcoded values that should come from config or discovery?
- Does the code handle ALL configured languages (python, rust, go, cpp) equally? Or is one language more complete?
- Are ALL 9 ActionType values handled? Check the Literal and the executor.
- Are ALL 4 CLI subcommands fully wired? Or are some still stubs?

### DIMENSION 5: Input/Output Contracts
For EVERY function:
- What are its input types? Are they validated? What happens on None/empty/wrong type?
- What are its output types? Are they always returned? Are there implicit None returns?
- What exceptions can it raise? Are they documented? Are callers handling them?
- Are there functions with side effects that aren't documented?
- Does every function that opens a file handle the "file not found" case?
- Does every function that parses JSON/TOML handle malformed input?

### DIMENSION 6: Error Paths and Edge Cases
For EVERY operation (file I/O, network call, config parse, data transform, CLI dispatch):
- What happens when the input is empty? (empty string, empty list, empty dict, empty file)
- What happens when the input is malformed? (bad JSON, bad TOML, wrong types)
- What happens on network failure? timeout? DNS failure? rate limit?
- What happens on filesystem error? (permission denied, disk full, path too long)
- What happens on version resolution failure? (Node major not found, Go version not in index)
- Are error messages actionable? Do they tell the user WHAT went wrong and HOW to fix it?
- Are error exit codes consistent? (0=success, 1=error, 2=usage)

### DIMENSION 7: Logic and Algorithm Correctness
For EVERY algorithm (sort, filter, search, parse, extract, build):
- Does it produce correct output for ALL valid inputs? Test boundary cases mentally.
- Does it handle the single-element case? The empty case? The maximum case?
- Are comparison operators correct? (>= vs >, == vs in, startswith vs prefix match)
- Are loops bounded? Can they infinite-loop on unexpected data?
- Are regular expressions anchored where needed? Do they handle edge cases?
- Is string parsing robust? (split, strip, replace, format — all have subtle bugs)

### DIMENSION 8: Type Safety and Data Boundaries
For EVERY variable, parameter, return value, and dict access:
- Is the type annotation correct and complete? (no `Any` unless truly dynamic)
- Are dict accesses guarded with `.get()` or checked with `in`?
- Are list/tuple indices bounds-checked?
- Are None checks present where needed?
- What happens if a `str` arrives where an `int` is expected? (Python doesn't catch this)
- Are Optional types handled? What happens on None?
- Are Literal types enforced? What happens on an unknown value?

### DIMENSION 9: Spec Traceability
For EVERY piece of behavior in the code:
- Which design doc section requires it? Quote the section number or line.
- Which plan task/step requires it? Quote the task number.
- If you CANNOT find a spec justification — flag it as UNTRACEABLE (a deviation).
For EVERY requirement in the spec (scan the plan and design doc):
- Which code implements it? Give file:line.
- If you CANNOT find the implementation — flag it as MISSING (a gap).

### DIMENSION 10: Test Quality — Beyond Count
Do NOT just count tests. Analyze them:
- Does each test have a clear, specific assertion? Or does it test too many things at once?
- Does each test verify the CORRECT behavior? Or does it test irrelevant properties?
- Are tests testing the implementation or the mock? (Monkeypatching too much = testing the mock)
- Are tests INDEPENDENT? (Test B should not depend on side effects from Test A)
- Do tests cover ERROR paths? (Not just happy path — test failures, edge cases, bad inputs)
- Do tests cover DATA INTEGRITY? (Not just "function returns" — verify every field of the return value)
- Are test assertions WEAK? (`assert "foo" in out` is weak — prefer `assert out == expected`)
- Are there tests that pass with placeholder/fake data? (CRITICAL FALSE POSITIVE)
- Do tests verify ABSENCE? (No .vsix files, no docker socket, no bare --force, no prevent_destroy)
- List every gap: what SHOULD be tested but ISN'T?

### DIMENSION 11: Design Constraint Compliance
Verify EVERY constraint from the design doc's "Critical Constraints" and "Risk Review Addendum":
- Workspace isolation: all paths under `/workspace/.cdev/`? No `/opt/cde/cache`?
- Download integrity: SHA256 verified? `.part` atomic rename? Tar path traversal protection?
- Immutability: workspace parameters immutable? Selection hash verified on restart?
- No host Docker socket: verified in template? tested?
- No prevent_destroy: verified? (only ignore_changes=all)
- Generated branch atomicity: `--force-with-lease`? No bare `--force`? `.git` excluded from cleanup?
- Date tag immutability: workflow checks tag existence before push? `allow_rebuild_date_tag` exists?
- Concurrency: workflow has concurrency group? cancel-in-progress: false?

### DIMENSION 12: Cross-File Consistency
Compare EVERY file against EVERY other related file:
- Do function signatures in `.py` match their imports in other files?
- Do config keys in `config/*.toml` match the field names in `models.py` and `config.py`?
- Do CLI argument names match the parameter names in the functions they call?
- Do build arg names in `Dockerfile` match the keys in `build_matrix()` output?
- Do workflow step names reference real CLI commands?
- Do runtime file paths in `startup.sh` match the paths in `run_actions.py`?
- Do plugin `id` values match the keys in `plugins/__init__.py` `_PLUGIN_TYPES`?
- Is `__version__` consistent across `__init__.py` and `pyproject.toml`?

### DIMENSION 13: Documentation and Code Clarity
- Does every module have a docstring explaining its purpose?
- Does every public function have a docstring with parameter and return descriptions?
- Are complex algorithms commented to explain WHY, not WHAT?
- Are magic numbers explained? (Why 30? Why "noble"? Why 20260511?)
- Are workarounds documented with the bug/limitation they work around?
- Are `# TODO:` comments specific with what/when/why?

### DIMENSION 14: Production Readiness
- Can this code run in production RIGHT NOW? If not, what's missing?
- What happens if the catalog refresh runs against real APIs? Will it work or fail?
- What happens if GHCR credentials are missing? Clear error or cryptic crash?
- What happens if the generated branch already exists? Race condition?
- What happens if two workflows run simultaneously? Is concurrency correctly handled?
- Are there any race conditions? (lock file creation, atomic rename, temp file cleanup)
- Are there any resource leaks? (open file handles, unclosed HTTP connections, temp files)

### DIMENSION 15: Security Review
- Are file paths validated before use? (Path traversal? Symlink attacks?)
- Are URLs validated? (SSRF? Unexpected protocols?)
- Are shell commands escaped? (Command injection in `subprocess.run`?)
- Are secrets handled properly? (No hardcoded tokens, no secrets in logs)
- Are file permissions correct? (executable scripts, readable configs)
- Are archive extractions safe? (Zip bombs? Path traversal in tar?)

### DIMENSION 16: Round-over-Round Improvement Analysis
If this is Round R >= 2, compare against the previous round:
- Were the SPECIFIC issues from Round {R-1} review synthesis fixed? Check each one.
- Did test count increase or decrease? If decreased, WHY?
- Were new issues introduced that didn't exist in Round {R-1}?
- Did the agent adopt the BEST PATTERNS from the previous synthesis?
- Is this a genuine improvement or a cosmetic resubmission?

## Output Format — Structured Review

After completing all 16 dimensions, output ONE review in this exact structure:

```
## STRUCTURED REVIEW — task{A}-r{R}-agent{N}

### TDD DISCIPLINE ASSESSMENT
Verdict: TDD_COMPLIANT / TDD_SUSPECT / TDD_VIOLATION
Evidence: [specific observations about test-first vs code-first order, test quality]

### PLACEHOLDER & DEAD CODE AUDIT
- PLACEHOLDER: [file:line] — value: <current> — should be: <real source> — fix: <action>
- DEAD_CODE: [file:line] — item: <what> — never referenced by: <evidence>
- HARDCODED_STALE: [file:line] — value: <what> — will become wrong because: <reason>

### CRITICAL ISSUES (must fix before merge — bugs, security, data loss, spec violations, placeholder values, TDD violations)
[file:line] — Description of issue. Why it's critical. How to fix.

### IMPORTANT ISSUES (should fix in next round — missing features, incomplete data, wrong patterns, dead code, duplicated constants)
[file:line] — Description. Why it matters. How to fix.

### MINOR ISSUES (code clarity, style, non-blocking gaps)
[file:line] — Description.

### DIMENSION SCORES (1-10)
0. TDD Discipline: X/10 — [reason]
1. File Inventory: X/10 — [reason]
2. Placeholder Audit: X/10 — [reason]
3. Data Flow: X/10 — [reason]
4. Completeness: X/10 — [reason]
5. I/O Contracts: X/10 — [reason]
6. Error Paths: X/10 — [reason]
7. Logic Correctness: X/10 — [reason]
8. Type Safety: X/10 — [reason]
9. Spec Traceability: X/10 — [reason]
10. Test Quality: X/10 — [reason]
11. Design Constraints: X/10 — [reason]
12. Cross-File Consistency: X/10 — [reason]
13. Documentation: X/10 — [reason]
14. Production Readiness: X/10 — [reason]
15. Security: X/10 — [reason]
16. Round Improvement: X/10 (N/A for R1) — [reason]

### DATA FLOW GAPS (specific instances where data is empty, placeholder, or missing its source)
- [object.field]: expected source → actual source → impact

### TODO AUDIT (every # TODO in the codebase — is it specific? what/when/why?)
[List every # TODO found, assess completeness of explanation]

### BEST PATTERNS (specific techniques to adopt — with file:line)
### PROBLEMS TO AVOID (specific anti-patterns — with file:line)
### VERDICT: PASS / FAIL
### SUMMARY: [2-3 sentences of the most important findings]
```

## Post-Review Protocol

After outputting the review:
1. Save the review to /home/hp/.claude/projects/-home-hp-Projects-OpenSource-CoderVPS/memory/task{A}-r{R}-review{N}.md
2. `git checkout master`
3. Report: branch reviewed, verdict, critical count, important count, lowest dimension score, TDD verdict

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

## Data Integrity Rules (NON-NEGOTIABLE)

### No Placeholders, Magic Numbers, or Fake Data

**Every value in the codebase MUST be one of:**
1. **Dynamically discovered** from an external source (API, filesystem, environment variable)
2. **Sourced from TOML configuration** files (`config/toolchains.toml`, `config/extensions.toml`)
3. **Derived from a real algorithm** operating on real inputs
4. **Marked with `# TODO:`** with a specific explanation of what real source will provide it and when it will be implemented

**The following are FORBIDDEN in any committed code:**
- Empty version lists: `[]` for python/rust/cpp versions when go has populated versions
- Magic strings: `"auto"`, `"resolved-*"`, `"placeholder"`, `"TBD"`, `"TODO"` (without colon+explanation)
- Hardcoded version numbers that will become stale: `"3.13"`, `"1.24.9"`, `"19"`
- Hardcoded URLs that silently redirect: `mozilla/sccache` instead of `rust-lang/sccache`
- Fake SHA256 hashes: `"sha-go-1263"`, `"resolved-sccache-release-sha256"`
- Made-up dates: `"20260511"` hardcoded instead of dynamically generated
- Duplicated constants across files: same value defined in multiple places independently

### `# TODO:` Label Requirements

When a value CANNOT be dynamically resolved (e.g., the external API doesn't exist yet, the discovery function is in a future task), it MUST be marked with `# TODO:` followed by:
- **What** specific real source will provide the value
- **Why** it cannot be resolved now
- **When** (which task/phase) it will be implemented

Example — CORRECT:
```python
# TODO: resolve base tag from Docker Hub API (codercom/example-base tags endpoint)
# Blocked by: no Docker Hub registry client implemented yet
# Will be implemented: Task D (T13 Full Validation)
base_tag = "ubuntu-noble-20260511"
```

Example — WRONG (forbidden):
```python
version = "auto"  # FORBIDDEN — no explanation of source
versions = []  # FORBIDDEN — should have discovery function or TODO
sha256 = "resolved-sccache-release-sha256"  # FORBIDDEN — fake placeholder
```

### Test Data Must Be Real

- Test fixtures MUST mirror real API response structures with real field names, real version strings, real SHA256 hashes
- Tests MUST NOT test against fake/placeholder data and pass — a test that asserts `version == "auto"` is a FALSE POSITIVE
- If real data cannot be obtained, the test MUST be marked with `# TODO:` explaining why and fail/skip appropriately

### Dead Code Elimination

- No unused imports, functions, constants, regex patterns, or parameters
- If a function exists, it MUST be called by something traceable to a user-facing feature
- If a constant is defined, it MUST be referenced by executable code (not just tests)
- Review agents MUST flag all dead code as CRITICAL issues

## TDD-First Development Workflow (MANDATORY for Dev Agents)

Every dev agent MUST follow this sequence. Deviating from this order is a CRITICAL failure.

### Phase 1: Framework Tests (write FIRST, before any implementation code)

Write tests that anchor the overall flow and structure:
- What modules/functions must exist
- What their signatures must be
- What the input/output contracts are
- What the data flow looks like end-to-end

These are NOT detailed unit tests. They are architectural scaffolding tests that define the shape of the solution. They should FAIL because no implementation exists yet.

Run them to confirm they fail with `ModuleNotFoundError` or `ImportError` — proving the code doesn't exist yet.

### Phase 2: Implementation (write MINIMAL code to pass Phase 1 tests)

Implement only enough to make the framework tests pass. Do NOT add features beyond what the tests require. Do NOT add helper functions that aren't needed yet. Do NOT write detailed unit tests yet.

### Phase 3: Detailed Tests (write AFTER Phase 2 implementation passes)

Now write thorough tests covering:
- Data integrity: every field of every return value verified
- Error paths: empty inputs, missing files, malformed data, network failures
- Edge cases: empty catalogs, single-element lists, maximum values
- Idempotency: two calls produce identical output for deterministic operations
- Cross-file consistency: Dockerfile ARGs match build_matrix keys, etc.

### Phase 4: Refine (fix issues found by Phase 3 tests)

Fix the implementation to pass detailed tests. No new features — only fixes.

### Anti-Patterns That Cause Failure

The following are CRITICAL failures:
1. **Writing implementation code first, then tests** — the tests will be biased toward the implementation and won't catch design flaws
2. **Fitting tests to code** — changing test assertions to match buggy output instead of fixing the bug
3. **Tests that only verify mocks are called** — must test real behavior, not mock interactions
4. **Tests that pass with placeholder data** — if `version == "auto"` passes, the test is broken

## Refactor Workflow

When implementing the refactor, follow the design doc and implementation plan in `docs/superpowers/`. Read the relevant documentation before changing code — do not implement from memory when a plan or design document exists. Keep commits small and intentional; commit documentation, plans, and code changes separately.

---

## Agent Mandatory Reading List (NON-NEGOTIABLE)

**Every agent (dev, review, or analysis) MUST read these files IN FULL before doing any other work.** The agent's prompt will list them; the agent MUST use the Read tool to read every one. No exceptions, no shortcuts, no "I already know this from the prompt."

### Required Reading (in order)

1. **`/home/hp/Projects/OpenSource/CoderVPS/CLAUDE.md`** — the complete project instructions, git protocol, and constraints
2. **`/home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/specs/2026-05-12-codervps-refactor-design.md`** — the full design specification with all architectural decisions, constraints, and risk review
3. **`/home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/plans/2026-05-12-codervps-refactor.md`** — the complete 13-task implementation plan with file structures, code patterns, and test specifications

### Why This Is Mandatory

- The prompt is a **pointer** to the task, not a replacement for the full spec. It gives context but cannot contain every detail.
- Agents that skip the docs miss critical constraints, implement wrong APIs, use wrong types, or violate workspace isolation rules.
- The design doc contains 700+ lines of architectural decisions, data flow rules, and risk mitigations. No prompt can summarize all of them.
- The implementation plan contains exact file paths, TOML config formats, dataclass field lists, and test code. Agents must match these exactly, not invent variants.
- Consistency across 5 independent agents requires all of them to read the same source documents.

### Reading Verification

The coordinating agent MUST include this requirement in every agent prompt:

```
## MANDATORY READING (do this FIRST, before any code changes)

Use the Read tool to read these files in full:
1. /home/hp/Projects/OpenSource/CoderVPS/CLAUDE.md
2. /home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/specs/2026-05-12-codervps-refactor-design.md
3. /home/hp/Projects/OpenSource/CoderVPS/docs/superpowers/plans/2026-05-12-codervps-refactor.md

You MUST read ALL three files completely. Do not skim. Do not skip sections.
Only after reading all three may you proceed to implementation.
```

The agent's first action after `git checkout` MUST be reading these three files. The agent must not write any code before completing all three reads.

---

## Git Data Integrity Protocol (MANDATORY)

### Before Any Agent Work — Branch Snapshot

Before launching ANY agent, the coordinating agent MUST record:

```bash
git log --oneline -10 > /tmp/pre-agent-snapshot.txt
git status --short >> /tmp/pre-agent-snapshot.txt
git branch --show-current >> /tmp/pre-agent-snapshot.txt
```

### Agent's Git Commit Requirements

Every dev agent MUST produce exactly ONE commit that:
- Has a descriptive `feat:` / `fix:` / `refactor:` prefix
- Mentions the task and round in the body (e.g., "Task A Round 1")
- Is signed with `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
- Leaves the branch in a clean state (no uncommitted changes, no untracked files outside intended additions)

### After Any Agent Work — Verification Chain

After EVERY agent (dev or review) completes, the coordinating agent MUST run these checks in order:

```bash
# 1. Switch back to master
git checkout master

# 2. Verify the agent's branch has new commits
git log task{A}-r{R}-agent{N} --oneline -5

# 3. Verify the branch differs from master
git diff master..task{A}-r{R}-agent{N} --stat

# 4. Verify master is still clean
git status --short

# 5. Verify the branch log shows exactly 1 new commit (for dev agents)
git log master..task{A}-r{R}-agent{N} --oneline
```

If any check fails:
- Do NOT proceed to the next agent
- Diagnose the issue
- If the agent's branch is missing commits, the agent may have failed to commit — check the agent's output
- If master is dirty, clean it before proceeding

### Branch Preservation

- **NEVER delete an agent's branch** until the task is fully complete (Round 5 merged to master)
- **NEVER force-overwrite a branch** — if an agent fails, create a new branch with a different name (e.g., `taskA-r1-agent1-retry`)
- All task branches remain in `git branch` output as a permanent record until cleanup
- The coordinating agent must be able to `git log` any agent branch at any time to trace what happened

### Recovery Procedure

If an agent fails partway through:
1. Do NOT delete its branch
2. `git checkout master`
3. Create a NEW branch: `git branch task{A}-r{R}-agent{N}-retry{M} master`
4. Launch a new agent on the retry branch with the same task spec
5. Keep the original failed branch for forensic comparison

---

## Agent Prompt — Complete Required Sections

Every agent prompt MUST include ALL of these sections. No section may be omitted.

### Section Order (fixed)

1. **Agent Identity** — who this agent is (task, round, number, role)
2. **CRITICAL FIRST STEP** — the exact `git checkout` command
3. **Bash Execution Rule** — one command per Bash call
4. **MANDATORY READING** — the three files that MUST be read first
5. **Data Integrity Rules** — no placeholders, magic numbers, fake data; `# TODO:` requirements
6. **Context** — round feedback synthesis from previous rounds
7. **Required Spec** — exact task specification with file lists, API signatures, test requirements
8. **TDD-First Workflow** — Phase 1 (framework tests) → Phase 2 (minimal impl) → Phase 3 (detailed tests) → Phase 4 (refine)
9. **Git Safety Reminder** — condensed git rules
10. **Verification Checklist** — exact sequence of commands including TDD phases
11. **Output Requirements** — what the agent must report when done

### Prompt Size and Detail

- Prompts must be **self-contained** — the agent should not need to ask clarifying questions
- Include exact file paths, function signatures, and test expectations
- Include the specific TOML config content if the task creates config files
- Include the specific test code if the plan provides it
- DO NOT summarize the spec — include the relevant portions verbatim from the plan

---

## Traceability Audit Trail

After EVERY agent completes, the coordinating agent MUST write a memory file recording:

```
---
name: task{A}-r{R}-agent{N}-result
description: Dev agent {N} round {R} task {A} result
type: project
---
Branch: task{A}-r{R}-agent{N}
Commit: <full 40-char hash>
Short hash: <7-char hash>
Parent commit: <parent hash>
Tests passed: <number>
Lint: clean/failed
Format: clean/failed
Files changed:
  - <file path> (+<additions> -<deletions>)
Approach: <one sentence describing unique approach>
Issues: <any problems, or "none">
```

This audit trail MUST be complete for all 70 agents per task (6 rounds × 10 agents + Round 7 analysis). It provides:
- Full traceability: which commit came from which agent
- Reproducibility: what each agent did differently
- Debugging: if master breaks after Round 5 merge, we can trace back to the source branch

The coordinating agent must NEVER skip a memory save. If context is low, save a minimal entry with at least: branch, commit hash, tests passed.
