from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clubs.models import Club, Membership
from notifications.models import Notification

from .forms import EventForm
from .models import Event


class EventTestBase(TestCase):
    def setUp(self):
        self.club = Club.objects.create(name="IUB Debate Club", description="We debate.")
        self.executive = User.objects.create_user("tasnia", password="pass12345")
        Membership.objects.create(
            user=self.executive, club=self.club,
            role=Membership.Role.EXECUTIVE, status=Membership.Status.APPROVED,
        )
        self.student = User.objects.create_user("arif", password="pass12345")
        self.dosa = User.objects.create_user("dosa", password="pass12345", role=User.Role.DOSA)

    def make_event(self, status=Event.Status.DRAFT, **kwargs):
        start = timezone.now() + timedelta(days=5)
        data = dict(
            club=self.club, title="Inter-University Debate", description="Big debate.",
            venue="Auditorium", start_time=start, end_time=start + timedelta(hours=3),
            capacity=100, status=status, created_by=self.executive,
        )
        data.update(kwargs)
        return Event.objects.create(**data)


class EventCreateTests(EventTestBase):
    def form_data(self):
        start = timezone.localtime() + timedelta(days=3)
        return {
            "title": "Debate Workshop", "description": "Learn to debate.", "venue": "Room 5001",
            "start_time": start.strftime("%Y-%m-%dT%H:%M"),
            "end_time": (start + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "capacity": 30,
        }

    def test_executive_creates_event_as_draft(self):
        self.client.login(username="tasnia", password="pass12345")
        self.client.post(reverse("events:create", args=[self.club.slug]), self.form_data())
        event = Event.objects.get(title="Debate Workshop")
        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(event.created_by, self.executive)

    def test_student_cannot_create_event(self):
        self.client.login(username="arif", password="pass12345")
        response = self.client.post(reverse("events:create", args=[self.club.slug]), self.form_data())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Event.objects.exists())

    def test_end_time_must_be_after_start_time(self):
        data = self.form_data()
        data["end_time"] = data["start_time"]
        self.assertFalse(EventForm(data).is_valid())

    def test_event_cannot_start_in_the_past(self):
        data = self.form_data()
        past = timezone.localtime() - timedelta(days=1)
        data["start_time"] = past.strftime("%Y-%m-%dT%H:%M")
        self.assertIn("start_time", EventForm(data).errors)


class EventVisibilityTests(EventTestBase):
    def test_draft_is_hidden_from_students(self):
        event = self.make_event()
        self.client.login(username="arif", password="pass12345")
        response = self.client.get(reverse("events:detail", args=[event.pk]))
        self.assertEqual(response.status_code, 404)

    def test_only_approved_events_are_listed(self):
        self.make_event(title="Approved one", status=Event.Status.APPROVED)
        self.make_event(title="Pending one", status=Event.Status.PENDING)
        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "Approved one")
        self.assertNotContains(response, "Pending one")


class ApprovalWorkflowTests(EventTestBase):
    def test_submit_sends_event_to_dosa(self):
        event = self.make_event()
        self.client.login(username="tasnia", password="pass12345")
        self.client.post(reverse("events:submit", args=[event.pk]))
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.PENDING)
        self.assertTrue(Notification.objects.filter(user=self.dosa).exists())

    def test_dosa_approves_event(self):
        event = self.make_event(status=Event.Status.PENDING)
        self.client.login(username="dosa", password="pass12345")
        self.client.post(reverse("events:review", args=[event.pk]), {"decision": "approve", "comment": ""})
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.APPROVED)
        self.assertEqual(event.reviewed_by, self.dosa)
        self.assertTrue(Notification.objects.filter(user=self.executive).exists())

    def test_rejecting_needs_a_comment(self):
        event = self.make_event(status=Event.Status.PENDING)
        self.client.login(username="dosa", password="pass12345")
        response = self.client.post(reverse("events:review", args=[event.pk]), {"decision": "reject", "comment": ""})
        self.assertContains(response, "Please tell the club why")
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.PENDING)

    def test_rejected_event_can_be_edited_again(self):
        event = self.make_event(status=Event.Status.PENDING)
        self.client.login(username="dosa", password="pass12345")
        self.client.post(reverse("events:review", args=[event.pk]), {"decision": "reject", "comment": "Change the venue."})
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.REJECTED)
        self.assertTrue(event.can_be_edited)

    def test_student_cannot_open_approval_queue(self):
        self.client.login(username="arif", password="pass12345")
        response = self.client.get(reverse("events:approval_queue"))
        self.assertEqual(response.status_code, 403)


class SeedDemoTests(TestCase):
    def test_seed_demo_can_run_twice(self):
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Club.objects.count(), 5)
        self.assertTrue(Event.objects.filter(status=Event.Status.PENDING).exists())
        self.assertTrue(User.objects.get(username="dosa").is_dosa)
