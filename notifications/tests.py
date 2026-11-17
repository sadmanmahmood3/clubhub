from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Notification
from .utils import notify


class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("nadia", password="pass12345")
        self.other = User.objects.create_user("arif", password="pass12345")

    def test_notify_one_user(self):
        notify(self.user, "Hello")
        self.assertEqual(self.user.notifications.count(), 1)

    def test_notify_many_users(self):
        notify([self.user, self.other], "Hello everyone")
        self.assertEqual(Notification.objects.count(), 2)

    def test_unread_count_is_in_every_page(self):
        notify(self.user, "One")
        notify(self.user, "Two")
        self.client.login(username="nadia", password="pass12345")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["unread_notification_count"], 2)

    def test_opening_marks_as_read_and_redirects(self):
        notify(self.user, "Go to clubs", "/clubs/")
        notification = self.user.notifications.get()
        self.client.login(username="nadia", password="pass12345")
        response = self.client.post(reverse("notifications:open", args=[notification.pk]))
        self.assertRedirects(response, "/clubs/", fetch_redirect_response=False)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_cannot_open_someone_elses_notification(self):
        notify(self.other, "Private")
        notification = self.other.notifications.get()
        self.client.login(username="nadia", password="pass12345")
        response = self.client.post(reverse("notifications:open", args=[notification.pk]))
        self.assertEqual(response.status_code, 404)
