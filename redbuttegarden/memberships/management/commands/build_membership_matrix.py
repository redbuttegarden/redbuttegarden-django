from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

from django.core.management.base import BaseCommand

from memberships.forms import MembershipSelectorForm
from memberships.services.recommendations import Level, recommend_levels


def load_levels_from_fixture(path: Path) -> List[Level]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    levels: List[Level] = []
    for obj in raw:
        if obj.get("model") != "memberships.membershiplevel":
            continue
        pk = int(obj["pk"])
        f = obj["fields"]
        levels.append(
            Level(
                pk=pk,
                name=f["name"],
                cardholders_included=int(f["cardholders_included"]),
                admissions_allowed=int(f["admissions_allowed"]),
                member_sale_ticket_allowance=int(f["member_sale_ticket_allowance"]),
                price=Decimal(str(f["price"])),
                active=bool(f.get("active", True)),
            )
        )
    return levels


class Command(BaseCommand):
    help = "Build an XLSX matrix of MembershipSelectorForm inputs -> recommendation outputs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default="/code/memberships/fixtures/membership_levels.json",
            help="Path to membership_levels.json fixture (default: membership_levels.json in CWD).",
        )
        parser.add_argument(
            "--out",
            default="membership_matrix.xlsx",
            help="Output xlsx filename (default: membership_matrix.xlsx).",
        )
        parser.add_argument(
            "--slots",
            type=int,
            default=4,
            help="How many non-highlighted suggestion cards to include (default: 4).",
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

        suggestion_slots = int(opts["slots"])

        levels = load_levels_from_fixture(fixture_path)

        # Input domain from your MembershipSelectorForm:
        cardholders_values = range(1, 4)  # 1..3
        admissions_values = range(0, 9)  # 0..8
        ticket_values = [0, 2, 4, 6]  # even only (matches validate_even + max 6)

        # Build rows
        rows: List[Dict[str, Any]] = []

        for c in cardholders_values:
            for a in admissions_values:
                for t in ticket_values:
                    # Use the form to determine validation + error message
                    form = MembershipSelectorForm(
                        data={
                            "cardholders": c,
                            "admissions": a,
                            "member_tickets": t,
                        }
                    )
                    valid = form.is_valid()
                    error_text = ""
                    if not valid:
                        # compact errors for spreadsheet
                        nfe = list(form.non_field_errors())
                        field_errs = []
                        for f_name in ("cardholders", "admissions", "member_tickets"):
                            errs = form.errors.get(f_name)
                            if errs:
                                field_errs.extend([f"{f_name}: {e}" for e in errs])
                        error_text = " | ".join(nfe + field_errs)

                        rows.append(
                            {
                                "cardholders": c,
                                "admissions": a,
                                "tickets": t,
                                "valid": False,
                                "error": error_text,
                                "match_type": None,
                                "highlighted_pk": None,
                                "highlighted_name": None,
                                "highlighted_price": None,
                                "highlighted_ticket_allowance": None,
                                "suggestion_pks": "",
                                "suggestion_names": "",
                                "suggestion_prices": "",
                            }
                        )
                        continue

                    rec = recommend_levels(
                        levels=levels,
                        cardholders=c,
                        guests=a,
                        tickets=t,
                        suggestion_slots=suggestion_slots,
                    )

                    highlighted = rec.highlighted
                    suggestions = rec.suggestions

                    rows.append(
                        {
                            "cardholders": c,
                            "admissions": a,
                            "tickets": t,
                            "valid": True,
                            "error": "",
                            "match_type": rec.match_type,
                            "highlighted_pk": highlighted.pk if highlighted else None,
                            "highlighted_name": (
                                highlighted.name if highlighted else None
                            ),
                            "highlighted_price": (
                                str(highlighted.price) if highlighted else None
                            ),
                            "highlighted_ticket_allowance": (
                                highlighted.member_sale_ticket_allowance
                                if highlighted
                                else None
                            ),
                            "suggestion_pks": ",".join(str(s.pk) for s in suggestions),
                            "suggestion_names": " | ".join(s.name for s in suggestions),
                            "suggestion_prices": " | ".join(
                                str(s.price) for s in suggestions
                            ),
                        }
                    )

        # Write XLSX
        self._write_xlsx(out_path, rows, levels, fixture_path, suggestion_slots)

        self.stdout.write(self.style.SUCCESS(f"Wrote: {out_path}"))
        self.stdout.write(f"Rows: {len(rows)} | Levels: {len(levels)}")

    def _write_xlsx(
        self,
        out_path: Path,
        rows: List[Dict[str, Any]],
        levels: List[Level],
        fixture_path: Path,
        slots: int,
    ) -> None:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, Alignment

        wb = Workbook()

        # Sheet 1: Matrix
        ws = wb.active
        ws.title = "Matrix"

        headers = [
            "cardholders",
            "admissions",
            "tickets",
            "valid",
            "error",
            "match_type",
            "highlighted_pk",
            "highlighted_name",
            "highlighted_price",
            "highlighted_ticket_allowance",
            "suggestion_pks",
            "suggestion_names",
            "suggestion_prices",
        ]
        ws.append(headers)

        header_font = Font(bold=True)
        for col, h in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for r in rows:
            ws.append([r.get(h) for h in headers])

        # Autosize columns (simple heuristic)
        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len = 0
            for cell in ws[col_letter]:
                val = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = min(max(10, max_len + 2), 80)

        ws.freeze_panes = "A2"

        # Sheet 2: Levels (source data)
        ws2 = wb.create_sheet("Levels")
        ws2_headers = [
            "pk",
            "name",
            "cardholders_included",
            "admissions_allowed",
            "member_sale_ticket_allowance",
            "price",
            "active",
        ]
        ws2.append(ws2_headers)
        for col, h in enumerate(ws2_headers, start=1):
            cell = ws2.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for l in sorted(levels, key=lambda x: x.pk):
            ws2.append(
                [
                    l.pk,
                    l.name,
                    l.cardholders_included,
                    l.admissions_allowed,
                    l.member_sale_ticket_allowance,
                    str(l.price),
                    l.active,
                ]
            )

        ws2.freeze_panes = "A2"

        # Sheet 3: Metadata
        ws3 = wb.create_sheet("Meta")
        ws3.append(["fixture_path", str(fixture_path)])
        ws3.append(["suggestion_slots", slots])
        ws3.append(
            [
                "notes",
                "Matrix built from MembershipSelectorForm domain + membership_levels.json fixture.",
            ]
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(out_path)
