.PHONY: help up down gen-data load-data dbt-deps dbt-run dbt-test app clean all

help:
	@echo "SaaS GTM Analytics - Available Commands:"
	@echo "  make all        - Run complete pipeline (up -> gen -> load -> dbt -> test)"
	@echo "  make up         - Start Docker containers"
	@echo "  make down       - Stop Docker containers"
	@echo "  make gen-data   - Generate synthetic data"
	@echo "  make load-data  - Load data into Postgres"
	@echo "  make dbt-deps   - Install dbt dependencies"
	@echo "  make dbt-run    - Run dbt models"
	@echo "  make dbt-test   - Run dbt tests"
	@echo "  make app        - Launch Streamlit dashboard"
	@echo "  make clean      - Remove generated data and dbt artifacts"

up:
	@echo "Starting Docker containers..."
	docker compose up -d
	@echo "Waiting for Postgres to be ready..."
	@sleep 10

down:
	@echo "Stopping Docker containers..."
	docker compose down

gen-data:
	@echo "Generating synthetic data..."
	cd data_gen && python generator.py

load-data:
	@echo "Loading data into Postgres..."
	cd loader && python load_csv_to_postgres.py

dbt-deps:
	@echo "Installing dbt dependencies..."
	cd dbt && dbt deps

dbt-run:
	@echo "Running dbt models..."
	cd dbt && dbt run

dbt-test:
	@echo "Running dbt tests..."
	cd dbt && dbt test

app:
	@echo "Launching Streamlit dashboard..."
	cd app && streamlit run streamlit_app.py

clean:
	@echo "Cleaning generated files..."
	rm -rf data_gen/output/*.csv
	rm -rf dbt/target/
	rm -rf dbt/logs/

all: up gen-data load-data dbt-deps dbt-run dbt-test
	@echo ""
	@echo "✅ Pipeline complete! Run 'make app' to launch the dashboard."
