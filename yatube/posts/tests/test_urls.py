from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
            first_name='Test Name',
            last_name='Test LastName',
            email='test@email.com',
        )
        cls.author = User.objects.create_user(
            username='author_user'
        )
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test_slug',
            description='Test Description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test Text',
        )
        cls.INDEX = '/'
        cls.GROUP_LIST = f'/group/{cls.group.slug}/'
        cls.PROFILE = f'/profile/{cls.user.username}/'
        cls.POST_DETAIL = f'/posts/{cls.post.id}/'
        cls.POST_CREATE = '/create/'
        cls.POST_EDIT = f'/posts/{cls.post.id}/edit/'
        cls.UNEXISTING_PAGE = '/existing_page/'
        cls.CREATE_REDIRECT = '/auth/login/?next=/create/'
        cls.EDIT_REDIRECT = f'/posts/{cls.post.id}/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_is_ok(self):
        """Страницы доступны по адресам"""
        adress_clients = [
            (self.INDEX, self.guest_client, HTTPStatus.OK),
            (self.GROUP_LIST, self.guest_client, HTTPStatus.OK),
            (self.PROFILE, self.guest_client, HTTPStatus.OK),
            (self.POST_DETAIL, self.guest_client, HTTPStatus.OK),
            (self.POST_CREATE, self.authorized_client, HTTPStatus.OK),
            (self.POST_EDIT, self.authorized_client, HTTPStatus.OK),
            (self.UNEXISTING_PAGE, self.guest_client, HTTPStatus.NOT_FOUND),
        ]
        for adress, client, http_status in adress_clients:
            with self.subTest(adress=adress):
                response = client.get(adress)
                self.assertEqual(response.status_code, http_status)

    def test_post_create_redirect(self):
        """
        Страница post_create перенаправит анонимного
        пользователя на страницу login.
        """
        response = self.guest_client.get(
            self.POST_CREATE, follow=True
        )
        self.assertRedirects(
            response, self.CREATE_REDIRECT
        )

    def test_post_edit_not_author_redirect(self):
        """
        Страница post_edit перенаправит не автора поста
        на страницу post_detail.
        """
        response = self.author_client.get(
            self.POST_EDIT, follow=True
        )
        self.assertRedirects(
            response, self.EDIT_REDIRECT
        )

    def test_urls_uses_correct_templates(self):
        """Проверка ссылок на соответствие шаблонам"""
        templates_url_names = {
            self.INDEX: 'posts/index.html',
            self.GROUP_LIST: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_CREATE: 'posts/create_post.html',
            self.POST_EDIT: 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
