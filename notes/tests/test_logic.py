from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """Проверка создания заметки, создания двух заметок с одинаковым slug
    и создании slug автоматически.
    """
    NOTES_ADD_URL = reverse('notes:add')

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            "title": 'Заголовок',
            'text': 'Текст',
        }

    def test_anonymous_user_cannot_create_note(self):
        """
        Анонимный пользователь не может создать заметку.
        """
        self.client.post(self.NOTES_ADD_URL, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """
        Залогиненный пользователь может создать заметку.
        """
        response = self.auth_client.post(
            self.NOTES_ADD_URL,
            data=self.form_data
        )
        self.assertRedirects(response, '/done/')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.user)

    def test_create_note_unique_slug(self):
        """
        Невозможно создать две заметки с одинаковым slug.
        """
        notes_quantity = (1, 2)
        for note in notes_quantity:
            response = self.auth_client.post(
                self.NOTES_ADD_URL,
                data=self.form_data
            )
        slug = slugify(self.form_data['title'])[:100]
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=slug + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_create_slug_via_slugify(self):
        """
        Если при создании заметки не заполнен slug, то он формируется
        автоматически, с помощью функции pytils.translit.slugify.
        """
        self.auth_client.post(self.NOTES_ADD_URL, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        note_slug = slugify(self.form_data['title'])[:100]
        self.assertEqual(note.slug, note_slug)


class TestNoteEditDelete(TestCase):
    """
    Пользователь может редактировать и удалять свои заметки,
    но не может редактировать или удалять чужие.
    """

    NOTE_TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user = User.objects.create(
            username='Аутентифицированный пользователь'
        )
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.url_to_success = reverse('notes:success')
        cls.form_data = {
            "title": 'Новый заголовок',
            'text': 'Новый текст',
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_success)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_another_user_cant_delete_note_of_author(self):
        response = self.another_user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_to_success)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.form_data['text'])

    def test_user_cant_edit_note_of_another_user(self):
        response = self.another_user_client.post(
            self.edit_url,
            data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
