"""Performance optimization benchmark (eager vs torch.compile)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch

from src.security.checkpoints import load_checkpoint_secure
from src.models.model_factory import create_model


OUT_DIR = Path("outputs/recovery_reports")


def bench(model: torch.nn.Module, device: torch.device, iters: int = 20) -> dict:
    x = torch.randn(1, 3, 768, 768, device=device)
    model.eval()

    # Warmup
    with torch.no_grad():
        for _ in range(5):
            _ = model(x)

    torch.cuda.synchronize() if device.type == "cuda" else None
    t0 = time.time()
    with torch.no_grad():
        for _ in range(iters):
            _ = model(x)
    torch.cuda.synchronize() if device.type == "cuda" else None
    elapsed = time.time() - t0

    latency_ms = (elapsed / iters) * 1000.0
    throughput = iters / elapsed
    return {"latency_ms": latency_ms, "throughput_ips": throughput}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt = load_checkpoint_secure("outputs/checkpoints/best_model.pth", map_location="cpu")
    cfg = ckpt["config"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = create_model(
        architecture=cfg["architecture"],
        encoder_name=cfg["encoder_name"],
        encoder_weights=None,
        in_channels=3,
        classes=cfg["classes"],
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)

    eager = bench(model, device)

    compile_supported = hasattr(torch, "compile")
    compiled_result = None
    compile_error = None
    if compile_supported:
        try:
            cmodel = torch.compile(model)
            compiled_result = bench(cmodel, device)
        except Exception as exc:
            compile_error = str(exc)

    out = {
        "device": str(device),
        "eager": eager,
        "torch_compile": compiled_result,
        "torch_compile_error": compile_error,
        "onnx": "BLOCKED: onnxruntime not installed in current environment",
        "tensorrt": "BLOCKED: TensorRT runtime unavailable in current environment",
    }

    (OUT_DIR / "performance_optimization_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    lines = [
        "# Performance Optimization Report",
        f"- device: {out['device']}",
        f"- eager latency (ms): {eager['latency_ms']:.3f}",
        f"- eager throughput (ips): {eager['throughput_ips']:.3f}",
    ]
    if compiled_result is not None:
        lines.append(f"- torch.compile latency (ms): {compiled_result['latency_ms']:.3f}")
        lines.append(f"- torch.compile throughput (ips): {compiled_result['throughput_ips']:.3f}")
    else:
        lines.append(f"- torch.compile: BLOCKED ({compile_error})")
    lines.append("- ONNX: BLOCKED (onnxruntime not installed)")
    lines.append("- TensorRT: BLOCKED (runtime not installed)")

    (OUT_DIR / "performance_optimization_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'performance_optimization_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
