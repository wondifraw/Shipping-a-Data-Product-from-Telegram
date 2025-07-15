# Telegram Data Lake Project

## Overview
This project scrapes messages and media from public Telegram channels relevant to Ethiopian medical businesses, stores the raw data in a partitioned data lake, and transforms it into a clean, analytics-ready warehouse using dbt and PostgreSQL.

## Project Structure
```
.
├── src/                # Source code (scrapers, loaders, config)
├── my_project/         # dbt project for data modeling and transformation
├── tests/              # Unit and integration tests
├── data/               # Data lake (raw messages, media)
├── logs/               # Log files
├── requirements.txt    # Python dependencies
├── requirements-dev.txt# Development dependencies
├── Dockerfile
├── docker-compose.yml
├── channels.yaml       # Channel configuration (if used)
└── README.md
```

## Setup
1. Copy `.env.example` to `.env` and fill in your secrets:
   - `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
   - `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
2. Build and start services (optional, if using Docker):
   ```sh
   docker-compose up --build
   ```
3. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   # For development:
   pip install -r requirements-dev.txt
   ```

## Usage
- **Scrape Telegram messages and media:**
  ```sh
  python src/telegram_scraper.py
  ```
- **Load raw data into PostgreSQL:**
  ```sh
  python src/data_loader.py
  ```
- **Transform and model data with dbt:**
  ```sh
  cd my_project
  dbt run
  ```
- **Run tests:**
  ```sh
  pytest
  ```

## Configuration
- All configuration is managed via environment variables (see `.env.example`).
- Telegram channels to scrape are listed in `src/config.py` under `TELEGRAM_CHANNELS`.

## Data Architecture
- **Data Lake:** Raw, partitioned JSON files in `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json` and media in `data/raw/media/`.
- **Database:** PostgreSQL for structured storage and analytics.
- **dbt:** Data modeling, transformation, and testing in `my_project/`.
- **Logging:** All scripts log to `logs/` and console.

## dbt Models
- **Staging:** `my_project/models/staging/` (e.g., `stg_telegram_messages.sql`)
- **Marts:** `my_project/models/marts/` (e.g., `fct_messages.sql`, `dim_channels.sql`, `dim_dates.sql`)
- **Example:** `my_project/models/example/` (starter models)

## Contributing
- Add new Telegram channels in `src/config.py` under `TELEGRAM_CHANNELS`.
- Add or update tests in `tests/`.
- Use pre-commit hooks for linting and formatting (`pre-commit install`).
- Follow best practices for Python and dbt development.

## License
MIT 