# Travel Buddy — Solo Traveller Companion Platform

A Flask + MySQL web app for solo travellers to publish trips, find compatible routes, request to join trips, and communicate after mutual acceptance.

## Features
- Registration/login with Werkzeug password hashing and Flask sessions
- Profile editing and emergency-contact field
- Publish, search, edit, and cancel bike/car/van trips
- Route substring search, exact or ±1-day date matching, and relevance ranking
- Join requests with owner-only accept/decline controls
- Mutual-consent chat: available only after a request is accepted
- Reviews (1–5 stars) for the trip owner after the trip date
- Safety guidance page and role-based access checks
- Responsive UI, form validation, flash messages, and 403/404 pages

## Important limitations
This is a portfolio/demo project, not a production safety service. Route matching uses text fields and a simple heuristic; it does not calculate geographic distance or actual route overlap. ID verification, live GPS sharing, SMS/push notifications, and a real emergency SOS dispatch are **not integrated**. The safety page explains that SOS is a demo workflow and must not replace emergency services. Do not enter real sensitive information in a public demo.

Before production use, add CSRF protection, email verification, rate limiting, password reset, secure cookie settings, audit logging, privacy/retention controls, moderation/reporting, tests, deployment hardening, and real vetted integrations for identity/location/notifications.

## Setup (Windows PowerShell)
1. Install Python 3.11+ and MySQL 8+.
2. Create a database:
   ```sql
   CREATE DATABASE travel_buddy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. In this project directory:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Edit `.env` and set your MySQL password and a strong `SECRET_KEY`.
5. Run:
   ```powershell
   flask --app app init-db
   flask --app app run
   ```
   Or `python app.py` (creates tables at startup).
6. Open http://127.0.0.1:5000 and register an account.

## Setup (macOS/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MySQL credentials
flask --app app init-db
flask --app app run
```

## Configuration
`DATABASE_URL` supports the standard SQLAlchemy URL format. Default is `mysql+pymysql://root:password@localhost/travel_buddy`. Never commit `.env`.

## Suggested manual smoke tests
- Register, log out, and log in again with the same account.
- Publish a future trip and confirm it appears in trip search.
- Search by origin/destination and test exact date vs ±1 day.
- Attempt to edit/cancel another user's trip; the server should return 403.
- Send a join request from a second account; owner accepts; both participants can chat.
- Confirm a user who is not part of an accepted request cannot view its chat.
- Submit a review after the trip date and verify duplicate reviews are rejected.

## Project structure
```
travel_buddy/
├── app.py
├── requirements.txt
├── schema.sql
├── .env.example
├── templates/
└── static/
```
