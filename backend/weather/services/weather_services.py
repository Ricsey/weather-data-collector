from datetime import date
import logging
from typing import Optional
import pandas as pd
from weather.repositories.weather_repository import (
    WeatherDataRepository,
    WeatherRecord,
)
from weather.utils.weather_fetchers import WeatherFetcher
from weather.utils.utils import log_action

logger = logging.getLogger("weather")


class WeatherDataCollectorService:
    def __init__(
        self,
        fetcher: WeatherFetcher,
    ):
        self.fetcher = fetcher
        self.df = None
        self.records: list[WeatherRecord] = []

    @log_action(action="Collecting historical data", logger=logger)
    def collect_historical_data(self) -> None:
        logger.info("Collecting historical data started.")
        self.df = self.fetcher.fetch()
        logger.info("Collecting historical data finished successfully.")

    def get_data(self):
        return self.df.copy()


class WeatherDataValidationService:
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    @log_action(action="Cleaning data", logger=logger)
    def clean_data(self):
        self.clean_types()
        self.check_missing_dates()
        self.check_missing_values()
        self.check_duplicates()
        self.check_sanity()
        self.check_consistency()
        self.clean_missing_values()

    @log_action(action="Cleaning types", logger=logger)
    def clean_types(self):
        logger.info("Cleaning types started.")
        for col in ["t_max", "t_mean", "t_min"]:
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        if not pd.api.types.is_datetime64_any_dtype(self.df["Time"]):
            self.df["Time"] = pd.to_datetime(self.df["Time"], format="%Y%m%d")
        logger.info("Cleaning types finished successfully.")

    @log_action(action="Cleaning missing values", logger=logger)
    def clean_missing_values(self):
        logger.info("Cleaning missing values started.")
        """Interpolating missing values with linear interpolation"""
        self.df[["t_max", "t_mean", "t_min"]] = self.df[
            ["t_max", "t_mean", "t_min"]
        ].interpolate(method="linear")
        logger.info("Cleaning missing values finished successfully.")

    @log_action(action="Checking missing dates", logger=logger)
    def check_missing_dates(self):
        logger.info("Checking missing dates started.")
        full_index = pd.date_range(self.df.index.min(), self.df.index.max(), freq="D")
        missing_dates = full_index.difference(self.df.index)
        if len(missing_dates) > 0:
            logger.warning(f"Missing dates: {missing_dates}")

    @log_action(action="Checking missing values", logger=logger)
    def check_missing_values(self):
        missing = self.df[["t_max", "t_mean", "t_min"]].isna()

        if missing.any().any():
            for col in ["t_max", "t_mean", "t_min"]:
                missing_dates = self.df.index[missing[col]].tolist()
                if missing_dates:
                    logger.warning(f"Missing values in {col} at dates: {missing_dates}")

    @log_action(action="Checking duplicates", logger=logger)
    def check_duplicates(self):
        logger.info("Checking duplicates started.")
        duplicates = self.df.index[self.df.index.duplicated()]
        if len(duplicates) > 0:
            logger.warning(f"Duplicates found at dates: {duplicates}")
            self.df = self.df[~self.df.index.duplicated(keep="first")]
        logger.info("Checking finished successfullz.")

    @log_action(action="Checking sanity", logger=logger)
    def check_sanity(self):
        logger.info("Rule: -50 °C < t < 60 °C.")
        min_temp = -50
        max_temp = 60

        for col in ["t_max", "t_mean", "t_min"]:
            invalid = self.df[(self.df[col] < min_temp) | (self.df[col] > max_temp)]
            if not invalid.empty:
                logger.warning(
                    f"{col} has unrealistic values at dates: {invalid.index.tolist()}"
                )
        logger.info("Checking sanity finished succesfully.")

    @log_action(action="Checking consistency", logger=logger)
    def check_consistency(self):
        logger.info("Checking consistency started.")
        inconsistent = self.df[
            (self.df["t_min"] > self.df["t_mean"])
            | (self.df["t_mean"] > self.df["t_max"])
        ]
        if not inconsistent.empty:
            logger.warning(
                f"Inconsistent temperature values at dates: {inconsistent.index.tolist()}",
                f"{inconsistent}",
            )
        logger.info("Checking consistency finished successfully.")

    def get_cleaned_data(self):
        return self.df.copy()


class RollingAverageService:
    def __init__(self, repository: WeatherDataRepository):
        self.repository = repository

    @log_action(action="Calculating rolling averages", logger=logger)
    def calculate(
        self,
        city: str,
        window: int = 7,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        records = self.repository.get(
            city=city, start_date=start_date, end_date=end_date
        )

        if not records:
            return []

        result_df = pd.DataFrame()

        df = pd.DataFrame([r.to_dict() for r in records])
        df = df.sort_values("time").set_index("time")

        result_df["t_max_avg"] = (
            df[WeatherDataFields.T_MAX.value]
            .rolling(window=window, min_periods=1)
            .mean()
        )
        result_df["t_mean_avg"] = (
            df[WeatherDataFields.T_MEAN.value]
            .rolling(window=window, min_periods=1)
            .mean()
        )
        result_df["t_min_avg"] = (
            df[WeatherDataFields.T_MIN.value]
            .rolling(window=window, min_periods=1)
            .mean()
        )

        return result_df.reset_index().to_dict(orient="records")
