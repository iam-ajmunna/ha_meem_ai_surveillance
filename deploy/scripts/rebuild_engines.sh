#!/bin/bash
# ── TRT ENGINE REBUILD ────────────────────────────────────────────────
# Run MANUALLY on each Jetson after a JetPack update ONLY.
# This is NOT part of CI/CD. Never trigger from GitHub Actions.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

MODELS_DIR="/opt/ha-meem/models"

echo "Stopping pipeline before engine rebuild..."
docker compose -f /opt/ha-meem/deploy/jetson/docker-compose.yml stop pipeline || true

echo "Building SCRFD Face Detector engine (GPU/DLA, Batch Size 3)..."
trtexec \
  --onnx="$MODELS_DIR/scrfd_10g_bnkps.onnx" \
  --saveEngine="$MODELS_DIR/scrfd_10g_bnkps.onnx_b3_gpu0_fp16.engine" \
  --fp16 \
  --minShapes=input.1:1x3x640x640 \
  --optShapes=input.1:3x3x640x640 \
  --maxShapes=input.1:3x3x640x640

echo "Building AdaFace Recognizer engine (GPU, Batch Size 16)..."
trtexec \
  --onnx="$MODELS_DIR/adaface.onnx" \
  --saveEngine="$MODELS_DIR/adaface.onnx_b16_gpu0_fp16.engine" \
  --fp16 \
  --minShapes=input:1x3x112x112 \
  --optShapes=input:16x3x112x112 \
  --maxShapes=input:16x3x112x112

echo "Recording SHA256 manifest..."
sha256sum "$MODELS_DIR"/*.engine > "$MODELS_DIR/MANIFEST.sha256"
cat "$MODELS_DIR/MANIFEST.sha256"

echo "Restarting pipeline with new engines..."
docker compose -f /opt/ha-meem/deploy/jetson/docker-compose.yml start pipeline
