from django.db import models
from django.contrib.auth.models import User
from django.db import models
import re
import uuid
from django.db import models
from django.contrib.auth.models import User


# ---------- Genre ----------
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"], name="genre_name_idx"),
        ]

    def __str__(self):
        return self.name


# ---------- Language ----------
class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"], name="language_name_idx"),
        ]

    def __str__(self):
        return self.name


# ---------- Movie ----------
class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    poster = models.ImageField(upload_to="posters/", blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    genres = models.ManyToManyField(Genre, blank=True, related_name="movies")
    language = models.ForeignKey(
        Language,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="movies",
    )
    trailer_url = models.URLField(
        blank=True,
        null=True,
        help_text="Paste the full YouTube video URL here (e.g. https://www.youtube.com/watch?v=abc123)",
    )

    def get_safe_trailer_embed_id(self):

        if not self.trailer_url:
            return None

        pattern = (
            r"(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
        )
        match = re.search(pattern, self.trailer_url)

        if match:
            return match.group(1)
        return None

    class Meta:
        indexes = [
            models.Index(fields=["title"], name="movie_title_idx"),
            models.Index(fields=["-rating"], name="movie_rating_idx"),
            models.Index(fields=["-release_date"], name="movie_release_idx"),
        ]

    def __str__(self):
        return self.title


# ---------- Theater ----------
class Theater(models.Model):
    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="theaters")
    time = models.DateTimeField()

    def __str__(self):
        return f"{self.name} - {self.movie.title} at {self.time}"


# ---------- Seat ----------
class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.seat_number} in {self.theater.name}"


# ---------- Booking ----------
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    ]

    # Links this payment to a booking (use your actual Booking model name)
    booking = models.OneToOneField(
        "Booking", on_delete=models.CASCADE, related_name="payment"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Razorpay IDs
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)

    # Idempotency key — prevents double processing
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default="INR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    # For replay attack prevention
    webhook_processed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.razorpay_order_id} - {self.status}"

    def __str__(self):
        return f"Booking by {self.user.username} for {self.seat.seat_number} at {self.theater.name}"
