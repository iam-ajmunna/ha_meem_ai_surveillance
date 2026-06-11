# 🎥 Ha-Meem AI Surveillance (DeepStream Edge Edition)

Hardware-accelerated edge face detection, tracking, and recognition system designed for factory entry gates. Optimized for **NVIDIA Jetson edge devices** running **NVIDIA DeepStream SDK 7.0 / JetPack 6.0+**.

---

## 🚀 Architecture Overview

This project bypasses traditional CPU-heavy Python processing, leveraging NVIDIA's hardware accelerators (GPU, NVDEC, VIC, and DLA) to achieve sub-millisecond real-time inference across multiple CCTV streams:

```mermaid
graph TD
    A[RTSP CCTV Streams] -->|NVDEC Hardware Decode| B[nvstreammux: Stream Multiplexer]
    B -->|Batched GPU Buffers| C[Primary GIE: SCRFD Face Detector]
    C -->|Custom C++ Parser: Stride Anchor Decode| D[nvtracker: NvDCF Tracker]
    D -->|Track IDs + BBoxes| E[Secondary GIE: AdaFace Face Recognizer]
    E -->|Tensor Metadata| F[Custom Python Pad Probe]
    F -->|FAISS Gallery Match| G[FastAPI Events API Server]
    G -->|SSE Stream / JSONL Log| H[Alert Bot / Frontend UI]
```

1. **Hardware Ingestion & Scale**: Decode RTSP H.264 streams on the hardware NVDEC decoder and multiplex them into a single GPU buffer using `nvstreammux`.
2. **Primary AI (`nvinfer`)**: Run **SCRFD Face Detection** using high-throughput TensorRT engine (`scrfd_10g_bnkps.onnx_b3_gpu0_fp16.engine`).
3. **C++ Custom Parser**: The custom bounding box parser (`custom_parser/libnvdsinfer_custom_impl_scrfd.so`) decodes multi-stride anchor distance outputs programmatically on the GPU.
4. **Hardware Tracker (`nvtracker`)**: Track detected faces across frames using the optimized **NvDCF (NVIDIA Discriminative Correlation Filter)** algorithm.
5. **Secondary AI (`nvinfer`)**: Extract 512-d embeddings using **AdaFace** (`adaface.onnx_b16_gpu0_fp16.engine`) for active face crops.
6. **Python Pad Probe & Consensus**: Match embeddings against the FAISS gallery database (`configs/gallery_embeddings.txt`) using cosine similarity. Temporal consensus is achieved via `EmbeddingAggregator` to ensure reliable authorized vs. unknown classification.

---

## 📂 Repository Structure

```text
ha_meem_ai_surveillance/
├── .github/workflows/
│   └── ci-cd.yml              # GitHub Actions central build & edge deploy workflow
├── apps/
│   ├── api_server/            # FastAPI event API server (SSE streaming)
│   └── deepstream_pipeline/   # GStreamer/DeepStream Python pipeline application
├── configs/                   # Consolidated surveillance & DeepStream configurations
│   ├── default.yaml           # Model paths, thresholds, and fusion parameters
│   ├── thresholds.yaml        # Identity verification confidence metrics
│   ├── config_infer_primary.txt      # SCRFD detector inference configuration
│   ├── config_infer_secondary.txt    # AdaFace recognizer inference configuration
│   └── config_tracker_NvDCF_perf.yml # NvDCF tracker parameters
├── custom_parser/             # Custom C++ shared libraries for nvinfer parser
│   ├── nvdsinfer_custom_parser_scrfd.cpp     # SCRFD bounding box decoder source
│   └── nvdsinfer_custom_parser_adaface.cpp   # AdaFace cosine lookup matcher source
├── deploy/
│   ├── jetson/
│   │   ├── docker-compose.yml # Orchestrates api & pipeline services on Jetson
│   │   └── .env.example       # Template for Jetson environment configurations
│   └── scripts/
│       ├── deploy_jetson.sh   # Native edge build & auto-rollback deploy script
│       ├── health_check.sh    # Fast API status query utility
│       └── rebuild_engines.sh # Manual TensorRT compiler helper
├── docker/
│   └── Dockerfile.jetson      # ARM64 production container (compiles C++ libraries)
└── requirements.txt           # Python dependencies (optimized for CI/CD runners)
```

---

## 🛠️ Prerequisites & Jetson Host Setup

Execute these steps once on each NVIDIA Jetson edge device to prepare the environment:

### Step 1: Install NVIDIA Container Toolkit
Ensure Docker and the Nvidia runtime are configured on your Tegra host:
```bash
# Configure the NVIDIA Container Toolkit runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Step 2: Configure Workspace Directories
Create the production directories on the host's NVMe drive:
```bash
sudo mkdir -p /opt/ha-meem/configs /opt/ha-meem/models /opt/ha-meem/engines /opt/ha-meem/logs /opt/ha-meem/snapshots
sudo chown -R $USER:$USER /opt/ha-meem
```

### Step 3: Populate Site-Specific Configurations (Host Only)
These files are git-ignored to prevent exposing local CCTV stream addresses or gallery databases:
1. **Cameras Configuration**: Copy or create `/opt/ha-meem/configs/cameras.yaml` containing your RTSP URLs:
   ```yaml
   cameras:
     - id: camera_01
       url: "rtsp://admin:password@192.168.1.50:554/h264"
       enabled: true
   ```
2. **Environment Variables**: Copy `deploy/jetson/.env.example` to `/opt/ha-meem/.env` and update configurations.
3. **Face Recognition Gallery**: Copy your database embeddings file to `/opt/ha-meem/configs/gallery_embeddings.txt`.

### Step 4: Add Model Weights & Compile Engines
1. Place the ONNX weights inside `/opt/ha-meem/models/`:
   - `scrfd_10g_bnkps.onnx`
   - `adaface.onnx`
2. Compile the TensorRT engines for the Jetson's specific hardware version:
   ```bash
   bash deploy/scripts/rebuild_engines.sh
   ```

---

## 🚀 Running the Services Manually on Jetson

If you want to start or stop services manually on the device:

### Start the Pipeline & API
```bash
docker compose -f deploy/jetson/docker-compose.yml --env-file /opt/ha-meem/.env up -d
```

### View Live Logs
```bash
docker compose -f deploy/jetson/docker-compose.yml logs -f pipeline
```

### Stop Services
```bash
docker compose -f deploy/jetson/docker-compose.yml down
```

---

## 🔄 Automated CI/CD Deployment Flow

Deployments to Jetson edge devices are completely automated using Git and GitHub Actions.

### Deployment Process

```text
Central Developer   ──► Push to 'main'
                          │
                          ▼
                  GitHub Actions Runner
               ┌────────────────────────┐
               │  Runs pytest validation │
               └──────────┬─────────────┘
                          │ (If changed)
                          ▼
                 Self-Hosted Runner (Central Server)
               ┌────────────────────────┐
               │ SSHes to Jetson A      │
               └──────────┬─────────────┘
                          │ (Triggers deploy_jetson.sh)
                          ▼
                 Jetson Device Deployment
               ┌────────────────────────┐
               │ 1. Git pull checkout   │
               │ 2. Docker tag snapshot │
               │ 3. Docker build native │
               │ 4. Graceful restart    │
               │ 5. Health Check Poll   │
               └──────────┬─────────────┘
                          ├─────────────────┐
                 [Passes] │                 │ [Fails]
                          ▼                 ▼
                  Deploy Jetson B       Restore tag snapshot
                  Send ✅ Telegram      Revert checkout
                                        Send 🚨 Telegram
```

### Safe Deployment Guards
1. **Working Hours Lock**: Deployments are blocked during working shifts (06:00–21:00) to prevent downtime. To deploy emergency hotfixes, run manually on the host:
   ```bash
   COMMIT=main FORCE=1 bash /opt/ha-meem/deploy/scripts/deploy_jetson.sh
   ```
2. **Sequential Rollouts**: The pipeline deploys to Jetson A first. If Jetson A fails health checks, it auto-reverts instantly and the workflow halts, leaving Jetson B untouched.
3. **Automatic Rollbacks**: If the FastAPI server `/health` check does not return `HTTP 200` within 90 seconds after service restarts, the deployment script restores the tagged snapshot image and git commit instantly.