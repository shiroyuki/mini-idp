dev-backend:
	fastapi dev app.py --port 8081

dev-backend-uv:
	uvicorn midp.web:app --host 0.0.0.0 --port 8081

config-default-json:
	@echo "##### conversation-app #####"
	cat config-conversation-app.yml | yq -o json -M

ui-build:
	cd ui && npm run build
	cd midp/webui && rm -r *
	cp -rv ui/build/* midp/webui

dev-ui:
	cd ui && npm run build-dev

dev-test:
	./scripts/run_test.sh discover -v