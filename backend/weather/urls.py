from django.urls import path
from .views import (
    RollingAverageAPIView,
    WeatherDataCollectAPIView,
    WeatherRawDataListView,
)

urlpatterns = [
    path(
        "weather/sync/",
        WeatherDataCollectAPIView.as_view(),
        name="weather-sync",
    ),
    path(
        "weather/rolling-averages/",
        RollingAverageAPIView.as_view(),
        name="rolling-average",
    ),
    path(
        "weather/data/",
        WeatherRawDataListView.as_view(),
        name="weather-raw-data-list",
    ),
]
