from django.urls import path
from .views import RollingAverageAPIView, WeatherDataCollectAPIView

urlpatterns = [
    path(
        "weather/sync/",
        WeatherDataCollectAPIView.as_view(),
        name="weather-sync",
    ),
    path(
        "weather/rolling-average/",
        RollingAverageAPIView.as_view(),
        name="rolling-average",
    ),
]
