from django.urls import path
from .views import WeatherDataAPIView

urlpatterns = [
    path("weather_data/", WeatherDataAPIView.as_view(), name="weather_data"),
]
