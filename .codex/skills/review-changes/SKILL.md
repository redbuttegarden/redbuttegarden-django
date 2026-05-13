---
name: review-changes
description: Review git working tree changes for commit readiness. Use when asked to inspect staged or unstaged changes, look for risky or sensitive files, coordinate orchestration-aware subagent review, summarize what changed, suggest .gitignore updates, or draft a commit message before committing.
---

# Review Changes

Run a focused pre-commit review.

## Load Repository Workflow

Before reviewing the diff:

1. Run `git status --short` first.
2. Look for repository instructions such as `AGENTS.md`, `ORCHESTRATION.md`, `SPEC.md`, and files under `agents/`.
3. If `ORCHESTRATION.md` exists, classify the working tree changes as Small, Standard, or High-Risk using that file.
4. Apply any required gates from the repository instructions, including subagent use, verification, security review, accessibility review, reviewer approval, and rollback notes.

If the repository has no orchestration framework, continue with the default review workflow below.

Classify from the diff, not file count alone:

- Small: isolated copy, style, small tests, or low-risk bug fixes with no data model, auth, personal data, forms, uploads, external requests, infrastructure, secrets, or deployment impact.
- Standard: normal Django/Wagtail, template, JavaScript, CSS, test, migration, or user-facing behavior changes.
- High-Risk: auth, authorization, personal data, forms accepting user input, rich text handling, uploads, payments, external services, production settings, infrastructure, secrets, or destructive migrations.

## Use Subagents During Analysis

When subagent tooling is available and allowed by the current runtime instructions, use subagents to improve the review instead of doing every gate locally.

- Start with an Orchestrator subagent when the repo has `ORCHESTRATION.md`; ask it to classify the change, identify required gates, and flag likely review focus areas.
- Use role-specific subagents for the required change class. Keep each task narrow and tied to the diff.
- For Small changes, prefer lightweight delegation: Orchestrator plus Reviewer, and Tester or Security only when behavior or production code changes require it.
- For Standard changes, use Architect, Tester, Security, and Reviewer roles when those gates apply.
- For High-Risk changes, use Project Manager, Architect, Tester, Security, and Reviewer roles, and require rollback or mitigation notes.
- For review-only tasks, treat the working tree as the Builder output; use a Builder subagent only when the user asks for fixes or implementation.
- Do not duplicate subagent work locally except to integrate findings, resolve conflicts, or verify claims needed for the final recommendation.

Ask subagents concrete questions, such as:

- Orchestrator: "Classify this diff and list required gates from `ORCHESTRATION.md`."
- Architect: "Does this diff fit the intended design and project boundaries?"
- Tester: "Which focused checks are required, and do the available results cover the risk?"
- Security: "Review changed trust boundaries, sensitive files, secrets, logs, permissions, and exposure."
- Reviewer: "Check final commit readiness, coherence, maintainability, and unresolved risks."

If a required subagent cannot be used, report the blocked role, affected gate, and residual risk in the final review.
Do not claim a required gate is independently satisfied when its subagent was unavailable.

## Inspect The Worktree

1. Inspect both staged and unstaged diffs when present.
2. Read file contents around changed hunks when the diff alone is not enough to judge behavior.
3. Separate findings by:
   - staged changes
   - unstaged changes
   - untracked files
4. Call out renames, deletions, generated files, or unexpectedly large diffs.

## Look For Risky Files

Flag any file that looks sensitive, machine-local, or accidentally generated.

Prioritize:

- `.env*`
- `*.pem`
- `*.key`
- `*.p12`
- `*.crt`
- dumps, logs, temp files, caches, credentials, or tokens
- editor- or OS-specific artifacts that should probably stay untracked

If these files appear intentional, say so carefully and explain the risk instead of assuming they are safe.
Do not quote secret, token, credential, or private-key values in the review output; report the path, key name, and risk instead.

## Judge Commit Readiness

Review whether the changes look coherent enough for one commit.

- Identify mixed concerns that should probably be split.
- Note missing migrations, tests, docs, or ignore rules when relevant.
- Suggest `.gitignore` updates when local-only files appear.
- Highlight anything that looks suspicious before recommending a commit.
- Compare the diff against any applicable `SPEC.md` or project-specific agent guidance.
- Integrate subagent findings, but keep the final recommendation grounded in the actual diff and validation output.

## Validate Relevant Invariants

Do not stop at a visual diff review when the repo likely has automated guards for the kind of change being made.

- Run at least one relevant validation step before recommending a commit when feasible.
- Prefer the narrowest meaningful check for the changed area first, then broaden if risk remains.
- Treat repo-wide policy tests as required when the diff touches their surface area.

Always look for these classes of invariant in the diff:

- templates that add or change external `<script>` or `<link>` tags
- security-sensitive headers, CSP, auth, secrets, or permission logic
- migrations or model/schema changes
- asset pipeline, build, lint, formatting, or static-analysis constraints

When templates introduce or modify external assets:

- inspect the changed tags directly for required `integrity` and `crossorigin` attributes
- search for an SRI or template-policy test and run it if present
- do not recommend commit readiness until that check passes or you explicitly report that you could not run it

When you cannot run a relevant check, call out the gap explicitly as residual risk instead of silently proceeding.

## Produce The Output

When orchestration applies, summarize the result in this order:

1. Classification and required gates
2. Subagents used, findings, or unavailable-subagent blockers
3. Commit readiness assessment
4. Findings by severity with file references
5. Risky or suspicious files
6. Validation run and any remaining gaps
7. Security and accessibility notes when relevant
8. Change summary by area
9. Recommended `.gitignore` updates, if any
10. Draft commit message

When orchestration does not apply, summarize the result in this order:

1. Commit readiness assessment
2. Findings by severity with file references
3. Risky or suspicious files
4. Change summary by area
5. Recommended `.gitignore` updates, if any
6. Draft commit message
7. Validation run and any remaining gaps

For the draft commit message, provide:

- a concise conventional commit subject
- a short recommended body when the diff is large enough to benefit from one

Do not commit automatically. Stop and ask for permission before running any commit command.
