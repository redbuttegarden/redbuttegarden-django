# Agent Instructions

All agent work in this repository must follow `ORCHESTRATION.md`.

## Required Subagent Use

All repository work must use subagents according to `ORCHESTRATION.md`.

Before implementation begins:

- Begin every task with an Orchestrator subagent that classifies the work as Small, Standard, or High-Risk and identifies the required workflow gates.
- Spawn or invoke subagents for the roles required by the change class in `ORCHESTRATION.md`.
- Assign each subagent a narrow role that matches one of the project role files under `agents/`.
- Keep role responsibilities separated: project management defines acceptance criteria, architecture defines solution shape, building implements, testing verifies, security reviews risk, and review checks final quality.
- Use the available subagent tooling even when the runtime does not expose subagents with the exact project role names. In that case, clearly state which project role each subagent is performing.
- Do not require every subagent for every task; preserve the balanced workflow in `ORCHESTRATION.md`.
- The primary agent must not self-certify implementation, testing, security, accessibility, or review gates that `ORCHESTRATION.md` assigns to a subagent.
- Do not mark work complete until the required subagent findings, implementation notes, test results, security review, and final review have been considered.

If the runtime cannot create subagents, document that blocker before making changes and follow `ORCHESTRATION.md` manually only with explicit user approval.

Before making code changes:

- Read `ORCHESTRATION.md` and classify the change as Small, Standard, or High-Risk.
- Apply the required workflow gates for that change class.
- Keep implementation consistent with `SPEC.md`.

For production code changes:

- Run focused tests that match the risk of the change.
- Run a Django system check for Standard and High-Risk changes when the environment supports it.
- Complete the security checklist in `agents/security.md`.
- Complete accessibility review for user-facing UI changes.
- Document blocked checks, residual risk, and rollback or mitigation notes when required.

High-Risk changes include authentication, authorization, personal data, APIs, external requests, forms, uploads, payments, settings, infrastructure, secrets, and destructive migrations.
