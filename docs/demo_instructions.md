# Demo UI Instructions

## Overview

The demo UI is a presentation layer for controlled finals demonstrations. Production inference runs through the secured API in `production/api.py`.

## Prerequisites

```bash
pip install -r requirements.txt
export SVAMITVA_API_KEY="demo-local-key"
```

Ensure required checkpoints are available in `outputs/checkpoints/`.

## Launch Order

1. Start API backend:

```bash
uvicorn production.api:app --host 0.0.0.0 --port 8000
```

2. Start UI:

```bash
streamlit run demo_ui/app.py
```

## Security and Validation

- API requests require the configured API key header.
- Upload validation enforces extension, MIME, file-size, and max-image-dimension constraints.
- Batch inference enforces a maximum file count.

## Data Governance

- Raw source datasets and generated outputs are excluded from version control.
- Demo operators must provision approved local input images separately.

## Supported Input Formats

| Format | Extension |
|--------|-----------|
| PNG | `.png` |
| JPEG | `.jpg`, `.jpeg` |
| TIFF | `.tif`, `.tiff` |
