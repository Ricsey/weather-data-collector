from functools import wraps
import logging
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
                city=str(row["city"]),
            )
        )
    return records


def log_action(action: str, logger: logging.Logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"{action} started.")
            result = func(*args, **kwargs)
            logger.info(f"{action} finished successfully")
            return result

        return wrapper

    return decorator


def log_debug_action(action: str, logger: logging.Logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"{action} started.")
            result = func(*args, **kwargs)
            logger.debug(f"{action} finished successfully")
            return result

        return wrapper

    return decorator
