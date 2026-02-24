from django.db import migrations


def _find_page_by_slug_under_root(Page, root_page, slug: str):
    """
    Finds the first descendant page with a matching slug under the site's root.
    Uses the tree path for site safety (multi-site friendly).
    """
    return (
        Page.objects
        .filter(path__startswith=root_page.path, slug=slug)
        .order_by("path")
        .first()
    )


def _link_internal_or_external(Page, root_page, *, label, slug=None, external_url=None, description=""):
    """
    Build a LinkBlock value dict.
    Prefers internal_page if slug resolves, otherwise external_url (if provided).
    """
    internal_page_id = None
    if slug:
        page = _find_page_by_slug_under_root(Page, root_page, slug)
        if page:
            internal_page_id = page.id

    if internal_page_id:
        return {
            "label": label,
            "description": description,
            "open_in_new_tab": False,
            "internal_page": internal_page_id,
            "external_url": "",
            "named_url": "",
            "routable_page": None,
            "route_name": "",
            "route_args_json": "",
            "route_kwargs_json": "",
        }

    # fall back
    return {
        "label": label,
        "description": description,
        "open_in_new_tab": False,
        "internal_page": None,
        "external_url": external_url or "#",
        "named_url": "",
        "routable_page": None,
        "route_name": "",
        "route_args_json": "",
        "route_kwargs_json": "",
    }


def _link_named(*, label, url_name, description=""):
    return {
        "label": label,
        "description": description,
        "open_in_new_tab": False,
        "internal_page": None,
        "external_url": "",
        "named_url": url_name,
        "routable_page": None,
        "route_name": "",
        "route_args_json": "",
        "route_kwargs_json": "",
    }


def _link_routable(Page, root_page, *, label, routable_slug, route_name, route_args=None, route_kwargs=None, description=""):
    routable = _find_page_by_slug_under_root(Page, root_page, routable_slug)
    return {
        "label": label,
        "description": description,
        "open_in_new_tab": False,
        "internal_page": None,
        "external_url": "" if routable else "#",
        "named_url": "",
        "routable_page": routable.id if routable else None,
        "route_name": route_name if routable else "",
        "route_args_json": (route_args or []),
        "route_kwargs_json": (route_kwargs or {}),
    }


def seed_navigation_settings(apps, schema_editor):
    Site = apps.get_model("wagtailcore", "Site")
    Page = apps.get_model("wagtailcore", "Page")
    NavigationSettings = apps.get_model("home", "NavigationSettings")

    for site in Site.objects.select_related("root_page").all():
        settings, _ = NavigationSettings.objects.get_or_create(site=site)

        # Only seed if empty (preserves any manual edits on existing DBs)
        if settings.navbar and len(settings.navbar) > 0:
            continue

        root = site.root_page

        # Build navbar groups mirroring your current hardcoded structure.
        # StreamField JSON-ish format: list of {"type": "...", "value": {...}}
        navbar_stream = [
            {
                "type": "group",
                "value": {
                    "heading": "Visit",
                    "key": "visit",
                    "group_link": None,
                    "links": [
                        _link_internal_or_external(Page, root, label="Plan Your Visit", slug="plan-your-garden-visit", external_url="/plan-your-garden-visit/"),
                        _link_internal_or_external(Page, root, label="General Info", slug="general-info", external_url="/general-info/"),
                        _link_internal_or_external(Page, root, label="About Us", slug="about-us", external_url="/about-us/"),
                        _link_internal_or_external(Page, root, label="Garden Maps", slug="garden-maps", external_url="/garden-maps/"),
                        _link_internal_or_external(Page, root, label="Gift Shop", slug="gift-shop", external_url="/gift-shop/"),
                        _link_internal_or_external(Page, root, label="Free Days & Events", slug="free-garden-events", external_url="/free-garden-events/"),
                        _link_internal_or_external(Page, root, label="Garden Tours", slug="garden-tours", external_url="/garden-tours/"),
                        _link_internal_or_external(Page, root, label="Poetry in the Garden", slug="poetry", external_url="/poetry/"),
                        _link_internal_or_external(Page, root, label="Themed Gardens", slug="themed-gardens", external_url="/themed-gardens/"),
                    ],
                },
            },
            {
                "type": "group",
                "value": {
                    "heading": "Collections & Gardening",
                    "key": "collections-gardening",
                    "group_link": None,
                    "links": [
                        _link_named(label="Interactive Plant Map", url_name="plants:plant-map"),
                        _link_named(label="Search Our Plant Collections", url_name="plants:collection-search"),
                        _link_internal_or_external(Page, root, label="Plant Collections Information", slug="plant-collections", external_url="/plant-collections/"),
                        _link_internal_or_external(Page, root, label="Gardening Information", slug="gardening-information", external_url="/gardening-information/"),
                        _link_internal_or_external(Page, root, label="Conservation Research", slug="conservation-research", external_url="/conservation-research/"),
                        _link_internal_or_external(Page, root, label="What's Blooming Now Blog", slug="whats-blooming-now", external_url="/whats-blooming-now/"),
                    ],
                },
            },
            {
                "type": "group",
                "value": {
                    "heading": "Events",
                    "key": "events",
                    "group_link": None,
                    "links": [
                        _link_internal_or_external(Page, root, label="Event Calendar", slug="calendar", external_url="/calendar/"),
                        _link_internal_or_external(Page, root, label="Outdoor Concert Series", slug="concerts", external_url="/concerts/"),
                        _link_internal_or_external(Page, root, label="Friends & Family Nights", slug="friends-and-family-night", external_url="/friends-and-family-night/"),
                        # Your old template used routable links off a main events page.
                        # Assuming the routable page slug is "events" (adjust if yours differs).
                        _link_routable(Page, root, label="Art Exhibits", routable_slug="events", route_name="event_by_category", route_args=["art-exhibits"]),
                        _link_routable(Page, root, label="Spring Events", routable_slug="events", route_name="event_by_category", route_args=["spring-events"]),
                        _link_routable(Page, root, label="Summer Events", routable_slug="events", route_name="event_by_category", route_args=["summer-events"]),
                        _link_routable(Page, root, label="Fall Events", routable_slug="events", route_name="event_by_category", route_args=["fall-events"]),
                        _link_routable(Page, root, label="Winter Events", routable_slug="events", route_name="event_by_category", route_args=["winter-events"]),
                    ],
                },
            },
            {
                "type": "group",
                "value": {
                    "heading": "Education",
                    "key": "education",
                    "group_link": None,
                    "links": [
                        _link_internal_or_external(Page, root, label="Classes & Workshops For Adults", slug="adult-education", external_url="/adult-education/"),
                        _link_internal_or_external(Page, root, label="Summer Camp & Classes For Kids", slug="kids-classes", external_url="/kids-classes/"),
                        _link_internal_or_external(Page, root, label="Teachers & Students", slug="teachers-and-students", external_url="/teachers-and-students/"),
                        _link_internal_or_external(Page, root, label="Boredom Busters", slug="boredom-busters", external_url="/boredom-busters/"),
                    ],
                },
            },
            {
                "type": "group",
                "value": {
                    "heading": "Get Involved",
                    "key": "get-involved",
                    "group_link": None,
                    "links": [
                        _link_internal_or_external(Page, root, label="Volunteer", slug="volunteer", external_url="/volunteer/"),
                        # "Give" is special in your template (include give-link.html). Use external_url placeholder or add a dedicated block.
                        _link_internal_or_external(Page, root, label="Give", slug=None, external_url="/give/"),
                        _link_internal_or_external(Page, root, label="Membership", slug="memberships", external_url="/memberships/"),
                        _link_internal_or_external(Page, root, label="Join Cottam Club", slug="cottam-club", external_url="/cottam-club/"),
                        _link_internal_or_external(Page, root, label="Memorials & Tributes", slug="memorials-and-tributes", external_url="/memorials-and-tributes/"),
                        _link_internal_or_external(Page, root, label="Legacy Giving", slug="legacy-giving", external_url="/legacy-giving/"),
                        _link_internal_or_external(Page, root, label="Corporate Sponsorship", slug="corporate-sponsors", external_url="/corporate-sponsors/"),
                        _link_internal_or_external(Page, root, label="Employment", slug="employment", external_url="/employment/"),
                    ],
                },
            },
            {
                "type": "group",
                "value": {
                    "heading": "Private Events",
                    "key": "private-events",
                    "group_link": None,
                    "links": [
                        _link_internal_or_external(Page, root, label="Weddings & Receptions", slug="weddings-receptions", external_url="/weddings-receptions/"),
                        _link_internal_or_external(Page, root, label="Corporate Events & Private Parties", slug="corporate-events-private-parties", external_url="/corporate-events-private-parties/"),
                        _link_internal_or_external(Page, root, label="Rental Sites", slug="rental-sites", external_url="/rental-sites/"),
                        _link_internal_or_external(Page, root, label="Rental Availability", slug="rental-availability", external_url="/rental-availability/"),
                        _link_internal_or_external(Page, root, label="Rental Pricing & Catering", slug="rental-rates-catering", external_url="/rental-rates-catering/"),
                        _link_internal_or_external(Page, root, label="Photo Policy", slug="photo-policy", external_url="/photo-policy/"),
                    ],
                },
            },
        ]

        top_links_stream = [
            {"type": "link", "value": _link_internal_or_external(Page, root, label="Join", slug="memberships", external_url="/memberships/")},
            {"type": "link", "value": _link_internal_or_external(Page, root, label="Give", slug=None, external_url="/give/")},
            {"type": "link", "value": _link_internal_or_external(Page, root, label="Volunteer", slug="volunteer", external_url="/volunteer/")},
            {
                "type": "link",
                "value": {
                    "label": "Cart Login",
                    "description": "Partner website login",
                    "open_in_new_tab": True,
                    "internal_page": None,
                    "external_url": "https://55218.blackbaudhosting.com/55218/page.aspx?pid=498",
                    "named_url": "",
                    "routable_page": None,
                    "route_name": "",
                    "route_args_json": "",
                    "route_kwargs_json": "",
                },
            },
        ]

        # Assign stream data. For use_json_field=True, Wagtail accepts plain python structures.
        settings.navbar = navbar_stream
        settings.top_links = top_links_stream

        # Choose defaults consistent with current template
        settings.show_search = True
        settings.search_placeholder = "Search"

        settings.save()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0098_navigationsettings"),
    ]

    operations = [
        migrations.RunPython(seed_navigation_settings, migrations.RunPython.noop),
    ]