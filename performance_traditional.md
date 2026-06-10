# Performance Profile Report: Baseline Surveillance Pipeline

Generated on: `2026-06-10 11:11:04`  
Profiling Duration: `60.0s` (Samples collected: `60`)

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
| **Total System CPU %** | 19.3% | 100.0% |
| **Total System RAM %** | 15.0% | 19.5% |
| **Pipeline Process CPU %** | 24.4% | 203.9% |
| **Pipeline Process RAM** | 224.9 MB | 802.9 MB |
| **GPU Utilization %** | 1.9% | 29.0% |
| **GPU VRAM Usage** | 248.0 MB | 249.0 MB |

## 🌳 Process & Thread Hierarchy Tree
> [!NOTE]
> CPU usage percentages for individual threads are relative to a single core (100% capacity = 1 full CPU core core).
> Memory (RAM) is shared globally by all threads within the main process address space.

```text
└─ [PID: 4866] python (Main Process) | Avg CPU: 24.4% | Avg RAM: 224.9 MB (1.4%)
   ├─ [TID: 4866] Main Thread            | Avg CPU: 6.1% | RAM: Shared
   ├─ [TID: 5523] WorkerThread-5523      | Avg CPU: 89.0% | RAM: Shared
   ├─ [TID: 5466] WorkerThread-5466      | Avg CPU: 32.9% | RAM: Shared
   ├─ [TID: 5467] WorkerThread-5467      | Avg CPU: 0.6% | RAM: Shared
   ├─ [TID: 5520] av:h264:df1            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 5522] av:h264:df3            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 5521] av:h264:df2            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 5519] av:h264:df0            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 5529] WorkerThread-5529      | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 5531] WorkerThread-5531      | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 4870] WorkerThread-4870      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 4871] WorkerThread-4871      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 4872] WorkerThread-4872      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 4928] WorkerThread-4928      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 4929] WorkerThread-4929      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 4930] WorkerThread-4930      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5026] WorkerThread-5026      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5027] WorkerThread-5027      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5028] WorkerThread-5028      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5440] WorkerThread-5440      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5480] WorkerThread-5480      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5524] WorkerThread-5524      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5525] WorkerThread-5525      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5526] WorkerThread-5526      | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 5530] WorkerThread-5530      | Avg CPU: 0.0% | RAM: Shared
   └─ [TID: 5579] QXcbEventQueue         | Avg CPU: 0.0% | RAM: Shared
```

## 🧵 Detailed Thread Breakdown

| Thread ID (TID) | Thread Name | Average CPU % | Status / Description |
| :--- | :--- | :--- | :--- |
| `4866` | `Main Thread` | 6.1% | Main application event loop |
| `5523` | `WorkerThread-5523` | 89.0% | Background worker thread |
| `5466` | `WorkerThread-5466` | 32.9% | Background worker thread |
| `5467` | `WorkerThread-5467` | 0.6% | Background worker thread |
| `5520` | `av:h264:df1` | 0.4% | Background worker thread |
| `5522` | `av:h264:df3` | 0.4% | Background worker thread |
| `5521` | `av:h264:df2` | 0.4% | Background worker thread |
| `5519` | `av:h264:df0` | 0.4% | Background worker thread |
| `5529` | `WorkerThread-5529` | 0.3% | Background worker thread |
| `5531` | `WorkerThread-5531` | 0.3% | Background worker thread |
| `4870` | `WorkerThread-4870` | 0.0% | Background worker thread |
| `4871` | `WorkerThread-4871` | 0.0% | Background worker thread |
| `4872` | `WorkerThread-4872` | 0.0% | Background worker thread |
| `4928` | `WorkerThread-4928` | 0.0% | Background worker thread |
| `4929` | `WorkerThread-4929` | 0.0% | Background worker thread |
| `4930` | `WorkerThread-4930` | 0.0% | Background worker thread |
| `5026` | `WorkerThread-5026` | 0.0% | Background worker thread |
| `5027` | `WorkerThread-5027` | 0.0% | Background worker thread |
| `5028` | `WorkerThread-5028` | 0.0% | Background worker thread |
| `5440` | `WorkerThread-5440` | 0.0% | Background worker thread |
| `5480` | `WorkerThread-5480` | 0.0% | Background worker thread |
| `5524` | `WorkerThread-5524` | 0.0% | Background worker thread |
| `5525` | `WorkerThread-5525` | 0.0% | Background worker thread |
| `5526` | `WorkerThread-5526` | 0.0% | Background worker thread |
| `5530` | `WorkerThread-5530` | 0.0% | Background worker thread |
| `5579` | `QXcbEventQueue` | 0.0% | Background worker thread |

## 📈 Performance Utilization Over Time

#### Pipeline Process CPU % Over Time
```text
203.9% |                                               *  
174.8% |                                                **
145.6% |                                                  
116.5% |                                                  
 87.4% |                                              *   
 58.3% |                                      *           
 29.1% | *                                  *  *     *    
  0.0% |* ********************************** *  *****     
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Utilization % Over Time
```text
 29.0% |    *                                             
 25.0% |                                                  
 21.0% |                                                  
 17.0% |                                                  
 13.0% |                                                  
  9.0% |                                                  
  5.0% |   *                                              
  1.0% |***  *********************************************
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU VRAM Used (MB) Over Time
```text
249.0 MB |   **                                             
248.9 MB |                                                  
248.7 MB |                                                  
248.6 MB |                                                  
248.4 MB |                                                  
248.3 MB |                                                  
248.1 MB |                                                  
248.0 MB |***  *********************************************
       +--------------------------------------------------
        0s                    30s                    60s
```
