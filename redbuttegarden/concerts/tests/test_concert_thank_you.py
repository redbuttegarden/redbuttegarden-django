from django.test import Client, TestCase
from django.urls import reverse


class TestConcertThankYou(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_concert_thank_you_without_purchase(self):
        """
        Requesting the thank you page should redirect to home
        """
        response = self.client.get(reverse('concerts:thank-you'), follow=True)
        self.assertRedirects(response, '/', status_code=302)

    def test_concert_thank_you_after_purchase(self):
        """
        Thank you page should load if referred from etix.com
        """
        response = self.client.get(reverse('concerts:thank-you'), HTTP_REFERER='https://etix.com/some/other/data')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you!')
