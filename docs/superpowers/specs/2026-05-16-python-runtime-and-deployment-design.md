# Python Runtime and Deployment UX Design

## Scope

This pass improves three connected surfaces:

1. Python runtime selection becomes catalog-driven at the interpreter build level.
2. The VS Code Web Coder app opens in a browser tab instead of a slim window.
3. Deployment documentation becomes a step-by-step operator guide for GitHub and a local VPS.

## Python Runtime Selection

The catalog continues to use `uv python list --only-downloads --all-versions --output-format json`,
but it no longer collapses Python choices to bare minor versions. It keeps one latest downloadable
entry per implementation/minor/variant combination for Linux x86_64 GNU builds.

Supported implementations in the UI are CPython, PyPy, and GraalPy. CPython default and
free-threaded variants are shown separately. Pre-release versions are allowed, but they are marked
as `preview` and labelled clearly.

The runtime value passed to `uv python install` is a stable uv request string, not the raw
`uv python list` key. The catalog keeps the raw key as metadata for traceability only.

Examples:

- CPython default: `cpython@3.13.13`
- CPython free-threaded: `cpython@3.13.13+freethreaded`
- PyPy: `pypy@3.11.15`
- GraalPy: `graalpy@3.12.0`

## Coder App Opening

The generated `coder_app` for VS Code Web sets `open_in = "tab"`. The Coder provider supports
`tab` and `slim-window`; `slim-window` is the provider default, so the generated template must be
explicit.

## Deployment Guide

The deployment guide is a concrete operator runbook. It covers GitHub repository setup, Actions
and GHCR expectations, generated branch publication, local VPS prerequisites, Coder import/update,
VSIX handling, and common troubleshooting commands. It does not require GitHub CLI on the VPS.
