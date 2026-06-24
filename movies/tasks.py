# movies/tasks.py
# Simplified version — works on Render and Vercel without Redis/Celery

import logging
import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("email_tasks")


def send_booking_confirmation_email(booking_data):
    """
    Sends email in a background thread.
    No Redis or Celery needed — works on Render and Vercel!
    """

    def send_email_thread():
        # Retry logic — tries up to 3 times
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"📧 Attempt {attempt}: Sending email to {booking_data['user_email']}"
                )

                # Fill the HTML template with booking data
                html_content = render_to_string(
                    "movies/booking_confirmation_email.html",
                    {
                        "user_name": booking_data["user_name"],
                        "movie_name": booking_data["movie_name"],
                        "theater_name": booking_data["theater_name"],
                        "show_date": booking_data["show_date"],
                        "show_time": booking_data["show_time"],
                        "screen_number": booking_data["screen_number"],
                        "seat_numbers": booking_data["seat_numbers"],
                        "payment_id": booking_data["payment_id"],
                        "amount_paid": booking_data["amount_paid"],
                        "booking_date": booking_data["booking_date"],
                    },
                )

                # Plain text fallback
                text_content = f"""
Hi {booking_data['user_name']},
Your booking is confirmed!

Movie     : {booking_data['movie_name']}
Theater   : {booking_data['theater_name']}
Date      : {booking_data['show_date']}
Time      : {booking_data['show_time']}
Seats     : {', '.join(booking_data['seat_numbers'])}
Payment ID: {booking_data['payment_id']}
Amount    : Rs. {booking_data['amount_paid']}

Enjoy the show!
Team BookMySeat
                """

                # Build and send the email
                email = EmailMultiAlternatives(
                    subject=f"🎬 Booking Confirmed - {booking_data['movie_name']} | BookMySeat",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[booking_data["user_email"]],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)

                logger.info(f"✅ Email sent to {booking_data['user_email']}")
                break  # ← Success! Stop retrying

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {str(e)}")
                if attempt == max_retries:
                    logger.error(
                        f"🚫 All {max_retries} attempts failed for {booking_data['user_email']}"
                    )

    # 🚀 Run the email function in a background thread
    # This means your API response is NOT blocked — same benefit as Celery!
    thread = threading.Thread(target=send_email_thread)
    thread.daemon = True  # Thread will stop if the main app stops
    thread.start()


from celery import shared_task
from django.utils import timezone


@shared_task
def expire_pending_payment(payment_id):
    """
    Called automatically 15 minutes after payment is created.
    If the user never completed payment, we expire it and release seats.
    """
    from .models import Payment

    try:
        payment = Payment.objects.get(id=payment_id, status="PENDING")
        payment.status = "EXPIRED"
        payment.save()

        # Release the seats so others can book them
        booking = payment.booking
        booking.is_confirmed = False
        booking.save()

    except Payment.DoesNotExist:
        # Payment was already processed — nothing to do
        pass
