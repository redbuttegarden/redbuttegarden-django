# Production Code Specification

This document defines the quality target for production code in this repository. New code should look like it belongs in a Django/Wagtail project maintained over many years: typed, readable, tested, secure, accessible, and conservative.

## Universal Standards

- Prefer small, explicit code over clever abstractions.
- Follow existing app boundaries and naming conventions.
- Add type hints to new or behavior-touched public Python functions, methods,
  and public attributes. Add docstrings to new or behavior-touched public
  modules, classes, functions, and methods. Document any practical exception in
  the handoff and review notes.
- Add type hints and docstrings to private helpers when their intent or contract
  is not obvious.
- Use comments to explain why code exists or why a non-obvious choice is safe. Do not comment what the next line already says.
- Validate input at the server boundary.
- Escape output by default.
- Avoid global state unless it is immutable or deliberately cached with clear invalidation.
- Keep queries bounded and avoid N+1 behavior.
- Preserve backwards compatibility for URLs, migrations, Wagtail page data, and public behavior unless the change explicitly requires otherwise.
- All user-facing features must conform to WCAG 2.1 AA.
- All production changes must pass security review appropriate to their risk.

## Python: Django and Wagtail

Use typed service functions for business logic that does not need to live directly on a model or view.

```python
"""Utilities for selecting public event summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from events.models import EventPage


@dataclass(frozen=True)
class EventSummary:
    """Public event data needed by listing templates."""

    title: str
    url: str
    starts_at: datetime


def get_upcoming_event_summaries(limit: int = 6) -> list[EventSummary]:
    """Return upcoming live events in chronological order.

    The query stays narrow because this function is used by public pages.
    Callers that need more fields should add them intentionally instead of
    passing model instances through the template by default.
    """

    now = timezone.now()
    events: QuerySet[EventPage] = (
        EventPage.objects.live()
        .filter(start_datetime__gte=now)
        .only("title", "slug", "url_path", "start_datetime")
        .order_by("start_datetime")[:limit]
    )

    return [
        EventSummary(
            title=event.title,
            url=event.get_url() or "",
            starts_at=event.start_datetime,
        )
        for event in events
    ]
```

Model methods should be typed when added or touched for new behavior.

```python
class Species(ClusterableModel):
    """Plant species represented in the living collections database."""

    def get_absolute_url(self) -> str:
        """Return the public detail URL for this species."""

        return reverse("plants:species-detail", args=[self.pk])
```

## Views and Forms

Views should keep request handling, permission checks, validation, and response selection clear. Complex selection or transformation logic belongs in tested helpers.

```python
from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from events.selectors import get_upcoming_event_summaries


def upcoming_events(request: HttpRequest) -> HttpResponse:
    """Render the public upcoming events list."""

    return render(
        request,
        "events/upcoming_events.html",
        {"events": get_upcoming_event_summaries()},
    )
```

Security expectations:

- Use Django forms or serializers for validation.
- Do not trust query parameters, POST bodies, path components, headers, or cookies.
- Check object-level permissions server-side.
- Avoid open redirects.
- Keep CSRF protection on state-changing views.

## Templates

Templates should be semantic, accessible, and escaped by default.

```django
{% extends "base.html" %}
{% load wagtailcore_tags wagtailimages_tags %}

{% block content %}
  <main id="main-content" class="event-list">
    <h1>{{ page.title }}</h1>

    <ul class="event-list__items" aria-label="Upcoming events">
      {% for event in events %}
        <li class="event-list__item">
          <article>
            <h2>
              <a href="{{ event.url }}">{{ event.title }}</a>
            </h2>
            <time datetime="{{ event.starts_at|date:'c' }}">
              {{ event.starts_at|date:"F j, Y" }}
            </time>
          </article>
        </li>
      {% empty %}
        <li>No upcoming events are currently scheduled.</li>
      {% endfor %}
    </ul>
  </main>
{% endblock %}
```

Image example:

```django
{% image page.thumbnail fill-300x300 as thumbnail %}
<img
  src="{{ thumbnail.url }}"
  width="{{ thumbnail.width }}"
  height="{{ thumbnail.height }}"
  alt="{{ page.thumbnail.title }}"
  loading="lazy"
>
```

Template rules:

- Use headings in order.
- Use buttons for actions and links for navigation.
- Every form control has a visible label or an accessible name.
- Error messages are associated with their fields.
- Use `|safe` only for trusted, deliberately sanitized content. Prefer Wagtail `richtext` or Django escaping.
- Embed JSON with safe framework patterns whenever possible instead of string-building scripts.

## JavaScript

JavaScript should progressively enhance server-rendered pages. Pages must remain understandable when JavaScript fails unless the feature explicitly requires scripting.

```javascript
/**
 * Attach accessible disclosure behavior to filter groups.
 *
 * @param {HTMLElement} root - Container that owns the disclosure buttons.
 */
function setupFilterDisclosures(root) {
    const buttons = root.querySelectorAll("[data-filter-disclosure]");

    buttons.forEach((button) => {
        const panelId = button.getAttribute("aria-controls");
        const panel = panelId ? document.getElementById(panelId) : null;
        if (!panel) return;

        button.addEventListener("click", () => {
            const isExpanded = button.getAttribute("aria-expanded") === "true";
            button.setAttribute("aria-expanded", String(!isExpanded));
            panel.hidden = isExpanded;
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const filterRoot = document.getElementById("collection-filter-form");
    if (filterRoot) setupFilterDisclosures(filterRoot);
});
```

JavaScript rules:

- Use `const` and `let`; avoid implicit globals.
- Guard against missing DOM elements.
- Keep keyboard behavior equivalent to pointer behavior.
- Update ARIA state when UI state changes.
- Avoid `innerHTML` for untrusted content. Use `textContent` or DOM APIs.
- Do not log sensitive data.
- Run `node --check path/to/file.js` for changed files.

## CSS

CSS should be resilient, responsive, and accessible. Prefer clear component-oriented selectors that work with the existing Bootstrap-based templates.

```css
.event-list__items {
    display: grid;
    gap: 1rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.event-list__item {
    border-block-end: 1px solid #d6d6d6;
    padding-block: 1rem;
}

.event-list__item a:focus-visible {
    outline: 3px solid #005fcc;
    outline-offset: 0.2rem;
}

@media (min-width: 48rem) {
    .event-list__items {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
```

CSS rules:

- Preserve readable text at all supported viewport sizes.
- Do not remove outlines unless replacing them with an equally visible focus style.
- Meet WCAG 2.1 AA contrast for text and interactive states.
- Do not rely on color alone to convey meaning.
- Respect reduced-motion preferences for animation.
- Avoid layout shifts caused by hover or focus states.

## Tests

Tests should prove behavior, not implementation details. Use focused names and direct assertions.

```python
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from plants.tests.utils import get_family, get_genus, get_species


class SpeciesDetailViewTests(TestCase):
    """Regression tests for public species detail pages."""

    def test_detail_page_renders_species_name(self) -> None:
        """The public detail page shows the requested species."""

        family = get_family(name="Sapindaceae")
        genus = get_genus(family, name="Acer")
        species = get_species(
            genus,
            name="rubrum",
            full_name="Acer rubrum",
            vernacular_name="Red maple",
        )

        response = self.client.get(
            reverse("plants:species-detail", args=[species.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acer rubrum")
        self.assertContains(response, "Red maple")
```

Test rules:

- Add regression tests for every bug fix.
- Add behavior tests for every feature.
- Include edge cases for empty input, missing optional fields, permissions, and invalid input.
- Use `assertNumQueries` for query-sensitive code.
- Assert accessibility-critical markup when templates change.
- Keep fixtures local and readable unless shared setup clearly reduces duplication.

## Terraform and Infrastructure

Infrastructure must be explicit, parameterized, and least-privilege.

```hcl
resource "aws_security_group" "database" {
  name                   = "rbg-web-${var.environment}-database"
  description            = "Database access for ${var.environment}"
  vpc_id                 = aws_vpc.main.id
  revoke_rules_on_delete = true

  ingress {
    description = "PostgreSQL from application security group"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [
      aws_security_group.application.id
    ]
  }

  tags = {
    Project     = "redbuttegarden"
    Environment = var.environment
  }
}
```

Infrastructure rules:

- No hard-coded secrets.
- Prefer security group references over broad CIDR ranges.
- Encrypt storage and databases.
- Avoid public exposure unless explicitly required.
- Avoid destructive settings like `force_destroy = true` or `skip_final_snapshot = true` for production resources unless documented and approved.
- Use consistent tags.
- Run `terraform fmt` and `terraform validate` for changed Terraform.

## Migrations

Migration rules:

- Keep schema and data migrations understandable and reversible where practical.
- Avoid long-running data migrations without batching.
- Preserve existing content and URLs.
- Add constraints only after existing data is known to satisfy them or after a data migration fixes it.
- Document deployment ordering when a migration needs a two-step release.

## Comments and Docstrings

Good comment:

```python
# Wagtail stores rich text links as custom attributes, so this parser preserves
# existing anchors before inserting species links.
```

Poor comment:

```python
# Loop through events.
for event in events:
    ...
```

Good docstring:

```python
def normalize_species_alias(value: str) -> str:
    """Return a single-line alias suitable for autolink matching."""
```

Docstrings should describe the contract, not narrate each line.

## Production Readiness Checklist

- The change satisfies the acceptance criteria.
- New or behavior-touched public Python code has type hints and docstrings;
  private helpers have them when intent or contract is not obvious.
- Tests cover the changed behavior and important edge cases.
- User-facing behavior meets WCAG 2.1 AA.
- Security-sensitive code has been reviewed by the security agent.
- Templates escape by default and avoid unsafe HTML.
- JavaScript is syntax-checked and keyboard-accessible.
- CSS preserves focus visibility and contrast.
- Terraform is formatted, validated, and reviewed for least privilege.
- Migrations are safe for existing data.
- The reviewer has approved the final diff.
