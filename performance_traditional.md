# Performance Profile Report: Baseline Surveillance Pipeline

Generated on: `2026-06-11 12:11:25`  
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
| **Total System CPU %** | 68.8% | 100.0% |
| **Total System RAM %** | 19.5% | 21.3% |
| **Pipeline Process CPU %** | 251.4% | 372.8% |
| **Pipeline Process RAM** | 885.8 MB | 1144.7 MB |
| **GPU Utilization %** | 7.8% | 37.0% |
| **GPU VRAM Usage** | 251.2 MB | 267.0 MB |

## 🌳 Process & Thread Hierarchy Tree
> [!NOTE]
> CPU usage percentages for individual threads are relative to a single core (100% capacity = 1 full CPU core core).
> Memory (RAM) is shared globally by all threads within the main process address space.

```text
└─ [PID: 17038] python (Main Process) | Avg CPU: 251.4% | Avg RAM: 885.8 MB (5.6%)
   ├─ [TID: 17038] Main Thread            | Avg CPU: 7.5% | RAM: Shared
   ├─ [TID: 17096] WorkerThread-17096     | Avg CPU: 87.3% | RAM: Shared
   ├─ [TID: 17115] WorkerThread-17115     | Avg CPU: 85.8% | RAM: Shared
   ├─ [TID: 17164] WorkerThread-17164     | Avg CPU: 75.5% | RAM: Shared
   ├─ [TID: 17070] WorkerThread-17070     | Avg CPU: 71.0% | RAM: Shared
   ├─ [TID: 17071] WorkerThread-17071     | Avg CPU: 19.7% | RAM: Shared
   ├─ [TID: 17160] av:hevc:df0            | Avg CPU: 0.6% | RAM: Shared
   ├─ [TID: 17101] WorkerThread-17101     | Avg CPU: 0.5% | RAM: Shared
   ├─ [TID: 17103] WorkerThread-17103     | Avg CPU: 0.5% | RAM: Shared
   ├─ [TID: 17102] WorkerThread-17102     | Avg CPU: 0.5% | RAM: Shared
   ├─ [TID: 17094] av:h264:df2            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 17093] av:h264:df1            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 17092] av:h264:df0            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 17095] av:h264:df3            | Avg CPU: 0.4% | RAM: Shared
   ├─ [TID: 17163] av:hevc:df3            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17113] av:h264:df2            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17112] av:h264:df1            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17111] av:h264:df0            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17114] av:h264:df3            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17161] av:hevc:df1            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17162] av:hevc:df2            | Avg CPU: 0.3% | RAM: Shared
   ├─ [TID: 17119] WorkerThread-17119     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17117] WorkerThread-17117     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17118] WorkerThread-17118     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17168] WorkerThread-17168     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17100] WorkerThread-17100     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17099] WorkerThread-17099     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17098] WorkerThread-17098     | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 17167] WorkerThread-17167     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17169] WorkerThread-17169     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17116] WorkerThread-17116     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17039] WorkerThread-17039     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17040] WorkerThread-17040     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17041] WorkerThread-17041     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17046] WorkerThread-17046     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17047] WorkerThread-17047     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17048] WorkerThread-17048     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17053] WorkerThread-17053     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17054] WorkerThread-17054     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17055] WorkerThread-17055     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17076] WorkerThread-17076     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 17097] WorkerThread-17097     | Avg CPU: 0.0% | RAM: Shared
   └─ [TID: 17172] QXcbEventQueue         | Avg CPU: 0.0% | RAM: Shared
```

## 🧵 Detailed Thread Breakdown

| Thread ID (TID) | Thread Name | Average CPU % | Status / Description |
| :--- | :--- | :--- | :--- |
| `17038` | `Main Thread` | 7.5% | Main application event loop |
| `17096` | `WorkerThread-17096` | 87.3% | Background worker thread |
| `17115` | `WorkerThread-17115` | 85.8% | Background worker thread |
| `17164` | `WorkerThread-17164` | 75.5% | Background worker thread |
| `17070` | `WorkerThread-17070` | 71.0% | Background worker thread |
| `17071` | `WorkerThread-17071` | 19.7% | Background worker thread |
| `17160` | `av:hevc:df0` | 0.6% | Background worker thread |
| `17101` | `WorkerThread-17101` | 0.5% | Background worker thread |
| `17103` | `WorkerThread-17103` | 0.5% | Background worker thread |
| `17102` | `WorkerThread-17102` | 0.5% | Background worker thread |
| `17094` | `av:h264:df2` | 0.4% | Background worker thread |
| `17093` | `av:h264:df1` | 0.4% | Background worker thread |
| `17092` | `av:h264:df0` | 0.4% | Background worker thread |
| `17095` | `av:h264:df3` | 0.4% | Background worker thread |
| `17163` | `av:hevc:df3` | 0.3% | Background worker thread |
| `17113` | `av:h264:df2` | 0.3% | Background worker thread |
| `17112` | `av:h264:df1` | 0.3% | Background worker thread |
| `17111` | `av:h264:df0` | 0.3% | Background worker thread |
| `17114` | `av:h264:df3` | 0.3% | Background worker thread |
| `17161` | `av:hevc:df1` | 0.3% | Background worker thread |
| `17162` | `av:hevc:df2` | 0.3% | Background worker thread |
| `17119` | `WorkerThread-17119` | 0.1% | Background worker thread |
| `17117` | `WorkerThread-17117` | 0.1% | Background worker thread |
| `17118` | `WorkerThread-17118` | 0.1% | Background worker thread |
| `17168` | `WorkerThread-17168` | 0.1% | Background worker thread |
| `17100` | `WorkerThread-17100` | 0.1% | Background worker thread |
| `17099` | `WorkerThread-17099` | 0.1% | Background worker thread |
| `17098` | `WorkerThread-17098` | 0.1% | Background worker thread |
| `17167` | `WorkerThread-17167` | 0.0% | Background worker thread |
| `17169` | `WorkerThread-17169` | 0.0% | Background worker thread |
| `17116` | `WorkerThread-17116` | 0.0% | Background worker thread |
| `17039` | `WorkerThread-17039` | 0.0% | Background worker thread |
| `17040` | `WorkerThread-17040` | 0.0% | Background worker thread |
| `17041` | `WorkerThread-17041` | 0.0% | Background worker thread |
| `17046` | `WorkerThread-17046` | 0.0% | Background worker thread |
| `17047` | `WorkerThread-17047` | 0.0% | Background worker thread |
| `17048` | `WorkerThread-17048` | 0.0% | Background worker thread |
| `17053` | `WorkerThread-17053` | 0.0% | Background worker thread |
| `17054` | `WorkerThread-17054` | 0.0% | Background worker thread |
| `17055` | `WorkerThread-17055` | 0.0% | Background worker thread |
| `17076` | `WorkerThread-17076` | 0.0% | Background worker thread |
| `17097` | `WorkerThread-17097` | 0.0% | Background worker thread |
| `17172` | `QXcbEventQueue` | 0.0% | Background worker thread |

## 📈 Performance Utilization Over Time

#### Pipeline Process CPU % Over Time
```text
372.8% |                                                  
319.5% |                               *******************
266.3% |               ****************                   
213.0% |                                                  
159.8% |             **                                   
106.5% |                                                  
 53.3% |     *      *                                     
  0.0% |***** ******                                      
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Utilization % Over Time
```text
 37.0% |                                 *                
 31.9% |                                                  
 26.7% |                                                  
 21.6% |                                                  
 16.4% |                                      *  *     *  
 11.3% |                                   *** ** ***** **
  6.1% |                               ** *               
  1.0% |*******************************                   
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU VRAM Used (MB) Over Time
```text
267.0 MB |                                ******************
263.4 MB |                                                  
259.9 MB |                                                  
256.3 MB |                                                  
252.7 MB |                                                  
249.1 MB |                                                  
245.6 MB |                                                  
242.0 MB |********************************                  
       +--------------------------------------------------
        0s                    30s                    60s
```
