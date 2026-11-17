from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Club, Membership


def club_list(request):
    """All active clubs."""
    clubs = Club.objects.filter(is_active=True).annotate(
        member_count=Count(
            "memberships", filter=Q(memberships__status=Membership.Status.APPROVED)
        )
    )
    return render(request, "clubs/club_list.html", {"clubs": clubs})


def club_detail(request, slug):
    club = get_object_or_404(Club, slug=slug, is_active=True)
    membership = None
    if request.user.is_authenticated:
        membership = club.memberships.filter(user=request.user).first()
    members = club.approved_members().select_related("user").order_by("role", "user__first_name")

    return render(request, "clubs/club_detail.html", {
        "club": club,
        "membership": membership,
        "members": members,
        "is_executive": club.is_executive(request.user),
    })


@login_required
@require_POST
def join_club(request, slug):
    """A student asks to join a club. The request waits for an executive."""
    club = get_object_or_404(Club, slug=slug, is_active=True)
    membership, created = Membership.objects.get_or_create(user=request.user, club=club)

    if not created and membership.status == Membership.Status.REJECTED:
        membership.status = Membership.Status.PENDING
        membership.save(update_fields=["status"])
        created = True

    if created:
        messages.success(request, f"Your request to join {club.name} was sent to the club executives.")
    elif membership.status == Membership.Status.PENDING:
        messages.info(request, "Your join request is already waiting for approval.")
    else:
        messages.info(request, f"You are already a member of {club.name}.")
    return redirect(club)


@login_required
@require_POST
def leave_club(request, slug):
    membership = get_object_or_404(Membership, user=request.user, club__slug=slug)
    if membership.role == Membership.Role.EXECUTIVE:
        messages.error(request, "Executives cannot leave the club here. Please contact DOSA.")
    else:
        club_name = membership.club.name
        membership.delete()
        messages.success(request, f"You left {club_name}.")
    return redirect("clubs:detail", slug=slug)


@login_required
def my_clubs(request):
    memberships = request.user.memberships.select_related("club").order_by("club__name")
    return render(request, "clubs/my_clubs.html", {"memberships": memberships})
