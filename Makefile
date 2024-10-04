dev-run:
	fastapi dev app.py --port 8081

uv-run:
	uvicorn midp.web:app --host 0.0.0.0 --port 8081

auto-test:
	python3 -m unittest discover -v

auto-quick-test:
	python3 -m unittest -v tests.test_common_enigma

config-default-json:
	cat config-default.yml | yq -o json -M

ui-build:
	cd ui && npm run build
	cd midp/webui && rm -r *
	cp -rv ui/build/* midp/webui
