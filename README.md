# 🎬 BookMyShow — Movie Ticket Booking System

## 🛠️ Tech Stack

- 🐍 Python
- 🌐 Django
- 🗄️ PostgreSQL
- ⚡ Redis
- 💳 Razorpay
- 🎨 HTML
- 🎨 CSS
- 🚀 Vercel — Deployment

## ✨ Features

- 🎭 **Genre & Language Filtering**
  - Server-side multi-select filtering for genres and languages.
  - Optimized database queries for large movie catalogs.
  - Pagination and sorting with combined filters.
  - Dynamic filter counts based on selected criteria.
  - Query optimization and indexing to reduce inefficient database scans.

- 📧 **Automated Booking Confirmation**
  - Automatically sends booking confirmation emails after successful payment.
  - Includes movie, show timing, seat numbers, payment ID, and theater details.
  - Uses email templates for consistent formatting.
  - Implements background processing and retry handling for failed emails.
  - Maintains logs for monitoring email delivery failures.

- ▶️ **Secure YouTube Trailer Integration**
  - Embeds movie trailers securely on movie detail pages.
  - Validates trailer URLs before embedding.
  - Implements lazy loading for better page performance.
  - Handles unavailable or removed trailers with fallback behavior.
  - Applies security practices to reduce XSS risks.

- 💳 **Secure Payment Gateway**
  - Integrated Razorpay for online ticket payments.
  - Implements server-side payment verification.
  - Handles successful, failed, cancelled, and duplicate transactions.
  - Uses idempotency and webhook verification to prevent duplicate bookings.
  - Handles payment timeouts and partial failures securely.

- 🎟️ **Concurrency-Safe Seat Reservation**
  - Temporarily locks selected seats before payment completion.
  - Prevents multiple users from booking the same seat simultaneously.
  - Uses database-level transactions for safe seat reservation.
  - Automatically releases expired seat reservations.
  - Handles network interruptions, app closure, and concurrent booking attempts.

- 📊 **Admin Analytics Dashboard**
  - Displays daily, weekly, and monthly revenue.
  - Tracks popular movies based on bookings.
  - Provides theater occupancy and peak booking-hour analytics.
  - Tracks cancellation rates.
  - Uses database-level aggregation for large datasets.
  - Implements caching to improve dashboard performance.
  - Includes role-based authentication for secure admin access.

## 📁 Folder Structure

```text
bookmyseat/
├── 📂 bookmyseat/
├── 📂 media/
│   ├── 📂 movies/
│   └── 📂 posters/
│
├── 📂 movies/
│   ├── 📂 migrations/
│   ├── 📂 templates/
│   │   └── 📂 movies/
│   ├── 📄 __init__.py
│   ├── 📄 admin.py
│   ├── 📄 apps.py
│   ├── 📄 models.py
│   ├── 📄 tasks.py
│   ├── 📄 tests.py
│   ├── 📄 urls.py
│   └── 📄 views.py
│
├── 📂 users/
│   ├── 📂 migrations/
│   ├── 📂 templates/
│   │   └── 📂 users/
│   ├── 📄 __init__.py
│   ├── 📄 admin.py
│   ├── 📄 apps.py
│   ├── 📄 forms.py
│   ├── 📄 models.py
│   ├── 📄 tests.py
│   ├── 📄 urls.py
│   └── 📄 views.py
│
├── 🔐 .env
├── 🚫 .gitignore
├── 🗄️ db.sqlite3
├── 📄 email_errors.log
├── 🐍 manage.py
├── 📦 requirements.txt
└── 🚀 vercel.json
