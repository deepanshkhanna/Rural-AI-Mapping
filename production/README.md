# Production API

Run:

```bash
export SVAMITVA_API_KEY="change-me"
PYTHONPATH=. .venv/bin/uvicorn production.api:app --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /health`
- `GET /ready`
- `GET /metrics`
- `POST /infer`
- `POST /infer-batch`

Authentication:
- All endpoints require header `x-api-key: <SVAMITVA_API_KEY>`

Startup validation:
- API key environment variable must be set.
- Required checkpoints must exist:
	- `outputs/checkpoints/best_model.pth`
	- `outputs/checkpoints/latest_model.pth`

Upload constraints:
- Allowed extensions: png, jpg, jpeg, tif, tiff
- Allowed MIME types: image/png, image/jpeg, image/tiff
- Maximum file size: configured via `platform_config.v1.json` (default 64MB)
- Maximum image dimension: configured via `platform_config.v1.json` (default 8192px)
- Batch file limit: configured via `platform_config.v1.json` (default 8 files)

Container run:

```bash
export SVAMITVA_API_KEY="change-me"
docker compose up --build
```
