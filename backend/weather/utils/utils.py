import pandas as pd
from weather.repositories.weather_repository import WeatherRecord


def convert_to_records(df: pd.DataFrame) -> list[WeatherRecord]:
    records = []
    for _, row in df.iterrows():
        records.append(
            WeatherRecord(
                time=pd.to_datetime(row["Time"]).date(),
                t_max=float(row["t_max"]),
                t_mean=float(row["t_mean"]),
                t_min=float(row["t_min"]),
            )
        )
    return records
