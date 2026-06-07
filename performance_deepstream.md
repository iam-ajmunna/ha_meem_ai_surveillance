# Performance Profile Report: DeepStream Hardware-Accelerated Pipeline

Generated on: `2026-06-07 19:55:55`  
Profiling Duration: `60.0s` (Samples collected: `60`)
Running Environment: `Docker Container (81676daaaae2)`

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
| **Total System CPU %** | 33.3% | 60.8% |
| **Total System RAM %** | 42.2% | 42.5% |
| **DeepStream Process CPU %** | 30.2% | 45.0% |
| **DeepStream Process RAM** | 1912.5 MB | 1912.5 MB |
| **GPU Utilization %** | 22.5% | 31.0% |
| **GPU VRAM Usage** | 1023.0 MB | 1043.0 MB |
| **GPU Decoder (NVDEC) Util %** | 3.5% | 4.0% |
| **GPU Encoder (NVENC) Util %** | 0.0% | 0.0% |
| **GPU Temperature** | 58.5°C | 60.0°C |

## 🏎️ Hardware Offload Performance Comparison

> [!IMPORTANT]
> **Why DeepStream CPU usage is minimal:**
> 1. **Zero-Copy Architecture:** Video frames are decoded via hardware (`NVDEC`) directly into GPU memory buffers (`NVMM`). They remain on the GPU throughout the entire primary inference (SCRFD), tracking (NvDCF), and secondary inference (AdaFace) steps, avoiding expensive Host-to-Device (CPU-to-GPU) memory transfers.
> 2. **C++ Execution Pipeline:** The pipeline is orchestrated natively in C++ via GStreamer plugins rather than interpreting frame-by-frame loops in Python. This completely bypasses the Python Global Interpreter Lock (GIL).
> 3. **Hardware-Accelerated Decoding & Scaling:** Preprocessing steps (resizing, colorspace conversion, normalization) are offloaded onto dedicated hardware engines (`VIC`/`nvvideoconvert`), freeing the CPU cores for application logic.

## ⚙️ Process Specs

- **Process ID (PID)**: `38316`  
- **Process Name**: `deepstream-app`  
- **Command Line**: `deepstream-app -c ha_meem_master_config.txt`  
- **Avg CPU Usage**: `30.2%` (relative to a single core)  
- **Avg RAM footprint**: `1912.5 MB` (`12.13%` of system RAM)  

## 📈 Performance Utilization Over Time

#### DeepStream Process CPU % Over Time
```text
 45.0% |   *                                              
 38.6% |  *                     *                         
 32.1% | *  **  **             * **             *         
 25.7% |      **  *************    ************* ** ******
 19.3% |                                           *      
 12.9% |                                                  
  6.4% |                                                  
  0.0% |*                                                 
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Core Utilization % Over Time
```text
 31.0% |                        *                         
 29.4% |                                                  
 27.9% |  **    *              *                          
 26.3% |         *                                        
 24.7% |    *                     *                       
 23.1% |                                         * *      
 21.6% | *   **   *      *   **  *  **** *     ** *  *    
 20.0% |*      *   ****** ***      *    * *****     * ****
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU VRAM Used (MB) Over Time
```text
1043.0 MB |                                          *       
1038.0 MB |     *******                             * **     
1033.0 MB |            *                         ***    **   
1028.0 MB | ** *                                             
1023.0 MB |*  *                                              
1018.0 MB |                                               ***
1013.0 MB |             ****    ****   ****                  
1008.0 MB |                 ****    ***    ******            
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Decoder (NVDEC) Utilization % Over Time
```text
  4.0% |* *    * ** **** * ** * **** ** * ** **** * ** ***
  3.9% |                                                  
  3.7% |                                                  
  3.6% |                                                  
  3.4% |                                                  
  3.3% |                                                  
  3.1% |                                                  
  3.0% | * **** *  *    * *  * *    *  * *  *    * *  *   
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
 60.0°C |    *                                             
 59.6°C |                                                  
 59.1°C |                                                  
 58.7°C |   *                    * * **********************
 58.3°C |                                                  
 57.9°C | **  ******************* * *                      
 57.4°C |                                                  
 57.0°C |*                                                 
       +--------------------------------------------------
        0s                    30s                    60s
```
