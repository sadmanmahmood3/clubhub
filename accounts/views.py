from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignUpForm


def signup(request):
    """Create a new student account and log the student in."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to ClubHub, {user.first_name}!")
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})
