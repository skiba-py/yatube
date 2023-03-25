from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test title',
            slug='slug',
            description='Test description',
        )
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.author,
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.author.username}'}
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_post_edit(self):
        """Редактирование поста изменяет пост в базе"""
        form_data = {
            'text': 'another post',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(
            Post.objects.filter(text='another post').exists()
        )

    def test_client_create_image(self):
        """Авторизованный пользователь создает запись c изображением."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        small_gif_name = 'small.gif'
        test_image = SimpleUploadedFile(
            name=small_gif_name,
            content=small_gif,
            content_type='image/gif'
        )
        post_aut_detail_url = reverse(
            'posts:profile', kwargs={'username': f'{self.author.username}'}
        )
        create_form_data = {
            'text': 'Test text',
            'group': self.group.id,
            'image': test_image,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True
        )
        self.assertRedirects(response, post_aut_detail_url)
        self.assertEqual(Post.objects.count(), 2)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test title',
            slug='slug',
            description='Test description',
        )
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.user = User.objects.create_user(username='AuthorizedClient')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.author,
        )
        cls.form = CommentForm()
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.COMMENT = reverse(
            'posts:add_comment', kwargs={'post_id': f'{cls.post.id}'}
        )

        def setUp(self):
            self.guest_client = Client()
            self.authorized_client = Client()
            self.authorized_client.force_login(self.user)

        def test_comment_only_user(self):
            """
            Комментировать посты может
            только авторизованный пользователь.
            """
            text = 'Test comment'
            comment_form_data = {'text': text}
            comment_response = self.authorized_client.post(
                self.COMMENT,
                data=comment_form_data,
                follow=True,
            )
            comment = Comment.objects.latest('created')
            self.assertEqual(Comment.objects.count(), 1)
            self.assertEqual(comment.text, text)
            self.assertEqual(comment.author, self.user)
            self.assertEqual(comment.post, self.post)
            self.assertRedirects(
                comment_response, self.POST_DETAIL_URL
            )
