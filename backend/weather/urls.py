from django.urls import path
from .views import RollingAverageAPIView, WeatherDataAPIView

urlpatterns = [
    path("weather/collect-data/", WeatherDataAPIView.as_view(), name="weather_data"),
    path(
        "weather/rolling-average/",
        RollingAverageAPIView.as_view(),
        name="rolling-average",
    ),
]
