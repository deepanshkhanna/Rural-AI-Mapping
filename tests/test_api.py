import os
from io import BytesIO

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from production import api as api_module


class _DummyEngine:
    def predict_batch(self, image_t, postprocess=True, strict_postprocess=False):
        b, _, h, w = image_t.shape
        preds = np.zeros((b, h, w), dtype=np.uint8)
        return preds, None

    def predict_large(self, image_rgb, postprocess=True, **kwargs):
        h, w = image_rgb.shape[:2]
        return np.zeros((h, w), dtype=np.uint8), None


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SVAMITVA_API_KEY", "test-key")
    monkeypatch.setenv("SVAMITVA_SKIP_ENGINE_INIT", "1")
    monkeypatch.setattr(api_module, "ENGINE", _DummyEngine())
    return TestClient(api_module.app)


def _auth_headers() -> dict[str, str]:
    return {api_module.API_KEY_HEADER_NAME: os.environ["SVAMITVA_API_KEY"]}


def test_health(client):
    r = client.get("/health", headers=_auth_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready(client):
    r = client.get("/ready", headers=_auth_headers())
    assert r.status_code == 200


def test_infer_png(client):
    img = Image.new("RGB", (32, 32), color=(0, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    r = client.post(
        "/infer",
        files={"file": ("x.png", buf.getvalue(), "image/png")},
        headers=_auth_headers(),
    )
    assert r.status_code == 200
    js = r.json()
    assert js["width"] == 32
    assert js["height"] == 32
    assert "class_stats" in js


def test_infer_invalid_extension(client):
    r = client.post(
        "/infer",
        files={"file": ("x.txt", b"abc", "text/plain")},
        headers=_auth_headers(),
    )
    assert r.status_code == 400


def test_reject_missing_api_key(client):
    r = client.get("/health")
    assert r.status_code == 401


def test_infer_batch_png(client):
    img = Image.new("RGB", (16, 16), color=(10, 10, 10))
    buf = BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()

    r = client.post(
        "/infer-batch",
        files=[
            ("files", ("a.png", payload, "image/png")),
            ("files", ("b.png", payload, "image/png")),
        ],
        headers=_auth_headers(),
    )
    assert r.status_code == 200
    js = r.json()
    assert js["count"] == 2
