# Telegram Data Lake Project

## Overview
This project scrapes messages and media from public Telegram channels relevant to Ethiopian medical businesses, stores the raw data in a partitioned data lake, and transforms it into a clean, analytics-ready warehouse using dbt and PostgreSQL. It also enriches the data with object detection using YOLOv8.

## Project Structure
```
.
├── src/                # Source code (scrapers, loaders, config, enrichment)
│   ├── config.py       # Loads environment variables and channel config
│   ├── data_loader.py  # Loads raw JSON messages into PostgreSQL
│   ├── database.py     # Database connection utilities
│   ├── telegram_scraper.py # Scrapes Telegram messages and media
│   └── image_detection.py  # YOLOv8 image enrichment script
├── my_project/         # dbt project for data modeling and transformation
│   ├── models/
│   │   ├── staging/    # Staging models (clean/structure raw data)
│   │   └── marts/      # Data marts (facts/dimensions)
│   └── tests/          # dbt custom tests
├── tests/              # Unit and integration tests (Python)
├── data/               # Data lake (raw messages, media)
│   ├── raw/telegram_messages/YYYY-MM-DD/channel_name.json
│   └── raw/media/      # Downloaded images/media
├── logs/               # Log files
├── requirements.txt    # Python dependencies
├── requirements-dev.txt# Development dependencies
├── Dockerfile
├── docker-compose.yml
├── channels.yaml       # Channel configuration (if used)
└── README.md
```

## Prerequisites
- Python 3.8+
- PostgreSQL 12+
- [dbt-postgres](https://docs.getdbt.com/docs/core/connect-data-platform/postgres-setup)
- (Optional) Docker & docker-compose

## Setup
1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd <repo-root>
   ```
2. **Copy and configure environment variables:**
   ```sh
   cp .env.example .env
   # Edit .env and fill in:
   # TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
   # POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
   ```
3. **Install Python dependencies:**
   ```sh
   pip install -r requirements.txt
   # For development:
   pip install -r requirements-dev.txt
   ```
4. **(Optional) Build and start services with Docker:**
   ```sh
   docker-compose up --build
   ```

## Usage
### 1. Scrape Telegram messages and media
```sh
python src/telegram_scraper.py
```
- Downloads messages and media to `data/raw/telegram_messages/` and `data/raw/media/`.

### 2. Load raw data into PostgreSQL
```sh
python src/data_loader.py
```
- Loads all JSON messages into the `raw.telegram_messages` table in your database.

### 3. Enrich images with YOLOv8 object detection
```sh
pip install ultralytics
python src/image_detection.py
```
- Scans all images in `data/raw/media/`, runs YOLOv8 detection, and stores results in `raw.image_detections`.

### 4. Transform and model data with dbt
```sh
cd my_project
# Configure your dbt profile (see below)
dbt run
```
- Runs all dbt models to build staging, fact, and dimension tables.

### 5. Run dbt tests
```sh
cd my_project
dbt test
```
- Runs built-in and custom data quality tests.

### 6. Generate and view dbt documentation
```sh
cd my_project
dbt docs generate
dbt docs serve
```
- Generates and serves interactive documentation for your data warehouse.

### 7. Run Python tests
```sh
pytest
```

## Configuration
- All configuration is managed via environment variables (see `.env.example`).
- Telegram channels to scrape are listed in `src/config.py` under `TELEGRAM_CHANNELS`.
- dbt connection is configured in `my_project/profiles.yml` (see your database credentials in `.env`).

## Environment Variables (.env)
- All sensitive credentials are managed via a `.env` file, which is excluded from version control for security.
- **Example:**
  ```env
  TELEGRAM_API_ID=your_telegram_api_id  # Replace with your Telegram API ID
  TELEGRAM_API_HASH=your_telegram_api_hash  # Replace with your Telegram API Hash
  TELEGRAM_PHONE=+1234567890  # Your Telegram phone number
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=telegram_db
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=your_secure_password
  ```
- **Important:** Never commit your real credentials. Use placeholder values and update `.env.example` accordingly.

## Data Architecture
- **Data Lake:** Raw, partitioned JSON files in `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json` and media in `data/raw/media/`.
- **Database:** PostgreSQL for structured storage and analytics.
- **dbt:** Data modeling, transformation, and testing in `my_project/`.
- **Logging:** All scripts log to `logs/` and console.
- **Enrichment:** YOLOv8 object detection results are stored in `raw.image_detections` and modeled in dbt.

## dbt Models
- **Staging:** `my_project/models/staging/` (e.g., `stg_telegram_messages.sql`, `stg_image_detections.sql`)
- **Marts:** `my_project/models/marts/` (e.g., `fct_messages.sql`, `dim_channels.sql`, `dim_dates.sql`, `fct_image_detections.sql`)
- **Tests:** `my_project/tests/` (e.g., `no_empty_messages.sql`)

## Logging
- All scripts use `loguru` for structured logging with timestamps, log levels, and output to both console and `logs/` directory.
- Log files are rotated and stored in `logs/telegram_scraper.log` and similar files for other scripts.
- Adjust verbosity and log format in the source code as needed.

## Troubleshooting
- **Docker fails to start:**
  - Check Docker Desktop is running.
  - Ensure ports 5432 (Postgres) and 8000 (if used) are free.
  - Run `docker-compose down -v` to reset volumes if needed.
- **Database connection errors:**
  - Verify `.env` and `my_project/profiles.yml` for correct credentials.
  - Ensure Postgres is running and accessible.
- **Missing dependencies:**
  - Run `pip install -r requirements.txt` and `pip install ultralytics` for YOLO.
- **dbt errors:**
  - Run `dbt debug` for environment checks.
- **Image detection issues:**
  - Ensure images are present in `data/raw/media/` and filenames start with the message ID.
- **Other issues:**
  - Check log files in `logs/` for detailed error messages.

## Data Lineage & dbt DAG
- Generate interactive data lineage and model documentation with dbt:
  ```sh
  cd my_project
  dbt docs generate
  dbt docs serve
  ```
- This provides a visual DAG (Directed Acyclic Graph) of your data pipeline and model dependencies.

## Data Quality & File Naming
- All raw data files follow the naming convention: `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`.
- The pipeline validates file structure and logs warnings for malformed or empty messages.
- Add additional validation as needed for your use case.

## dbt Testing
- Includes basic tests (e.g., `not_null`) and encourages adding custom tests for business logic (e.g., `message length > 0`).
- Example custom test:
  ```sql
  -- tests/no_empty_messages.sql
  SELECT * FROM {{ ref('stg_telegram_messages') }} WHERE LENGTH(message_text) = 0
  ```
- Add more tests in `my_project/tests/` as your business logic evolves.

## Code Documentation & Comments
- Inline comments exist but are sparse in some scripts (e.g., `telegram_scraper.py`).
- Contributions to improve code documentation and add explanatory comments are welcome!


## Contributing
- Add new Telegram channels in `src/config.py` under `TELEGRAM_CHANNELS`.
- Add or update tests in `tests/`.
- Use pre-commit hooks for linting and formatting (`pre-commit install`).
- Follow best practices for Python and dbt development.

