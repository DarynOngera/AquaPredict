.PHONY: help setup install test clean build deploy

help:
	@echo "AquaPredict - Makefile Commands"
	@echo "================================"
	@echo "setup       - Initial setup (venv, dependencies, directories)"
	@echo "install     - Install Python and Node dependencies"
	@echo "test        - Run all tests"
	@echo "test-python - Run Python tests only"
	@echo "test-frontend - Run frontend tests only"
	@echo "lint        - Run linters"
	@echo "clean       - Clean build artifacts"
	@echo "build       - Build Docker images"
	@echo "push        - Push images to registry"
	@echo "deploy-local - Deploy locally with docker-compose"
	@echo "deploy-oci  - Deploy to OCI"
	@echo "logs        - View docker-compose logs"
	@echo "stop        - Stop local services"

setup:
	@echo "Setting up AquaPredict..."
	@bash scripts/setup.sh

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	cd modules/frontend && npm install

test: test-python test-frontend

test-python:
	@echo "Running Python tests..."
	pytest tests/ -v --cov

test-frontend:
	@echo "Running frontend tests..."
	cd modules/frontend && npm test

lint:
	@echo "Running linters..."
	black modules/ --check
	flake8 modules/
	cd modules/frontend && npm run lint

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

build:
	@echo "Building Docker images..."
	@bash scripts/build_images.sh latest

push:
	@echo "Pushing images to registry..."
	@bash scripts/push_images.sh latest

deploy-local:
	@echo "Deploying locally with docker-compose..."
	docker-compose up -d
	@echo "Services starting..."
	@echo "Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Airflow: http://localhost:8080"

deploy-oci:
	@echo "Deploying to OCI..."
	@bash scripts/deploy_oci.sh

logs:
	docker-compose logs -f

stop:
	@echo "Stopping services..."
	docker-compose down

# Data pipeline commands
ingest-data:
	@echo "Running data ingestion..."
	cd modules/data-ingestion && python main.py --dataset all

preprocess-data:
	@echo "Running preprocessing..."
	cd modules/preprocessing && python main.py --input-dir ../../data/raw --output-dir ../../data/processed

generate-features:
	@echo "Generating features..."
	cd modules/feature-engineering && python main.py

train-models:
	@echo "Training models..."
	cd modules/modeling && python main.py

# Development commands
dev-api:
	@echo "Starting API in development mode..."
	cd modules/prediction-service && uvicorn main:app --reload

dev-frontend:
	@echo "Starting frontend in development mode..."
	cd modules/frontend && npm run dev

# Database commands
db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here

db-seed:
	@echo "Seeding database..."
	# Add seed commands here
