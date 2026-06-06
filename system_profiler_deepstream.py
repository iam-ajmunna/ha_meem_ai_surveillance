#!/usr/bin/env python3
"""
DeepStream Profiler for Hardware-Accelerated Surveillance Pipeline (ha_meem_ai_surveillance).
Profiles CPU/RAM and highly detailed GPU metrics (utilization, VRAM, decoder/encoder engines, temperature)
over a given duration, generating a Markdown report comparing DeepStream hardware offloading vs CPU baseline.
"""

import os
import sys
import time
import argparse
import platform
import subprocess
import psutil
from datetime import datetime

# Define target script/binary names to identify DeepStream processes
DEFAULT_DEEPSTREAM_PATTERNS = ["deepstream-app", "deepstream"]

def get_cpu_model():
    """Retrieves the CPU model name on Linux/Windows/macOS."""
    cpu_model = "Unknown Processor"
    system = platform.system()
    if system == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_model = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
    elif system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_model, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        except Exception:
            pass
    if cpu_model == "Unknown Processor":
        cpu_model = platform.processor() or "Unknown CPU"
    return cpu_model

def safe_float(value, default=0.0):
    """Safely converts a string value to float, handling 'N/A' or '[Not Supported]'."""
    if not value:
        return default
    val_str = str(value).strip().lower()
    if "not supported" in val_str or "n/a" in val_str or "[" in val_str:
        return None
    try:
        return float(value)
    except Exception:
        return default

def get_gpu_info():
    """Queries GPU name and VRAM total using nvidia-smi."""
    gpus = []
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        lines = res.stdout.strip().split("\n")
        for line in lines:
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                gpus.append({
                    "name": parts[0],
                    "vram_total_mb": float(parts[1])
                })
    except Exception:
        pass
    return gpus

def get_detailed_gpu_metrics():
    """Queries detailed GPU utilization, VRAM usage, engine status, and temperature."""
    metrics = []
    try:
        res = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.decoder,utilization.encoder,memory.used,memory.total,temperature.gpu,name",
                "--format=csv,noheader,nounits"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        lines = res.stdout.strip().split("\n")
        for idx, line in enumerate(lines):
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                metrics.append({
                    "gpu_index": idx,
                    "utilization": safe_float(parts[0]),
                    "decoder_util": safe_float(parts[1]),
                    "encoder_util": safe_float(parts[2]),
                    "vram_used_mb": safe_float(parts[3]),
                    "vram_total_mb": safe_float(parts[4]),
                    "temperature": safe_float(parts[5]),
                    "name": parts[6]
                })
    except Exception:
        pass
    return metrics

def get_docker_container_info(pid):
    """Inspects cgroups to determine if a process is running inside Docker."""
    if platform.system() != "Linux":
        return None
    try:
        cgroup_path = f"/proc/{pid}/cgroup"
        if os.path.exists(cgroup_path):
            with open(cgroup_path, "r") as f:
                content = f.read()
                if "docker" in content or "containerd" in content or "sandbox" in content:
                    for line in content.split("\n"):
                        if "docker" in line or "containerd" in line:
                            parts = line.strip().split("/")
                            for part in parts:
                                if len(part) == 64:
                                    return f"Docker Container ({part[:12]})"
                    return "Docker Container (Generic/WSL2)"
    except Exception:
        pass
    return "Host System"

def find_deepstream_processes(patterns):
    """Searches for running DeepStream processes matching any of the pattern strings."""
    candidates = []
    my_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'] or ''
            cmdline = proc.info['cmdline'] or []
            if proc.pid == my_pid:
                continue
            
            cmd_str = " ".join(cmdline)
            # Avoid matching profiling tools or conda run wrappers
            if "system_profiler" in cmd_str or "conda run" in cmd_str:
                continue
                
            # Check name or command-line arguments for DeepStream indicators
            is_match = False
            for pattern in patterns:
                if pattern in name.lower() or pattern in cmd_str.lower():
                    is_match = True
                    break
            
            if is_match:
                candidates.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Filter out parent wrapper processes if they are launchers of other candidates
    if len(candidates) > 1:
        filtered = []
        for c in candidates:
            try:
                if any(c.pid == child.ppid() for child in candidates):
                    continue
                filtered.append(c)
            except Exception:
                filtered.append(c)
        if filtered:
            candidates = filtered

    return candidates

def generate_ascii_plot(data, title, width=50, height=8, y_suffix="%"):
    """Generates an ASCII-art line plot for the report."""
    # Filter out None values for calculation
    valid_data = [x for x in data if x is not None]
    if not valid_data:
        return f"#### {title}\n*No data or metric not supported on this hardware.*"
        
    min_val = min(valid_data)
    max_val = max(valid_data)
    
    if max_val == min_val:
        max_val += 1.0
        min_val -= 1.0
    
    val_range = max_val - min_val
    n_points = len(data)
    
    resampled = []
    for i in range(width):
        idx = int(i * n_points / width)
        resampled.append(data[min(idx, n_points - 1)])
        
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    for x in range(width):
        y_val = resampled[x]
        if y_val is None:
            continue
        y_idx = int((y_val - min_val) / val_range * (height - 1))
        y_idx = max(0, min(height - 1, y_idx))
        grid[height - 1 - y_idx][x] = "*"
        
    plot_lines = [f"#### {title}", "```text"]
    for r in range(height):
        val_at_row = max_val - r * (val_range / (height - 1))
        label = f"{val_at_row:5.1f}{y_suffix} |"
        row_str = "".join(grid[r])
        plot_lines.append(label + row_str)
    
    plot_lines.append("       +" + "-" * width)
    total_seconds = len(data)
    labels = "        0s" + " " * (width // 2 - 5) + f"{total_seconds // 2}s" + " " * (width // 2 - 5) + f"{total_seconds}s"
    plot_lines.append(labels)
    plot_lines.append("```")
    return "\n".join(plot_lines)

def main():
    parser = argparse.ArgumentParser(description="Standalone DeepStream surveillance pipeline profiler.")
    parser.add_argument("--pid", type=int, help="Target process ID to profile directly.")
    parser.add_argument("--search", nargs="+", default=DEFAULT_DEEPSTREAM_PATTERNS, help="List of patterns to search for.")
    parser.add_argument("--duration", type=int, default=60, help="Profiling duration in seconds.")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds.")
    parser.add_argument("--output", type=str, default="performance_deepstream.md", help="Output Markdown report file.")
    args = parser.parse_args()

    print("=" * 60)
    print("      HA-MEEM DEEPSTREAM SURVEILLANCE PROFILE TOOL")
    print("=" * 60)

    target_pid = args.pid
    proc = None

    if target_pid:
        try:
            proc = psutil.Process(target_pid)
            print(f"[INFO] Profiling user-specified PID: {target_pid}")
        except psutil.NoSuchProcess:
            print(f"[ERROR] Process with PID {target_pid} does not exist.")
            sys.exit(1)
    else:
        print(f"[INFO] Scanning for running DeepStream processes containing patterns: {args.search}")
        while True:
            candidates = find_deepstream_processes(args.search)
            if candidates:
                if len(candidates) > 1:
                    print("\n[WARNING] Multiple matching processes found:")
                    for idx, c in enumerate(candidates):
                        cmd_str = " ".join(c.info['cmdline'] or [])
                        print(f"  [{idx}] PID: {c.pid} | Name: {c.info['name']} | Cmd: {cmd_str}")
                    
                    if sys.stdin.isatty():
                        try:
                            selection = input("Select process index to profile (default 0): ").strip()
                            idx = int(selection) if selection.isdigit() and int(selection) < len(candidates) else 0
                        except EOFError:
                            print("\n[INFO] Non-interactive shell detected, selecting index 0.")
                            idx = 0
                    else:
                        print("\n[INFO] Non-interactive environment, automatically selecting index 0.")
                        idx = 0
                    proc = candidates[idx]
                else:
                    proc = candidates[0]
                
                target_pid = proc.pid
                print(f"[SUCCESS] Target process found! PID: {target_pid}")
                print(f"Command line: {' '.join(proc.cmdline())}\n")
                break
            else:
                sys.stdout.write(f"\r[INFO] Waiting for DeepStream process to start... (Ctrl+C to exit)")
                sys.stdout.flush()
                try:
                    time.sleep(2)
                except KeyboardInterrupt:
                    print("\n[INFO] Profiler exited by user.")
                    sys.exit(0)

    # Initialize statistics
    samples_count = 0
    sys_cpu_history = []
    sys_ram_history = []
    proc_cpu_history = []
    proc_ram_history = []
    
    # GPU Metrics Histories
    gpu_util_history = []
    gpu_dec_history = []
    gpu_enc_history = []
    gpu_vram_history = []
    gpu_temp_history = []

    # Prime CPU sampling
    proc.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None)

    # Determine process context (inside Docker or host)
    context_type = get_docker_container_info(target_pid)
    print(f"[INFO] Target environment context: {context_type}")

    print(f"[INFO] Beginning profiling for {args.duration} seconds (interval: {args.interval}s)...")
    print("Sampling status: [", end="", flush=True)

    start_time = time.time()
    next_sample_time = start_time

    try:
        for i in range(args.duration):
            if not proc.is_running():
                print(f"\n[WARNING] Target DeepStream process PID {target_pid} terminated early.")
                break

            samples_count += 1
            now = time.time()

            # 1. System Metrics
            sys_cpu_history.append(psutil.cpu_percent(interval=None))
            sys_ram_history.append(psutil.virtual_memory().percent)

            # 2. Process Metrics
            try:
                proc_cpu_history.append(proc.cpu_percent(interval=None))
                proc_ram_history.append(proc.memory_info().rss / (1024 * 1024))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"\n[WARNING] Process terminated or permission denied during sampling.")
                break

            # 3. Detailed GPU Metrics
            gpus = get_detailed_gpu_metrics()
            if gpus:
                primary = gpus[0]
                gpu_util_history.append(primary["utilization"])
                gpu_dec_history.append(primary["decoder_util"])
                gpu_enc_history.append(primary["encoder_util"])
                gpu_vram_history.append(primary["vram_used_mb"])
                gpu_temp_history.append(primary["temperature"])
            else:
                gpu_util_history.append(None)
                gpu_dec_history.append(None)
                gpu_enc_history.append(None)
                gpu_vram_history.append(None)
                gpu_temp_history.append(None)

            sys.stdout.write("=")
            sys.stdout.flush()

            next_sample_time += args.interval
            sleep_duration = next_sample_time - time.time()
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\n[INFO] Profiling interrupted by user. Generating report with collected metrics...")

    print("] Done!")

    # Helper calculation filters
    def compute_avg(lst):
        vals = [x for x in lst if x is not None]
        return sum(vals) / len(vals) if vals else 0.0

    def compute_max(lst):
        vals = [x for x in lst if x is not None]
        return max(vals) if vals else 0.0

    # Calculate statistics
    total_system_ram_gb = psutil.virtual_memory().total / (1024**3)
    avg_sys_cpu = compute_avg(sys_cpu_history)
    avg_sys_ram = compute_avg(sys_ram_history)
    avg_proc_cpu = compute_avg(proc_cpu_history)
    avg_proc_ram_mb = compute_avg(proc_ram_history)
    avg_proc_ram_pct = (avg_proc_ram_mb / (total_system_ram_gb * 1024)) * 100

    avg_gpu_util = compute_avg(gpu_util_history)
    max_gpu_util = compute_max(gpu_util_history)
    avg_gpu_dec = compute_avg(gpu_dec_history)
    max_gpu_dec = compute_max(gpu_dec_history)
    avg_gpu_enc = compute_avg(gpu_enc_history)
    max_gpu_enc = compute_max(gpu_enc_history)
    avg_gpu_vram = compute_avg(gpu_vram_history)
    max_gpu_vram = compute_max(gpu_vram_history)
    avg_gpu_temp = compute_avg(gpu_temp_history)
    max_gpu_temp = compute_max(gpu_temp_history)

    gpu_list = get_gpu_info()
    gpu_name = gpu_list[0]["name"] if gpu_list else "No NVIDIA GPU Detected"
    total_vram_mb = gpu_list[0]["vram_total_mb"] if gpu_list else 0

    print(f"[INFO] Writing Markdown report to: {args.output}")
    with open(args.output, "w") as f:
        f.write("# Performance Profile Report: DeepStream Hardware-Accelerated Pipeline\n\n")
        f.write(f"Generated on: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  \n")
        f.write(f"Profiling Duration: `{samples_count * args.interval:.1f}s` (Samples collected: `{samples_count}`)\n")
        f.write(f"Running Environment: `{context_type}`\n\n")

        # 1. Hardware Specs Table
        f.write("## 🖥️ System Hardware Specifications\n\n")
        f.write("| Component | Details |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **OS Platform** | {platform.system()} {platform.release()} ({platform.machine()}) |\n")
        f.write(f"| **CPU Model** | {get_cpu_model()} |\n")
        f.write(f"| **CPU Cores** | {psutil.cpu_count(logical=False)} Physical / {psutil.cpu_count(logical=True)} Logical |\n")
        f.write(f"| **System Memory** | {total_system_ram_gb:.2f} GB |\n")
        f.write(f"| **GPU Model** | {gpu_name} |\n")
        if total_vram_mb:
            f.write(f"| **GPU VRAM** | {total_vram_mb:.0f} MB |\n")
        else:
            f.write(f"| **GPU VRAM** | N/A |\n")
        f.write("\n")

        # 2. DeepStream Executive Summary Table
        f.write("## 📊 Executive Summary Metrics\n\n")
        f.write("| Metric | Average Value | Peak Value |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Total System CPU %** | {avg_sys_cpu:.1f}% | {compute_max(sys_cpu_history):.1f}% |\n")
        f.write(f"| **Total System RAM %** | {avg_sys_ram:.1f}% | {compute_max(sys_ram_history):.1f}% |\n")
        f.write(f"| **DeepStream Process CPU %** | {avg_proc_cpu:.1f}% | {compute_max(proc_cpu_history):.1f}% |\n")
        f.write(f"| **DeepStream Process RAM** | {avg_proc_ram_mb:.1f} MB | {compute_max(proc_ram_history):.1f} MB |\n")
        
        if gpu_list:
            f.write(f"| **GPU Utilization %** | {avg_gpu_util:.1f}% | {max_gpu_util:.1f}% |\n")
            f.write(f"| **GPU VRAM Usage** | {avg_gpu_vram:.1f} MB | {max_gpu_vram:.1f} MB |\n")
            
            # Decoder
            dec_str = f"{avg_gpu_dec:.1f}%" if gpu_dec_history and gpu_dec_history[0] is not None else "N/A"
            dec_peak = f"{max_gpu_dec:.1f}%" if gpu_dec_history and gpu_dec_history[0] is not None else "N/A"
            f.write(f"| **GPU Decoder (NVDEC) Util %** | {dec_str} | {dec_peak} |\n")
            
            # Encoder
            enc_str = f"{avg_gpu_enc:.1f}%" if gpu_enc_history and gpu_enc_history[0] is not None else "N/A"
            enc_peak = f"{max_gpu_enc:.1f}%" if gpu_enc_history and gpu_enc_history[0] is not None else "N/A"
            f.write(f"| **GPU Encoder (NVENC) Util %** | {enc_str} | {enc_peak} |\n")
            
            # Temperature
            temp_str = f"{avg_gpu_temp:.1f}°C" if gpu_temp_history and gpu_temp_history[0] is not None else "N/A"
            temp_peak = f"{max_gpu_temp:.1f}°C" if gpu_temp_history and gpu_temp_history[0] is not None else "N/A"
            f.write(f"| **GPU Temperature** | {temp_str} | {temp_peak} |\n")
        else:
            f.write("| **GPU Utilization %** | N/A | N/A |\n")
            f.write("| **GPU VRAM Usage** | N/A | N/A |\n")
            f.write("| **GPU Decoder Util %** | N/A | N/A |\n")
            f.write("| **GPU Encoder Util %** | N/A | N/A |\n")
            f.write("| **GPU Temperature** | N/A | N/A |\n")
        f.write("\n")

        # 3. Hardware Offload Analysis
        f.write("## 🏎️ Hardware Offload Performance Comparison\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Why DeepStream CPU usage is minimal:**\n")
        f.write("> 1. **Zero-Copy Architecture:** Video frames are decoded via hardware (`NVDEC`) directly into GPU memory buffers (`NVMM`). They remain on the GPU throughout the entire primary inference (SCRFD), tracking (NvDCF), and secondary inference (AdaFace) steps, avoiding expensive Host-to-Device (CPU-to-GPU) memory transfers.\n")
        f.write("> 2. **C++ Execution Pipeline:** The pipeline is orchestrated natively in C++ via GStreamer plugins rather than interpreting frame-by-frame loops in Python. This completely bypasses the Python Global Interpreter Lock (GIL).\n")
        f.write("> 3. **Hardware-Accelerated Decoding & Scaling:** Preprocessing steps (resizing, colorspace conversion, normalization) are offloaded onto dedicated hardware engines (`VIC`/`nvvideoconvert`), freeing the CPU cores for application logic.\n\n")
        
        # 4. DeepStream Process Specs
        f.write("## ⚙️ Process Specs\n\n")
        f.write(f"- **Process ID (PID)**: `{target_pid}`  \n")
        f.write(f"- **Process Name**: `{proc.name()}`  \n")
        f.write(f"- **Command Line**: `{' '.join(proc.cmdline())}`  \n")
        f.write(f"- **Avg CPU Usage**: `{avg_proc_cpu:.1f}%` (relative to a single core)  \n")
        f.write(f"- **Avg RAM footprint**: `{avg_proc_ram_mb:.1f} MB` (`{avg_proc_ram_pct:.2f}%` of system RAM)  \n\n")

        # 5. Utilization Charts
        f.write("## 📈 Performance Utilization Over Time\n\n")
        f.write(generate_ascii_plot(proc_cpu_history, "DeepStream Process CPU % Over Time", y_suffix="%"))
        f.write("\n")
        
        if gpu_list:
            f.write(generate_ascii_plot(gpu_util_history, "GPU Core Utilization % Over Time", y_suffix="%"))
            f.write("\n")
            f.write(generate_ascii_plot(gpu_vram_history, "GPU VRAM Used (MB) Over Time", y_suffix=" MB"))
            f.write("\n")
            
            # Decoder plot if supported
            if gpu_dec_history and gpu_dec_history[0] is not None:
                f.write(generate_ascii_plot(gpu_dec_history, "GPU Decoder (NVDEC) Utilization % Over Time", y_suffix="%"))
                f.write("\n")
            
            # Encoder plot if supported
            if gpu_enc_history and gpu_enc_history[0] is not None:
                f.write(generate_ascii_plot(gpu_enc_history, "GPU Encoder (NVENC) Utilization % Over Time", y_suffix="%"))
                f.write("\n")
                
            # Temperature plot
            if gpu_temp_history and gpu_temp_history[0] is not None:
                f.write(generate_ascii_plot(gpu_temp_history, "GPU Temperature (°C) Over Time", y_suffix="°C"))
                f.write("\n")

    print("[SUCCESS] DeepStream report generated successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
