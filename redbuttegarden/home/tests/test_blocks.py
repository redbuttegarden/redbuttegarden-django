import json

from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model

from home.models import GeneralPage


class TestMultiColumnAlignedParagraphBlock(WagtailPageTests):
    def setUp(self):
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_view_one_paragraph(self):
        general_page = GeneralPage(owner=self.user,
                                   slug='general-test-page',
                                   title='General Test Page',
                                   body=json.dumps([
                                       {'type': 'multi_column_paragraph', 'value': {
                                           'alignment': 'left',
                                           'background_color': 'default',
                                           'paragraph': ['<p>Testing!</p>']
                                       }}
                                   ]))
        Page.objects.get(slug='home').add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get('/general-test-page', follow=True)
        html = response.content.decode('utf8')
        self.assertIn('<div class="col-sm-12">\n                        <p>Testing!</p>\n                    </div>', html)
