from django.test import TestCase, Client
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
import tempfile
from .models import *

# TOTAL TEST: 48

class UserProfileTests(TestCase):
    def setUp(self):

        self.reader_group = Group.objects.create(name="Reader")
        self.editor_group = Group.objects.create(name="Editor")
        self.editor_in_chief_group = Group.objects.create(name='Editor in Chief')

        self.user1 = User.objects.create_user(username="testuser1", password="testpassword")
        self.user1.groups.add(self.reader_group)

        self.user2 = User.objects.create_user(username="testuser2", password="testpassword")
        self.user2.groups.add(self.reader_group)
        self.user2.groups.add(self.editor_group)

        self.user3 = User.objects.create_user(username="testuser3", password="testpassword")
        self.user3.groups.add(self.reader_group)
        self.user3.groups.add(self.editor_group)
        self.user3.groups.add(self.editor_in_chief_group)

        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        self.profile3 = Profile.objects.create(user=self.user3)

    def test_test(self):
        self.assertEqual(123, 123)

    def test_get_profile_name(self):
        self.assertEqual(self.profile1.get_profile_name(), "profile_testuser1")
        self.assertEqual(self.profile2.get_profile_name(), "profile_testuser2")
        self.assertEqual(self.profile3.get_profile_name(), "profile_testuser3")

    def test_belong_to_method(self):

        self.assertTrue(self.profile1.belong_to("Reader"))
        self.assertFalse(self.profile1.belong_to("Editor"))
        self.assertFalse(self.profile1.belong_to("Editor"))

        self.assertTrue(self.profile2.belong_to("Reader"))
        self.assertTrue(self.profile2.belong_to("Editor"))
        self.assertFalse(self.profile2.belong_to("Editor in Chief"))

        self.assertTrue(self.profile3.belong_to("Reader"))
        self.assertTrue(self.profile3.belong_to("Editor"))
        self.assertTrue(self.profile3.belong_to("Editor in Chief"))


    def test_profile1_flags(self):
        self.assertFalse(self.profile1.is_editor)
        self.assertFalse(self.profile1.is_editor_in_chief)

    def test_profile2_flags(self):
        self.assertTrue(self.profile2.is_editor)
        self.assertFalse(self.profile2.is_editor_in_chief)

    def test_profile3_flags(self):
        self.assertTrue(self.profile3.is_editor)
        self.assertTrue(self.profile3.is_editor_in_chief)

class ArticleParagraphTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        
        self.article1 = Article.objects.create(
            title="Test article",
            author=self.user,
            for_display=True,
        )
        self.paragraph1 = Paragraph.objects.create(
            title="Test Paragraph 1",
            article=self.article1,
            text="Text of Paragraph",
            is_lead=True
            )

        self.article2 = Article.objects.create(author=self.user)
        self.paragraph2 = Paragraph.objects.create(article=self.article2)


    def test_article_auto_parameters(self):
        self.assertEqual(self.article2.title, "New article")
        self.assertFalse(self.article2.for_display)
        self.assertTrue(self.article2.pub_date)


    def test_article_auto_date(self):
        now = timezone.now()
        self.assertAlmostEqual(self.article1.pub_date, now, delta=datetime.timedelta(minutes=30))

    def test_article_publishing_in_period_methods(self):
        self.assertTrue(self.article1.published_today)
        self.assertTrue(self.article1.published_last_day)
        self.assertTrue(self.article1.published_last_week)
        self.assertTrue(self.article1.published_last_month)

    def test_paragraph_auto_parameters(self):
        self.assertEqual(self.paragraph2.title, "paragraph")
        self.assertEqual(self.paragraph2.text, "")
        self.assertFalse(self.paragraph2.is_lead)

    def test_add_second_lead_paragraph(self):
        with self.assertRaises(ValidationError):
            paragraph = Paragraph.objects.create(article=self.article1, is_lead=True)
    
class ImageModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.article = Article.objects.create(author=self.user)

    def create_temp_image(self):
        """Creates a temporary image file"""
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        temp_file.write(b"Test image content")
        temp_file.seek(0)
        return SimpleUploadedFile(temp_file.name, temp_file.read(), content_type='image/jpeg')

    def test_create_image(self):
        """Test creating an image instance"""
        temp_image = self.create_temp_image()
        image = Image.objects.create(photo=temp_image)
        self.assertTrue(isinstance(image, Image))
        self.assertEqual(image.photo.name, "article_images/" + temp_image.name.split('/')[-1])

    def test_str_method(self):
        """Test the __str__ method"""
        temp_image = self.create_temp_image()
        image = Image.objects.create(name="Test Image", photo=temp_image)
        self.assertEqual(str(image), "Test Image")

    def test_get_name(self):
        """Test the get_name method"""
        temp_image = self.create_temp_image()
        image = Image.objects.create(photo=temp_image)
        expected_name = "image_" + str(image.pub_date)
        self.assertEqual(image.get_name(), expected_name)

    def test_date_method(self):
        """Test the date method"""
        temp_image = self.create_temp_image()
        image = Image.objects.create(photo=temp_image)
        self.assertEqual(image.date(), image.pub_date.date())

    def test_save_method_with_provided_name(self):
        """Test the save method when name is provided"""
        temp_image = self.create_temp_image()
        image = Image(name="Custom Name", photo=temp_image)
        image.save()
        self.assertEqual(image.name, "Custom Name")
    
class TagTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.article1 = Article.objects.create(author=self.user)
        self.tag1 = Tag.objects.create(name="   test tag1")
        self.tag2 = Tag.objects.create(name="test tag2")

    def create_temp_image(self):
        """Creates a temporary image file"""
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        temp_file.write(b"Test image content")
        temp_file.seek(0)
        return SimpleUploadedFile(temp_file.name, temp_file.read(), content_type='image/jpeg')
    
    def test_auto_name(self):
        self.assertEqual(self.tag1.name, "Test tag1")
        self.assertEqual(self.tag2.name, "Test tag2")

    def test_auto_flags(self):
        self.assertFalse(self.tag1.major)
        self.assertFalse(self.tag2.major)

    def test_create_with_existing_name(self):
        tags_num_before = len(Tag.objects.all())
        new_tag = Tag.objects.create(name="Test tag1")
        tags_num_after = len(Tag.objects.all())
        self.assertEqual(tags_num_before, tags_num_after)

class CommentTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.article1 = Article.objects.create(author=self.user)
        self.comment1 = Comment.objects.create(author=self.user, article=self.article1)

    def test_auto_text(self):
        self.assertEqual(self.comment1.text, "")
    
    def test_auto_date(self):
        now = timezone.now()
        self.assertAlmostEqual(self.comment1.pub_date, now, delta=datetime.timedelta(minutes=30))

class ViewsTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.reader_group = Group.objects.create(name="Reader")
        self.editor_group = Group.objects.create(name="Editor")
        self.editor_in_chief_group = Group.objects.create(name='Editor in Chief')

        self.user1 = User.objects.create_user(username="testuser1", password="testpassword")
        self.user1.groups.add(self.reader_group)

        self.user2 = User.objects.create_user(username="testuser2", password="testpassword")
        self.user2.groups.add(self.reader_group)
        self.user2.groups.add(self.editor_group)

        self.user3 = User.objects.create_user(username="testuser3", password="testpassword")
        self.user3.groups.add(self.reader_group)
        self.user3.groups.add(self.editor_group)
        self.user3.groups.add(self.editor_in_chief_group)

        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        self.profile3 = Profile.objects.create(user=self.user3)

        self.client.login(username='testuser3', password='testpassword')

        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        temp_file.write(b"Test image content")
        temp_file.seek(0)
        img_file = SimpleUploadedFile(temp_file.name, temp_file.read(), content_type='image/jpeg')
        self.image = Image.objects.create(name='default', photo=img_file)

        self.article = Article.objects.create(for_display=True, author=self.user3)
        self.paragraph1 = Paragraph.objects.create(is_lead=True, title='Test Paragraph1', article=self.article)
        self.paragraph2 = Paragraph.objects.create(title='Test Paragraph2', article=self.article)
        self.comment1 = Comment.objects.create(author=self.user1, article=self.article, text="Comment text")

        self.tag1 = Tag.objects.create(name="tag")
        self.tag1.articles.add(self.article)
        self.tag1.images.add(self.image)


    def test_index_view(self):
        response = self.client.get(reverse('newsharborapp:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The News Harbor')
    
    def test_info_view(self):
        response = self.client.get(reverse('newsharborapp:info'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The News Harbor')
    
    def test_api_info_view(self):
        response = self.client.get(reverse('newsharborapp:info-api'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'API')

    def test_article_list_view(self):
        response = self.client.get(reverse('newsharborapp:articles'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Article selector')

    def test_article_list_view_searchif_found(self):
        base_url = reverse('newsharborapp:articles')
        query_params = f"?search={self.tag1}&category=&author=&pub_period="
        url = f"{base_url}{query_params}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_image_list_view_search_if_not_found(self):
        base_url = reverse('newsharborapp:articles')
        query_params = f"?search=error&category=&author=&pub_period="
        url = f"{base_url}{query_params}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.article.name)

    def test_article_detail_view(self):
        response = self.client.get(reverse('newsharborapp:article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.paragraph1.title)
        self.assertContains(response, self.paragraph2.title)
        self.assertContains(response, self.comment1.text)

    def test_login_view(self):
        response = self.client.get(reverse('newsharborapp:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'username')

    def test_register_view(self):
        response = self.client.get(reverse('newsharborapp:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'username')

    def test_register_editor_view(self):
        response = self.client.get(reverse('newsharborapp:register-editor'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'username')
        self.assertContains(response, 'Editor')

    def test_profile_view(self):
        response = self.client.get(reverse('newsharborapp:profile', kwargs={'pk': self.profile3.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.profile3.user.username)
    
    def test_profile_edit_view(self):
        response = self.client.get(reverse('newsharborapp:user-edit', kwargs={'pk': self.profile3.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name')

    def test_profile_change_password_view(self):
        response = self.client.get(reverse('newsharborapp:change-password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'password')
    
    def test_editor_panel_view(self):
        response = self.client.get(reverse('newsharborapp:editor-panel'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'panel')
    
    def test_image_list_view(self):
        response = self.client.get(reverse('newsharborapp:images'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Image selector')

    def test_image_list_view_search_if_found(self):
        base_url = reverse('newsharborapp:images')
        query_params = f'?search={self.tag1}&category=&author=&pub_period='
        url = f"{base_url}{query_params}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.name)

    def test_image_list_view_search_if_not_found(self):
        base_url = reverse('newsharborapp:images')
        query_params = f'?search=error&category=&author=&pub_period='
        url = f'{base_url}{query_params}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.image.name)

    def test_image_detail_view(self):
        response = self.client.get(reverse('newsharborapp:image', kwargs={'pk': self.image.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.name)

    def test_image_rename_view(self):
        response = self.client.get(reverse('newsharborapp:image-rename', kwargs={'pk': self.image.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SAVE')

    def test_image_assign_view(self):
        response = self.client.get(reverse('newsharborapp:image-assign', kwargs={'pk': self.image.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'UNASSIGN')

    def test_image_delete_view(self):
        response = self.client.get(reverse('newsharborapp:image-delete', kwargs={'pk': self.image.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'delete')

    def test_article_select_view(self):
        response = self.client.get(reverse('newsharborapp:article-select'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_article_select_view_search_if_found(self):
        base_url = reverse('newsharborapp:article-select')
        query_params = f'?search={self.tag1}&category=&author=&pub_period='
        url = f"{base_url}{query_params}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_article_select_view_search_if_not_found(self):
        base_url = reverse('newsharborapp:article-select')
        query_params = f'?search=error&category=&author=&pub_period='
        url = f'{base_url}{query_params}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.article.title)

    def test_article_edit_view(self):
        response = self.client.get(reverse('newsharborapp:article-edit', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.paragraph1.title)
        self.assertContains(response, self.paragraph2.title)

    def test_article_add_image_view(self):
        response = self.client.get(reverse('newsharborapp:article-add-image', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.name)

    def test_tag_list_view(self):
        response = self.client.get(reverse('newsharborapp:tags'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag1.name)

    def test_tag_detail_view(self):
        response = self.client.get(reverse('newsharborapp:tag', kwargs={'pk': self.tag1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag1.name)
        self.assertContains(response, self.article.title)
