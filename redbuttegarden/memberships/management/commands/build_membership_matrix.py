from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from memberships.services.matrix import (
    DEFAULT_MEMBERSHIP_MATRIX_FIXTURE_PATH,
    build_membership_matrix_rows,
    build_membership_matrix_workbook_bytes,
    load_levels_from_fixture,
)
from memberships.widget_config import MembershipWidgetConfig


class Command(BaseCommand):
    help = "Build an XLSX matrix of MembershipSelectorForm inputs -> recommendation outputs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default=str(DEFAULT_MEMBERSHIP_MATRIX_FIXTURE_PATH),
            help="Path to membership_levels.json fixture.",
        )
        parser.add_argument(
            "--out",
            default="membership_matrix.xlsx",
            help="Output xlsx filename (default: membership_matrix.xlsx).",
        )

    def handle(self, *args, **opts):
        fixture_path = Path(opts["fixture"])
        if not fixture_path.is_absolute():
            fixture_path = Path.cwd() / fixture_path
        if not fixture_path.exists():
            raise SystemExit(f"Fixture not found: {fixture_path}")

        out_path = Path(opts["out"])
        if not out_path.is_absolute():
            out_path = Path.cwd() / out_path

        levels = load_levels_from_fixture(fixture_path)

        # Use the same cfg as production so validation messages match.
        cfg = MembershipWidgetConfig.get_solo()
        rows = build_membership_matrix_rows(levels=levels, cfg=cfg, formulas=None)
        workbook_bytes = build_membership_matrix_workbook_bytes(
            rows=rows,
            levels=levels,
            level_source=fixture_path,
            formulas=None,
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(workbook_bytes)

        self.stdout.write(self.style.SUCCESS(f"Wrote: {out_path}"))
        self.stdout.write(f"Rows: {len(rows)} | Levels loaded: {len(levels)}")
