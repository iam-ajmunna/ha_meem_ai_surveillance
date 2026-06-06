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

Run this profiler when benchmark testing the baseline CPU-based Python/OpenCV pipeline.

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

Run this profiler when benchmark testing the hardware-accelerated NVIDIA DeepStream pipeline.

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
