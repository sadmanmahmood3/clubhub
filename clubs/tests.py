from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification

from .models import Club, Membership


class ClubMembershipTests(TestCase):
    def setUp(self):
        self.club = Club.objects.create(
            name="IUB Computer Club", category=Club.Category.TECH, description="Coding and more."
        )
        self.executive = User.objects.create_user("rafi", password="pass12345", first_name="Rafi")
        Membership.objects.create(
            user=self.executive, club=self.club,
            role=Membership.Role.EXECUTIVE, status=Membership.Status.APPROVED,
        )
        self.student = User.objects.create_user("nadia", password="pass12345", first_name="Nadia")

    def test_club_list_shows_active_clubs(self):
        Club.objects.create(name="Old Club", description="Closed", is_active=False)
        response = self.client.get(reverse("clubs:list"))
        self.assertContains(response, "IUB Computer Club")
        self.assertNotContains(response, "Old Club")

    def test_slug_is_created_from_name(self):
        self.assertEqual(self.club.slug, "iub-computer-club")

    def test_student_can_request_to_join(self):
        self.client.login(username="nadia", password="pass12345")
        self.client.post(reverse("clubs:join", args=[self.club.slug]))
        membership = Membership.objects.get(user=self.student, club=self.club)
        self.assertEqual(membership.status, Membership.Status.PENDING)
        # the executive gets a notification about the request
        self.assertTrue(Notification.objects.filter(user=self.executive).exists())

    def test_executive_can_approve_request(self):
        membership = Membership.objects.create(user=self.student, club=self.club)
        self.client.login(username="rafi", password="pass12345")
        self.client.post(reverse(
            "clubs:update_membership", args=[self.club.slug, membership.pk, "approve"]
        ))
        membership.refresh_from_db()
        self.assertEqual(membership.status, Membership.Status.APPROVED)
        self.assertTrue(Notification.objects.filter(user=self.student).exists())

    def test_student_cannot_manage_members(self):
        self.client.login(username="nadia", password="pass12345")
        response = self.client.get(reverse("clubs:manage_members", args=[self.club.slug]))
        self.assertEqual(response.status_code, 403)

    def test_is_executive(self):
        self.assertTrue(self.club.is_executive(self.executive))
        self.assertFalse(self.club.is_executive(self.student))
