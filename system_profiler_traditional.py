#!/usr/bin/env python3
"""
System Profiler for Python/OpenCV surveillance pipeline (ha_meem_ai_surveillance).
Profiles CPU/RAM per thread and GPU utilization over a given duration, generating a Markdown report.
"""

import os
import sys
import time
import argparse
import platform
import subprocess
import psutil
from datetime import datetime

# Define target script to identify the pipeline process
DEFAULT_TARGET_PATTERN = "main.py"

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
            # Query registry
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_model, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        except Exception:
            pass
    if cpu_model == "Unknown Processor":
        cpu_model = platform.processor() or "Unknown CPU"
    return cpu_model

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

def get_gpu_metrics():
    """Queries current GPU utilization and VRAM usage."""
    metrics = []
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
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
            if len(parts) >= 3:
                metrics.append({
                    "gpu_index": idx,
                    "utilization": float(parts[0]),
                    "vram_used_mb": float(parts[1]),
                    "vram_total_mb": float(parts[2])
                })
    except Exception:
        pass
    return metrics

def get_thread_name(pid, tid):
    """Retrieves OS-level thread name from /proc on Linux, or returns a generic name."""
    if platform.system() == "Linux":
        try:
            comm_path = f"/proc/{pid}/task/{tid}/comm"
            if os.path.exists(comm_path):
                with open(comm_path, "r") as f:
                    name = f.read().strip()
                    if name:
                        return name
        except Exception:
            pass
    return "python-thread"

def find_target_process(pattern):
    """Searches for a Python process running a script matching pattern."""
    candidates = []
    my_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if not cmdline:
                continue
            if proc.pid == my_pid:
                continue
            cmd_str = " ".join(cmdline)
            # Ignore profiling scripts and conda run wrappers
            if "system_profiler" in cmd_str or "conda run" in cmd_str:
                continue
            # Match python processes executing our target script
            if "python" in proc.info['name'].lower() or "python" in cmdline[0].lower():
                is_match = False
                for arg in cmdline[1:]:
                    if pattern in arg:
                        is_match = True
                        break
                    # If pattern is default 'main.py', also match module execution (e.g., -m apps.entry_pipeline.main)
                    if pattern == "main.py" and (arg.endswith(".main") or "apps.entry_pipeline.main" in arg or "apps.multi_pipeline.main" in arg):
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
    if not data:
        return "No data to plot."
    min_val = min(data)
    max_val = max(data)
    
    # Ensure non-zero range
    if max_val == min_val:
        max_val += 1.0
        min_val -= 1.0
    
    val_range = max_val - min_val
    n_points = len(data)
    
    # Resample data to fit width
    resampled = []
    for i in range(width):
        idx = int(i * n_points / width)
        resampled.append(data[min(idx, n_points - 1)])
        
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    for x in range(width):
        y_val = resampled[x]
        y_idx = int((y_val - min_val) / val_range * (height - 1))
        # Keep inside bounds
        y_idx = max(0, min(height - 1, y_idx))
        grid[height - 1 - y_idx][x] = "*"
        
    plot_lines = [f"#### {title}", "```text"]
    for r in range(height):
        val_at_row = max_val - r * (val_range / (height - 1))
        label = f"{val_at_row:5.1f}{y_suffix} |"
        row_str = "".join(grid[r])
        plot_lines.append(label + row_str)
    
    plot_lines.append("       +" + "-" * width)
    # X Labels
    total_seconds = len(data)
    labels = "        0s" + " " * (width // 2 - 5) + f"{total_seconds // 2}s" + " " * (width // 2 - 5) + f"{total_seconds}s"
    plot_lines.append(labels)
    plot_lines.append("```")
    return "\n".join(plot_lines)

def main():
    parser = argparse.ArgumentParser(description="Standalone surveillance pipeline profiler.")
    parser.add_argument("--pid", type=int, help="Target process ID to profile directly.")
    parser.add_argument("--search", type=str, default=DEFAULT_TARGET_PATTERN, help="Pattern to identify target process.")
    parser.add_argument("--duration", type=int, default=60, help="Profiling duration in seconds.")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds.")
    parser.add_argument("--output", type=str, default="performance_traditional.md", help="Output Markdown report file.")
    args = parser.parse_args()

    print("=" * 60)
    print("      HA-MEEM SURVEILLANCE PIPELINE PROFILE TOOL")
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
        print(f"[INFO] Scanning for running Python processes containing pattern: '{args.search}'")
        while True:
            candidates = find_target_process(args.search)
            if candidates:
                if len(candidates) > 1:
                    print("\n[WARNING] Multiple matching processes found:")
                    for idx, c in enumerate(candidates):
                        cmd_str = " ".join(c.info['cmdline'] or [])
                        print(f"  [{idx}] PID: {c.pid} | Cmd: {cmd_str}")
                    
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
                sys.stdout.write(f"\r[INFO] Waiting for target process to start... (Ctrl+C to exit)")
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
    gpu_util_history = []
    gpu_vram_history = []

    # Thread performance trackers
    # Maps tid -> list of cpu_percent samples
    thread_cpu_history = {}
    thread_names = {}
    thread_prev_times = {}  # tid -> (cpu_time, timestamp)

    # Prime psutil process CPU percent calculations (first call returns 0.0)
    proc.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None)

    print(f"[INFO] Beginning profiling for {args.duration} seconds (interval: {args.interval}s)...")
    print("Sampling status: [", end="", flush=True)

    start_time = time.time()
    next_sample_time = start_time

    try:
        for i in range(args.duration):
            if not proc.is_running():
                print(f"\n[WARNING] Target process PID {target_pid} terminated early.")
                break

            samples_count += 1
            now = time.time()

            # 1. System Metrics
            sys_cpu = psutil.cpu_percent(interval=None)
            sys_ram = psutil.virtual_memory().percent
            sys_cpu_history.append(sys_cpu)
            sys_ram_history.append(sys_ram)

            # 2. GPU Metrics
            gpus = get_gpu_metrics()
            if gpus:
                # Target the primary GPU (GPU 0)
                gpu_util_history.append(gpus[0]["utilization"])
                gpu_vram_history.append(gpus[0]["vram_used_mb"])
            else:
                gpu_util_history.append(0.0)
                gpu_vram_history.append(0.0)

            # 3. Target Process Metrics
            try:
                proc_cpu = proc.cpu_percent(interval=None)
                proc_ram_mb = proc.memory_info().rss / (1024 * 1024)
                proc_cpu_history.append(proc_cpu)
                proc_ram_history.append(proc_ram_mb)

                # 4. Thread-level CPU Metrics
                curr_threads = proc.threads()
                active_tids = set()
                
                for t in curr_threads:
                    tid = t.id
                    active_tids.add(tid)
                    
                    # Resolve OS thread name if new
                    if tid not in thread_names:
                        raw_name = get_thread_name(target_pid, tid)
                        # Clean up Python-level thread display names
                        if tid == target_pid:
                            thread_names[tid] = "Main Thread"
                        elif raw_name in ("python", "python3", "python-thread"):
                            thread_names[tid] = f"WorkerThread-{tid}"
                        else:
                            thread_names[tid] = raw_name
                            
                    curr_cpu_time = t.user_time + t.system_time
                    
                    # Calculate thread CPU utilization
                    if tid in thread_prev_times:
                        prev_cpu_time, prev_timestamp = thread_prev_times[tid]
                        time_delta = now - prev_timestamp
                        cpu_delta = curr_cpu_time - prev_cpu_time
                        
                        if time_delta > 0:
                            thread_cpu_pct = (cpu_delta / time_delta) * 100
                            # Clamp values to avoid small negative timings or scheduler anomalies
                            thread_cpu_pct = max(0.0, thread_cpu_pct)
                            
                            if tid not in thread_cpu_history:
                                thread_cpu_history[tid] = []
                            thread_cpu_history[tid].append(thread_cpu_pct)
                            
                    thread_prev_times[tid] = (curr_cpu_time, now)

                # Prune threads that are no longer running from the prev times tracker
                dead_tids = set(thread_prev_times.keys()) - active_tids
                for dead_tid in dead_tids:
                    if dead_tid in thread_prev_times:
                        del thread_prev_times[dead_tid]

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"\n[WARNING] Permission denied or process terminated while querying metrics.")
                break

            # Print progress bar block
            sys.stdout.write("=")
            sys.stdout.flush()

            # Precise timing control for sample interval
            next_sample_time += args.interval
            sleep_duration = next_sample_time - time.time()
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\n[INFO] Profiling interrupted by user. Generating report with collected data...")

    print("] Done!")

    # Calculate average / peak statistics
    avg_sys_cpu = sum(sys_cpu_history) / samples_count if samples_count else 0
    avg_sys_ram = sum(sys_ram_history) / samples_count if samples_count else 0
    avg_proc_cpu = sum(proc_cpu_history) / samples_count if samples_count else 0
    avg_proc_ram_mb = sum(proc_ram_history) / samples_count if samples_count else 0
    
    total_system_ram_gb = psutil.virtual_memory().total / (1024**3)
    avg_proc_ram_pct = (avg_proc_ram_mb / (total_system_ram_gb * 1024)) * 100

    # Thread average calculations
    threads_summary = []
    for tid, name in thread_names.items():
        history = thread_cpu_history.get(tid, [])
        avg_cpu = sum(history) / len(history) if history else 0.0
        threads_summary.append({
            "tid": tid,
            "name": name,
            "avg_cpu": avg_cpu,
            "samples": len(history)
        })
    
    # Sort threads: Main thread first, then by avg CPU usage descending
    threads_summary.sort(key=lambda x: (x["tid"] != target_pid, -x["avg_cpu"]))

    # GPU statistics
    gpu_list = get_gpu_info()
    gpu_name = gpu_list[0]["name"] if gpu_list else "No NVIDIA GPU Detected"
    total_vram_mb = gpu_list[0]["vram_total_mb"] if gpu_list else 0
    
    avg_gpu_util = sum(gpu_util_history) / samples_count if gpu_util_history else 0
    max_gpu_util = max(gpu_util_history) if gpu_util_history else 0
    avg_gpu_vram = sum(gpu_vram_history) / samples_count if gpu_vram_history else 0
    max_gpu_vram = max(gpu_vram_history) if gpu_vram_history else 0

    # Build ASCII Thread Tree
    tree_lines = []
    tree_lines.append(f"└─ [PID: {target_pid}] python (Main Process) | Avg CPU: {avg_proc_cpu:.1f}% | Avg RAM: {avg_proc_ram_mb:.1f} MB ({avg_proc_ram_pct:.1f}%)")
    for idx, t in enumerate(threads_summary):
        is_last = (idx == len(threads_summary) - 1)
        connector = "   └─" if is_last else "   ├─"
        tree_lines.append(f"{connector} [TID: {t['tid']}] {t['name']:<22} | Avg CPU: {t['avg_cpu']:.1f}% | RAM: Shared")
    ascii_tree = "\n".join(tree_lines)

    # Generate the Markdown Report
    print(f"[INFO] Writing Markdown report to: {args.output}")
    with open(args.output, "w") as f:
        f.write(f"# Performance Profile Report: Baseline Surveillance Pipeline\n\n")
        f.write(f"Generated on: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  \n")
        f.write(f"Profiling Duration: `{samples_count * args.interval:.1f}s` (Samples collected: `{samples_count}`)\n\n")
        
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

        # 2. Executive Summary Metrics Table
        f.write("## 📊 Executive Summary Metrics\n\n")
        f.write("| Metric | Average Value | Peak Value |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Total System CPU %** | {avg_sys_cpu:.1f}% | {max(sys_cpu_history) if sys_cpu_history else 0.0:.1f}% |\n")
        f.write(f"| **Total System RAM %** | {avg_sys_ram:.1f}% | {max(sys_ram_history) if sys_ram_history else 0.0:.1f}% |\n")
        f.write(f"| **Pipeline Process CPU %** | {avg_proc_cpu:.1f}% | {max(proc_cpu_history) if proc_cpu_history else 0.0:.1f}% |\n")
        f.write(f"| **Pipeline Process RAM** | {avg_proc_ram_mb:.1f} MB | {max(proc_ram_history) if proc_ram_history else 0.0:.1f} MB |\n")
        if gpu_list:
            f.write(f"| **GPU Utilization %** | {avg_gpu_util:.1f}% | {max_gpu_util:.1f}% |\n")
            f.write(f"| **GPU VRAM Usage** | {avg_gpu_vram:.1f} MB | {max_gpu_vram:.1f} MB |\n")
        else:
            f.write("| **GPU Utilization %** | N/A | N/A |\n")
            f.write("| **GPU VRAM Usage** | N/A | N/A |\n")
        f.write("\n")

        # 3. Process & Thread ASCII Tree
        f.write("## 🌳 Process & Thread Hierarchy Tree\n")
        f.write("> [!NOTE]\n")
        f.write("> CPU usage percentages for individual threads are relative to a single core (100% capacity = 1 full CPU core core).\n")
        f.write("> Memory (RAM) is shared globally by all threads within the main process address space.\n\n")
        f.write("```text\n")
        f.write(ascii_tree)
        f.write("\n```\n\n")

        # 4. Detailed Thread Breakdown Table
        f.write("## 🧵 Detailed Thread Breakdown\n\n")
        f.write("| Thread ID (TID) | Thread Name | Average CPU % | Status / Description |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for t in threads_summary:
            desc = "Main application event loop" if t["tid"] == target_pid else "Background worker thread"
            if "CameraWorker" in t["name"]:
                desc = "Captures, decodes, and runs inference for a camera stream"
            elif "io-worker" in t["name"]:
                desc = "Asynchronously writes event logs and JPEG snapshots to disk"
            f.write(f"| `{t['tid']}` | `{t['name']}` | {t['avg_cpu']:.1f}% | {desc} |\n")
        f.write("\n")

        # 5. Visual performance plots (ASCII sparklines)
        f.write("## 📈 Performance Utilization Over Time\n\n")
        f.write(generate_ascii_plot(proc_cpu_history, "Pipeline Process CPU % Over Time", y_suffix="%"))
        f.write("\n")
        if gpu_list:
            f.write(generate_ascii_plot(gpu_util_history, "GPU Utilization % Over Time", y_suffix="%"))
            f.write("\n")
            f.write(generate_ascii_plot(gpu_vram_history, "GPU VRAM Used (MB) Over Time", y_suffix=" MB"))
            f.write("\n")

    print("[SUCCESS] Report generated successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
