# 🎥 3-Camera Integration Update

This document details the configuration and architectural changes made to transition both the **Traditional Python/OpenCV Pipeline** and the **Hardware-Accelerated NVIDIA DeepStream Pipeline** from a single camera input to a 3-camera concurrent stream setup.

---

## 🛠️ Summary of Changes & Rationale

| Modified File | Change Made | Rationale (Why) |
| :--- | :--- | :--- |
| [configs/cameras.yaml](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/configs/cameras.yaml) | Set `enabled: true` for `camera_02` & `camera_03`. Added fallback RTSP URLs containing `channel=32` & `channel=25`. | Standardizes the traditional pipeline to dynamically load and display three camera feeds, while ensuring it doesn't crash if environment variables are not set. |
| [core/config.py](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/core/config.py) | Added mappings for `CAMERA_03_URL` & `CAMERA_04_URL` into the `overrides` dictionary inside `_apply_env_overrides`. | Ensures environment variables are correctly mapped onto the nested config list positions, maintaining deployment flexibility. |
| [ha_meem_master_config.txt](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/deepstream-sdk-map/configs/ha_meem_master_config.txt) | 1. Configured tiled display to a 2x2 grid (`rows=2`, `columns=2`).<br>2. Enabled `[source1]` & added `[source2]`.<br>3. Changed `[streammux]` & `[primary-gie]` `batch-size` to `3`.<br>4. Updated model engine paths to their `_b3` (primary) and `_b16` (secondary) versions. | 1. Visualizes 3 feeds side-by-side.<br>2. Feeds channels 31, 32, and 25 into GStreamer.<br>3. Matches GStreamer batch allocations to the number of input sources.<br>4. Leverages optimized multi-batch TensorRT compilation. |
| [config_infer_primary.txt](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/deepstream-sdk-map/configs/config_infer_primary.txt) | Updated `batch-size=3` and pointed `model-engine-file` to the batch-3 engine. | Commands `nvinfer` to perform hardware-accelerated face detection in batches of 3, optimizing GPU throughput. |
| [config_infer_secondary.txt](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/deepstream-sdk-map/configs/config_infer_secondary.txt) | Updated `batch-size=16` and pointed `model-engine-file` to the batch-16 engine. | Empowers the secondary face recognizer (AdaFace) to extract feature embeddings for up to 16 faces concurrently in one batch pass across all 3 streams. |

---

## 🔍 Detailed Breakdown

### 1. Traditional Python/OpenCV Pipeline
The traditional pipeline uses a dynamic, thread-safe Python architecture. 
* **Dynamic Grid Render**: In [apps/entry_pipeline/main.py](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/apps/entry_pipeline/main.py), the grid columns/rows and cell widths scale dynamically using `math.sqrt(len(workers))`. Because of this, **zero python code edits** were needed to adjust the GUI. Enabling cameras `02` and `03` in `cameras.yaml` automatically partitions the GUI window into a 2x2 grid, showing the 3 active feeds and leaving the 4th cell blank.
* **Environment Overrides**: We updated [core/config.py](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/core/config.py)'s environment parser to ensure that if `CAMERA_03_URL` or `CAMERA_04_URL` are provided inside host shells or `.env` configurations, they will properly override the YAML file structure.

### 2. DeepStream C++ Pipeline (`deepstream-app`)
DeepStream orchestrates its streams natively in C++ via GStreamer. Unlike the Python pipeline, it requires explicit, static hardware mappings inside configuration files:
* **Tiled Display Grid**: The tiled-display element merges multiple decoded streams into a single composite frame. Changing `rows=2` and `columns=2` ensures that a 2x2 grid space is allocated on the GPU, displaying the three video panels side-by-side.
* **Batch Size Rationale**: 
  * The **Stream Multiplexer (`streammux`)** collects incoming frames from the sources and packages them into a single batch. For 3 cameras, we set the batch size to `3` to guarantee that exactly 1 frame from each camera is processed in sync per inference pass.
  * The **Primary GIE (SCRFD Face Detection)** operates on the batched multiplexed frames. Setting its batch size to `3` tells TensorRT to execute the neural network over the three frame matrices concurrently.
  * The **Secondary GIE (AdaFace Recognition)** operates on face chips cropped by the primary detector. Because a single frame may contain multiple faces across the three cameras, the secondary classifier's batch size is set to `16` to handle spikes in face detections without queue latency or lag.

---

## 🔑 DeepStream Face Identification & Custom Probes

### The Problem
The native C++ DeepStream application (`deepstream-app`) is a generic utility. It does not natively understand how to compare feature vectors (embeddings) against our pre-compiled FAISS identity database (`gallery_embeddings_80px_faiss.npy`), nor does it run the temporal consensus aggregator. Because AdaFace outputs a 512-dimensional embedding vector (rather than standard classification logits), `deepstream-app` was unable to map them to real identity names, displaying either generic bounding boxes or random/incorrect labels.

### The Solution
We fully implemented the Custom Python-based GStreamer pipeline at [apps/deepstream_pipeline/main.py](file:///home/ajmunna/Workspace/TDI%20Workspace/Munna/ha_meem_ai_surveillance/apps/deepstream_pipeline/main.py). It functions as follows:
1. **Pipeline Composition**: Creates the multi-source GStreamer pipeline dynamically linking the three active RTSP camera feeds into `nvstreammux` -> `nvinfer` (SCRFD) -> `nvtracker` (NvDCF) -> `nvinfer` (AdaFace) -> `nvmultistreamtiler` -> `nvdsosd` -> `sink`.
2. **Metadata Pad Probe**: Attaches a custom pad probe (`sgie_src_pad_probe`) on the source pad of the secondary GIE (`sgie`).
3. **Embedding Extraction**: Inside the pad probe, reads the raw float tensor outputs (embeddings) using DeepStream Python bindings (`pyds`) and casts them using `ctypes` & `np.ctypeslib`.
4. **Consensus Aggregation**: Passes the embeddings into our core `EmbeddingAggregator` using the hardware-tracked `object_id` as the track key. This reduces frame-level noise.
5. **Database Matching**: Performs cosine similarity queries against the FAISS gallery using `FaceDatabase`.
6. **Overlay Styling & Color Gates**:
   * **Authorized Face**: Dynamically overrides the OSD metadata overlay text to the matching identity name (`a31_mazeda`, `b20_tahamina`, etc.) and sets the box border color to **Green**.
   * **Unknown Face**: Overrides display text to `"UNKNOWN"` and sets the box border color to **Red**.
7. **Asynchronous Snapshot Logging**: Uses `pyds.get_nvds_buf_surface` to extract the raw frame surface as a NumPy array only when a new event is triggered, passing it to our core `io_worker` to write event entries (`logs/events.jsonl`) and snapshots (`snapshots/`) in background threads.

### 📦 Prerequisites for the Custom Python Pipeline
Before running the Python script for the first time inside the DeepStream Docker container, you must install the required dependencies (such as OpenCV, FAISS, and YAML utilities) which are not included in the raw DeepStream Triton base image:
```bash
pip3 install opencv-python-headless faiss-cpu PyYAML python-dotenv
```


