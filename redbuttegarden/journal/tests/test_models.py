import json
from django.contrib.auth.models import Group
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, streamfield, inline_formset

from journal.models import JournalPage, JournalIndexPage


class JournalPageTests(WagtailPageTests):
    def test_cannot_create_journal(self):
        """
        JournalPage can only be created under JournalIndexPage.
        """
        self.assertCanNotCreateAt(Page, JournalPage)

    def test_can_create_journal_index(self):
        self.assertCanCreateAt(Page, JournalIndexPage)


class JournalInstanceTests(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        try:
            self.journal_index = JournalIndexPage(title='Journal Index Test Page',
                                                  body=json.dumps([]),
                                                  bottom_button_info=json.dumps([]))
            self.home.add_child(instance=self.journal_index)
        except:
            pass

    def test_can_create_journal(self):
        self.assertCanCreate(self.journal_index, JournalPage, nested_form_data(
            {'title': 'Journal Test Page',
             'date': '2006-10-25 14:30:59',
             'body': streamfield([
                 ('green_heading', 'Testing!'),
             ]),
             'gallery_images': inline_formset([])}
        ))

    def test_can_create_journal_index(self):
        self.assertCanCreate(self.home, JournalIndexPage, nested_form_data(
            {'title': 'Another Journal Index Test Page',
             'body': streamfield([]),
             'bottom_button_info': streamfield([])}
        ))
