from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from weather.repositories.weather_repository import DjangoWeatherDataRepository
from weather.services.weather_services import (
    WeatherDataCollectorService,
    WeatherDataValidationService,
)
from weather.utils.weather_fetchers import HungarometWeatherFetcher
from weather.utils.utils import convert_to_records


class WeatherDataAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
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

            return Response(
                {"status": "success"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
