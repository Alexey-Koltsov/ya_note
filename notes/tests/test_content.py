from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """Тестирование контента"""

    NOTES_LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.another_user = User.objects.create(
            username='Аутентифицированный пользователь'
        )
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_notes_page(self):
        """
        Отдельная заметка передаётся на страницу со списком
        заметок в списке object_list в словаре context,
        в список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        users_count = (
            (self.author, 1),
            (self.another_user, 0),
        )
        for user, count in users_count:
            self.client.force_login(user)
            with self.subTest(user=user):
                response = self.client.get(self.NOTES_LIST_URL)
                object_list = response.context['object_list']
                notes_count = len(object_list)
                self.assertEqual(notes_count, count)

    def test_authorized_client_has_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(user=self.author, name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
