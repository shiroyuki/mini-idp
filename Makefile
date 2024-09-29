dev-run:
	fastapi dev app.py --port 8081

uv-run:
	uvicorn midp.web:app --host 0.0.0.0 --port 8081

auto-test:
	python3 -m unittest discover tests