import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from .wcag import contrast_ratio

RBG_COLOR_VARIABLE_CHOICES = [
    ("", "Theme default"),
    ("--rbg-lavender-purple", "Lavender Purple"),
    ("--rbg-oak-green", "Oak Green"),
    ("--rbg-conifer-green", "Conifer Green"),
    ("--rbg-cactus-flower-yellow", "Cactus Flower Yellow"),
    ("--rbg-penstemon-blue", "Penstemon Blue"),
    ("--rbg-night-sky-blue", "Night Sky Blue"),
    ("--rbg-fall-leaves-red", "Fall Leaves Red"),
    ("--rbg-highlight-bg", "Highlight Background"),
    ("--rbg-teal", "Teal"),
    ("--rbg-dark-blue", "Dark Blue"),
    ("--rbg-red", "Red"),
    ("--rbg-purple", "Purple"),
    ("--rbg-orange", "Orange"),
    ("--rbg-gray", "Gray"),
    ("--rbg-white", "White"),
]

RBG_COLORS = {
    "--rbg-lavender-purple": "#C1B5D5",
    "--rbg-oak-green": "#0b412d",
    "--rbg-conifer-green": "#D0E8E5",
    "--rbg-cactus-flower-yellow": "#EFB544",
    "--rbg-penstemon-blue": "#5A75B5",
    "--rbg-night-sky-blue": "#243656",
    "--rbg-fall-leaves-red": "#B2392F",
    "--rbg-highlight-bg": "#F2EDE4",
    "--rbg-teal": "#005a65",
    "--rbg-dark-blue": "#1a2d44",
    "--rbg-red": "#82261b",
    "--rbg-purple": "#432f71",
    "--rbg-orange": "#FF7744",
    "--rbg-gray": "#BBBABA",
    "--rbg-white": "#FFFFFF",
}



ANCHOR_ID_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z][A-Za-z0-9\-_:.]*$",
    message="Use a valid HTML id (start with a letter; then letters/numbers, '-', '_', ':', '.').",
)

CSS_CLASS_LIST_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9\-_ ]*$",
    message="CSS classes may only contain letters/numbers, spaces, hyphens and underscores.",
)


DEFAULT_BG = "#dff3ef"
DEFAULT_TEXT = "#083426"
DEFAULT_HEADING = "#072d22"

MIN_BODY = 4.5
MIN_HEADING = 3.0


def resolve_token_or_default(token: str | None, default_hex: str) -> str:
    """
    token is like '--rbg-teal' or ''/None.
    """
    if not token:
        return default_hex
    try:
        return RBG_COLORS[token]
    except KeyError:
        # Unknown token should be treated as invalid config
        raise ValidationError(f"Unknown color token: {token}")


class LinkedCarouselSlideBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False, max_length=255)
    link_page = blocks.PageChooserBlock(
        required=False, help_text="Choose an internal page"
    )
    link_url = blocks.URLBlock(
        required=False,
        help_text="Or enter an external URL (will be used if no internal page selected)",
    )
    open_in_new_tab = blocks.BooleanBlock(
        required=False, default=False, help_text="Open the link in a new tab"
    )

    class Meta:
        icon = "image"
        label = "Slide"


class LinkedCarouselBlock(blocks.ListBlock):
    def __init__(self, *args, **kwargs):
        super().__init__(LinkedCarouselSlideBlock(), *args, **kwargs)

    class Meta:
        icon = "placeholder"
        label = "Linked Image carousel"
        template = "blocks/linked_carousel_block.html"


class PricingCardCTA(blocks.StructBlock):
    text = blocks.CharBlock(
        required=False,
        label="Button text",
        help_text="Text shown on the CTA button (e.g. “Join now”).",
    )
    page = blocks.PageChooserBlock(
        required=False,
        label="Link to internal page",
    )
    url = blocks.URLBlock(
        required=False,
        label="Link to external URL",
    )
    style = blocks.ChoiceBlock(
        required=False,
        default="primary",
        label="Button style",
        help_text="Applies ONLY to the CTA button (Bootstrap btn-* style).",
        choices=[
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("outline-primary", "Outline primary"),
            ("outline-secondary", "Outline secondary"),
            ("link", "Link style"),
        ],
    )
    full_width = blocks.BooleanBlock(
        required=False,
        default=False,
        label="Full-width button",
    )
    new_tab = blocks.BooleanBlock(
        required=False,
        default=False,
        label="Open link in new tab",
    )

    def clean(self, value):
        cleaned = super().clean(value)
        text = (cleaned.get("text") or "").strip()
        page = cleaned.get("page")
        url = cleaned.get("url")

        if (page or url) and not text:
            raise ValidationError(
                {"text": "Button text is required when you provide a link."}
            )
        if text and not (page or url):
            raise ValidationError({"page": "Choose a Page or URL for the button."})
        if page and url:
            raise ValidationError({"url": "Choose either Page or URL (not both)."})
        return cleaned

    class Meta:
        icon = "link"
        label = "Button"


class PricingCardDisplayOptions(blocks.StructBlock):
    # Layout
    width = blocks.ChoiceBlock(
        required=False,
        default="col-12",
        label="Width",
        choices=[
            ("col-12", "Full width"),
            ("col-md-10 col-lg-8", "Centered (md 10 / lg 8)"),
            ("col-md-8", "Medium (md 8)"),
            ("col-md-6", "Half (md 6)"),
            ("col-lg-4", "Third (lg 4)"),
        ],
    )
    align = blocks.ChoiceBlock(
        required=False,
        default="",
        choices=[
            ("", "No auto alignment"),
            ("mx-auto", "Center"),
            ("me-auto", "Left"),
            ("ms-auto", "Right"),
        ],
    )
    margin_y = blocks.ChoiceBlock(
        required=False,
        default="my-2",
        choices=[
            ("my-1", "Tight"),
            ("my-2", "Normal"),
            ("my-3", "Spacious"),
            ("my-4", "Extra spacious"),
        ],
    )

    # Card look
    variant = blocks.ChoiceBlock(
        required=False,
        default="default",
        choices=[
            ("default", "Default"),
            ("light", "Light"),
            ("dark", "Dark"),
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("success", "Success"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("danger", "Danger"),
        ],
        help_text="Maps to Bootstrap background/text utilities (e.g. text-bg-primary).",
    )
    border = blocks.BooleanBlock(required=False, default=True)
    shadow = blocks.ChoiceBlock(
        required=False,
        default="sm",
        choices=[
            ("none", "None"),
            ("sm", "Small"),
            ("md", "Medium"),
            ("lg", "Large"),
        ],
    )
    padding = blocks.ChoiceBlock(
        required=False,
        default="p-3",
        choices=[
            ("p-2", "Compact"),
            ("p-3", "Normal"),
            ("p-4", "Spacious"),
        ],
    )

    # Typography / alignment
    text_align = blocks.ChoiceBlock(
        required=False,
        default="start",
        choices=[("start", "Left"), ("center", "Center"), ("end", "Right")],
    )
    heading_align = blocks.ChoiceBlock(
        required=False,
        default="start",
        choices=[("start", "Left"), ("center", "Center"), ("end", "Right")],
    )
    heading_placement = blocks.ChoiceBlock(
        required=False,
        default="body",
        choices=[
            ("body", "Heading in card body"),
            ("header", "Heading in card header"),
        ],
    )
    show_heading = blocks.BooleanBlock(required=False, default=True)

    # Section controls
    show_prices_section = blocks.BooleanBlock(required=False, default=True)
    show_concert_section = blocks.BooleanBlock(required=False, default=True)
    show_definitions_section = blocks.BooleanBlock(required=False, default=True)

    prices_heading = blocks.CharBlock(required=False, default="Membership Prices")
    concert_heading = blocks.CharBlock(
        required=False, default="Concert Access Options*"
    )
    definitions_heading = blocks.CharBlock(
        required=False, default="Membership Definitions"
    )

    show_maximums = blocks.BooleanBlock(required=False, default=True)
    show_dividers = blocks.BooleanBlock(required=False, default=True)

    definitions_layout = blocks.ChoiceBlock(
        required=False,
        default="stacked",
        choices=[("stacked", "Stacked"), ("accordion", "Accordion")],
        help_text="Accordion uses Bootstrap collapse JS.",
    )

    # Colors (map to CSS variables defined in theme.css)
    background_color = blocks.ChoiceBlock(
        required=False,
        default="",
        choices=RBG_COLOR_VARIABLE_CHOICES,
        label="Background color",
        help_text="Choose from theme color variables (uses CSS var).",
    )
    border_color = blocks.ChoiceBlock(
        required=False,
        default="",
        choices=RBG_COLOR_VARIABLE_CHOICES,
        label="Border color",
    )
    text_color = blocks.ChoiceBlock(
        required=False,
        default="",
        choices=RBG_COLOR_VARIABLE_CHOICES,
        label="Text color",
    )
    heading_color = blocks.ChoiceBlock(
        required=False,
        default="",
        choices=RBG_COLOR_VARIABLE_CHOICES,
        label="Heading color",
    )

    border_width = blocks.ChoiceBlock(
        required=False,
        default="10px",
        choices=[
            ("0", "None"),
            ("1px", "Thin"),
            ("2px", "Normal"),
            ("4px", "Thick"),
            ("10px", "Extra thick"),
        ],
        label="Border width",
    )
    border_radius = blocks.ChoiceBlock(
        required=False,
        default="16px",
        choices=[
            ("0", "Square"),
            ("8px", "Slightly rounded"),
            ("16px", "Rounded"),
            ("24px", "Extra rounded"),
        ],
        label="Border radius",
    )

    # IDs / custom hooks
    anchor_id = blocks.CharBlock(
        required=False,
        validators=[ANCHOR_ID_VALIDATOR],
        help_text="Optional anchor id for linking (e.g. membership-pricing). Must be unique per page.",
    )
    extra_classes = blocks.CharBlock(
        required=False,
        validators=[CSS_CLASS_LIST_VALIDATOR],
        help_text="Optional extra CSS classes added to the outer wrapper.",
    )

    class Meta:
        icon = "cog"
        label = "Display options"


class PricingCardBlock(blocks.StructBlock):
    # ----- Content fields (your existing ones) -----
    heading = blocks.CharBlock(
        required=False,
        default="Flexible Options for your Unique Situation",
        help_text="Main heading for the card",
    )

    first_cardholder_price = blocks.DecimalBlock(
        required=True,
        decimal_places=0,
        max_digits=10,
        help_text="Price for the first cardholder (numbers only, no $ sign).",
    )

    additional_cardholder_price = blocks.DecimalBlock(
        required=True,
        decimal_places=0,
        max_digits=10,
        help_text="Price for each additional cardholder.",
    )
    additional_cardholder_max = blocks.IntegerBlock(
        required=False,
        default=3,
        help_text="Maximum number of additional cardholders (e.g. 3).",
    )

    guest_admission_price = blocks.DecimalBlock(
        required=True,
        decimal_places=0,
        max_digits=10,
        help_text="Price per guest for garden visits.",
    )
    guest_admission_max = blocks.IntegerBlock(
        required=False,
        default=8,
        help_text="Maximum number of guests allowed (e.g. 8).",
    )

    two_tickets_included = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="If unchecked, don't render the 'Two tickets per show: included' line.",
    )

    four_tickets_price = blocks.DecimalBlock(
        required=False,
        decimal_places=0,
        max_digits=10,
        help_text="Price to increase to four tickets per show. Leave blank if not offered.",
    )
    four_tickets_qualifier = blocks.CharBlock(
        required=False,
        help_text="Who qualifies for the 4-ticket upgrade",
    )

    six_tickets_price = blocks.DecimalBlock(
        required=False,
        decimal_places=0,
        max_digits=10,
        help_text="Price to increase to six tickets per show. Leave blank if not offered.",
    )
    six_tickets_qualifier = blocks.CharBlock(
        required=False,
        help_text="Who qualifies for the 6-ticket upgrade",
    )

    concert_access_footer_note = blocks.CharBlock(
        required=False,
        help_text="Small italic footer note.",
    )

    membership_level_benefits_text = blocks.RichTextBlock(required=False)
    cardholder_level_benefits_text = blocks.RichTextBlock(required=False)
    primary_member_text = blocks.RichTextBlock(required=False)
    additional_cardholders_text = blocks.RichTextBlock(required=False)
    guests_text = blocks.RichTextBlock(required=False)

    # ----- New: display + CTA -----
    display = PricingCardDisplayOptions(
        required=False,
        default={
            "width": "col-12",
            "align": "",
            "margin_y": "my-2",
            "variant": "default",
            "border": True,
            "shadow": "sm",
            "padding": "p-3",
            "text_align": "start",
            "heading_align": "start",
            "heading_placement": "body",
            "show_heading": True,
            "show_prices_section": True,
            "show_concert_section": True,
            "show_definitions_section": True,
            "prices_heading": "Membership Prices",
            "concert_heading": "Concert Access Options*",
            "definitions_heading": "Membership Definitions",
            "show_maximums": True,
            "show_dividers": True,
            "definitions_layout": "stacked",
            "background_color": "",
            "border_color": "",
            "text_color": "",
            "heading_color": "",
            "border_width": "10px",
            "border_radius": "16px",
        },
    )

    cta = PricingCardCTA(required=False)

    def clean(self, value):
        cleaned = super().clean(value)

        d = cleaned.get("display") or {}

        bg_hex = resolve_token_or_default(d.get("background_color"), DEFAULT_BG)
        text_hex = resolve_token_or_default(d.get("text_color"), DEFAULT_TEXT)
        heading_hex = resolve_token_or_default(d.get("heading_color"), DEFAULT_HEADING)

        body_ratio = contrast_ratio(text_hex, bg_hex)
        heading_ratio = contrast_ratio(heading_hex, bg_hex)

        errors = {}

        if body_ratio < MIN_BODY:
            errors["display"] = ValidationError(
                f"Body text contrast is {body_ratio:.2f}:1, but must be at least {MIN_BODY}:1 "
                f"against the chosen background (WCAG AA). Pick a different background or text color."
            )

        if heading_ratio < MIN_HEADING:
            # If you want, merge with existing display error rather than overwrite.
            msg = (
                f"Heading contrast is {heading_ratio:.2f}:1, but must be at least {MIN_HEADING}:1 "
                f"against the chosen background. Pick a different heading or background color."
            )
            if "display" in errors:
                # append second message
                errors["display"] = ValidationError(
                    [errors["display"], ValidationError(msg)]
                )
            else:
                errors["display"] = ValidationError(msg)

        if errors:
            raise ValidationError(errors)

        # Validate money fields are non-negative
        money_fields = [
            "first_cardholder_price",
            "additional_cardholder_price",
            "guest_admission_price",
            "four_tickets_price",
            "six_tickets_price",
        ]
        for k in money_fields:
            v = cleaned.get(k)
            if v is not None and v < 0:
                raise ValidationError({k: "Price must be zero or a positive number."})

        # Validate maxima sensible
        add_max = cleaned.get("additional_cardholder_max") or 0
        if add_max < 0 or add_max > 20:
            raise ValidationError(
                {"additional_cardholder_max": "Enter a realistic maximum (0–20)."}
            )

        guest_max = cleaned.get("guest_admission_max") or 0
        if guest_max < 0 or guest_max > 200:
            raise ValidationError(
                {"guest_admission_max": "Enter a realistic maximum (0–200)."}
            )

        # If price is provided for an upgrade, ensure it's > 0
        if (
            cleaned.get("four_tickets_price") is not None
            and cleaned["four_tickets_price"] <= 0
        ):
            raise ValidationError(
                {"four_tickets_price": "Provide a positive price or leave blank."}
            )
        if (
            cleaned.get("six_tickets_price") is not None
            and cleaned["six_tickets_price"] <= 0
        ):
            raise ValidationError(
                {"six_tickets_price": "Provide a positive price or leave blank."}
            )

        return cleaned

    def get_context(self, value, parent_context=None):
        """
        Compute Bootstrap classes and CSS custom properties so templates stay readable.

        Exposes:
        - pricing_card_wrapper_classes
        - pricing_card_card_classes
        - pricing_card_body_padding
        - pricing_card_style_vars   (inline style string of CSS vars)
        - pricing_card_heading_id / pricing_card_accordion_id
        - has_definitions
        """
        context = super().get_context(value, parent_context=parent_context)

        d = value.get("display") or {}
        variant = d.get("variant") or "default"

        # ---- Content presence flags ----
        definition_fields = [
            "membership_level_benefits_text",
            "cardholder_level_benefits_text",
            "primary_member_text",
            "additional_cardholders_text",
            "guests_text",
        ]
        context["has_definitions"] = any(value.get(f) for f in definition_fields)

        # ---- Wrapper classes (width + alignment + spacing) ----
        wrapper_classes = [
            "pricing-card",
            d.get("margin_y") or "my-2",
            d.get("width") or "col-12",
            d.get("align") or "",
            d.get("extra_classes") or "",
        ]

        # ---- Card classes (Bootstrap card + variant + shadow + border) ----
        card_classes = ["card"]

        # If user explicitly picked a background token, don't also apply text-bg-*,
        # otherwise you get competing backgrounds.
        bg_token = d.get("background_color") or ""
        if variant != "default" and not bg_token:
            card_classes.append(
                "text-bg-light" if variant == "light" else f"text-bg-{variant}"
            )

        if not d.get("border", True):
            card_classes.append("border-0")

        shadow_map = {
            "none": "shadow-none",
            "sm": "shadow-sm",
            "md": "shadow",
            "lg": "shadow-lg",
        }
        card_classes.append(shadow_map.get(d.get("shadow") or "sm", "shadow-sm"))

        # ---- Unique ids for aria + accordion ----
        base_id = d.get("anchor_id") or f"pricing-card-{uuid.uuid4().hex[:10]}"
        context["pricing_card_heading_id"] = f"{base_id}-heading"
        context["pricing_card_accordion_id"] = f"{base_id}-defs"

        # ---- Export computed class strings ----
        context["pricing_card_wrapper_classes"] = " ".join(
            c for c in wrapper_classes if c.strip()
        )
        context["pricing_card_card_classes"] = " ".join(
            c for c in card_classes if c.strip()
        )
        context["pricing_card_body_padding"] = d.get("padding") or "p-3"

        # ---- Inline CSS custom properties ----
        # Values are either "" (Theme default) or "--rbg-..." tokens
        style_vars: list[str] = []

        def set_var(css_name: str, token: str | None):
            if token:
                style_vars.append(f"{css_name}: var({token});")

        # Base card styling vars
        set_var("--pricing-card-bg", d.get("background_color"))
        set_var("--pricing-card-border", d.get("border_color"))
        set_var("--pricing-card-text", d.get("text_color"))
        set_var("--pricing-card-heading", d.get("heading_color"))

        # Non-color sizing options
        border_width = d.get("border_width")
        border_radius = d.get("border_radius")
        if border_width:
            style_vars.append(f"--pricing-card-border-width: {border_width};")
        if border_radius:
            style_vars.append(f"--pricing-card-radius: {border_radius};")

        # ---- Accordion derived vars (only when using accordion layout) ----
        # Goal: make accordion items harmonize with the card background instead of white.
        if d.get("definitions_layout") == "accordion":
            # If no bg token is chosen, --pricing-card-bg may be unset, so we fall back
            # to your theme default token in CSS.
            fallback_bg = "var(--pricing-card-bg, var(--rbg-conifer-green))"

            # Simple dark-token list to flip mixing direction.
            # (Tune this set to match your palette.)
            DARK_BG_TOKENS = {
                "--rbg-oak-green",
                "--rbg-night-sky-blue",
                "--rbg-dark-blue",
                "--rbg-purple",
                "--rbg-red",
            }

            # If bg token isn't explicitly chosen, treat as light (conifer green default).
            is_dark_bg = bg_token in DARK_BG_TOKENS

            if is_dark_bg:
                # Slightly darker panel for dark cards (keeps it rich, avoids chalky look)
                style_vars.append(
                    f"--pricing-accordion-bg: color-mix(in srgb, {fallback_bg} 85%, black 15%);"
                )
                style_vars.append(
                    f"--pricing-accordion-border: color-mix(in srgb, {fallback_bg} 65%, white 35%);"
                )
            else:
                # Slightly lighter panel for light cards (avoids harsh white)
                style_vars.append(
                    f"--pricing-accordion-bg: color-mix(in srgb, {fallback_bg} 88%, white 12%);"
                )
                style_vars.append(
                    f"--pricing-accordion-border: color-mix(in srgb, {fallback_bg} 70%, black 30%);"
                )

            # Keep button bg in sync (Bootstrap reads these vars)
            style_vars.append(
                "--pricing-accordion-btn-bg: var(--pricing-accordion-bg);"
            )

        context["pricing_card_style_vars"] = " ".join(style_vars).strip()

        return context

    class Meta:
        template = "blocks/pricing_card_block.html"
        icon = "list-ul"
        label = "Pricing / Options Card"

