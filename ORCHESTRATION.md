# Agent Orchestration Workflow

This project uses a balanced solo-development workflow. The goal is to get high-quality code without turning every small local change into a heavyweight ceremony. Each agent has a narrow role and should stay inside that role.

Agent definitions live in:

- `agents/project-manager.md`
- `agents/orchestrator.md`
- `agents/architect.md`
- `agents/builder.md`
- `agents/tester.md`
- `agents/security.md`
- `agents/reviewer.md`

All final production code must conform to `SPEC.md`.

## Core Principles

- Work starts from a clear user outcome, not from an implementation guess.
- The orchestrator chooses the lightest workflow that still protects correctness, security, accessibility, and maintainability.
- Every user-facing feature must satisfy WCAG 2.1 AA.
- Every production change must receive security consideration; security-sensitive changes require a dedicated security pass.
- Tests must match the risk of the change.
- Agents consider only their own area of expertise.
- Code is done only when implementation, verification, review, accessibility, and security expectations are resolved or explicitly documented.

## Change Classes

### Small

Use for isolated copy, style, small tests, or low-risk bug fixes with no data model, authentication, authorization, personal data, rich text, forms, external requests, deployment, or infrastructure impact.

Required agents:

- Orchestrator
- Builder
- Tester, if behavior changes
- Reviewer
- Security checklist, if any production code changes

### Standard

Use for normal feature work touching Django/Wagtail code, templates, JavaScript, CSS, tests, migrations, or user-facing behavior.

Required agents:

- Project Manager, when acceptance criteria are not already clear
- Orchestrator
- Architect
- Builder
- Tester
- Security
- Reviewer

### High-Risk

Use for authentication, authorization, personal data, forms accepting user input, rich text handling, file uploads, payments, external services, production settings, infrastructure, secrets, or destructive migrations.

Required agents:

- Project Manager
- Orchestrator
- Architect
- Builder
- Tester
- Security
- Reviewer

High-risk changes also need rollback or mitigation notes.

## Standard Workflow

1. Intake

   The orchestrator restates the request, classifies the change, and identifies required agents and gates.

2. Scope

   The project manager defines acceptance criteria when the request is ambiguous, user-visible, or risky.

3. Design

   The architect defines the solution shape, affected modules, data impact, accessibility requirements, security requirements, and test expectations.

4. Implementation

   The builder implements the smallest complete change that satisfies the architect's design and `SPEC.md`.

5. Verification

   The tester runs focused tests first, then broader tests when risk justifies it. User-facing changes receive WCAG 2.1 AA verification.

6. Security

   The security agent reviews changed trust boundaries, input handling, output encoding, permissions, secrets, dependency changes, and infrastructure exposure.

7. Review

   The reviewer checks correctness, maintainability, project fit, test coverage, accessibility evidence, and security evidence.

8. Completion

   The orchestrator summarizes changed files, verification, remaining risk, and follow-up work.

## Balanced Gate Matrix

| Gate | Small | Standard | High-Risk |
| --- | --- | --- | --- |
| Acceptance criteria | Optional | Required when unclear | Required |
| Architecture pass | Optional | Required | Required |
| Type hints and docstrings for new or behavior-touched public Python code | Required | Required | Required |
| Focused tests | Required for behavior changes | Required | Required |
| Full test suite | Optional | Required when shared behavior changes | Required unless blocked |
| Django system check | Optional | Required | Required |
| WCAG 2.1 AA review | Required for UI changes | Required for UI changes | Required for UI changes |
| Security checklist | Required | Required | Required |
| Dedicated security pass | If relevant | Required | Required |
| Reviewer approval | Required | Required | Required |
| Rollback notes | Optional | When migration/deploy risk exists | Required |

For this gate, "behavior-touched" means a Python function, method, class, or
module whose signature, contract, return shape, validation, side effects, or
substantive body logic changed. Pure formatting, import sorting, comments, and
mechanical moves do not by themselves require expanding documentation unless
the public contract becomes unclear.

The builder must report type-hint and docstring compliance for new or
behavior-touched public Python code before handoff. The reviewer must request
changes when a touched public function, method, class, or module leaves review
below the `SPEC.md` bar, unless an explicit exception is documented with a
practical reason.

## Repository-Aware Verification

This repository is a Django/Wagtail project rooted under `redbuttegarden/`, with pytest configured through `redbuttegarden/pytest.ini`.

Common local checks:

```bash
env HOME=/home/dev docker compose run --rm -e DJANGO_SETTINGS_MODULE=redbuttegarden.settings.testing web pytest path/to/test_file.py -q
env HOME=/home/dev docker compose run --rm -e DJANGO_SETTINGS_MODULE=redbuttegarden.settings.testing web pytest
env HOME=/home/dev docker compose run --rm -e DJANGO_SETTINGS_MODULE=redbuttegarden.settings.testing web python manage.py check
node --check path/to/file.js
terraform -chdir=redbuttegarden/terraform validate
```

Security-focused checks when the environment supports them:

```bash
env HOME=/home/dev docker compose run --rm -e DJANGO_SETTINGS_MODULE=redbuttegarden.settings.production web python manage.py check --deploy
bandit -r redbuttegarden
pip-audit -r redbuttegarden/requirements.txt
checkov -d redbuttegarden/terraform
```

If a recommended tool is not installed, the tester or security agent records the gap and performs the closest available manual review.

## Accessibility Gate

Every user-facing change must be checked against WCAG 2.1 AA. At minimum:

- Pages have a logical heading structure.
- Interactive controls are reachable and operable by keyboard.
- Focus indicators are visible.
- Links and buttons have accessible names and correct semantics.
- Form fields have labels and accessible error messages.
- Images have useful alt text or are marked decorative.
- Dynamic updates communicate state changes where needed.
- Text and UI controls meet contrast requirements.
- Layout works at mobile and desktop widths without text overlap or loss of function.

## Security Gate

Every production change receives the security checklist in `agents/security.md`. Dedicated security review blocks completion for changes involving:

- Auth, permissions, sessions, or user identity.
- Personal data.
- Forms, query parameters, uploads, APIs, external requests, redirects, or rich text.
- Use of `mark_safe`, `|safe`, `innerHTML`, raw SQL, subprocesses, or filesystem paths.
- Dependency changes.
- Settings, deployment, Terraform, network exposure, or secrets.

## Definition of Done

A change is done when:

- Acceptance criteria are met.
- Code conforms to `SPEC.md`.
- New or behavior-touched public Python code satisfies `SPEC.md` type-hint and
  docstring requirements, or documented exceptions are accepted by review.
- Required tests and checks pass, or blocked checks are documented with reason.
- WCAG 2.1 AA review is complete for user-facing changes.
- Security review is complete at the required level.
- Reviewer has approved or all requested changes are resolved.
- The orchestrator records any residual risk or follow-up work.
