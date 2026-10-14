from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A ClubHub user.

    Every account is either a Student or a DOSA admin.
    A club executive is a student who has the "executive" role in a club
    membership (see clubs.Membership), so it is not stored here.
    """

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        DOSA = "dosa", "DOSA Admin"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    student_id = models.CharField(max_length=10, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    @property
    def is_dosa(self):
        """True for DOSA admins (superusers are treated as DOSA too)."""
        return self.role == self.Role.DOSA or self.is_superuser

    def __str__(self):
        return self.get_full_name() or self.username
