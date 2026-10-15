from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Club(models.Model):
    """A student club at IUB, e.g. "IUB Computer Club"."""

    class Category(models.TextChoices):
        TECH = "tech", "Technology"
        CULTURAL = "cultural", "Cultural"
        SPORTS = "sports", "Sports"
        BUSINESS = "business", "Business"
        SOCIAL = "social", "Social Service"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    description = models.TextField()
    email = models.EmailField(blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Build a URL-friendly name automatically: "IUB Computer Club" -> "iub-computer-club"
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def approved_members(self):
        return self.memberships.filter(status=Membership.Status.APPROVED)

    def is_executive(self, user):
        """True if this user is an approved executive of this club."""
        if not user.is_authenticated:
            return False
        return self.memberships.filter(
            user=user,
            role=Membership.Role.EXECUTIVE,
            status=Membership.Status.APPROVED,
        ).exists()


class Membership(models.Model):
    """Connects a student to a club. A student asks to join (pending),
    and a club executive approves or rejects the request."""

    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        EXECUTIVE = "executive", "Executive"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-joined_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "club"], name="unique_club_membership")
        ]

    def __str__(self):
        return f"{self.user} in {self.club} ({self.status})"
