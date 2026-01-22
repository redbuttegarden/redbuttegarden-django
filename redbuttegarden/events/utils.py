# events/utils.py
import json
import re
from decimal import Decimal, InvalidOperation
from django.utils.html import strip_tags
from django.utils.timezone import is_aware

PRICE_RE = re.compile(r"(?P<num>\d+(?:[.,]\d+)?)")


def _as_iso(dt, date_only=False):
    """
    Return ISO representation for a datetime.
    - If date_only is True, returns 'YYYY-MM-DD' (date-only).
    - Otherwise returns full ISO (preserves timezone offset when present).
    """
    if not dt:
        return None
    if date_only:
        # dt may be a date or datetime; ensure we use date()
        return dt.date().isoformat()
    return dt.isoformat()


def parse_amount_from_text(text):
    """
    Try to extract a Decimal from a human-entered price string.
    Returns Decimal or None. Interprets 'free' as 0.00.
    Examples it will parse: '$35', '35.00', '35 - 45' -> returns first numeric 35.
    """
    if not text:
        return None
    txt = text.strip().lower()
    if "free" in txt:
        return Decimal("0.00")
    # remove thousands separator commas to aid parsing
    cleaned = text.replace(",", "")
    m = PRICE_RE.search(cleaned)
    if not m:
        return None
    try:
        return Decimal(m.group("num"))
    except InvalidOperation:
        return None


def _price_offer_dict(
    name_text=None,
    amount_decimal=None,
    display_text=None,
    purchase_url=None,
    valid_from=None,
    valid_through=None,
    currency="USD",
    date_only=False,
):
    """
    Build an Offer dict. If date_only=True, validFrom/validThrough will be date-only
    strings (YYYY-MM-DD); otherwise full ISO datetimes are used.
    """
    offer = {"@type": "Offer"}

    if purchase_url:
        offer["url"] = purchase_url

    if valid_from:
        offer["validFrom"] = _as_iso(valid_from, date_only=date_only)
    if valid_through:
        offer["validThrough"] = _as_iso(valid_through, date_only=date_only)

    if amount_decimal is not None:
        offer["price"] = str(amount_decimal)
        offer["priceCurrency"] = currency
    else:
        if display_text:
            txt = display_text.strip()
            if txt.lower().startswith("free"):
                offer["price"] = "0"
                offer["priceCurrency"] = currency
                offer["priceSpecification"] = {
                    "@type": "PriceSpecification",
                    "name": txt,
                }
            else:
                offer["priceSpecification"] = {
                    "@type": "PriceSpecification",
                    "name": txt,
                }

    if name_text:
        offer["name"] = name_text

    return offer


def build_structured_event_dict(page, request=None):
    """
    Build schema.org Event dict.
    If both page.display_times_on_index and page.display_times_on_detail are False,
    structured date/time values will be emitted as date-only (YYYY-MM-DD).
    """
    # determine whether to emit times in the JSON-LD:
    # If either flag is True, include times; only omit times if BOTH are False.
    display_index = getattr(page, "display_times_on_index", False)
    display_detail = getattr(page, "display_times_on_detail", False)
    include_times = bool(display_index or display_detail)
    date_only = not include_times

    data = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": page.title,
        "description": strip_tags(
            getattr(page, "search_description", None)
            or getattr(page, "sub_heading", "")
            or ""
        )[:300],
        "url": (
            request.build_absolute_uri(page.get_url())
            if request is not None
            else page.get_url()
        ),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {
            "@type": "Place",
            "name": "Red Butte Garden & Arboretum"
            + (
                f" - {getattr(page, 'location', '')}"
                if getattr(page, "location", None)
                else ""
            ),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "300 Wakara Way",
                "addressLocality": "Salt Lake City",
                "addressRegion": "UT",
                "postalCode": "84108",
                "addressCountry": "US",
            },
        },
        "organizer": {
            "@type": "Organization",
            "name": "Red Butte Garden & Arboretum",
            "url": "https://redbuttegarden.org/",
        },
    }

    # image (try to include rendition; skip on failure)
    try:
        thumbnail = getattr(page, "thumbnail", None)
        if thumbnail:
            rendition = thumbnail.get_rendition("fill-1200x630")
            img_url = rendition.url
            if request is not None:
                img_url = request.build_absolute_uri(img_url)
            data["image"] = [img_url]
    except Exception:
        pass

    # start / end date: use date_only flag when serializing
    if getattr(page, "start_datetime", None):
        data["startDate"] = _as_iso(page.start_datetime, date_only=date_only)
    if getattr(page, "end_datetime", None):
        data["endDate"] = _as_iso(page.end_datetime, date_only=date_only)

    # performer
    if getattr(page, "instructor", None):
        data["performer"] = {"@type": "Person", "name": page.instructor}

    # offers - use date_only for validFrom/validThrough as well
    offers = []
    if (getattr(page, "member_cost_amount", None) is not None) or getattr(
        page, "member_cost", None
    ):
        offers.append(
            _price_offer_dict(
                name_text="Garden Members",
                amount_decimal=getattr(page, "member_cost_amount", None),
                display_text=getattr(page, "member_cost", None),
                purchase_url=(
                    getattr(page, "purchase_url", None)
                    or (
                        request.build_absolute_uri(page.get_url())
                        if request is not None
                        else None
                    )
                ),
                valid_from=(
                    getattr(page, "start_datetime", None)
                    or getattr(page, "order_date", None)
                ),
                valid_through=getattr(page, "end_datetime", None),
                date_only=date_only,
            )
        )

    if (getattr(page, "public_cost_amount", None) is not None) or getattr(
        page, "public_cost", None
    ):
        offers.append(
            _price_offer_dict(
                name_text="General Public",
                amount_decimal=getattr(page, "public_cost_amount", None),
                display_text=getattr(page, "public_cost", None),
                purchase_url=(
                    getattr(page, "purchase_url", None)
                    or (
                        request.build_absolute_uri(page.get_url())
                        if request is not None
                        else None
                    )
                ),
                valid_from=(
                    getattr(page, "start_datetime", None)
                    or getattr(page, "order_date", None)
                ),
                valid_through=getattr(page, "end_datetime", None),
                date_only=date_only,
            )
        )

    if offers:
        data["offers"] = offers

    # Keep the legacy human-readable schedule if present
    if getattr(page, "event_dates", None):
        data["eventSchedule"] = strip_tags(getattr(page, "event_dates"))

    return data


def build_structured_event_json(page, request=None):
    """
    Return a JSON string suitable for embedding in an ld+json script tag.
    Uses default=str so datetimes/decimals are serialized to strings.
    """
    return json.dumps(
        build_structured_event_dict(page, request=request),
        default=str,
        ensure_ascii=False,
    )
