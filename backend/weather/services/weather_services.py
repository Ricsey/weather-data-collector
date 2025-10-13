import pandas as pd
from weather.repositories.weather_repository import (
    WeatherDataRepository,
    WeatherRecord,
)
from weather.utils.weather_fetchers import WeatherFetcher


class WeatherDataCollectorService:
    def __init__(
        self,
        fetcher: WeatherFetcher,
    ):
        self.fetcher = fetcher
        self.df = None
        self.records: list[WeatherRecord] = []

    def collect_historical_data(self) -> None:
        self.df = self.fetcher.fetch()

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
        self.check_ranges()
        self.check_consistency()
        self.clean_missing_values()

    def clean_types(self):
        for col in ["t_max", "t_mean", "t_min"]:
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        if not pd.api.types.is_datetime64_any_dtype(self.df["Time"]):
            self.df["Time"] = pd.to_datetime(self.df["Time"], format="%Y%m%d")

    def clean_missing_values(self):
        """Interpolating missing values with linear interpolation"""
        self.df[["t_max", "t_mean", "t_min"]] = self.df[
            ["t_max", "t_mean", "t_min"]
        ].interpolate(method="linear")

    def check_missing_dates(self):
        full_index = pd.date_range(self.df.index.min(), self.df.index.max(), freq="D")
        missing_dates = full_index.difference(self.df.index)
        if len(missing_dates) > 0:
            print(f"[Warning] Missing dates: {missing_dates}")

    def check_missing_values(self):

        missing = self.df[["t_max", "t_mean", "t_min"]].isna()

        if missing.any().any():
            for col in ["t_max", "t_mean", "t_min"]:
                missing_dates = self.df.index[missing[col]].tolist()
                if missing_dates:
                    print(
                        f"[Warning] Missing values in {col} at dates: {missing_dates}"
                    )

    def check_duplicates(self):
        duplicates = self.df.index[self.df.index.duplicated()]
        if len(duplicates) > 0:
            print(f"[Warning] Duplicates found at dates: {duplicates}")
            self.df = self.df[~self.df.index.duplicated(keep="first")]

    def check_ranges(self):
        min_temp = -50
        max_temp = 60

        for col in ["t_max", "t_mean", "t_min"]:
            invalid = self.df[(self.df[col] < min_temp) | (self.df[col] > max_temp)]
            if not invalid.empty:
                print(
                    f"[Warning] {col} has unrealistic values at dates: {invalid.index.tolist()}"
                )

    def check_consistency(self):
        inconsistent = self.df[
            (self.df["t_min"] > self.df["t_mean"])
            | (self.df["t_mean"] > self.df["t_max"])
        ]
        if not inconsistent.empty:
            print(
                f"[Warning] Inconsistent temperature values at dates: {inconsistent.index.tolist()}",
                f"{inconsistent}",
            )

    def get_cleaned_data(self):
        return self.df.copy()


class RollingAvgCalculatorService:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def calculate(self):
        pass
