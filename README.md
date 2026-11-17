# ClubHub: IUB Club & Event Management System

ClubHub brings club and event activity at Independent University, Bangladesh (IUB) into one place.
Students find clubs, join them and register for events. Club executives create events and manage
members. DOSA (Division of Student Activities) approves events and sees participation reports.

CSE 451 Software Engineering group project, Autumn 2026.

## Team

| Member | Responsibility | Django app |
| --- | --- | --- |
| Sadman Mahmood | Project setup, accounts and roles, event pages, dashboard | `accounts`, `events` (pages) |
| Anika Tabassum | Clubs and membership, notifications | `clubs`, `notifications` |
| Shawon | Registration, check-in attendance, reports | `registrations` |
| Fatema | Event model, DOSA approval workflow, demo data | `events` |

## Features

- **Accounts:** sign up with IUB student ID, log in, profile, role-based dashboard (Student / DOSA)
- **Clubs:** browse and search clubs, request to join, executives approve members and promote executives
- **Events:** executives create events as drafts and submit them to DOSA; public events page with search
- **DOSA approval:** approval queue, approve or reject with a comment, history of decisions
- **Registration:** one-click registration with seat limits, cancel, "My registrations"
- **Attendance:** executives show a 6-letter check-in code at the venue, students enter it to check in,
  attendance downloads as CSV
- **Notifications:** bell icon with unread count for join requests, approvals and decisions
- **Reports:** DOSA sees events, registrations and turnout per club

## How to run it (Windows)

```bash
# 1. Create and activate a virtual environment (first time only)
python -m venv venv
venv\Scripts\activate

# 2. Install Django
pip install -r requirements.txt

# 3. Create the database tables
python manage.py migrate

# 4. (Optional) Load demo data
python manage.py seed_demo

# 5. Start the server, then open http://127.0.0.1:8000
python manage.py runserver
```

On macOS/Linux, activate with `source venv/bin/activate`.

### Demo accounts (after `seed_demo`)

All demo accounts use the password `clubhub2026`.

| Username | Role |
| --- | --- |
| `dosa` | DOSA admin (can also open `/admin/`) |
| `rafi` | Executive of IUB Computer Club |
| `tasnia` | Executive of IUB Debate Club and IUB Photography Club |
| `nadia`, `mim`, `arif` | Students |

### Run the tests

```bash
python manage.py test
```

## Project structure

```
config/          settings and main URLs
accounts/        users, roles, sign up, profile, dashboard
clubs/           clubs and memberships
events/          events, the DOSA approval workflow and the demo data command
registrations/   registrations, check-in, CSV export, reports
notifications/   in-app notifications
templates/       shared templates (base layout, home, accounts pages)
static/          CSS
```

## Tech stack

Python 3, Django 5.1, HTML/CSS with Bootstrap 5, SQLite.
