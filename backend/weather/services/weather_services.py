import logging
import pandas as pd
from weather.repositories.weather_repository import (
    WeatherDataRepository,
    WeatherRecord,
)
from weather.utils.weather_fetchers import WeatherFetcher


logger = logging.getLogger("weather")


class WeatherDataCollectorService:
    def __init__(
        self,
        fetcher: WeatherFetcher,
    ):
        self.fetcher = fetcher
        self.df = None
        self.records: list[WeatherRecord] = []

    def collect_historical_data(self) -> None:
        logger.info("Collecting historical data started.")
        self.df = self.fetcher.fetch()
        logger.info("Collecting historical data finished successfully.")

    def get_data(self):
        return self.df.copy()


class WeatherDataValidationService:
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def clean_data(self):
        self.clean_types()
        self.check_missing_dates()
        self.check_missing_values()
        self.check_duplicates()
        self.check_sanity()
        self.check_consistency()
        self.clean_missing_values()

    def clean_types(self):
        logger.info("Cleaning types started.")
        for col in ["t_max", "t_mean", "t_min"]:
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        if not pd.api.types.is_datetime64_any_dtype(self.df["Time"]):
            self.df["Time"] = pd.to_datetime(self.df["Time"], format="%Y%m%d")
        logger.info("Cleaning types finished successfully.")

    def clean_missing_values(self):
        logger.info("Cleaning missing values started.")
        """Interpolating missing values with linear interpolation"""
        self.df[["t_max", "t_mean", "t_min"]] = self.df[
            ["t_max", "t_mean", "t_min"]
        ].interpolate(method="linear")
        logger.info("Cleaning missing values finished successfully.")

    def check_missing_dates(self):
        logger.info("Checking missing dates started.")
        full_index = pd.date_range(self.df.index.min(), self.df.index.max(), freq="D")
        missing_dates = full_index.difference(self.df.index)
        if len(missing_dates) > 0:
            logger.warning(f"Missing dates: {missing_dates}")
        logger.info("Checking missing dates finished successfully.")

    def check_missing_values(self):
        logger.info("Checking missing values started.")

        missing = self.df[["t_max", "t_mean", "t_min"]].isna()

        if missing.any().any():
            for col in ["t_max", "t_mean", "t_min"]:
                missing_dates = self.df.index[missing[col]].tolist()
                if missing_dates:
                    logger.warning(f"Missing values in {col} at dates: {missing_dates}")
        logger.info("Checking missing values finished successfullz.")

    def check_duplicates(self):
        logger.info("Checking duplicates started.")
        duplicates = self.df.index[self.df.index.duplicated()]
        if len(duplicates) > 0:
            logger.warning(f"Duplicates found at dates: {duplicates}")
            self.df = self.df[~self.df.index.duplicated(keep="first")]
        logger.info("Checking finished successfullz.")

    def check_sanity(self):
        logger.info("Checking sanity started.")
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
