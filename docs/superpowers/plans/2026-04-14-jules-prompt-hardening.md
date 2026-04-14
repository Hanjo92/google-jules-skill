# Jules Prompt Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden every Jules task prompt so the agent stays narrowly scoped by default, asks clarifying questions when ambiguous, and avoids unrelated cleanup or refactors.

**Architecture:** Add a shared strict-scope prompt builder in `google-jules-control/scripts/jules_api.py` and route session creation, follow-up messages, resume flows, and PR rework prompts through it. Expose only a small set of CLI controls for extra scope notes and non-goals, then document and test the shared behavior.

**Tech Stack:** Python 3, argparse, unittest, GitHub CLI, Markdown docs

---

### Task 1: Add failing tests for strict prompt wrapping

**Files:**
- Modify: `tests/test_jules_api.py`
- Test: `tests/test_jules_api.py`

- [ ] **Step 1: Write failing tests for the prompt builder and wrapped API payloads**
- [ ] **Step 2: Run targeted `pytest` cases and confirm the new assertions fail for the expected reason**
- [ ] **Step 3: Implement the smallest shared prompt builder and command wiring needed to satisfy the tests**
- [ ] **Step 4: Re-run the targeted `pytest` cases and confirm they pass**

### Task 2: Add CLI scope controls and rework-message tightening

**Files:**
- Modify: `google-jules-control/scripts/jules_api.py`
- Modify: `tests/test_jules_api.py`
- Test: `tests/test_jules_api.py`

- [ ] **Step 1: Write failing tests for `--scope-note`, `--non-goal`, and PR rework scoping behavior**
- [ ] **Step 2: Run the targeted tests and confirm failure matches the missing strict-scope behavior**
- [ ] **Step 3: Implement the minimal parser and prompt changes to pass those tests**
- [ ] **Step 4: Re-run the targeted tests and confirm they pass**

### Task 3: Update docs to match the hardened contract

**Files:**
- Modify: `google-jules-control/SKILL.md`
- Modify: `Platform/Codex-Prompt.md`
- Modify: `Platform/Codex-Prompt-Minimal.md`
- Modify: `Platform/Codex-Prompt-Strict-Ops.md`
- Modify: `Platform/Claude-Code-Prompt.md`
- Modify: `Platform/Claude-Code-Prompt-Minimal.md`
- Modify: `Platform/Claude-Code-Prompt-Strict-Ops.md`
- Modify: `Platform/Google-Antigravity-Prompt.md`
- Modify: `Platform/Google-Antigravity-Prompt-Minimal.md`
- Modify: `Platform/Google-Antigravity-Prompt-Strict-Ops.md`

- [ ] **Step 1: Update skill and platform prompt docs to explain the strict-scope wrapper and ambiguity behavior**
- [ ] **Step 2: Review examples and wording for consistency with the new CLI flags and default behavior**

### Task 4: Verify the whole change set

**Files:**
- Modify: `tests/test_jules_api.py`

- [ ] **Step 1: Run `pytest tests/test_jules_api.py -v`**
- [ ] **Step 2: Review modified docs and command help text for scope-hardening consistency**
- [ ] **Step 3: Summarize the issue link, verification evidence, and remaining follow-up ideas**
