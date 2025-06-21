import datetime
from django.contrib.auth.models import Group
from wagtail.models import Page, Site
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, rich_text, inline_formset

from home.models import HomePage, RBGHours


class TestHomePage(WagtailPageTests):
    @classmethod
    def setUpTestData(cls):
        get_image_model().objects.create(title='Test image', file=get_test_image_file())

        """
        Create a test RBGHours object that should display the hours as 9AM-5PM for Monday to Friday, months May-August
        """
        RBGHours.objects.create(
            name='Test Hours One',
            garden_open=datetime.time(hour=9, minute=0),
            garden_close=datetime.time(hour=17, minute=0),
            additional_message='Hours One additional message',
            additional_emphatic_mesg='Hours One emphatic message',
            garden_open_message='Hours One garden open message',
            garden_closed_message='Hours One garden close message',
            days_of_week=[1, 2, 3, 4, 5],
            months_of_year=[5, 6, 7, 8],
        )
        """
        Create a test RBGHours object that should display the hours as 10AM-8PM for Sunday to Friday, months January & 
        May-August
        """
        RBGHours.objects.create(
            name='Test Hours Two',
            garden_open=datetime.time(hour=10, minute=0),
            garden_close=datetime.time(hour=20, minute=0),
            additional_message='Hours Two additional message',
            additional_emphatic_mesg='Hours Two emphatic message',
            garden_open_message='Hours Two garden open message',
            garden_closed_message='Hours Two garden close message',
            days_of_week=[0, 1, 2, 3, 4, 5],
            months_of_year=[0, 5, 6, 7, 8],
        )
        """
        Create a test RBGHours object that should display the hours as 7:30AM-8:30PM for Saturday & Sunday, months 
        August-November
        """
        RBGHours.objects.create(
            name='Test Hours Three',
            garden_open=datetime.time(hour=7, minute=30),
            garden_close=datetime.time(hour=20, minute=30),
            additional_message='Hours Three additional message',
            additional_emphatic_mesg='Hours Three emphatic message',
            garden_open_message='Hours Three garden open message',
            garden_closed_message='Hours Three garden close message',
            days_of_week=[0, 6],
            months_of_year=[8, 9, 10, 11],
        )

    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_can_create_home(self):
        rbg_hour = RBGHours.objects.create(name="Test Hours")
        self.assertCanCreate(self.home, HomePage, nested_form_data(
            {'title': 'Home Test Page',
             'rbg_hours': inline_formset([{'hours': rbg_hour.id, 'ORDER': 0}]),
             'event_slides': inline_formset([])}
        ))

    def test_home_page(self):
        home_page = HomePage(owner=self.user,
                             title='Home Test Page',
                             hours_section_text=rich_text('<p>Example hours section text.</p>')
                             )
        self.home.add_child(instance=home_page)
        home_page.save_revision().publish()
        response = self.client.get(home_page.url, follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf8')
        self.assertIn('Example hours section text.', html)
