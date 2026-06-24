from django.contrib import admin
from .models import Movie, Theater, Seat, Booking, Genre, Language  # ← only ONE import line


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display      = ['title', 'language', 'rating', 'release_date', 'trailer_url']  # ← just add trailer_url here
    list_filter       = ['genres', 'language']
    search_fields     = ['title']
    filter_horizontal = ['genres']


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'movie', 'time']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater', 'seat_number', 'is_booked']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'seat', 'movie', 'theater', 'booked_at']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display  = ['name']
    search_fields = ['name']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display  = ['name']
    search_fields = ['name']