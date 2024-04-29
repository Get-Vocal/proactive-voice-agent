.PHONY: checks
checks:
	poetry run pre-commit run --all-files

.PHONY: app-start
app-start:
	poetry run uvicorn app.main:app --port=8080 --host=0.0.0.0 --workers=2

.PHONY: public-url
public-url:
	cloudflared tunnel --url http://0.0.0.0:8080 --protocol http2
