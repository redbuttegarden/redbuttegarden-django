"""Editor blocks for additional same-day garden opening periods."""

from typing import Any

from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.admin.telepath import register
from wagtail.admin.telepath.widgets import WidgetAdapter
from wagtail.admin.widgets import AdminTimeInput


class OpeningPeriodTimeInput(AdminTimeInput):
    """Retain accessible input attributes through the generic widget adapter."""


# The specialized time adapter creates a bare input and drops widget attributes.
# The generic adapter preserves rendered HTML and initializes the same chooser.
register(WidgetAdapter(), OpeningPeriodTimeInput)


class OpeningPeriodBlock(blocks.StructBlock):
    """A labeled opening period that closes later on the same day."""

    garden_open = blocks.TimeBlock(label="Opening time")
    garden_close = blocks.TimeBlock(label="Closing time")
    label = blocks.CharBlock(required=False, max_length=200)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Associate each editor input with Wagtail's existing error container."""

        super().__init__(*args, **kwargs)
        for block in self.child_blocks.values():
            if isinstance(block, blocks.TimeBlock):
                block.field.widget = OpeningPeriodTimeInput(format=block.format)
            # Telepath replaces __ID__ throughout widget HTML when it creates
            # each input; FieldBlock creates the matching -errors container.
            block.field.widget.attrs["aria-describedby"] = "__ID__-errors"

    def clean(self, value: Any) -> Any:
        """Validate both endpoints and associate ordering errors with closing time."""

        cleaned = super().clean(value)
        if cleaned["garden_close"] <= cleaned["garden_open"]:
            raise blocks.StructBlockValidationError(
                block_errors={
                    "garden_close": ValidationError(
                        "Closing time must be later than opening time on the same day."
                    )
                }
            )
        return cleaned

    class Meta:
        label = "Opening period"
        icon = "time"
