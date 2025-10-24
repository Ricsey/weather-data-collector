from rest_framework.pagination import PageNumberPagination


class WeatherDataPagination(PageNumberPagination):
    """Custom pagination for weather data."""

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class RollingAveragePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
