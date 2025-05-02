import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from django.http import HttpResponse
from wagtail.admin.rich_text.converters.html_to_contentstate import InlineStyleElementHandler
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("register_rich_text_features")
def register_code_styling(features):
    """Add the code to the richtext editor"""
    feature_name = "code"
    type_ = "CODE"
    tag = "code"

    control = {
        "type": type_,
        "label": "</>",
        "description": "Code"
    }

    features.register_editor_plugin(
        "draftail", feature_name, draftail_features.InlineStyleFeature(control)
    )

    db_conversion = {
        "from_database_format": {tag: InlineStyleElementHandler(type_)},
        "to_database_format": {"style_map": {type_: {"element": tag}}}
    }

    features.register_converter_rule("contentstate", feature_name, db_conversion)


@hooks.register('before_serve_document')
def serve_pdf(document, request):
    if document.file_extension != 'pdf':
        return
    response = HttpResponse(document.file.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'filename="' + document.file.name.split('/')[-1] + '"'
    if request.GET.get('download', False) in [True, 'True', 'true']:
        response['Content-Disposition'] = 'attachment; ' + response['Content-Disposition']
    return response


@hooks.register('register_help_menu_item')
def register_rbg_style_guide_menu_item():
    return MenuItem(name='rbg_style_guide', label='RBG Style Guide',
                        url='https://uofu.box.com/s/gb5psi7cn82tm62a8ndmouv53y47nre1', icon_name='link')
