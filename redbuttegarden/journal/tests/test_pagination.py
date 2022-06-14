import json

from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import inline_formset

from journal.models import JournalIndexPage, JournalPage


class JournalIndexPagePaginationTests(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        try:
            self.journal_index = JournalIndexPage(title='Journal Index Test Page',
                                                  slug='journal-index-test-page',
                                                  body=json.dumps([]),
                                                  bottom_button_info=json.dumps([]))
            self.home.add_child(instance=self.journal_index)
        except:
            pass

    def test_nav_control_display(self):
        """
        Page nav buttons should only be displayed when there are more
        than 9 child pages.
        """
        for num in range(9):
            child_page = JournalPage(title=f'Child Page {str(num)}')
            self.journal_index.add_child(instance=child_page)
            response = self.client.get('/journal-index-test-page', follow=True)
            self.assertNotContains(response, "next")
            self.assertNotContains(response, "previous")

        # After adding the 10th child, the nav buttons should appear
        child_page = JournalPage(title=f'Child Page 10')
        self.journal_index.add_child(instance=child_page)
        response = self.client.get('/journal-index-test-page', follow=True)
        self.assertContains(response, "next")
        self.assertContains(response, "previous")
