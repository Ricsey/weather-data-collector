from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
import logging
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyViewSet

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
    def post(self, request):
        """
        Calculates the rolling average for weather data.

        Request body:
            {
                "city": "CityName",
                "window": integer,
                "start_date": "YYYY-MM-DD",  # optional
                "end_date": "YYYY-MM-DD"     # optional
            }

        Response:
            [
                {
                    "date": "YYYY-MM-DD",
                    "t_max_avg": float,
                    "t_mean_avg": float,
                    "t_min_avg": float
                },
                ...
            ]
        """
        try:
            serializer = RollingAverageRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data
            city = validated_data["city"]
            window = validated_data["window"]
            start_date = validated_data.get("start_date")
            end_date = validated_data.get("end_date")

            repository = DjangoWeatherDataRepository()
            service = RollingAverageService(repository)

            data = service.calculate(
                city=city, window=window, start_date=start_date, end_date=end_date
            )
        except Exception as e:
            logger.error(f"Error in RollingAverageAPIView: {e}", exc_info=True)
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(data, status=status.HTTP_200_OK)
