from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from django.db import transaction
import logging

from ..models import WeatherData


logger = logging.getLogger("weather")


@dataclass
class WeatherRecord:
    time: date
    t_max: float
    t_mean: float
    t_min: float
    city: str


class WeatherDataRepository(ABC):
    @abstractmethod
    def save_all(self, records: list[WeatherRecord]) -> None:
        pass


class DjangoWeatherDataRepository(WeatherDataRepository):
    @transaction.atomic
    def save_all(self, records: list[WeatherRecord]) -> None:
        """
        Persist all WeatherRecord entities to the database.

        Efficiently handles:
        - New records → created
        - Existing records (with changed values) → updated
        - Existing records (identical values) → skipped
        """
        logger.debug("Saving weather data to db started.")

        if not records:
            return

        record_map = {r.time: r for r in records}
        record_dates = list(record_map.keys())

        existing_qs = WeatherData.objects.filter(time__in=record_dates)
        existing_map = {obj.time: obj for obj in existing_qs}
        to_create: list[WeatherData] = []
        to_update: list[WeatherData] = []

        for date_, record in record_map.items():
            existing = existing_map.get(date_)

            if existing is None:
                to_create.append(
                    WeatherData(
                        time=record.time,
                        t_max=record.t_max,
                        t_mean=record.t_mean,
                        t_min=record.t_min,
                        city=record.city,
                    )
                )
            else:
                if (
                    existing.t_max != record.t_max
                    or existing.t_mean != record.t_mean
                    or existing.t_min != record.t_min
                    or existing.city != record.city
                ):
                    existing.t_max = record.t_max
                    existing.t_mean = record.t_mean
                    existing.t_min = record.t_min
                    existing.city = record.city
                    to_update.append(existing)

        if to_create:
            WeatherData.objects.bulk_create(to_create)

        if to_update:
            WeatherData.objects.bulk_update(to_update, ["t_max", "t_mean", "t_min"])

        logger.debug("Saving weather data to db finished successfully.")
