from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError


def movie_list(request):
    search_query = request.GET.get("search")
    if search_query:
        movies = Movie.objects.filter(name__icontains=search_query)
    else:
        movies = Movie.objects.all()
    return render(request, "movies/movie_list.html", {"movies": movies})


def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theater = Theater.objects.filter(movie=movie)
    return render(
        request, "movies/theater_list.html", {"movie": movie, "theaters": theater}
    )


@login_required(login_url="/login/")
def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater)

    if request.method == "POST":
        selected_seats = request.POST.getlist("seats")

        if not selected_seats:
            return render(
                request,
                "movies/seat_selection.html",
                {"theater": theater, "seats": seats, "error": "Please select a seat!"},
            )

        # ✅ Allow only ONE seat at a time
        if len(selected_seats) > 1:
            return render(
                request,
                "movies/seat_selection.html",
                {"theater": theater, "seats": seats, "error": "Please select only one seat at a time!"},
            )

        seat_id = selected_seats[0]  # ✅ get only first seat
        seat = get_object_or_404(Seat, id=seat_id, theater=theater)

        if seat.is_booked:
            return render(
                request,
                "movies/seat_selection.html",
                {"theater": theater, "seats": seats, "error": f"Seat {seat.seat_number} is already booked!"},
            )

        try:
            Booking.objects.create(
                user=request.user,
                seat=seat,
                movie=theater.movie,
                theater=theater
            )
            seat.is_booked = True
            seat.save()
            return redirect("profile")  # ✅ redirect to profile after booking

        except IntegrityError:
            return render(
                request,
                "movies/seat_selection.html",
                {"theater": theater, "seats": seats, "error": f"Seat {seat.seat_number} is already booked!"},
            )

    return render(
        request,
        "movies/seat_selection.html",
        {"theater": theater, "seats": seats},
    )
