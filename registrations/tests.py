from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clubs.models import Club, Membership
from events.models import Event

from .models import Registration
from .services import seats_left


class RegistrationTestBase(TestCase):
    def setUp(self):
        self.club = Club.objects.create(name="IUB Computer Club", description="Code.")
        self.executive = User.objects.create_user("rafi", password="pass12345")
        Membership.objects.create(
            user=self.executive, club=self.club,
            role=Membership.Role.EXECUTIVE, status=Membership.Status.APPROVED,
        )
        self.student = User.objects.create_user("nadia", password="pass12345", student_id="2310003")
        self.other = User.objects.create_user("arif", password="pass12345")
        start = timezone.now() + timedelta(days=2)
        self.event = Event.objects.create(
            club=self.club, title="Python Workshop", description="Learn Python.",
            venue="Room 6010", start_time=start, end_time=start + timedelta(hours=2),
            capacity=1, status=Event.Status.APPROVED,
        )

    def register(self, username):
        self.client.login(username=username, password="pass12345")
        return self.client.post(reverse("registrations:register", args=[self.event.pk]))


class RegisterTests(RegistrationTestBase):
    def test_student_can_register(self):
        self.register("nadia")
        self.assertTrue(Registration.objects.filter(user=self.student, event=self.event).exists())
        self.assertEqual(seats_left(self.event), 0)

    def test_cannot_register_when_event_is_full(self):
        self.register("nadia")
        self.register("arif")
        self.assertFalse(Registration.objects.filter(user=self.other).exists())

    def test_cancel_frees_the_seat(self):
        self.register("nadia")
        self.client.post(reverse("registrations:cancel", args=[self.event.pk]))
        self.assertEqual(seats_left(self.event), 1)

    def test_cannot_register_for_pending_event(self):
        self.event.status = Event.Status.PENDING
        self.event.save()
        self.register("nadia")
        self.assertFalse(Registration.objects.exists())


class CheckInTests(RegistrationTestBase):
    def setUp(self):
        super().setUp()
        # the event is happening right now
        self.event.start_time = timezone.now() - timedelta(minutes=10)
        self.event.end_time = timezone.now() + timedelta(hours=1)
        self.event.checkin_code = "ABC234"
        self.event.save()
        self.registration = Registration.objects.create(user=self.student, event=self.event)
        self.client.login(username="nadia", password="pass12345")

    def test_check_in_with_correct_code(self):
        self.client.post(reverse("registrations:checkin", args=[self.event.pk]), {"code": "abc234"})
        self.registration.refresh_from_db()
        self.assertTrue(self.registration.checked_in)

    def test_check_in_with_wrong_code(self):
        self.client.post(reverse("registrations:checkin", args=[self.event.pk]), {"code": "WRONG1"})
        self.registration.refresh_from_db()
        self.assertFalse(self.registration.checked_in)

    def test_executive_can_make_a_new_code(self):
        self.client.login(username="rafi", password="pass12345")
        self.client.post(reverse("registrations:generate_code", args=[self.event.pk]))
        self.event.refresh_from_db()
        self.assertEqual(len(self.event.checkin_code), 6)
        self.assertNotEqual(self.event.checkin_code, "ABC234")


class ManagerPageTests(RegistrationTestBase):
    def test_executive_can_download_attendance_csv(self):
        Registration.objects.create(user=self.student, event=self.event)
        self.client.login(username="rafi", password="pass12345")
        response = self.client.get(reverse("registrations:export", args=[self.event.pk]))
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("2310003", response.content.decode())

    def test_student_cannot_see_registration_list(self):
        self.client.login(username="nadia", password="pass12345")
        response = self.client.get(reverse("registrations:event_registrations", args=[self.event.pk]))
        self.assertEqual(response.status_code, 403)

    def test_report_is_only_for_dosa(self):
        self.client.login(username="nadia", password="pass12345")
        self.assertEqual(self.client.get(reverse("registrations:report")).status_code, 403)
        User.objects.create_user("dosa", password="pass12345", role=User.Role.DOSA)
        self.client.login(username="dosa", password="pass12345")
        self.assertContains(self.client.get(reverse("registrations:report")), "IUB Computer Club")
