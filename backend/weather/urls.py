from django.urls import path
from .views import RollingAverageAPIView, WeatherDataCollectAPIView, RawDataListAPIView

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
        "weather/raw-data/",
        RawDataListAPIView.as_view(),
        name="raw-data",
    ),
]
