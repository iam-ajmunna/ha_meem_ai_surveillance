# Performance Profile Report: DeepStream Hardware-Accelerated Pipeline

Generated on: `2026-06-11 12:35:07`  
Profiling Duration: `60.0s` (Samples collected: `60`)
Running Environment: `Docker Container (9c57fccf4b2d)`

## 🖥️ System Hardware Specifications

| Component | Details |
| :--- | :--- |
| **OS Platform** | Linux 6.8.0-124-generic (x86_64) |
| **CPU Model** | Intel(R) Pentium(R) Gold G7400 |
| **CPU Cores** | 2 Physical / 4 Logical |
| **System Memory** | 15.40 GB |
| **GPU Model** | NVIDIA GeForce GTX 1650 SUPER |
| **GPU VRAM** | 4096 MB |

## 📊 Executive Summary Metrics

| Metric | Average Value | Peak Value |
| :--- | :--- | :--- |
| **Total System CPU %** | 12.0% | 32.1% |
| **Total System RAM %** | 26.1% | 26.4% |
| **DeepStream Process CPU %** | 12.5% | 62.0% |
| **DeepStream Process RAM** | 2087.1 MB | 2114.6 MB |
| **GPU Utilization %** | 8.5% | 26.0% |
| **GPU VRAM Usage** | 1175.2 MB | 1194.0 MB |
| **GPU Decoder (NVDEC) Util %** | 1.6% | 25.0% |
| **GPU Encoder (NVENC) Util %** | 0.0% | 0.0% |
| **GPU Temperature** | 50.2°C | 54.0°C |

## 🏎️ Hardware Offload Performance Comparison

> [!IMPORTANT]
> **Why DeepStream CPU usage is minimal:**
> 1. **Zero-Copy Architecture:** Video frames are decoded via hardware (`NVDEC`) directly into GPU memory buffers (`NVMM`). They remain on the GPU throughout the entire primary inference (SCRFD), tracking (NvDCF), and secondary inference (AdaFace) steps, avoiding expensive Host-to-Device (CPU-to-GPU) memory transfers.
> 2. **C++ Execution Pipeline:** The pipeline is orchestrated natively in C++ via GStreamer plugins rather than interpreting frame-by-frame loops in Python. This completely bypasses the Python Global Interpreter Lock (GIL).
> 3. **Hardware-Accelerated Decoding & Scaling:** Preprocessing steps (resizing, colorspace conversion, normalization) are offloaded onto dedicated hardware engines (`VIC`/`nvvideoconvert`), freeing the CPU cores for application logic.

## ⚙️ Process Specs

- **Process ID (PID)**: `5049`  
- **Process Name**: `deepstream-app`  
- **Command Line**: `deepstream-app -c ha_meem_master_config.txt`  
- **Avg CPU Usage**: `12.5%` (relative to a single core)  
- **Avg RAM footprint**: `2087.1 MB` (`13.24%` of system RAM)  

## 📈 Performance Utilization Over Time

#### DeepStream Process CPU % Over Time
```text
 62.0% | *                                                
 53.1% |  *                                               
 44.3% |                                                  
 35.4% |                                                  
 26.6% |                                *        *     *  
 17.7% |                             *   ** * *    *      
  8.9% |     ***  **  *** *    *             * ** * *** **
  0.0% |*  **   **  **   * **** ***** **   *              
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Core Utilization % Over Time
```text
 26.0% |                                               *  
 22.4% |                                                  
 18.9% |                                *    *      *     
 15.3% |                             *         * * *    * 
 11.7% |           *   **                **   *   *   *  *
  8.1% |                       *           **   *    *    
  4.6% |   *  * *         **     *  *                     
  1.0% |*** ** * ** ***  *  *** * **  **                  
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU VRAM Used (MB) Over Time
```text
1194.0 MB |                                ********          
1159.0 MB |     ***************************        **********
1124.0 MB |   **                                             
1089.0 MB |  *                                               
1054.0 MB |                                                  
1019.0 MB | *                                                
984.0 MB |                                                  
949.0 MB |*                                                 
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Decoder (NVDEC) Utilization % Over Time
```text
 25.0% |*                                                 
 21.4% |                                                  
 17.9% |                                                  
 14.3% |                                                  
 10.7% |                                                  
  7.1% |                                                  
  3.6% |                                               *  
  0.0% | ********************************************** **
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Encoder (NVENC) Utilization % Over Time
```text
  1.0% |                                                  
  0.7% |                                                  
  0.4% |                                                  
  0.1% |                                                  
 -0.1% |**************************************************
 -0.4% |                                                  
 -0.7% |                                                  
 -1.0% |                                                  
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Temperature (°C) Over Time
```text
 54.0°C |                                                * 
 53.1°C |                                                  
 52.3°C |                                               * *
 51.4°C |                                         **** *   
 50.6°C |                                *********    *    
 49.7°C | *            ***     **********                  
 48.9°C |* ************   *****                            
 48.0°C |                                                  
       +--------------------------------------------------
        0s                    30s                    60s
```
