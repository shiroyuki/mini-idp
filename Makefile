dev-run:
	fastapi dev app.py --port 8081

uv-run:
	uvicorn midp.web:app --host 0.0.0.0 --port 8081

config-default-json:
	@echo "##### conversation-app #####"
	cat config-conversation-app.yml | yq -o json -M

ui-build:
	cd ui && npm run build
	cd midp/webui && rm -r *
	cp -rv ui/build/* midp/webui
