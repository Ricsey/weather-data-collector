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

### Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/weather/sync/` | Sync weather data for a city | No |
| GET | `/weather/data/rolling-averages/` | Calculate rolling averages | No |
| GET | `/weather/data/raw/` | List raw weather data with filters | No |


### 1. Sync Weather Data

Fetch and store historical weather data from Hungaromet for a specified city.

### Endpoint
```
POST /api/v1/weather/sync/
```

### Request Headers
```
Content-Type: application/json
```

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `city` | string | Yes | - | City name to sync data for |
| `force` | boolean | No | `false` | Force re-sync even if data exists |

#### Example Request
```json
{
    "city": "Budapest",
    "force": false
}
```

### Response

#### Success Response (200 OK)
```json
{
    "status": "success"
}
```

#### Data Already Exists (200 OK)
```json
{
    "status": "success",
    "message": "Data for Budapest already exists. Use force=true to re-sync.",
    "data": {
        "city": "Budapest",
        "skipped": true
    }
}
```

#### Validation Error (400 Bad Request)
```json
{
    "status": "error",
    "message": "Invalid request data",
    "errors": {
        "city": ["This field is required."]
    }
}
```

#### City Not Available (400 Bad Request)
```json
{
    "status": "error",
    "message": "City 'London' is not available. Choose from ['Budapest']."
}
```

#### Server Error (500 Internal Server Error)
```json
{
    "status": "error",
    "message": "An unexpected error occurred during sync",
    "detail": "Connection timeout to external API"
}
```

#### Example Usage

#### cURL
```bash
curl -X POST http://localhost:8000/api/v1/weather/sync/ \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Budapest",
    "force": false
  }'
```


### Calculate Rolling Averages

Calculate rolling averages for temperature data over a specified window period.

### Endpoint
```
GET /api/v1/weather/data/rolling-averages/
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `city` | string | Yes | - | City name for calculation |
| `window` | integer | No | `7` | Number of days for rolling average (min: 1) |
| `start_date` | string | No | - | Start date (format: YYYY-MM-DD) |
| `end_date` | string | No | - | End date (format: YYYY-MM-DD) |
| `page` | integer | No | `1` | Page number for pagination |
| `page_size` | integer | No | `50` | Results per page (max: 200) |

### Response

#### Success Response (200 OK)
```json
{
    "status": "success",
    "message": "Rolling averages calculated successfully",
    "data": [
        {
            "time": "2024-01-01",
            "t_max_avg": 5.234,
            "t_mean_avg": 2.156,
            "t_min_avg": -0.923
        },
        {
            "time": "2024-01-02",
            "t_max_avg": 5.456,
            "t_mean_avg": 2.345,
            "t_min_avg": -0.678
        }
    ]
}
```

#### Validation Error (400 Bad Request)
```json
{
    "status": "error",
    "message": "Invalid request data",
    "errors": {
        "city": ["This field is required."],
        "window": ["Ensure this value is greater than or equal to 1."],
        "date_range": ["start_date must be before or equal to end_date"]
    }
}
```

#### No Data Found (404 Not Found)
```json
{
    "status": "error",
    "message": "No weather data found for Budapest. Please sync data first."
}
```

#### Server Error (500 Internal Server Error)
```json
{
    "status": "error",
    "message": "An unexpected error occurred while calculating rolling averages",
    "detail": "Memory allocation failed"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `time` | string | Date in YYYY-MM-DD format |
| `t_max_avg` | float | Rolling average of maximum temperature (°C) |
| `t_mean_avg` | float | Rolling average of mean temperature (°C) |
| `t_min_avg` | float | Rolling average of minimum temperature (°C) |

#### Pagination
The response includes pagination links when there are multiple pages:
```json
{
    "count": 365,
    "next": "http://localhost:8000/api/v1/weather/data/rolling-averages/?city=Budapest&page=2",
    "previous": null,
    "results": [...]
}
```
#### Example Usage

#### cURL
```bash
# Basic request
curl "http://localhost:8000/api/v1/weather/data/rolling-averages/?city=Budapest"

# With all parameters
curl "http://localhost:8000/api/v1/weather/data/rolling-averages/?city=Budapest&window=30&start_date=2024-01-01&end_date=2024-12-31&page=1&page_size=100"
```

### List Raw Weather Data

Retrieve raw weather data records with filtering and pagination support.

### Endpoint
```
GET /api/v1/weather/data/raw/
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `city` | string | No | - | Filter by city name (exact match) |
| `time__gte` | string | No | - | Filter from date (format: YYYY-MM-DD) |
| `time__lte` | string | No | - | Filter to date (format: YYYY-MM-DD) |
| `time` | string | No | - | Filter exact date (format: YYYY-MM-DD) |
| `page` | integer | No | `1` | Page number |
| `page_size` | integer | No | `100` | Results per page (max: 1000) |
| `ordering` | string | No | `time` | Sort field (use `-time` for descending) |

### Response

#### Success Response (200 OK)
```json
{
    "count": 45289,
    "next": "http://localhost:8000/api/v1/weather/data/raw/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "time": "1901-01-01",
            "t_max": 2.5,
            "t_mean": 0.3,
            "t_min": -1.9,
            "city": "Budapest",
            "created_at": "2025-10-24T10:30:15.123456Z",
            "updated_at": null
        },
        {
            "id": 2,
            "time": "1901-01-02",
            "t_max": 3.1,
            "t_mean": 1.2,
            "t_min": -0.7,
            "city": "Budapest",
            "created_at": "2025-10-24T10:30:15.234567Z",
            "updated_at": null
        }
    ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique record identifier |
| `time` | string | Date of weather record (YYYY-MM-DD) |
| `t_max` | float | Maximum temperature for the day (°C) |
| `t_mean` | float | Mean temperature for the day (°C) |
| `t_min` | float | Minimum temperature for the day (°C) |
| `city` | string | City name |
| `created_at` | string | Timestamp when record was created (ISO 8601) |
| `updated_at` | string | Timestamp when record was last updated (ISO 8601, null if never updated) |

#### Pagination

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of records matching the filter |
| `next` | string/null | URL for next page (null if last page) |
| `previous` | string/null | URL for previous page (null if first page) |
| `results` | array | Array of weather data records |

#### Example Usage

#### cURL
```bash
# Get all data for Budapest
curl "http://localhost:8000/api/v1/weather/data/raw/?city=Budapest"

# Get data for specific date range
curl "http://localhost:8000/api/v1/weather/data/raw/?city=Budapest&time__gte=2024-01-01&time__lte=2024-12-31"

# Get data with custom page size
curl "http://localhost:8000/api/v1/weather/data/raw/?city=Budapest&page_size=500"

# Get data sorted by date descending (most recent first)
curl "http://localhost:8000/api/v1/weather/data/raw/?city=Budapest&ordering=-time"
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
-   **API Views:** `WeatherDataCollectAPIView`, `RollingAverageAPIView`, `WeatherRawDataListView`
-   **Serializers:** `RollingAverageRequestSerializer`, `WeatherDataSerializer`, `WeatherSyncRequestSerializer`

------------------------------------------------------------------------
