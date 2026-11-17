from django.test import TestCase
from django.urls import reverse

from .models import User


class SignUpTests(TestCase):
    def data(self, **changes):
        data = {
            "username": "sadman", "first_name": "Sadman", "last_name": "Mahmood",
            "email": "sadman@example.com", "student_id": "2320619", "department": "CSE",
            "password1": "Str0ng-pass-2026", "password2": "Str0ng-pass-2026",
        }
        data.update(changes)
        return data

    def test_student_can_sign_up(self):
        response = self.client.post(reverse("accounts:signup"), self.data())
        self.assertRedirects(response, reverse("accounts:dashboard"))
        user = User.objects.get(username="sadman")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_dosa)

    def test_student_id_must_have_7_digits(self):
        response = self.client.post(reverse("accounts:signup"), self.data(student_id="12AB"))
        self.assertContains(response, "exactly 7 digits")
        self.assertFalse(User.objects.exists())

    def test_student_id_must_be_unique(self):
        User.objects.create_user("someone", password="x", student_id="2320619")
        response = self.client.post(reverse("accounts:signup"), self.data())
        self.assertContains(response, "already exists")


class DashboardTests(TestCase):
    def test_dashboard_needs_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_dosa_sees_statistics(self):
        User.objects.create_user("dosa", password="pass12345", role=User.Role.DOSA)
        self.client.login(username="dosa", password="pass12345")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "events waiting for approval")

    def test_student_does_not_see_statistics(self):
        User.objects.create_user("nadia", password="pass12345")
        self.client.login(username="nadia", password="pass12345")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertNotContains(response, "events waiting for approval")

    def test_profile_update(self):
        user = User.objects.create_user("nadia", password="pass12345")
        self.client.login(username="nadia", password="pass12345")
        self.client.post(reverse("accounts:profile"), {
            "first_name": "Nadia", "last_name": "Islam", "email": "n@example.com",
            "department": "CSE", "phone": "01700000000",
        })
        user.refresh_from_db()
        self.assertEqual(user.phone, "01700000000")
