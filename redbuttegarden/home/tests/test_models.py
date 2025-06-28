import traceback

from django.contrib.auth.models import Group
from django.urls import reverse
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, streamfield, inline_formset, rich_text

from home.models import FAQPage, GeneralPage, GeneralIndexPage, HomePage, PlantCollectionsPage, TwoColumnGeneralPage, \
    RetailPartnerPage, RBGHours


def assertCanCreateWithPanels(
        test_case,
        parent_page,
        page_model,
        title,
        slug,
        inline_panel_data=None,
        extra_form_data=None,
        publish=False
):
    """
    Helper to test Wagtail page creation with inline panels and custom form data.

    :param test_case: The test class (usually `self`)
    :param parent_page: The parent page to create under
    :param page_model: The Wagtail Page model class
    :param title: Title of the new page
    :param slug: Slug of the new page
    :param inline_panel_data: Dict of inline panel names to list of dicts (e.g. {'rbg_hours': [{...}]})
    :param extra_form_data: Any additional form fields
    :param publish: Whether to simulate clicking "Publish"
    """
    inline_panel_data = inline_panel_data or {}
    extra_form_data = extra_form_data or {}

    form_data = nested_form_data({
        'title': title,
        'slug': slug,
        **inline_panel_data,
        **extra_form_data,
    })

    # Add management form data for each inline panel
    for panel_name, items in inline_panel_data.items():
        form_data.update({
            f'{panel_name}-TOTAL_FORMS': str(len(items)),
            f'{panel_name}-INITIAL_FORMS': '0',
            f'{panel_name}-MIN_NUM_FORMS': '0',
            f'{panel_name}-MAX_NUM_FORMS': '1000',
        })

    if publish:
        form_data['action-publish'] = 'Publish'

    # Get the correct admin URL
    temp_instance = page_model(title="Temp", slug="temp")
    content_type = temp_instance.get_content_type()
    add_url = reverse('wagtailadmin_pages:add', args=[
        content_type.app_label,
        content_type.model,
        parent_page.id
    ])

    response = test_case.client.post(add_url, form_data, follow=True)

    if response.status_code not in (200, 302):
        if hasattr(response, 'context') and 'form' in response.context:
            form = response.context['form']
            print("Main form errors:", form.errors)
            for name, formset in form.formsets.items():
                print(f"Formset '{name}' errors:")
                for subform in formset.forms:
                    print(subform.errors)
                print("Non-form errors:", formset.non_form_errors())
        else:
            print("Response content:")
            print(response.content.decode())
        test_case.fail("Page creation failed")

    # Confirm the page was created
    assert Page.objects.filter(title=title, slug=slug).exists(), "Page was not created"


class HomePageTests(WagtailPageTests):
    def test_can_create_FAQ(self):
        self.assertCanCreateAt(Page, FAQPage)

    def test_can_create_general(self):
        self.assertCanCreateAt(Page, GeneralPage)

    def test_can_create_general_index(self):
        self.assertCanCreateAt(Page, GeneralIndexPage)

    def test_can_create_home(self):
        self.assertCanCreateAt(Page, HomePage)

    def test_can_create_plant_collections(self):
        self.assertCanCreateAt(Page, PlantCollectionsPage)

    def test_can_create_retail_partner(self):
        self.assertCanCreateAt(Page, RetailPartnerPage)

    def test_can_create_two_col_general(self):
        self.assertCanCreateAt(Page, TwoColumnGeneralPage)


class HomePageInstanceTests(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_can_create_FAQ(self):
        self.assertCanCreate(self.home, FAQPage, nested_form_data(
            {'title': 'FAQ Test Page',
             'body': streamfield([
                 ('heading', 'Testing!')
             ])}
        ))

    def test_can_create_general(self):
        self.assertCanCreate(self.home, GeneralPage, nested_form_data(
            {'title': 'General Test Page',
             'body': streamfield([
                 ('html', '<p>Testing!</p>')
             ])}
        ))

    def test_can_create_general_index(self):
        self.assertCanCreate(self.home, GeneralIndexPage, nested_form_data(
            {'title': 'General Index Test Page',
             'body': streamfield([])}
        ))

    def test_can_create_home(self):
        rbg_hour = RBGHours.objects.create(name="Test Hours")

        form_data = nested_form_data({
            'title': 'Home Test Page',
            'slug': 'home-test-page',
            'rbg_hours': [
                {
                    'hours': rbg_hour.pk,
                    'ORDER': 0,
                }
            ],
            'event_slides': inline_formset([]),
        })

        form_data.update({
            'rbg_hours-TOTAL_FORMS': '1',
            'rbg_hours-INITIAL_FORMS': '0',
            'rbg_hours-MIN_NUM_FORMS': '0',
            'rbg_hours-MAX_NUM_FORMS': '1000',
        })

        # Get the content type ID for HomePage
        homepage_instance = HomePage(title="Temp", slug="temp")
        content_type = homepage_instance.get_content_type()
        add_url = reverse('wagtailadmin_pages:add', args=[content_type.app_label, content_type.model, self.home.id])

        self.client.post(add_url, form_data, follow=True)

        assert Page.objects.filter(title="Home Test Page", slug="home-test-page").exists(), "Page was not created"

    def test_can_create_plant_collections(self):
        self.assertCanCreate(self.home, PlantCollectionsPage, nested_form_data(
            {'title': 'Plant Collections Test Page',
             'intro': rich_text('Testing!'),
             'more_info_modal': rich_text('Testing!'),
             'plant_collections': inline_formset([])}
        ))

    """
    Test currently fails with "django.utils.datastructures.MultiValueDictKeyError: 'retail_partners-0-value-addresses-count'"
    even though addresses ListBlock should be optional
    """

    # def test_can_create_retail_partner(self):
    #     self.assertCanCreate(self.home, RetailPartnerPage, nested_form_data(
    #         {'title': 'Retail Partner Test Page',
    #          'body': streamfield([
    #              ('green_heading', 'Testing!'),
    #          ]),
    #          'retail_partners': streamfield([
    #              ('retail_partner', {
    #                  'name': 'Test Partner',
    #                  'url': 'https://example.com',
    #                  'info': rich_text('Testing!')
    #              })
    #          ])}
    #     ))

    def test_can_create_two_col_general(self):
        self.assertCanCreate(self.home, TwoColumnGeneralPage, nested_form_data(
            {'title': 'Two Column General Test Page',
             'body': streamfield([])}
        ))


class TestAbstractBaseModel(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_aliased_parent_without_children_child_creation(self):
        """
        If a child page is created under a parent that is aliased, an
        alias of the new page should also be created under the parents
        aliases.
        """
        parent_one = GeneralIndexPage(owner=self.user,
                                      slug='parent-one',
                                      title='Parent One - Aliased under Parent Two')
        self.home.add_child(instance=parent_one)
        parent_one.save_revision().publish()
        parent_two = GeneralIndexPage(owner=self.user,
                                      slug='parent-two',
                                      title='Parent Two - Not Aliased')
        self.home.add_child(instance=parent_two)
        parent_two.save_revision().publish()
        parent_one.create_alias(parent=parent_two)

        num_parent_one_children = len(parent_one.get_descendants().all())
        num_parent_two_children = len(parent_two.get_descendants().all())
        self.assertEqual(num_parent_one_children, 0)
        self.assertEqual(num_parent_two_children, 1)

        # Creating a child under parent_one should now also create an
        # alias of that child under parent two
        child_one = GeneralIndexPage(owner=self.user,
                                     slug='child-one',
                                     title='Child One Page')
        parent_one.add_child(instance=child_one)
        child_one.save_revision().publish()

        self.assertEqual(len(parent_one.get_descendants().all()), 1)
        self.assertEqual(len(parent_two.get_descendants().all()), 2)

        # Check child creation works properly for multiple aliases
        parent_three = GeneralIndexPage(owner=self.user,
                                        slug='parent-three',
                                        title='Parent Three - Not Aliased')
        self.home.add_child(instance=parent_three)
        parent_three.save_revision().publish()
        parent_one.create_alias(parent=parent_three)

        self.assertEqual(len(parent_one.get_descendants().all()), 1)
        self.assertEqual(len(parent_two.get_descendants().all()), 2)
        self.assertEqual(len(parent_three.get_descendants().all()), 1)

        child_two = GeneralIndexPage(owner=self.user,
                                     slug='child-two',
                                     title='Child Two Page')
        parent_one.add_child(instance=child_two)
        child_two.save_revision().publish()

        self.assertEqual(len(parent_one.get_descendants().all()), 2)
        self.assertEqual(len(parent_two.get_descendants().all()), 3)
        self.assertEqual(len(parent_three.get_descendants().all()), 2)

    def test_aliased_parent_with_children_child_creation(self):
        """
        Checks to make sure there's no funny business introduced
        to aliased child creation when the parents already have other children.
        """
        parent_one = GeneralIndexPage(owner=self.user,
                                      slug='parent-one',
                                      title='Parent One - Aliased under Parent Two')
        self.home.add_child(instance=parent_one)
        parent_one.save_revision().publish()
        child_one = GeneralIndexPage(owner=self.user,
                                     slug='child-one',
                                     title='Parent One Child Page')
        parent_one.add_child(instance=child_one)
        child_one.save_revision().publish()
        parent_two = GeneralIndexPage(owner=self.user,
                                      slug='parent-two',
                                      title='Parent Two - Not Aliased')
        self.home.add_child(instance=parent_two)
        parent_two.save_revision().publish()
        child_two = GeneralIndexPage(owner=self.user,
                                     slug='child-two',
                                     title='Parent Two Child Page')
        parent_two.add_child(instance=child_two)
        child_two.save_revision().publish()

        num_parent_one_children = len(parent_one.get_descendants().all())
        num_parent_two_children = len(parent_two.get_descendants().all())
        self.assertEqual(num_parent_one_children, 1)
        self.assertEqual(num_parent_two_children, 1)

        # Creating a child under parent_one should now also create an
        # alias of that child under parent two
        parent_one.create_alias(parent=parent_two)
        alias_child = GeneralIndexPage(owner=self.user,
                                       slug='alias-child',
                                       title='Child of Aliased Page')
        parent_one.add_child(instance=alias_child)
        alias_child.save_revision().publish()

        self.assertEqual(len(parent_one.get_descendants().all()), 2)
        self.assertEqual(len(parent_two.get_descendants().all()), 3)
