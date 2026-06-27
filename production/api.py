"""Production FastAPI service for SVAMITVA inference."""

from __future__ import annotations

import io
import logging
import os
import time
from pathlib import Path, PurePath
from threading import Lock
from typing import Any

import numpy as np
import torch
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from PIL import Image
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.platform_config import load_platform_config
from src.inference.calibrated_engine import CalibratedEngine
from src.intelligence.survey_report import build_survey_intelligence


LOGGER = logging.getLogger("svamitva.api")
if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

CFG = load_platform_config()
SECURITY_CFG = CFG.security


app = FastAPI(title="SVAMITVA Production API", version="1.0.0")
START_TS = time.time()
REQUEST_COUNT = 0
REQUEST_LOCK = Lock()

ALLOWED_EXT = {
    "." + str(ext).lower().lstrip(".") for ext in SECURITY_CFG.get("allowed_upload_ext", ["png", "jpg", "jpeg", "tif", "tiff"])
}
ALLOWED_MIME = {
    str(m).lower()
    for m in SECURITY_CFG.get(
        "allowed_upload_mime",
        [
            "image/png",
            "image/jpeg",
            "image/tiff",
        ],
    )
}
MAX_UPLOAD_MB = int(SECURITY_CFG.get("max_upload_size_mb", 64))
MAX_BATCH_FILES = int(SECURITY_CFG.get("max_batch_files", 8))
MAX_IMAGE_DIM = int(SECURITY_CFG.get("max_image_dimension_px", 8192))

API_KEY_HEADER_NAME = str(SECURITY_CFG.get("api_key_header", "x-api-key"))
API_KEY_ENV = str(SECURITY_CFG.get("api_key_env", "SVAMITVA_API_KEY"))
API_KEY_HEADER = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

ENGINE: CalibratedEngine | None = None


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float


class InferenceResponse(BaseModel):
    width: int
    height: int
    inference_seconds: float
    class_stats: dict[str, dict[str, float | int]]


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests above configured byte size before full processing."""

    async def dispatch(self, request: Request, call_next):
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > max_bytes:
                    return JSONResponse(status_code=413, content={"detail": "Request body too large"})
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid content-length header"})
        return await call_next(request)


app.add_middleware(RequestSizeLimitMiddleware)


def _api_key_value() -> str:
    value = os.getenv(API_KEY_ENV, "").strip()
    if not value:
        raise RuntimeError(f"Missing required API key env var: {API_KEY_ENV}")
    return value


def _require_api_key(header_value: str | None = Depends(API_KEY_HEADER)) -> str:
    expected = _api_key_value()
    if header_value is None or header_value != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return header_value


def _safe_filename(name: str | None) -> str:
    filename = (name or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Missing file name")
    parts = PurePath(filename).parts
    if any(part in {"..", "/", "\\"} for part in parts):
        raise HTTPException(status_code=400, detail="Unsafe file name")
    if len(filename) > 255:
        raise HTTPException(status_code=400, detail="File name too long")
    return filename


def _class_stats(mask: np.ndarray) -> dict[str, dict[str, float | int]]:
    out: dict[str, dict[str, float | int]] = {}
    total = int(mask.size)
    class_names = {0: "Background", 1: "Road", 2: "Bridge", 3: "Built-Up Area", 4: "Water Body"}
    for class_id, class_name in class_names.items():
        px = int((mask == class_id).sum())
        out[class_name] = {
            "pixels": px,
            "pct": round((100.0 * px / max(total, 1)), 4),
        }
    return out


def _read_image(upload: UploadFile) -> np.ndarray:
    filename = _safe_filename(upload.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported extension: {suffix}")

    content_type = (upload.content_type or "").lower().strip()
    if content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {content_type}")

    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (>{MAX_UPLOAD_MB}MB)")

    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}") from exc

    if max(img.size) > MAX_IMAGE_DIM:
        raise HTTPException(status_code=400, detail=f"Image dimension exceeds {MAX_IMAGE_DIM}px")
    return np.array(img)


@app.on_event("startup")
def startup_validation() -> None:
    global ENGINE
    _ = _api_key_value()

    if os.getenv("SVAMITVA_SKIP_ENGINE_INIT", "0") == "1":
        LOGGER.warning("Skipping engine initialization due to SVAMITVA_SKIP_ENGINE_INIT=1")
        return

    best_ckpt = Path("outputs/checkpoints/best_model.pth")
    latest_ckpt = Path("outputs/checkpoints/latest_model.pth")
    if not best_ckpt.exists() or not latest_ckpt.exists():
        missing = [str(p) for p in (best_ckpt, latest_ckpt) if not p.exists()]
        raise RuntimeError(f"Missing required checkpoint files: {missing}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ENGINE = CalibratedEngine.from_checkpoints(
        best_ckpt,
        latest_ckpt,
        device=device,
        bias_path=Path("outputs/optimal_bias.json"),
        use_tta=True,
    )
    LOGGER.info("API startup validation complete")


@app.get("/health", response_model=HealthResponse)
def health(_: str = Depends(_require_api_key)) -> HealthResponse:
    return HealthResponse(status="ok", uptime_seconds=time.time() - START_TS)


@app.get("/ready", response_model=HealthResponse)
def ready(_: str = Depends(_require_api_key)) -> HealthResponse:
    if ENGINE is None:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    return HealthResponse(status="ready", uptime_seconds=time.time() - START_TS)


@app.get("/metrics")
def metrics(_: str = Depends(_require_api_key)) -> dict[str, Any]:
    return {
        "requests_total": REQUEST_COUNT,
        "uptime_seconds": time.time() - START_TS,
    }


@app.post("/infer", response_model=InferenceResponse)
def infer(file: UploadFile = File(...), _: str = Depends(_require_api_key)) -> InferenceResponse:
    global REQUEST_COUNT
    if ENGINE is None:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    with REQUEST_LOCK:
        REQUEST_COUNT += 1

    arr = _read_image(file)
    h, w = arr.shape[:2]

    t0 = time.time()
    mask, _ = ENGINE.predict_large(arr, postprocess=True)
    elapsed = time.time() - t0

    stats = _class_stats(mask)
    return InferenceResponse(
        width=w,
        height=h,
        inference_seconds=elapsed,
        class_stats=stats,
    )


@app.post("/infer-tiff")
def infer_tiff(file: UploadFile = File(...), _: str = Depends(_require_api_key)) -> dict[str, Any]:
    """Run georeferenced inference on an uploaded GeoTIFF (written to temp, streamed output metadata)."""
    global REQUEST_COUNT
    if ENGINE is None:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    with REQUEST_LOCK:
        REQUEST_COUNT += 1

    filename = _safe_filename(file.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in {".tif", ".tiff"}:
        raise HTTPException(status_code=400, detail="infer-tiff requires .tif or .tiff upload")

    import tempfile

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
        tmp_in.write(data)
        in_path = Path(tmp_in.name)

    t0 = time.time()
    try:
        mask, meta = ENGINE.predict_tiff(in_path, output_path=None, postprocess=True)
    finally:
        in_path.unlink(missing_ok=True)

    elapsed = time.time() - t0
    return {
        "width": meta["width"],
        "height": meta["height"],
        "crs": meta["crs"],
        "epsg": meta["epsg"],
        "pixel_size_m": meta["pixel_size_m"],
        "inference_seconds": elapsed,
        "class_stats": _class_stats(mask),
        "infrastructure_stats": meta.get("stats", {}),
    }


@app.post("/survey-report")
def survey_report(file: UploadFile = File(...), _: str = Depends(_require_api_key)) -> dict[str, Any]:
    """
    Full survey intelligence: segmentation + spatial analysis + explainability + recommendations.
    Decision-support endpoint for GIS / Panchayati Raj workflows.
    """
    global REQUEST_COUNT
    if ENGINE is None:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    with REQUEST_LOCK:
        REQUEST_COUNT += 1

    arr = _read_image(file)
    t0 = time.time()
    mask, logits = ENGINE.predict_large(arr, postprocess=True)
    elapsed = time.time() - t0

    gsd = float(CFG.geospatial.get("default_pixel_size_m", 0.3))
    report = build_survey_intelligence(
        mask,
        pixel_size_m=gsd,
        village_name=Path(_safe_filename(file.filename)).stem,
        logits=logits,
        provenance={"inference_seconds": round(elapsed, 3), "engine": "CalibratedEngine"},
    )
    return report.to_dict()


@app.post("/infer-batch")
def infer_batch(files: list[UploadFile] = File(...), _: str = Depends(_require_api_key)) -> dict[str, Any]:
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(status_code=400, detail=f"Too many files (max={MAX_BATCH_FILES})")
    results = []
    for f in files:
        res = infer(f, _)
        results.append(res.model_dump())
    return {"count": len(results), "results": results}
