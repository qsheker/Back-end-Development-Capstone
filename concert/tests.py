from datetime import date
from unittest.mock import Mock, patch
import requests
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Concert, ConcertAttending


class BandWorkflowTests(TestCase):
    def setUp(self):
        self.concert = Concert.objects.create(concert_name='Test Concert', city='Almaty', date=date(2030, 6, 1), duration=2)
        self.user = User.objects.create_user('listener', password='Concert-test-724!')

    def test_anonymous_can_browse_but_cannot_book(self):
        self.assertContains(self.client.get(reverse('concerts')), 'Test Concert')
        self.assertEqual(self.client.post(reverse('concert_attendee'), {'concert_id': self.concert.pk, 'attendee_choice': 'Attending'}).status_code, 302)
        self.assertFalse(ConcertAttending.objects.exists())

    def test_signup_login_logout_and_invalid_password(self):
        result = self.client.post(reverse('signup'), {'username': 'newlistener', 'password1': 'Concert-test-724!', 'password2': 'Concert-test-724!'})
        self.assertRedirects(result, '/')
        self.assertTrue(User.objects.get(username='newlistener').check_password('Concert-test-724!'))
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        result = self.client.post(reverse('login'), {'username': 'newlistener', 'password': 'wrong'})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        result = self.client.post(reverse('login'), {'username': 'newlistener', 'password': 'Concert-test-724!'})
        self.assertRedirects(result, '/')

    def test_attendance_is_idempotent_and_cancellation_is_isolated(self):
        self.client.force_login(self.user)
        other = User.objects.create_user('other')
        ConcertAttending.objects.create(concert=self.concert, user=other, attending='Attending')
        payload = {'concert_id': self.concert.pk, 'attendee_choice': 'Attending'}
        for _ in range(2):
            self.assertRedirects(self.client.post(reverse('concert_attendee'), payload), reverse('concerts'))
        self.assertEqual(ConcertAttending.objects.filter(user=self.user).count(), 1)
        payload['attendee_choice'] = 'Not Attending'
        self.client.post(reverse('concert_attendee'), payload)
        self.assertFalse(ConcertAttending.objects.filter(user=self.user).exists())
        self.assertTrue(ConcertAttending.objects.filter(user=other).exists())

    def test_invalid_attendance_and_missing_concert(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('concert_attendee'), {'concert_id': 'bad'}).status_code, 400)
        self.assertEqual(self.client.post(reverse('concert_attendee'), {'concert_id': self.concert.pk, 'attendee_choice': 'invalid'}).status_code, 400)
        self.assertEqual(self.client.get(reverse('concert_detail', args=[999])).status_code, 404)

    @patch('concert.views.requests.get')
    def test_songs_and_photos_service_integration(self, get):
        get.return_value = Mock(**{'json.return_value': {'songs': [{'id': 1, 'title': 'Test song', 'lyrics': 'Test lyrics'}]}})
        self.assertContains(self.client.get(reverse('songs')), 'Test lyrics')
        get.assert_called_with('http://127.0.0.1:5002/song', timeout=5)
        get.return_value = Mock(**{'json.return_value': [{'id': 1, 'pic_url': 'https://example.com/picture.png', 'event_city': 'Almaty'}]})
        self.assertContains(self.client.get(reverse('photos')), 'picture.png')

    @patch('concert.views.requests.get', side_effect=requests.Timeout)
    def test_service_failure_is_visible(self, get):
        result = self.client.get(reverse('songs'))
        self.assertContains(result, 'temporarily unavailable', status_code=503)

    def test_admin_can_edit_concert(self):
        admin = User.objects.create_superuser('administrator', password='Admin-test-943!')
        self.client.force_login(admin)
        url = reverse('admin:concert_concert_change', args=[self.concert.pk])
        result = self.client.post(url, {'concert_name': 'Updated Concert', 'duration': 3, 'city': 'Astana', 'date': '2030-07-01', '_save': 'Save'})
        self.assertEqual(result.status_code, 302)
        self.concert.refresh_from_db()
        self.assertEqual(self.concert.date, date(2030, 7, 1))
