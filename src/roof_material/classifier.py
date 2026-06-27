"""ResNet18-based roof material classifier (official Roof_type codes 1–4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torchvision import models

from src.roof_material.crops import INDEX_TO_CODE, ROOF_TYPE_CODES
from src.roof_material.flags import ROOF_CLASSIFIER_ENABLED


class RoofMaterialNet(nn.Module):
    """ImageNet ResNet18 backbone with 4-class head for Roof_type codes."""

    def __init__(self, num_classes: int = len(ROOF_TYPE_CODES), pretrained: bool = True) -> None:
        super().__init__()
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = models.resnet18(weights=weights)
        in_features = backbone.fc.in_features
        backbone.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, num_classes),
        )
        self.backbone = backbone

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class RoofMaterialClassifier:
    """Load checkpoint and predict Roof_type codes for RGB crops."""

    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str | torch.device | None = None,
    ) -> None:
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = RoofMaterialNet(pretrained=False).to(self.device)
        ckpt = torch.load(Path(checkpoint_path), map_location=self.device, weights_only=False)
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state)
        self.model.eval()
        self._meta: dict[str, Any] = {
            k: ckpt[k] for k in ("epoch", "macro_f1", "accuracy") if k in ckpt
        }

    @classmethod
    def from_env(cls, env_var: str = "ROOF_CLASSIFIER_CKPT") -> RoofMaterialClassifier | None:
        if not ROOF_CLASSIFIER_ENABLED:
            return None
        import os

        path = os.environ.get(env_var, "").strip()
        if not path:
            default = Path(__file__).resolve().parents[2] / "checkpoints" / "roof_material" / "best.pt"
            path = str(default) if default.exists() else ""
        if not path or not Path(path).exists():
            return None
        return cls(path)

    @property
    def metadata(self) -> dict[str, Any]:
        return dict(self._meta)

    def predict_crop(self, crop_chw: np.ndarray) -> int:
        """Predict official Roof_type code (1–4) for a (3,H,W) float [0,1] crop."""
        probs = self.predict_batch([crop_chw])
        idx = int(np.argmax(probs[0]))
        return INDEX_TO_CODE[idx]

    def predict_batch(self, crops: list[np.ndarray]) -> np.ndarray:
        """Return (N, 4) softmax probabilities."""
        if not crops:
            return np.zeros((0, len(ROOF_TYPE_CODES)), dtype=np.float32)

        batch = torch.stack(
            [torch.from_numpy(c).float() for c in crops],
            dim=0,
        ).to(self.device)
        with torch.inference_mode():
            logits = self.model(batch)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict_codes(self, crops: list[np.ndarray]) -> list[int]:
        probs = self.predict_batch(crops)
        return [INDEX_TO_CODE[int(i)] for i in probs.argmax(axis=1)]
