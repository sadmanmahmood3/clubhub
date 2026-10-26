from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from clubs.models import Club


class Event(models.Model):
    """An event organised by a club.

    Lifecycle:  Draft -> Pending (sent to DOSA) -> Approved / Rejected -> Completed
    A rejected event can be edited and sent again.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField()
    venue = models.CharField(max_length=150)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=50, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_events",
    )

    # Filled in by DOSA when the event is reviewed
    dosa_comment = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_events",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Code students type in at the event to mark attendance
    checkin_code = models.CharField(max_length=6, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} ({self.club})"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after the start time."})

    @property
    def is_upcoming(self):
        return self.start_time >= timezone.now()

    @property
    def has_ended(self):
        return self.end_time < timezone.now()

    @property
    def can_be_edited(self):
        """Only drafts and rejected events can be changed by the club."""
        return self.status in (self.Status.DRAFT, self.Status.REJECTED)
