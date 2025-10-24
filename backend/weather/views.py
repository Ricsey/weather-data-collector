from django_filters.rest_framework import DjangoFilterBackend
import logging
from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from weather.paginations import RollingAveragePagination, WeatherDataPagination
from weather.models import WeatherData
from weather.serializers import (
    RollingAverageRequestSerializer,
    WeatherDataSerializer,
    WeatherSyncRequestSerializer,
)
from weather.repositories.weather_repository import DjangoWeatherDataRepository
from weather.services.weather_services import (
    RollingAverageService,
    WeatherDataCollectorService,
    WeatherDataValidationService,
)
from weather.utils.weather_fetchers import HungarometWeatherFetcher
from weather.utils.utils import convert_to_records


logger = logging.getLogger("weather")


class WeatherDataCollectAPIView(APIView):
    def post(self, request):
        """
        Fetch and store weather data for a city.

        POST /api/v1/weather/sync/

        Request Body:
            {
                "city": "Budapest",
                "force": false
            }

        Response:
            {
                "status": "success",
                "message": "Weather data synced successfully for Budapest",
                "data": {
                    "city": "Budapest",
                }
            }
        """

        serializer = WeatherSyncRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        city = serializer.validated_data["city"]
        force = serializer.validated_data.get("force", False)

        try:
            logger.debug(f"POST request to {self.__class__.__name__} started.")
            repository = DjangoWeatherDataRepository()
            fetcher = HungarometWeatherFetcher(city=city)
            collector_service = WeatherDataCollectorService(fetcher=fetcher)

            if force or not repository.exists_for_city("Budapest"):
                collector_service.collect_historical_data()
                data = collector_service.get_data()

                validator_service = WeatherDataValidationService(dataframe=data)
                validator_service.clean_data()
                clean_data = validator_service.get_cleaned_data()

                records = convert_to_records(clean_data)

                repository.save_all(records)
            else:
                logger.info(
                    "Data for Budapest already exists in the database. Skipping fetch."
                )
                return Response(
                    {
                        "status": "success",
                        "message": f"Data for {city} already exists. Use force=true to re-sync.",
                        "data": {"city": city, "skipped": True},
                    },
                    status=status.HTTP_200_OK,
                )

            logger.debug(
                f"POST request to {self.__class__.__name__} finished successfully."
            )
            return Response(
                {"status": "success"},
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            logger.error(f"Validation error during sync for {city}: {e}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"POST request to {self.__class__.__name__} failed.\n{e}")
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred during sync",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RollingAverageAPIView(APIView):
    pagination_class = RollingAveragePagination

    def get(self, request):
        """
        Calculates the rolling average for weather data.

        GET /api/v1/weather/data/rolling-averages/?city=Budapest&page=4

        Query Parameters:
            - city: str (required) - City name
            - window: int (default: 7) - Number of days for rolling average
            - start_date: YYYY-MM-DD (optional) - Start date
            - end_date: YYYY-MM-DD (optional) - End date
        """
        serializer = RollingAverageRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        validated_data = serializer.validated_data
        city = validated_data["city"]
        window = validated_data["window"]
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")

        try:
            repository = DjangoWeatherDataRepository()
            if not repository.exists_for_city(city):
                return Response(
                    {
                        "status": "error",
                        "message": f"No weather data found for {city}. Please sync data first.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            service = RollingAverageService(repository)
            data = service.calculate(
                city=city,
                window=window,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            logger.error(f"Error in RollingAverageAPIView: {e}", exc_info=True)
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred while calculating rolling averages",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(data, request)
        return Response(
            {
                "status": "success",
                "message": "Rolling averages calculated successfully",
                "data": paginated_data,
            },
            status=status.HTTP_200_OK,
        )


class WeatherRawDataListView(generics.ListAPIView):
    """
    List weather data records with filtering and pagination.

    GET /api/v1/weather/data/raw/?city=Budapest&start_date=2024-01-01&page=1&page_size=100

    Query Parameters:
        - city: str (optional) - Filter by city
        - time__gte: YYYY-MM-DD (optional) - Filter from date (start_date)
        - time__lte: YYYY-MM-DD (optional) - Filter to date (end_date)
        - page: int (default: 1) - Page number
        - page_size: int (default: 100, max: 1000) - Records per page
    """

    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    pagination_class = WeatherDataPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "city": ["exact"],
        "time": ["gte", "lte", "exact"],
    }
    ordering_fields = ["time"]
    ordering = ["time"]
