"""
The social media page doesn't use a wagtail model so we just want to load it to make sure there are no errors
"""
from wagtail.tests.utils import WagtailPageTests


class SocialMediaPageTest(WagtailPageTests):
    def test_social_media(self):
        response = self.client.get('/social-media', follow=True)

        self.assertEqual(response.status_code, 200)
