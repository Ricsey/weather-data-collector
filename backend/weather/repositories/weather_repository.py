from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import Enum
from django.db import transaction

from ..models import WeatherData


class WeatherDataFields(Enum):
    T_MAX = "t_max"
    T_MEAN = "t_mean"
    T_MIN = "t_min"


@dataclass
class WeatherRecord:
    time: date
    t_max: float
    t_mean: float
    t_min: float
    city: str

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            WeatherDataFields.T_MAX.value: self.t_max,
            WeatherDataFields.T_MEAN.value: self.t_mean,
            WeatherDataFields.T_MIN.value: self.t_min,
            "city": self.city,
        }

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            WeatherDataFields.T_MAX.value: self.t_max,
            WeatherDataFields.T_MEAN.value: self.t_mean,
            WeatherDataFields.T_MIN.value: self.t_min,
            "city": self.city,
        }


class WeatherDataRepository(ABC):
    @abstractmethod
    def save_all(self, records: list[WeatherRecord]) -> None:
        pass

    @abstractmethod
    def get_all(self) -> list[WeatherRecord]:
        pass

    @abstractmethod
    def get(
        self,
        city: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> list[WeatherRecord]:
        pass

    @abstractmethod
    def exists_for_city(self, city: str) -> bool:
        pass


class DjangoWeatherDataRepository(WeatherDataRepository):
    def get_all(self) -> list[WeatherRecord]:
        qs = WeatherData.objects.all()
        return [
            WeatherRecord(
                time=obj.time,
                t_max=obj.t_max,
                t_mean=obj.t_mean,
                t_min=obj.t_min,
                city=obj.city,
            )
            for obj in qs
        ]

    def get(
        self,
        city: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> list[WeatherRecord]:
        qs = WeatherData.objects.all()

        if city is not None:
            qs = qs.filter(city=city)
        if start_date is not None:
            qs = qs.filter(time__gte=start_date)
        if end_date is not None:
            qs = qs.filter(time__lte=end_date)
        if limit is not None:
            qs = qs[:limit]

        return [
            WeatherRecord(
                time=obj.time,
                t_max=obj.t_max,
                t_mean=obj.t_mean,
                t_min=obj.t_min,
                city=obj.city,
            )
            for obj in qs
        ]

    @transaction.atomic
    def save_all(self, records: list[WeatherRecord]) -> None:
        """
        Persist all WeatherRecord entities to the database.

        Efficiently handles:
        - New records → created
        - Existing records (with changed values) → updated
        - Existing records (identical values) → skipped
        """

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
                    )
                )
            else:
                if (
                    existing.t_max != record.t_max
                    or existing.t_mean != record.t_mean
                    or existing.t_min != record.t_min
                ):
                    existing.t_max = record.t_max
                    existing.t_mean = record.t_mean
                    existing.t_min = record.t_min
                    to_update.append(existing)

        if to_create:
            WeatherData.objects.bulk_create(to_create)

        if to_update:
            WeatherData.objects.bulk_update(
                to_update, [field.value for field in WeatherDataFields]
            )

    def exists_for_city(self, city: str) -> bool:
        return WeatherData.objects.filter(city=city).exists()
