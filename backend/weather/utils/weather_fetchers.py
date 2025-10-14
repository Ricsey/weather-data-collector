from abc import ABC, abstractmethod
import io
import logging
from typing import Any
import unicodedata
import zipfile
import requests
import pandas as pd

from weather.utils.utils import log_action, log_debug_action


logger = logging.getLogger("weather")


class WeatherFetcher(ABC):
    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        pass


class HungarometWeatherFetcher(WeatherFetcher):
    BASE_URL_19010101_20231231 = (
        "https://odp.met.hu/climate/homogenized_data/station_data_series/from_1901"
    )
    BASE_URL_20141002_20241231 = (
        "https://odp.met.hu/climate/observations_hungary/daily/historical/"
    )
    MAX_TEMPREATURE_URL = "/maximum_temperature/tx_h_{city}_19012023.csv.zip"
    MIN_TEMPREATURE_URL = "/minimum_temperature/tn_h_{city}_19012023.csv.zip"
    MEAN_TEMPREATURE_URL = "/mean_temperature/t_h_{city}_19012023.csv.zip"

    FILENAME_20141002_20241231 = "HABP_1D_{station_number}_20141002_20241231_hist.zip"

    CITY_STATION_NUMBERS = {
        "Budapest": 34429,
    }

    NA = -999

    def __init__(self, city):
        self._check_city_availability(city)
        self.city = city

    @log_action(action="Fetching weather data", logger=logger)
    def fetch(self) -> pd.DataFrame:
        """
        Collect maximum, mean, and minimum daily temperatures for a city
        by combining long-term (1901-2023) and recent (2014-2024) datasets.
        """

        df_older = self.collect_historical_data()
        df_recent = self.collect_recent_data()

        df_merged = (
            df_older.set_index("Time")
            .combine_first(df_recent.set_index("Time"))
            .reset_index()
        )
        df_merged["city"] = self.city

        return df_merged

    def _check_city_availability(self, city: str) -> None:
        if city not in self.CITY_STATION_NUMBERS:
            error_msg = f"City '{city}' is not available. Choose from {list(self.CITY_STATION_NUMBERS.keys())}."
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.debug(f"City {city} is available.")

    @log_debug_action(action="Downloading csv file", logger=logger)
    def _download_csv(self, url: str) -> io.BytesIO:
        response = requests.get(url)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
            csv_filename = zfile.namelist()[0]
            with zfile.open(csv_filename) as f:
                return io.BytesIO(f.read())

    @log_debug_action(action="Removing accents", logger=logger)
    def _remove_accents(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text)
        return "".join(
            c for c in normalized if unicodedata.category(c) != "Mn"
        )  # 'Mn' = non-spacing marks

    @log_action(action="Collecting historical data", logger=logger)
    def collect_historical_data(self):
        """Collect temperature data between 1901-2023."""

        city_normalized = self._remove_accents(self.city)

        datasets = {
            "t_max": (self.MAX_TEMPREATURE_URL, {"tx": "t_max"}),
            "t_min": (self.MIN_TEMPREATURE_URL, {"tn": "t_min"}),
            "t_mean": (self.MEAN_TEMPREATURE_URL, {"ta": "t_mean"}),
        }

        dfs: list[pd.DataFrame] = []
        for _, (url_template, rename_map) in datasets.items():
            url = f"{self.BASE_URL_19010101_20231231}{url_template.format(city=city_normalized)}"
            csv_file = self._download_csv(url)
            df = pd.read_csv(csv_file, sep=";")
            dfs.append(self.clean_dataframe(df, rename_map))

        return dfs[0].merge(dfs[1], on="Time").merge(dfs[2], on="Time")

    @log_action(action="Cleaning dataframe", logger=logger)
    def clean_dataframe(
        self, df: pd.DataFrame, rename_map: dict[str, str] = None
    ) -> pd.DataFrame:
        """Standardize and clean up a weather DataFrame."""

        df.columns = df.columns.str.strip()

        if rename_map:
            df = df.rename(columns=rename_map).drop(columns=["EOR"], errors="ignore")

        df.replace(self.NA, pd.NA, inplace=True)

        return df

    @log_action(action="Collecting recent data", logger=logger)
    def collect_recent_data(self):
        station_number = self.CITY_STATION_NUMBERS[self.city]
        url = self.BASE_URL_20141002_20241231 + self.FILENAME_20141002_20241231.format(
            station_number=station_number
        )
        csv_file = self._download_csv(url)

        df = pd.read_csv(csv_file, skiprows=5, sep=";")

        df.columns = df.columns.str.strip()
        df = df[["Time", "t", "tx", "tn"]]
        df = df.rename(columns={"tx": "t_max", "tn": "t_min", "t": "t_mean"})

        return self.clean_dataframe(df)
