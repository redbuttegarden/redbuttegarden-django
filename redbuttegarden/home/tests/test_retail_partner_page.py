import json
from django.contrib.auth.models import Group
from wagtail.models import Page
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailPageTests, get_user_model

from home.models import RetailPartnerPage


class TestRetailPartnerPage(WagtailPageTests):
    def setUp(self):
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        self.image = get_image_model().objects.create(title='Test image', file=get_test_image_file())

    def test_retail_partner_with_three_retail_partners(self):
        """
        All three retail partners should exist within a div with the classes "tan-bg" and "row".
        There should not be a div with class "default"
        """
        retail_partner_page = RetailPartnerPage(owner=self.user,
                                                title='Retail Partner Test Page',
                                                banner=self.image,
                                                body=json.dumps([
                                                    {'type': 'green_heading', 'value': 'Testing!'}
                                                ]),
                                                retail_partners=json.dumps([
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'First Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }},
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'Second Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }},
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'Third Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }}
                                                ]))
        Page.objects.get(slug='home').add_child(instance=retail_partner_page)
        retail_partner_page.save_revision().publish()
        response = self.client.get('/retail-partner-test-page', follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf8')
        self.assertIn('<div class="tan-bg row">', html)
        self.assertNotIn('<div class="default row">', html)

    def test_retail_partner_with_four_retail_partners(self):
        """
        The first three retail partners should exist within a div with the classes "tan-bg" and "row".
        The fourth partner should be contained in a div with the class "default" rather than "tan-bg"
        """
        retail_partner_page = RetailPartnerPage(owner=self.user,
                                                title='Retail Partner Test Page',
                                                banner=self.image,
                                                body=json.dumps([
                                                    {'type': 'green_heading', 'value': 'Testing!'}
                                                ]),
                                                retail_partners=json.dumps([
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'First Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }},
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'Second Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }},
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'Third Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }},
                                                    {'type': 'retail_partner',
                                                     'value': {
                                                         'name': 'Fourth Test Partner',
                                                         'addresses': [
                                                             {'street_address': '123 Test Lane',
                                                              'city': 'Test City',
                                                              'zipcode': 12345,
                                                              'phone': '(123) 123-1234'},
                                                         ],
                                                         'url': 'https://example.com',
                                                         'info': '<p>Testing!</p>'
                                                     }}
                                                ]))
        Page.objects.get(slug='home').add_child(instance=retail_partner_page)
        retail_partner_page.save_revision().publish()
        response = self.client.get('/retail-partner-test-page', follow=True)
        self.assertEqual(response.status_code, 200)
        # The HTML Code here represents the first 3 retail partners
        self.assertContains(response, """<div class="tan-bg row">\n            \n                <div class="col-md-4">\n                    \n\n<h3 class="green">First Test Partner</h3>\n\n\n    <h6>123 Test Lane, Test City, 12345\n    -\n    <a href="tel:(123) 123-1234">(123) 123-1234</a>\n</h6>\n\n\n<p><a href="https://example.com">https://example.com</a></p>\n\n<p>Testing!</p>\n\n                </div>\n\n                \n            \n                <div class="col-md-4">\n                    \n\n<h3 class="green">Second Test Partner</h3>\n\n\n    <h6>123 Test Lane, Test City, 12345\n    -\n    <a href="tel:(123) 123-1234">(123) 123-1234</a>\n</h6>\n\n\n<p><a href="https://example.com">https://example.com</a></p>\n\n<p>Testing!</p>\n\n                </div>\n\n                \n            \n                <div class="col-md-4">\n                    \n\n<h3 class="green">Third Test Partner</h3>\n\n\n    <h6>123 Test Lane, Test City, 12345\n    -\n    <a href="tel:(123) 123-1234">(123) 123-1234</a>\n</h6>\n\n\n<p><a href="https://example.com">https://example.com</a></p>\n\n<p>Testing!</p>\n\n                </div>\n\n                \n                    </div>""",
                            count=1, html=True)
        # The HTML Code here represents the fourth retail partner. It should also include 2 instances of "Your business could be here!"
        self.assertContains(response, """<div class="default row">\n                \n            \n                <div class="col-md-4">\n                    \n\n<h3 class="green">Fourth Test Partner</h3>\n\n\n    <h6>123 Test Lane, Test City, 12345\n    -\n    <a href="tel:(123) 123-1234">(123) 123-1234</a>\n</h6>\n\n\n<p><a href="https://example.com">https://example.com</a></p>\n\n<p>Testing!</p>\n\n                </div>\n\n                \n            \n\n            \n            \n                \n                \n                    <div class="col-md-4">\n                        <h3 class="green">Your business could be here!</h3>\n                    </div>\n                    <div class="col-md-4">\n                        <h3 class="green">Your business could be here!</h3>\n                    </div>\n                    \n            \n        </div>""",
                            count=1, html=True)
