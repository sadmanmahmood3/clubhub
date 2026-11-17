"""Fill the database with demo data so the whole system can be shown in class.

    python manage.py seed_demo

Safe to run more than once: existing demo rows are updated, not duplicated.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from clubs.models import Club, Membership
from events.models import Event
from registrations.models import Registration

PASSWORD = "clubhub2026"


class Command(BaseCommand):
    help = "Create demo users, clubs, events and registrations."

    def handle(self, *args, **options):
        now = timezone.localtime().replace(second=0, microsecond=0)

        def at(days, hour):
            """A date `days` from today at a fixed hour, e.g. at(7, 14) = next week, 2 PM."""
            return (now + timedelta(days=days)).replace(hour=hour, minute=0)

        # ---- users
        dosa = self.user("dosa", "DOSA", "Office", role=User.Role.DOSA, staff=True)
        rafi = self.user("rafi", "Rafi", "Ahmed", "2210001", "CSE")
        tasnia = self.user("tasnia", "Tasnia", "Rahman", "2210002", "English")
        nadia = self.user("nadia", "Nadia", "Islam", "2310003", "CSE")
        arif = self.user("arif", "Arif", "Hossain", "2310004", "BBA")
        mim = self.user("mim", "Mim", "Chowdhury", "2410005", "EEE")

        # ---- clubs
        computer = self.club("IUB Computer Club", Club.Category.TECH, 2001,
                             "Workshops, contests and hackathons for everyone who likes to build software.")
        debate = self.club("IUB Debate Club", Club.Category.CULTURAL, 2003,
                           "Weekly practice sessions and national and international debate tournaments.")
        business = self.club("IUB Business Club", Club.Category.BUSINESS, 2005,
                             "Case competitions, career talks and networking with industry.")
        photo = self.club("IUB Photography Club", Club.Category.CULTURAL, 2010,
                          "Photo walks, exhibitions and editing workshops.")
        self.club("IUB Sports Club", Club.Category.SPORTS, 2002,
                  "Football, cricket and indoor games tournaments on campus.")

        # ---- memberships (executives first)
        self.member(rafi, computer, executive=True)
        self.member(tasnia, debate, executive=True)
        self.member(tasnia, photo, executive=True)
        self.member(arif, business, executive=True)
        self.member(nadia, computer)
        self.member(mim, computer)
        self.member(nadia, debate)
        self.member(mim, photo, status=Membership.Status.PENDING)

        # ---- events
        workshop = self.event(
            computer, "Python for Beginners Workshop", at(7, 14), 3, 40,
            Event.Status.APPROVED, rafi, dosa, "Room 6010, IUB",
            "A hands-on workshop: variables, loops and functions. Bring your laptop.",
        )
        live = self.event(
            computer, "Git & GitHub Live Session", now - timedelta(minutes=30), 2, 60,
            Event.Status.APPROVED, rafi, dosa, "Multipurpose Hall",
            "Learn branches, pull requests and teamwork on GitHub. Happening right now!",
            code="GIT26A",
        )
        self.event(
            debate, "Inter-University Debate 2026", at(14, 10), 6, 150,
            Event.Status.APPROVED, tasnia, dosa, "IUB Auditorium",
            "Teams from 12 universities compete. Spectators welcome.",
        )
        self.event(
            photo, "Old Dhaka Photo Walk", at(10, 7), 4, 25,
            Event.Status.PENDING, tasnia, None, "Meeting point: IUB main gate",
            "A guided photo walk through Old Dhaka. Waiting for DOSA approval.",
        )
        self.event(
            business, "Career Talk: Getting Your First Job", at(20, 15), 2, 80,
            Event.Status.DRAFT, arif, None, "Room 3020",
            "Alumni share how they got their first job. Still a draft.",
        )
        orientation = self.event(
            computer, "Club Orientation 2026", at(-10, 11), 2, 100,
            Event.Status.COMPLETED, rafi, dosa, "Room 6010, IUB",
            "Welcome session for new members.",
        )

        # ---- registrations
        for student in (nadia, mim, arif):
            self.register(student, workshop)
        self.register(nadia, live)
        self.register(mim, live, checked_in=True)
        for student in (nadia, mim, arif, tasnia):
            self.register(student, orientation, checked_in=student != arif)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write(f"All demo accounts use the password: {PASSWORD}")
        self.stdout.write("  dosa   - DOSA admin (can also open /admin/)")
        self.stdout.write("  rafi   - executive of IUB Computer Club")
        self.stdout.write("  tasnia - executive of IUB Debate Club and IUB Photography Club")
        self.stdout.write("  nadia, mim, arif - students")

    # ---------------------------------------------------------------- helpers
    def user(self, username, first, last, student_id="", department="", role=User.Role.STUDENT, staff=False):
        user, _ = User.objects.get_or_create(username=username)
        user.first_name, user.last_name = first, last
        user.email = f"{username}@demo.iub.edu.bd"
        user.student_id, user.department, user.role = student_id, department, role
        user.is_staff = user.is_superuser = staff
        user.set_password(PASSWORD)
        user.save()
        return user

    def club(self, name, category, founded, description):
        club, _ = Club.objects.update_or_create(name=name, defaults={
            "category": category, "founded_year": founded, "description": description,
            "email": f"{name.lower().replace(' ', '.')}@demo.iub.edu.bd",
        })
        return club

    def member(self, user, club, executive=False, status=Membership.Status.APPROVED):
        Membership.objects.update_or_create(user=user, club=club, defaults={
            "role": Membership.Role.EXECUTIVE if executive else Membership.Role.MEMBER,
            "status": status,
        })

    def event(self, club, title, start, hours, capacity, status, creator, reviewer, venue,
              description, code=""):
        event, _ = Event.objects.update_or_create(club=club, title=title, defaults={
            "start_time": start, "end_time": start + timedelta(hours=hours),
            "capacity": capacity, "status": status, "created_by": creator,
            "reviewed_by": reviewer, "reviewed_at": timezone.now() if reviewer else None,
            "venue": venue, "description": description, "checkin_code": code,
        })
        return event

    def register(self, user, event, checked_in=False):
        Registration.objects.update_or_create(user=user, event=event, defaults={
            "status": Registration.Status.REGISTERED,
            "checked_in": checked_in,
            "checked_in_at": event.start_time + timedelta(minutes=5) if checked_in else None,
        })
