from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import nested_form_data, streamfield, inline_formset, rich_text

from home.models import FAQPage, GeneralPage, GeneralIndexPage, HomePage, PlantCollectionsPage, TwoColumnGeneralPage, \
    RetailPartnerPage


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
        self.assertCanCreate(self.home, HomePage, nested_form_data(
            {'title': 'Home Test Page',
             'event_slides': inline_formset([])}
        ))

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
