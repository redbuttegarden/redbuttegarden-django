import json
from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import nested_form_data, streamfield

from events.models import EventIndexPage, EventPage, EventGeneralPage


class EventPageTests(WagtailPageTests):
    def test_can_create_event_index(self):
        self.assertCanCreateAt(Page, EventIndexPage)

    def test_cannot_create_event(self):
        """
        Event pages can only be created under EventIndexPages or GeneralIndexPages
        """
        self.assertCanNotCreateAt(Page, EventPage)

    def test_canot_create_event_general(self):
        """
        EventGeneral pages can only be created under EventIndexPages or GeneralIndexPages
        """
        self.assertCanNotCreateAt(Page, EventGeneralPage)


class EventPageInstanceTests(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        try:
            self.event_index = EventIndexPage(title='Event Index Test Page',
                                              body=json.dumps([
                                                  {u'type': u'html', u'value': '<p>Testing!</p>'}
                                              ]))
            self.home.add_child(instance=self.event_index)
        except:
            raise

    def test_can_create_event_index(self):
        self.assertCanCreate(self.home, EventIndexPage,
                             nested_form_data(
                                 {'title': 'Another Event Index Test Page',
                                  'body': streamfield([]),  # Need to pass empty list to avoid ValidationError
                                  'order_date': '2021-03-30 19:44:13.041150'
                                  }
                             ))

    def test_can_create_event(self):
        self.assertCanCreate(self.event_index, EventPage,
                             nested_form_data(
                                 {'title': 'Event Test Page',
                                  'location': 'Test Location',
                                  'event_dates': 'January',
                                  'body': streamfield([
                                      ('html', '<p>Testing!</p>')
                                  ]),
                                  'order_date': '2021-03-30 19:44:13.041150'
                                  }
                             ))

    def test_can_create_event_general(self):
        self.assertCanCreate(self.event_index, EventGeneralPage,
                             nested_form_data(
                                 {'title': 'Event General Test Page',
                                  'event_dates': 'January',
                                  'body': streamfield([
                                      ('html', '<p>Testing!</p>')
                                  ]),
                                  'order_date': '2021-03-30 19:44:13.041150'
                                  }
                             ))