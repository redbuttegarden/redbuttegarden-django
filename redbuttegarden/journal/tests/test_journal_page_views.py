from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.models import Page
from wagtail.images.tests.utils import Image, get_test_image_file

from journal.models import JournalCategory, JournalIndexPage, JournalPage, JournalPageTag


class TestJournalIndex(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')

    def test_journal_index_page(self):
        journal_index = JournalIndexPage(owner=self.user,
                                         slug='journal-index-page',
                                         title='Journal Index Page')
        self.root_page.add_child(instance=journal_index)
        journal_index.save_revision().publish()

        response = self.client.get(journal_index.url, follow=True)
        self.assertEqual(response.status_code, 200)


class TestEventPage(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.journal_index = JournalIndexPage(owner=self.user,
                                              slug='journal-index-page',
                                              title='Journal Index Page')
        self.root_page.add_child(instance=self.journal_index)
        self.journal_index.save_revision().publish()

    def test_event_page(self):
        journal_page = JournalPage(owner=self.user,
                                   slug='journal-page',
                                   title='Journal Page')
        self.journal_index.add_child(instance=journal_page)
        journal_page.save_revision().publish()

        response = self.client.get(journal_page.url, follow=True)
        self.assertEqual(response.status_code, 200)


class TestJournalCategory(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.journal_index = JournalIndexPage(owner=self.user,
                                              slug='journal-index-page',
                                              title='Journal Index Page')
        self.root_page.add_child(instance=self.journal_index)
        self.journal_index.save_revision().publish()

        self.fall_category = JournalCategory(name="Fall", slug="fall")
        self.spring_category = JournalCategory(name="Spring", slug="spring")
        self.fall_category.save()
        self.spring_category.save()

        self.journal_page_fall = JournalPage(owner=self.user,
                                             slug='journal-page-fall',
                                             title='Fall Journal Page')
        self.journal_index.add_child(instance=self.journal_page_fall)
        self.journal_page_fall.save_revision()
        self.journal_page_fall.categories = [self.fall_category.pk]
        self.journal_page_fall.save_revision().publish()

        self.journal_page_spring = JournalPage(owner=self.user,
                                               slug='journal-page-spring',
                                               title='Spring Journal Page')
        self.journal_index.add_child(instance=self.journal_page_spring)
        self.journal_page_spring.save_revision()
        self.journal_page_spring.categories = [self.spring_category.pk]
        self.journal_page_spring.save_revision().publish()

    def test_category_view(self):
        cat_url = self.journal_index.reverse_subpage('post_by_category', args=(self.fall_category.slug,))
        response = self.client.get(self.journal_index.url + cat_url)
        html = response.content.decode('utf8')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<div class="eventname">Fall Journal Page</div>', html)
        self.assertNotIn('<div class="eventname">Spring Journal Page</div>', html)
