from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
        )
        cls.group = Group.objects.create(
            title='Test Group',
            slug='slug',
            description='Test Description',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )
        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.user.username}'}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.POST_CREATE_URL = reverse('posts:post_create')
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.user.username}'}
        )
        cls.PROFILE_FOLLOW_URL = reverse(
            'posts:profile_follow', kwargs={
                'username': f'{cls.user.username}'
            }
        )
        cls.PROFILE_UNFOLLOW_URL = reverse(
            'posts:profile_unfollow', kwargs={
                'username': f'{cls.user.username}'
            }
        )
        cls.FOLLOW_URL = reverse('posts:follow_index')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        urls_templates_names = [
            (self.INDEX_URL, 'posts/index.html'),
            (self.GROUP_LIST_URL, 'posts/group_list.html'),
            (self.PROFILE_URL, 'posts/profile.html'),
            (self.POST_DETAIL_URL, 'posts/post_detail.html'),
            (self.POST_CREATE_URL, 'posts/create_post.html'),
            (self.POST_EDIT_URL, 'posts/create_post.html'),
        ]
        for reverse_name, template in urls_templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_page_obj_is_valid(self, url):
        """Функция проверки контекста: 'page_obj'."""
        response = self.authorized_client.get(url)
        first_object = response.context['page_obj'][0]
        self.assertIsInstance(first_object, Post)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def context_title_is_valid(self, url, title_content):
        """Функция проверки контекста: 'title'."""
        response = self.authorized_client.get(url)
        title_object = response.context['title']
        self.assertEqual(title_object, title_content)

    def test_index_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        title_content = 'Это главная страница проекта Yatube'
        self.context_page_obj_is_valid(self.INDEX_URL)
        self.context_title_is_valid(self.INDEX_URL, title_content)

    def test_group_list_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        self.context_page_obj_is_valid(self.GROUP_LIST_URL)
        response = self.authorized_client.get(self.GROUP_LIST_URL)
        first_group = response.context['group']
        self.assertIsInstance(first_group, Group)
        self.assertEqual(first_group, self.group)
        title_content = f'Записи сообщества { self.group.title }'
        self.context_title_is_valid(self.GROUP_LIST_URL, title_content)

    def test_profile_page_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.context_page_obj_is_valid(self.PROFILE_URL)
        response = self.authorized_client.get(self.PROFILE_URL)
        self.assertEqual(len(response.context['page_obj']), 1)
        first_author = response.context['author']
        self.assertIsInstance(first_author, User)
        self.assertEqual(first_author, self.user)
        post_count = Post.objects.filter(
            author__exact=self.post.author
        ).count()
        self.assertEqual(post_count, 1)

    def context_post_is_valid(self, url):
        """Функция проверки контекста: 'post'."""
        response = self.authorized_client.get(url)
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.image, self.post.image)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        self.context_post_is_valid(self.POST_DETAIL_URL)
        post_count = Post.objects.filter(
            author__exact=self.post.author
        ).count()
        self.assertEqual(post_count, 1)

    def form_fields_is_valid(self, url):
        """Функция проверки типов полей формы."""
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        self.form_fields_is_valid(self.POST_CREATE_URL)

    def test_edit_page_show_correct_context(self):
        """Шаблон create_post редактирования записи
        сформирован с правильным контекстом."""
        self.context_post_is_valid(self.POST_EDIT_URL)
        self.form_fields_is_valid(self.POST_EDIT_URL)
        response = self.authorized_client.get(
            self.POST_EDIT_URL
        )
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_index_cache(self):
        """Кэширование главной страницы работает."""
        Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
        )
        now = self.authorized_client.get(self.INDEX_URL)
        content_now = now.content
        cache.clear()
        clear = self.authorized_client.get(self.INDEX_URL)
        content_after_clear = clear.content
        self.assertNotEqual(content_now, content_after_clear)

    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        new_user = User.objects.create(username='Lermontov')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        response_follow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_follow = response_follow.context
        self.assertEqual(len(context_follow['page_obj']), 1)

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        new_user = User.objects.create(username='Lermontov')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        response_unfollow = authorized_client.get(self.FOLLOW_URL)
        context_unfollow = response_unfollow.context
        self.assertEqual(len(context_unfollow['page_obj']), 0)

    def test_follow(self):
        """Тестирование подписки на автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Lermontov')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, new_author)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """Тестирование отписки от автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Lermontov')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Test title',
            slug='slug',
            description='Description',
        )
        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.POSTS_PER_PAGE = 10
        cls.ADDPOSTS = 5
        cls.posts = Post.objects.bulk_create(
            Post(
                author=cls.author,
                text=f'{i + 1} длинный тестовый пост',
                group=cls.group
            )
            for i in range(cls.POSTS_PER_PAGE + cls.ADDPOSTS)
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_accordance_posts_per_pages(self):
        """Проверяем, что количество постов
        на первой странице равно 10, а на второй - 5"""
        for url in [
            self.INDEX_URL,
            self.GROUP_LIST_URL,
            self.PROFILE_URL
        ]:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.POSTS_PER_PAGE
                )
                response_second = self.author_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    self.ADDPOSTS
                )
