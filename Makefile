start_db:
	docker-compose up -d database

run_api_tests:
	docker-compose up -d database && pytest api_tests/ && docker-compose down

generate_test_data:
	docker exec -it restaurant_app_backend_1 chmod +x data/populate_db_with_test_data.py && poetry run python data/populate_db_with_test_data.py

run_app:
	docker-compose up -d
