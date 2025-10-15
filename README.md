# Meteorology Analysis API

A Django-based backend service for collecting, validating, storing, and
analyzing historical and recent weather data (right now focused on Budapest). 
The project provides REST APIs for weather data ingestion and
rolling average calculations, and is containerized.

------------------------------------------------------------------------

### Features

- **Weather Data Collection**  

    Fetches and stores historical weather data for Budapest
    from Hungaromet.

- **Data Validation & Cleaning**  
  Cleans, interpolates, and checks for missing or inconsistent data.

- **REST API**

  - `POST /api/v1/weather/collect-data/`\
    Fetches and stores weather data into postgres database.

  - `POST /api/v1/weather/rolling-average/``\
    Calculates rolling averages for temperature fields.

- **Rolling Average Calculation**

    Computes rolling averages for max, mean, and min temperatures over a
    configurable window.

- **Dockerized & Deployable**

    Run with Docker and Docker Compose (includes Postgres
    database).

- Extensible

    Modular design for adding new cities, data sources, or analytics.


#### Further improvements

-   Protecting endpoints only for authenticated users.
-   Deploying the application with Gunicorn in a production environment
-   Creating auto tests
------------------------------------------------------------------------

## Getting Started

1.  **Clone the Repository**

2.  **Set Up Environment Variables**\
    Copy `.env template` to `.env` and fill in your database
    credentials.
    ```bash
    cp .env\ template .env
    # Edit .env DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT
    ```
3.  **Build and Run with Docker Compose**
    ```bash
    docker compose up --build
    ```
    -   Backend: <http://localhost:8000/>\
    -   Database: host port `55432`, container port `5432`

------------------------------------------------------------------------

## API Reference

### Collect Weather Data

- **POST** `/api/v1/weather/collect-data/`

- **Response:**

    `{ "status": "success" }` or `{ "status": "error", "message": "..." }`

### Rolling Average

- **POST** `/api/v1/weather/rolling-average/`

- **Body:**
    ``` json
    {
        "city": "Budapest",
        "window": 7,                // optional, defaults at 7
        "start_date": "YYYY-MM-DD", // optional
        "end_date": "YYYY-MM-DD"    // optional
    }
    ```

- **Response:**

    ``` json
    [
        {
            "date": "YYYY-MM-DD",
            "t_max_avg": float,
            "t_mean_avg": float,
            "t_min_avg": float
        },
        ...
    ]
    ```

------------------------------------------------------------------------

## Code Overview

-   **Models:** `WeatherData`
-   **Repositories:** `DjangoWeatherDataRepository`
-   **Services:** Data collection, validation, and rolling average
    (`weather_services.py`)
-   **Fetchers:** Download and parse weather data
    (`weather_fetchers.py`)
-   **Utilities:** Logging, data conversion (`utils.py`)
-   **API Views:** `WeatherDataAPIView`, `RollingAverageAPIView`
-   **Serializers:** `RollingAverageRequestSerializer`
-   **Management Commands:** `collect_weather`

------------------------------------------------------------------------
