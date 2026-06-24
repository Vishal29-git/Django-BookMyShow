from django.urls import path
from . import views

app_name = "movies"

urlpatterns = [
    path("", views.movie_list, name="movie_list"),
    path("<int:movie_id>/theaters", views.theater_list, name="theater_list"),
    path("theater/<int:theater_id>/seats/book/", views.book_seats, name="book_seats"),
    path("movie/<int:pk>/", views.movie_detail, name="movie-detail"),
    path('payment/<int:booking_id>/',   views.initiate_payment,  name='initiate_payment'),
    path('payment/callback/',           views.payment_callback,  name='payment_callback'),
    path('payment/webhook/',            views.razorpay_webhook,  name='razorpay_webhook'),
    path('payment/success/',            views.payment_success,   name='payment_success'),
    path('payment/failed/',             views.payment_failed,    name='payment_failed'),
]
