from django.urls import path
from .views import RollingAverageAPIView, WeatherDataCollectAPIView

urlpatterns = [
    path(
        "weather/collect-data/",
        WeatherDataCollectAPIView.as_view(),
        name="weather_data",
    ),
    path(
        "weather/rolling-average/",
        RollingAverageAPIView.as_view(),
        name="rolling-average",
    ),
]
