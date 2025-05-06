import datetime
import json
from django.contrib.auth.models import Group
from wagtail.models import Page
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, rich_text

from home.models import HomePage, RBGHours, RBGHoursOrderable


class TestHomePage(WagtailPageTests):
    def setUpTestData(cls):
        cls.root_page = Page.objects.first()
        cls.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        cls.user.groups.add(Group.objects.get(name="Moderators"))
        cls.client.force_login(cls.user)

        cls.image = get_image_model().objects.create(title='Test image', file=get_test_image_file())

        """
        Create a test RBGHours object that should display the hours as 9AM-5PM for Monday to Friday, months May-August
        """
        cls.hours_one = RBGHours.objects.create(
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
        cls.hours_two = RBGHours.objects.create(
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
        cls.hours_three = RBGHours.objects.create(
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

    def test_can_create_home_page(self):
        self.assertCanCreate(self.root_page, HomePage, nested_form_data({
            'title': 'Home Test Page',
            'hours_section_text': rich_text('<p>Example hours section text.</p>'),
        }))

    def test_home_page(self):
        home_page = HomePage(owner=self.user,
                             title='Home Test Page',
                             hours_section_text=rich_text('<p>Example hours section text.</p>')
                             )
        self.root_page.add_child(instance=home_page)
        home_page.save_revision().publish()
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf8')
        self.assertIn('<p>Example hours section text.</p>', html)
