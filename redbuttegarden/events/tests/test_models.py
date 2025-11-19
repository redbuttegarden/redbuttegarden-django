import json
from django.contrib.auth.models import Group
from django.urls import reverse
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, streamfield

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
    def assertCanCreateWithM2M(self, parent, model, post_data):
            # Build the correct Wagtail admin URL for adding a child page
            add_url = reverse('wagtailadmin_pages:add_subpage', args=[parent.id])

            # Add required hidden fields for Wagtail page creation
            post_data.update({
                'action': 'publish',  # or 'save_draft'
            })

            # Simulate POST to create the page
            response = self.client.post(add_url, post_data, follow=True)
            self.assertEqual(response.status_code, 200, f"Expected success page, got {response.status_code}")

            # Fetch the created page
            page = model.objects.last()

            # Rebuild the form and save M2M fields explicitly
            form_class = model.get_edit_handler().get_form_class()
            form = form_class(post_data, instance=page)
            if form.is_valid():
                form.save_m2m()

            return page


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
        self.assertCanCreateWithM2M(self.event_index, EventPage,
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