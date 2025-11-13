.PHONY: help setup install run-etl run-index run-api run-frontend run-eval docker-up docker-down clean test

help:
	@echo "Shakespearean Scholar - Available Commands"
	@echo "=========================================="
	@echo "setup          - Run initial setup"
	@echo "install        - Install Python dependencies"
	@echo "run-etl        - Run ETL pipeline"
	@echo "run-index      - Run indexing"
	@echo "run-api        - Start FastAPI server"
	@echo "run-frontend   - Start Streamlit frontend"
	@echo "run-eval       - Run evaluation"
	@echo "docker-up      - Start all services with Docker"
	@echo "docker-down    - Stop all Docker services"
	@echo "clean          - Clean generated files"
	@echo "test           - Run tests"

setup:
	chmod +x setup.sh
	./setup.sh

install:
	pip install -r requirements.txt

run-etl:
	python src/A2_etl_chunking.py

run-index:
	python src/A2_indexing.py

run-api:
	cd api && uvicorn A2_api:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && streamlit run A2_frontend.py

run-eval:
	python evaluation/A2_evaluation.py

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf api/__pycache__
	rm -rf evaluation/__pycache__
	rm -rf .ipynb_checkpoints
	rm -rf data/processed_chunks.jsonl
	rm -rf data/chroma_db
	rm -rf evaluation/results
	find . -type f -name "*.pyc" -delete

test:
	@echo "Running API health check..."
	curl -s http://localhost:8000/health | python -m json.tool
