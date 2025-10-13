from django.core.management.base import BaseCommand, CommandError

from weather.utils.utils import convert_to_records
from weather.repositories.weather_repository import DjangoWeatherDataRepository
from weather.services.weather_services import (
    WeatherDataCollectorService,
    WeatherDataValidationService,
)
from weather.utils.weather_fetchers import HungarometWeatherFetcher


class Command(BaseCommand):
    def handle(self, *args, **options):
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
