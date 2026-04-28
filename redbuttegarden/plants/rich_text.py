import re

from django.utils.html import escape
from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters.html_to_contentstate import LinkElementHandler
from wagtail.rich_text import LinkHandler
from wagtail.whitelist import check_url

from .models import Collection, Species


PLANT_LINK_URL_PATTERN = re.compile(
    r"^https?://[^/]+/plants/(?P<link_type>species|collection)/(?P<id>\d+)/?$"
    r"|^/plants/(?P<relative_link_type>species|collection)/(?P<relative_id>\d+)/?$"
)


def get_plant_link_type_from_url(url, id_):
    if not url or id_ is None:
        return None

    match = PLANT_LINK_URL_PATTERN.match(url)
    if not match:
        return None

    link_type = match.group("link_type") or match.group("relative_link_type")
    url_id = match.group("id") or match.group("relative_id")
    if str(id_) != url_id:
        return None

    return link_type


def plant_link_entity(props):
    id_ = props.get("id")
    link_type = props.get("linkType") or get_plant_link_type_from_url(
        props.get("url"),
        id_,
    )

    if id_ is not None and link_type in {"species", "collection"}:
        return DOM.create_element(
            "a",
            {
                "linktype": link_type,
                "id": id_,
            },
            props["children"],
        )

    link_props = {}
    if id_ is not None:
        link_props["linktype"] = "page"
        link_props["id"] = id_
    else:
        link_props["href"] = check_url(props.get("url"))

    return DOM.create_element("a", link_props, props["children"])


class BasePlantLinkHandler(LinkHandler):
    model = None

    @classmethod
    def expand_db_attributes(cls, attrs):
        try:
            instance = cls.get_instance(attrs)
        except cls.model.DoesNotExist:
            return "<a>"

        return f'<a href="{escape(instance.get_absolute_url())}">'


class SpeciesLinkHandler(BasePlantLinkHandler):
    identifier = "species"
    model = Species

    @classmethod
    def get_model(cls):
        return cls.model


class CollectionLinkHandler(BasePlantLinkHandler):
    identifier = "collection"
    model = Collection

    @classmethod
    def get_model(cls):
        return cls.model


class BasePlantEditorHTMLLinkHandler:
    model = None
    identifier = None

    @staticmethod
    def get_db_attributes(tag):
        return {"id": tag["data-id"]}

    @classmethod
    def expand_db_attributes(cls, attrs):
        try:
            instance = cls.model.objects.get(id=attrs["id"])
        except cls.model.DoesNotExist:
            return f'<a data-linktype="{cls.identifier}">'

        return (
            f'<a data-linktype="{cls.identifier}" '
            f'data-id="{instance.pk}" '
            f'href="{escape(instance.get_absolute_url())}">'
        )


class SpeciesEditorHTMLLinkHandler(BasePlantEditorHTMLLinkHandler):
    identifier = "species"
    model = Species


class CollectionEditorHTMLLinkHandler(BasePlantEditorHTMLLinkHandler):
    identifier = "collection"
    model = Collection


class BasePlantLinkElementHandler(LinkElementHandler):
    model = None
    link_type = None

    def get_attribute_data(self, attrs):
        try:
            instance = self.model.objects.get(id=attrs["id"])
        except self.model.DoesNotExist:
            return {
                "id": int(attrs["id"]),
                "parentId": None,
                "url": None,
                "linkType": self.link_type,
            }

        return {
            "id": instance.pk,
            "parentId": None,
            "url": instance.get_absolute_url(),
            "linkType": self.link_type,
        }


class SpeciesLinkElementHandler(BasePlantLinkElementHandler):
    model = Species
    link_type = "species"


class CollectionLinkElementHandler(BasePlantLinkElementHandler):
    model = Collection
    link_type = "collection"
