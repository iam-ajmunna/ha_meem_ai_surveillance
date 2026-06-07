# Performance Profile Report: Baseline Surveillance Pipeline

Generated on: `2026-06-07 19:49:39`  
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
| **Total System CPU %** | 68.4% | 88.5% |
| **Total System RAM %** | 36.2% | 36.3% |
| **Pipeline Process CPU %** | 231.3% | 318.0% |
| **Pipeline Process RAM** | 832.4 MB | 834.5 MB |
| **GPU Utilization %** | 26.4% | 39.0% |
| **GPU VRAM Usage** | 489.4 MB | 514.0 MB |

## 🌳 Process & Thread Hierarchy Tree
> [!NOTE]
> CPU usage percentages for individual threads are relative to a single core (100% capacity = 1 full CPU core core).
> Memory (RAM) is shared globally by all threads within the main process address space.

```text
└─ [PID: 35758] python (Main Process) | Avg CPU: 231.3% | Avg RAM: 832.4 MB (5.3%)
   ├─ [TID: 35758] Main Thread            | Avg CPU: 9.4% | RAM: Shared
   ├─ [TID: 35866] WorkerThread-35866     | Avg CPU: 99.0% | RAM: Shared
   ├─ [TID: 35909] WorkerThread-35909     | Avg CPU: 97.5% | RAM: Shared
   ├─ [TID: 35913] WorkerThread-35913     | Avg CPU: 6.0% | RAM: Shared
   ├─ [TID: 35914] WorkerThread-35914     | Avg CPU: 5.8% | RAM: Shared
   ├─ [TID: 35867] WorkerThread-35867     | Avg CPU: 5.6% | RAM: Shared
   ├─ [TID: 35915] WorkerThread-35915     | Avg CPU: 5.5% | RAM: Shared
   ├─ [TID: 35908] av:h264:df3            | Avg CPU: 0.9% | RAM: Shared
   ├─ [TID: 35906] av:h264:df1            | Avg CPU: 0.9% | RAM: Shared
   ├─ [TID: 35907] av:h264:df2            | Avg CPU: 0.8% | RAM: Shared
   ├─ [TID: 35905] av:h264:df0            | Avg CPU: 0.8% | RAM: Shared
   ├─ [TID: 35910] WorkerThread-35910     | Avg CPU: 0.2% | RAM: Shared
   ├─ [TID: 35911] WorkerThread-35911     | Avg CPU: 0.2% | RAM: Shared
   ├─ [TID: 35912] WorkerThread-35912     | Avg CPU: 0.2% | RAM: Shared
   ├─ [TID: 35918] QXcbEventQueue         | Avg CPU: 0.1% | RAM: Shared
   ├─ [TID: 35759] WorkerThread-35759     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35760] WorkerThread-35760     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35761] WorkerThread-35761     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35791] WorkerThread-35791     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35792] WorkerThread-35792     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35793] WorkerThread-35793     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35818] WorkerThread-35818     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35819] WorkerThread-35819     | Avg CPU: 0.0% | RAM: Shared
   ├─ [TID: 35820] WorkerThread-35820     | Avg CPU: 0.0% | RAM: Shared
   └─ [TID: 35880] WorkerThread-35880     | Avg CPU: 0.0% | RAM: Shared
```

## 🧵 Detailed Thread Breakdown

| Thread ID (TID) | Thread Name | Average CPU % | Status / Description |
| :--- | :--- | :--- | :--- |
| `35758` | `Main Thread` | 9.4% | Main application event loop |
| `35866` | `WorkerThread-35866` | 99.0% | Background worker thread |
| `35909` | `WorkerThread-35909` | 97.5% | Background worker thread |
| `35913` | `WorkerThread-35913` | 6.0% | Background worker thread |
| `35914` | `WorkerThread-35914` | 5.8% | Background worker thread |
| `35867` | `WorkerThread-35867` | 5.6% | Background worker thread |
| `35915` | `WorkerThread-35915` | 5.5% | Background worker thread |
| `35908` | `av:h264:df3` | 0.9% | Background worker thread |
| `35906` | `av:h264:df1` | 0.9% | Background worker thread |
| `35907` | `av:h264:df2` | 0.8% | Background worker thread |
| `35905` | `av:h264:df0` | 0.8% | Background worker thread |
| `35910` | `WorkerThread-35910` | 0.2% | Background worker thread |
| `35911` | `WorkerThread-35911` | 0.2% | Background worker thread |
| `35912` | `WorkerThread-35912` | 0.2% | Background worker thread |
| `35918` | `QXcbEventQueue` | 0.1% | Background worker thread |
| `35759` | `WorkerThread-35759` | 0.0% | Background worker thread |
| `35760` | `WorkerThread-35760` | 0.0% | Background worker thread |
| `35761` | `WorkerThread-35761` | 0.0% | Background worker thread |
| `35791` | `WorkerThread-35791` | 0.0% | Background worker thread |
| `35792` | `WorkerThread-35792` | 0.0% | Background worker thread |
| `35793` | `WorkerThread-35793` | 0.0% | Background worker thread |
| `35818` | `WorkerThread-35818` | 0.0% | Background worker thread |
| `35819` | `WorkerThread-35819` | 0.0% | Background worker thread |
| `35820` | `WorkerThread-35820` | 0.0% | Background worker thread |
| `35880` | `WorkerThread-35880` | 0.0% | Background worker thread |

## 📈 Performance Utilization Over Time

#### Pipeline Process CPU % Over Time
```text
318.0% |              *                                   
293.1% |             *                      *             
268.2% |                                                  
243.3% |                                                  
218.5% |  **** ******  ************** ****** *************
193.6% | *    *                                           
168.7% |                             *                    
143.8% |*                                                 
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU Utilization % Over Time
```text
 39.0% |    *                                    *        
 34.1% |         * *  * *                                 
 29.3% |     **             *    *  *       ** *    * *  *
 24.4% | *           * *  ** ** *  * * * *        *    *  
 19.6% |          * *    *     *  *   * * **  * *  * *    
 14.7% |*       *                                       * 
  9.9% |   *   *                                          
  5.0% |  *                                               
       +--------------------------------------------------
        0s                    30s                    60s
```
#### GPU VRAM Used (MB) Over Time
```text
514.0 MB |      *                                           
509.0 MB |     * *                                          
504.0 MB |        **                                        
499.0 MB |          *                 **                    
494.0 MB |   *                 * ****                       
489.0 MB |*   *      ********** *    *                      
484.0 MB | **                           ***                 
479.0 MB |                                 *****************
       +--------------------------------------------------
        0s                    30s                    60s
```
