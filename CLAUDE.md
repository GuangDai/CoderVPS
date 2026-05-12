# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoderVPS is a Coder-based VPS development environment being refactored from a monolithic shell-driven system into a pluginized Python generator with GitHub-built images and isolated workspace runtimes. The repo currently contains the **legacy** system; the refactor design and implementation plan are in `docs/superpowers/`.

## Branch Model

- **`main`** — source code: Python generator (`codervps/`), config (`config/`), Dockerfile (`docker/`), runtime shell modules (`runtime/`), tests, workflows.
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

## Multi-Agent Execution Rules (MANDATORY)

### Overview

Each implementation task requires **5 rounds** of iterative refinement. Each round runs **5 dev agents** followed by **5 review agents** — all serial, each on its own git branch. No branches are merged into `master` until the **end of Round 5**, when a final review + synthesis selects ONE winning branch to merge.

### Branch Naming Convention

```
task{N}-r{R}-agent{A}   # dev agent branches  (A = 1..5)
task{N}-r{R}-review{A}  # review agent branches (A = 1..5)
```

Example: `task1-r1-agent1`, `task1-r1-review1`, `task1-r2-agent3`

### Round Structure (per task)

**Phase A — Dev Agents (5 serial agents, one after another):**

1. Create 5 branches from master: `git branch task{N}-r{R}-agent{1..5} master`
2. Launch Agent 1 → checks out its branch → implements the task from scratch → commits
3. Wait for Agent 1 to complete. Verify commit exists on the branch.
4. Launch Agent 2 → checks out ITS OWN branch → implements the task from scratch → commits
5. Continue serially through Agent 5.

Each dev agent starts from the SAME master baseline. They do NOT see each other's work. This is "5 people solving the same problem independently."

**Phase B — Review Agents (5 serial agents, one after another):**

1. Launch Review Agent 1 → checks out `task{N}-r{R}-agent1` → reviews the code → outputs feedback (does NOT commit code changes)
2. Launch Review Agent 2 → checks out `task{N}-r{R}-agent2` → reviews → outputs feedback
3. Continue serially through Review Agent 5.

Each reviewer picks ONE dev agent's branch to review. Reviewers do NOT make commits on the dev branch. They only inspect and report problems, suggestions, and assessment.

### Feedback Flow (between rounds)

After both phases complete, the human (or coordinating agent) synthesizes all review feedback. The NEXT round's dev agents receive:

1. The full review feedback from the previous round
2. Knowledge of which approaches worked and which didn't across all 5 branches
3. Instruction to improve upon the best ideas from the previous round

Round 2+ dev agents start from master AGAIN (clean slate), but armed with the synthesized feedback. This is NOT incremental patching — each round is a fresh implementation informed by the previous round's learnings.

### Final Round (Round 5) — Merge Decision

After Round 5's review phase:
1. Run 5 **analysis agents** — one per branch — that evaluate code quality, spec compliance, and test coverage
2. Select the BEST branch to merge into master
3. `git checkout master && git merge task{N}-r5-agent{X}` — only ONE branch merged
4. Delete all task branches for the completed task

### Per-Agent Workflow (the agent's internal steps)

Each dev agent prompt must include these exact instructions:
1. `git checkout task{N}-r{R}-agent{A}` — switch to your assigned branch
2. Read existing files on the branch
3. Implement the task (write/edit code)
4. Run `uv sync` (single command)
5. Run `uv run pytest tests/test_foo.py -q` (single command)
6. Run `uv run ruff check codervps tests` (single command)
7. `git add` changed files
8. `git commit -m "feat: <task description>"`

Each review agent prompt must include these exact instructions:
1. `git checkout task{N}-r{R}-agent{A}` — switch to the branch being reviewed
2. Read all files on the branch
3. Inspect code quality, spec compliance, test coverage, edge cases
4. Output a structured review: what's good, what's wrong, specific suggestions
5. Do NOT make commits — review is read-only

### Serial Execution (MANDATORY)

- **NEVER launch multiple Agent tool calls in parallel.**
- Each agent runs in foreground. Wait for completion before launching the next.
- Verify `git log <branch> --oneline -2` after each agent confirms its commit.

### Cleanup

After a task is fully complete (Round 5 merged):
```bash
git branch -D task{N}-r*-agent* task{N}-r*-review*  # delete all branches for this task
```

### No Worktree Parallelism

Never use `isolation: "worktree"` with `run_in_background: true`. Agents write files using absolute paths and will corrupt each other's work if run in parallel.

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
