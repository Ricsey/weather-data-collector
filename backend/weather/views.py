from django.shortcuts import render
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from weather.serializers import RollingAverageRequestSerializer
from weather.repositories.weather_repository import DjangoWeatherDataRepository
from weather.services.weather_services import (
    RollingAverageService,
    WeatherDataCollectorService,
    WeatherDataValidationService,
)
from weather.utils.weather_fetchers import HungarometWeatherFetcher
from weather.utils.utils import convert_to_records


logger = logging.getLogger("weather")


class WeatherDataAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            logger.debug(f"POST request to {self.__class__.__name__} started.")
            repository = DjangoWeatherDataRepository()
            fetcher = HungarometWeatherFetcher(city="Budapest")
            collector_service = WeatherDataCollectorService(fetcher=fetcher)

            collector_service.collect_historical_data()
            data = collector_service.get_data()

            validator_service = WeatherDataValidationService(dataframe=data)
            validator_service.clean_data()
            clean_data = validator_service.get_cleaned_data()

            records = convert_to_records(clean_data)

            repository.save_all(records)

            logger.debug(
                f"POST request to {self.__class__.__name__} finished successfully."
            )
            return Response(
                {"status": "success"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"POST request to {self.__class__.__name__} failed.\n{e}")
            return Response(
                {"status": "error", "message": str(e)},
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
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(data, status=status.HTTP_200_OK)
