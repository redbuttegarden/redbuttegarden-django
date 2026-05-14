import json
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.text import slugify
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, streamfield

from events.models import EventGeneralPage, EventIndexPage, EventPage, PolicyLink


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

    def assertCanCreateEventPageInAdmin(
        self, title: str, extra_form_data: dict | None = None
    ) -> EventPage:
        """Assert that Wagtail's typed admin create view can save an EventPage."""

        post_data = nested_form_data(
            {
                'title': title,
                'slug': slugify(title),
                'location': 'Test Location',
                'event_dates': 'January',
                'body': streamfield([
                    ('html', '<p>Testing!</p>')
                ]),
                'order_date': '2021-03-30 19:44:13.041150',
            }
        )
        post_data.update(extra_form_data or {})
        post_data['action-publish'] = 'Publish'
        add_url = reverse(
            'wagtailadmin_pages:add',
            args=['events', 'eventpage', self.event_index.id],
        )

        response = self.client.post(add_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EventPage.objects.filter(title=title).exists())
        return EventPage.objects.get(title=title)

    def test_can_create_event_index(self):
        self.assertCanCreate(self.home, EventIndexPage,
                             nested_form_data(
                                 {'title': 'Another Event Index Test Page',
                                  'body': streamfield([]),  # Need to pass empty list to avoid ValidationError
                                  'order_date': '2021-03-30 19:44:13.041150'
                                  }
                             ))

    def test_can_create_event(self):
        page = self.assertCanCreateEventPageInAdmin('Event Test Page')

        self.assertEqual(list(page.policies.all()), [])

    def test_can_create_event_with_policy(self):
        policy = PolicyLink.objects.create(
            name='Test Policy',
            link_text='Read the test policy',
        )

        page = self.assertCanCreateEventPageInAdmin(
            'Event Test Page With Policy',
            {'policies': [policy.pk]},
        )

        self.assertEqual(list(page.policies.all()), [policy])

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
