setup:
	pip install -r requirements.txt

scrape-messages:
	python src/scrape_telegram.py

scrape-images:
	python src/scrape_images_telegram.py

load-db:
	python scripts/load_json_to_postgres.py

dbt-run:
	cd dbt && dbt run

test:
	pytest tests/

lint:
	flake8 src/ scripts/ 