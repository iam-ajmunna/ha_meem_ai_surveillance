# Ha-Meem AI Surveillance

A professional-grade AI surveillance system for real-time inference and data management.

## Structure

- `python_deepstream_pipeline/`: Hybrid Python GStreamer application pipeline (configurations, main script, custom parser source).
- `cpp_deepstream_pipeline/`: DeepStream Native C++ application pipeline (configurations, custom parser source).
- `apps/dataset_tools/`: Database utility scripts for face alignment and gallery embedding generation.
- `core/`: Shared core libraries (detection, recognition, FAISS database, fusion tracker).
- `models/`: Centralized model storage for SCRFD and AdaFace ONNX files and TensorRT engines.
- `configs/`: YAML configurations for RTSP streams and thresholds.
- `docker/`: Dockerfile build environment for target Triton container.
- `scripts/`: Benchmark, calibration, and presentation helper utilities.
- `requirements.txt`: Python dependencies.

## Prerequisites

### 1. External Software (For running in CUDA/Linux environments)
- **NVIDIA Driver**: Installed on Host OS.
- **NVIDIA Container Toolkit**: For Docker GPU acceleration.
- **DeepStream SDK 7.0**: Triton multiarch Docker container (`nvcr.io/nvidia/deepstream:7.0-triton-multiarch`).

### 2. Models & Data
- Place model weights (`scrfd_10g_bnkps.onnx`, `adaface.onnx`) in the root `models/` directory.
- Place dataset folders (for gallery building) in `data/`.

## Setup & Running the Pipelines

### Step 1: Ingest & Build the Identity Gallery
1. **Extract Faces**: Detects and crops faces from raw input images to create a clean aligned faces dataset:
   ```bash
   python3 -m apps.dataset_tools.extract_faces
   ```
2. **Build Gallery**: Generates 512-d embeddings for the extracted faces and saves them into the gallery database:
   ```bash
   python3 -m apps.dataset_tools.build_gallery
   ```

### Step 2: Running the Pipelines (Inside the DeepStream Container)

For complete startup, C++ compilation/running, and Python hybrid pipeline execution instructions, refer to:
- **Python DeepStream Pipeline**: [README.md](file:///Users/ajmunna/Desktop/Workspace/TDI%20WorkSpace/Ha-Meem%20Group/ha_meem_ai_surveillance/python_deepstream_pipeline/README.md)
- **C++ Native Pipeline**: [README.md](file:///Users/ajmunna/Desktop/Workspace/TDI%20WorkSpace/Ha-Meem%20Group/ha_meem_ai_surveillance/cpp_deepstream_pipeline/README.md)
- **System Profiling & Benchmarking**: [instruction.md](file:///Users/ajmunna/Desktop/Workspace/TDI%20WorkSpace/Ha-Meem%20Group/ha_meem_ai_surveillance/instruction.md)