# 📊 Surveillance Pipeline Profiler Instructions

This guide provides instructions on how to use the custom benchmarking scripts to profile the performance of both the traditional Python/OpenCV pipeline and the hardware-accelerated DeepStream pipeline.

---

## 🔍 Profiler Overview

| Profiler Script | Target Architecture | Key Metrics Tracked | Output Report |
| :--- | :--- | :--- | :--- |
| **`system_profiler_traditional.py`** | Traditional Python threading (multiple `CameraWorker` threads, `io-worker`) | Process & Thread-Level CPU %, Global Process Memory, Host GPU Utilization & VRAM | `performance_traditional.md` |
| **`system_profiler_deepstream.py`** | Hardware-accelerated NVIDIA DeepStream C++ Pipeline (`deepstream-app`) | Host Process CPU/RAM, Detailed GPU Core %, VRAM, NVDEC (Decoder), NVENC (Encoder), Temp | `performance_deepstream.md` |

---

## 🛠️ Prerequisites

Both scripts rely on standard python modules and `psutil`. Before running, ensure your python environment (e.g. `mlvision` conda environment) has the dependencies installed:
```bash
# Check or install psutil
pip install psutil
```

Ensure both scripts have execution permissions:
```bash
chmod +x system_profiler_traditional.py system_profiler_deepstream.py
```

---

## 🚀 How to Run the Profilers

### 1. Traditional Pipeline Profiler (`system_profiler_traditional.py`)

Run this profiler when benchmarking the CPU-based Python/OpenCV pipeline. Because the profiler has a built-in auto-detection/wait feature, it can be started either **before** or **after** the pipeline is launched.

#### Step-by-Step Running Sequence:
1. **Open a separate terminal window/tab** (do not run it in the same terminal as the pipeline since both run interactively).
2. **Activate your python environment** (e.g., conda environment `mlvision`):
   ```bash
   conda activate mlvision
   ```
3. **Start the profiler** (it will block and wait for the pipeline process to start):
   ```bash
   python system_profiler_traditional.py
   ```
4. **In your primary terminal, start the traditional pipeline** (as detailed in the root [README.md](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/README.md)):
   ```bash
   # Option A: Single camera / entry pipeline
   py -m apps.entry_pipeline.main
   
   # Option B: Multi-camera grid pipeline
   py -m apps.multi_pipeline.main
   ```
5. As soon as the pipeline starts, the profiler will detect the `main.py` entry point, begin sampling metrics, and output the performance report to `performance_traditional.md` when the duration (default: 60s) completes.

*(Alternatively, if the pipeline is already running, starting the profiler in step 3 will immediately attach to it and begin profiling).*

#### Command Examples:
```bash
# Run with default settings (Search for 'main.py', sample for 60s, output to performance_traditional.md)
python system_profiler_traditional.py

# Specify custom search pattern if your entry point script has a different name
python system_profiler_traditional.py --search entry_pipeline.py

# Profile a specific process directly using its Process ID (PID)
python system_profiler_traditional.py --pid 12345 --duration 30

# Specify custom output path
python system_profiler_traditional.py --output benchmarks/my_traditional_run.md
```

### 2. DeepStream Pipeline Profiler (`system_profiler_deepstream.py`)

Run this profiler when benchmarking the hardware-accelerated NVIDIA DeepStream pipeline. 

> [!IMPORTANT]
> **Host Execution:** The DeepStream profiler must be run on the **Host** machine (not inside the Docker container) so that it can query the host system's GPU metrics (`nvidia-smi`) and retrieve the container context details from `/proc`.

#### Step-by-Step Running Sequence:
1. **Open a terminal on your host machine** (outside of the Docker container).
2. **Start the profiler** depending on which application you plan to run inside the container:
   * **To profile the Native C++ App (`deepstream-app`)**:
     ```bash
     python system_profiler_deepstream.py
     ```
   * **To profile the Custom Python Pipeline (`main.py`)**:
     ```bash
     python system_profiler_deepstream.py --search deepstream_pipeline/main.py
     ```
3. **In your primary terminal, start and run the DeepStream pipeline**:
    - Enable display forwarding on your host and start the container:
      ```bash
      xhost +local:docker
      docker run --gpus all -it --rm --net=host \
          -e DISPLAY=$DISPLAY \
          -v /tmp/.X11-unix:/tmp/.X11-unix \
          -v "/home/ajmunna/Workspace/TDI Workspace/Munna/ha_meem_ai_surveillance:/app" \
          nvcr.io/nvidia/deepstream:7.0-triton-multiarch bash
      ```
    - Inside the container, launch the target application:
      * **For C++ App**:
        ```bash
        cd /app/deepstream-sdk-map/configs && deepstream-app -c ha_meem_master_config.txt
        ```
      * **For Python Pipeline**:
        ```bash
        python3 /app/apps/deepstream_pipeline/main.py
        ```
4. The host profiler will automatically detect the running process, map it to the Docker Container ID, record performance metrics, and output the report to `performance_deepstream.md` when the duration completes.

*(Alternatively, if the DeepStream app is already running inside the container, running the host profiler will immediately target and profile it).*

#### Command Examples:
```bash
# Run with default settings (Search for 'deepstream-app' or 'deepstream', sample for 60s, output to performance_deepstream.md)
python system_profiler_deepstream.py

# Profile a custom deepstream command name or a python deepstream wrapper
python system_profiler_deepstream.py --search deepstream_wrapper.py

# Profile a specific PID directly (e.g. inside Docker or Host system)
python system_profiler_deepstream.py --pid 54321 --duration 120

# Specify custom output path
python system_profiler_deepstream.py --output benchmarks/my_deepstream_run.md
```

---

## ⚙️ Command-Line Arguments Reference

Both scripts share a consistent command-line interface:

*   `--pid <int>`: Direct PID of the process to profile. Skips the search phase.
*   `--search <str>`: Pattern to search for in active process command lines (e.g., `main.py` or `deepstream-app`).
*   `--duration <int>`: Total benchmark time in seconds. *(Default: `60`)*
*   `--interval <float>`: Sampling rate frequency in seconds. *(Default: `1.0`)*
*   `--output <str>`: File path where the Markdown performance report will be generated.

---

## 💡 Notes on Process Auto-Detection

1.  **Waiting Mode**: If the target process is not active yet, the profilers will block and poll, waiting for the process to launch before initiating the benchmark.
2.  **Parent Process Filtering**: Profilers ignore launcher wrappers (such as `conda run`) and instead identify the child Python or DeepStream process actually executing the code.
3.  **Docker Container Support**: If DeepStream is running inside a Docker container, the host profiler will resolve container details (such as the short Container ID) via `/proc/{pid}/cgroup` and document it in the report.
4.  **Hardware Capability Parsing**: For metrics not supported by specific hardware configurations (e.g., Decoder/Encoder utilization on older consumer GPUs), the scripts will print `N/A (Not Supported)` and omit those sparklines rather than crashing.
