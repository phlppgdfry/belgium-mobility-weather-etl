.PHONY: up down install run dashboard test lint

up:
	docker compose up -d postgres

down:
	docker compose down

install:
	python -m pip install -e '.[dashboard,dev]'

run:
	mobility-etl

dashboard:
	streamlit run dashboard/app.py

test:
	pytest

lint:
	ruff check .

