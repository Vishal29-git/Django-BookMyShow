from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.utils import timezone
import razorpay
import hmac
import hashlib
import json
import uuid
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Payment  # add Payment to your existing import

from .tasks import send_booking_confirmation_email
from .models import Movie, Theater, Seat, Booking, Genre, Language


# ✅ Movie List (Search + Filter + Sort + Pagination)
def movie_list(request):

    search_query = request.GET.get("search")
    selected_genres = request.GET.getlist("genre")
    selected_languages = request.GET.getlist("language")
    sort_by = request.GET.get("sort", "-release_date")
    page_number = request.GET.get("page", 1)

    ALLOWED_SORTS = {
        "title": "title",
        "-title": "-title",
        "rating": "rating",
        "-rating": "-rating",
        "release_date": "release_date",
        "-release_date": "-release_date",
    }
    sort_by = ALLOWED_SORTS.get(sort_by, "-release_date")

    movies_qs = Movie.objects.select_related("language").prefetch_related("genres")

    if search_query:
        movies_qs = movies_qs.filter(title__icontains=search_query)

    if selected_genres:
        movies_qs = movies_qs.filter(genres__id__in=selected_genres).distinct()

    if selected_languages:
        movies_qs = movies_qs.filter(language__id__in=selected_languages)

    movies_qs = movies_qs.order_by(sort_by)

    paginator = Paginator(movies_qs, 20)
    page_obj = paginator.get_page(page_number)

    genre_filter_qs = Movie.objects.all()
    if selected_languages:
        genre_filter_qs = genre_filter_qs.filter(language__id__in=selected_languages)

    all_genres = Genre.objects.annotate(
        movie_count=Count("movies", filter=Q(movies__in=genre_filter_qs))
    ).order_by("name")

    lang_filter_qs = Movie.objects.all()
    if selected_genres:
        lang_filter_qs = lang_filter_qs.filter(
            genres__id__in=selected_genres
        ).distinct()

    all_languages = Language.objects.annotate(
        movie_count=Count("movies", filter=Q(movies__in=lang_filter_qs))
    ).order_by("name")

    context = {
        "page_obj": page_obj,
        "movies": page_obj,
        "all_genres": all_genres,
        "all_languages": all_languages,
        "selected_genres": [int(g) for g in selected_genres],
        "selected_languages": [int(l) for l in selected_languages],
        "sort_by": sort_by,
        "total_count": movies_qs.count(),
        "search_query": search_query,
    }

    return render(request, "movies/movie_list.html", context)


# ✅ Theater List
def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)

    return render(
        request, "movies/theater_list.html", {"movie": movie, "theaters": theaters}
    )


def movie_detail(request, pk):

    movie = get_object_or_404(Movie, pk=pk)
    context = {"movie": movie}
    return render(request, "movies/movie_detail.html", context)


# ✅ Seat Booking — EMAIL CONFIRMATION ADDED HERE
@login_required(login_url="/login/")
def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater)

    if request.method == "POST":
        selected_seats = request.POST.getlist("seats")

        # ── Validation: No seat selected ──
        if not selected_seats:
            return render(
                request,
                "movies/seat_selection.html",
                {"theater": theater, "seats": seats, "error": "Please select a seat!"},
            )

        # ── Validation: More than one seat ──
        if len(selected_seats) > 1:
            return render(
                request,
                "movies/seat_selection.html",
                {
                    "theater": theater,
                    "seats": seats,
                    "error": "Please select only one seat at a time!",
                },
            )

        # ── Get the seat object ──
        seat_id = selected_seats[0]
        seat = get_object_or_404(Seat, id=seat_id, theater=theater)

        # ── Validation: Seat already booked ──
        if seat.is_booked:
            return render(
                request,
                "movies/seat_selection.html",
                {
                    "theater": theater,
                    "seats": seats,
                    "error": f"Seat {seat.seat_number} is already booked!",
                },
            )

        try:
            # ── Step 1: Save booking to database ──
            booking = Booking.objects.create(
                user=request.user,
                seat=seat,
                movie=theater.movie,
                theater=theater,
            )

            seat.is_booked = True
            seat.save()

            # ── Step 3: Build email data using YOUR model fields ──
            booking_data = {
                # User details
                "user_name": request.user.get_full_name() or request.user.username,
                "user_email": request.user.email,
                # Movie details — from booking.movie (Movie model)
                "movie_name": booking.movie.title,
                # Theater details — from booking.theater (Theater model)
                "theater_name": booking.theater.name,
                # Show date & time — theater.time is a DateTimeField
                "show_date": booking.theater.time.strftime(
                    "%d %B %Y"
                ),  # e.g. 25 December 2024
                "show_time": booking.theater.time.strftime("%I:%M %p"),  # e.g. 06:30 PM
                # You don't have screen in your model, so N/A
                "screen_number": "N/A",
                # Seat — booking.seat.seat_number (Seat model)
                # We wrap in a list because template loops over seats
                "seat_numbers": [booking.seat.seat_number],  # e.g. ['D4']
                # You don't have payment_id in model, so we use booking ID
                "payment_id": f"BMS{booking.id}",  # e.g. BMS42
                # You don't have amount in your model, so N/A
                "amount_paid": "N/A",
                # When booking was created — booked_at is auto_now_add
                "booking_date": booking.booked_at.strftime("%d %B %Y, %I:%M %p"),
            }

            # ── Step 4: Send email in background (does NOT block redirect) ──
            send_booking_confirmation_email(booking_data)

            # ── Step 5: Redirect user to profile ──
            return redirect("profile")

        except IntegrityError:
            return render(
                request,
                "movies/seat_selection.html",
                {
                    "theater": theater,
                    "seats": seats,
                    "error": f"Seat {seat.seat_number} is already booked!",
                },
                
            )
            
    return render(
        request, "movies/seat_selection.html", {"theater": theater, "seats": seats}
    )


# ─────────────────────────────────────────
# Step 1: Create a Razorpay order
# ─────────────────────────────────────────
@login_required
def initiate_payment(request, booking_id):
    """
    Called when user clicks 'Pay Now'.
    Creates a Razorpay order and shows the payment page.
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Prevent creating a second payment for the same booking
    if hasattr(booking, "payment") and booking.payment.status == "SUCCESS":
        return redirect("booking_confirmation", booking_id=booking.id)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    amount_in_paise = int(booking.total_price * 100)  # Razorpay uses paise

    # Create order on Razorpay's server
    razorpay_order = client.order.create(
        {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(uuid.uuid4()),  # unique receipt ID
        }
    )

    # Save to our database
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            "user": request.user,
            "razorpay_order_id": razorpay_order["id"],
            "amount": booking.total_price,
        },
    )

    # Schedule auto-expiry after 15 minutes (Celery task)
    from .tasks import expire_pending_payment

    expire_pending_payment.apply_async(
        args=[payment.id], countdown=900  # 15 minutes in seconds
    )

    context = {
        "booking": booking,
        "payment": payment,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": amount_in_paise,
        "currency": "INR",
    }
    return render(request, "movies/payment.html", context)


# ─────────────────────────────────────────
# Step 2: Frontend callback (DO NOT trust alone)
# ─────────────────────────────────────────
@login_required
def payment_callback(request):
    """
    Razorpay calls this after the popup closes (success or failure).
    We verify the signature here but ALSO rely on webhooks for safety.
    """
    if request.method != "POST":
        return redirect("movie_list")

    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")

    payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    params = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }

    try:
        # Verify signature — this is the security check
        client.utility.verify_payment_signature(params)

        # Signature is valid — mark as success
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = "SUCCESS"
        payment.save()

        # Confirm the booking
        payment.booking.is_confirmed = True
        payment.booking.save()

        return redirect("payment_success")

    except razorpay.errors.SignatureVerificationError:
        # Signature is WRONG — possible fraud attempt
        payment.status = "FAILED"
        payment.save()
        return redirect("payment_failed")


# ─────────────────────────────────────────
# Step 3: Webhook — the REAL source of truth
# ─────────────────────────────────────────
@csrf_exempt  # Razorpay can't send CSRF tokens
def razorpay_webhook(request):
    """
    Razorpay sends events here automatically.
    This is more reliable than the frontend callback.
    Always verify the signature before trusting it.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    # ── Security check ──────────────────────────────────
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    received_sig = request.headers.get("X-Razorpay-Signature", "")

    # Compute expected signature using HMAC-SHA256
    expected_sig = hmac.new(
        webhook_secret.encode("utf-8"), request.body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_sig, expected_sig):
        # Signature mismatch = someone is trying to fake a webhook
        return HttpResponse("Invalid signature", status=400)

    # ── Parse the event ─────────────────────────────────
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Bad JSON", status=400)

    event = payload.get("event")

    if event == "payment.captured":
        order_id = payload["payload"]["payment"]["entity"]["order_id"]

        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
        except Payment.DoesNotExist:
            return HttpResponse("Order not found", status=404)

        # ── Idempotency check — prevent double processing ──
        if payment.webhook_processed_at is not None:
            # Already processed this event — safely ignore it
            return HttpResponse("Already processed", status=200)

        # Mark as processed RIGHT NOW to block any race conditions
        payment.status = "SUCCESS"
        payment.webhook_processed_at = timezone.now()
        payment.save()

        # Confirm the booking
        payment.booking.is_confirmed = True
        payment.booking.save()

    elif event == "payment.failed":
        order_id = payload["payload"]["payment"]["entity"]["order_id"]
        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
            if payment.status == "PENDING":
                payment.status = "FAILED"
                payment.save()
        except Payment.DoesNotExist:
            pass

    return HttpResponse("OK", status=200)


# ─────────────────────────────────────────
# Step 4: Success and failure pages
# ─────────────────────────────────────────
@login_required
def payment_success(request):
    return render(request, "movies/payment_success.html")


@login_required
def payment_failed(request):
    return render(request, "movies/payment_failed.html")

    return render(
        request, "movies/seat_selection.html", {"theater": theater, "seats": seats}
    )
