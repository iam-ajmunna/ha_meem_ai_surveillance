# DeepStream Surveillance Pipeline Integration (SCRFD + AdaFace)

This directory contains the configurations, models, and custom C++ output parser for running the hardware-accelerated surveillance pipeline using the NVIDIA DeepStream SDK.

---

## What is Happening Here?

Your DeepStream application (`deepstream-app`) is orchestrating a GStreamer multimedia pipeline:

1. **Source**: Decodes an RTSP camera stream (`rtsp://admin:admin123@175.29.168.110:6222/cam/realmonitor?channel=31&subtype=0`).
2. **Primary AI (`nvinfer`)**: Runs hardware-accelerated inference using the **SCRFD face detector** (`scrfd_10g_bnkps.onnx`).
3. **Custom Parser (`libnvdsinfer_custom_impl_scrfd.so`)**: Dynamically parses the raw output tensors of the SCRFD model (class scores and box offsets across strides 8, 16, and 32) into DeepStream bounding box metadata.
4. **Tracker (`nvds_nvmultiobjecttracker`)**: Tracks detected faces frame-to-frame using the highly optimized NvDCF tracking algorithm.
5. **Secondary AI (`nvinfer`)**: Extracts face embeddings from the tracked face bounding boxes using **AdaFace** (`adaface.onnx`).
6. **Sink**: Outputs/discards video frames headlessly (`fakesink`) since inference metadata is processed downstream in Python probes.

---

## What Made the App Run Successfully? (Key Changes)

We resolved three critical issues that were causing crashes:

### 1. Fixed TensorRT Spatial Shape Compilation Error

- **Problem**: The original SCRFD model had dynamic input spatial dimensions `[1, 3, '?', '?']`. TensorRT failed to compile it under DeepStream because no optimization profile was defined.
- **Fix**: Programmatically modified the ONNX input dimensions to static `640x640` spatial dimensions: `['batch_size', 3, 640, 640]`.

### 2. Resolved Memory Out-of-Bounds Violations (`cudaErrorIllegalAddress`/`cudaErrorMisalignedAddress`)

- **Problem**: The original model's output tensors lacked a batch dimension (e.g. `[12800, 1]`). In DeepStream's default _implicit batch mode_, `nvinfer` stripped the first dimension (`12800`) as the batch dimension, leaving an allocated buffer size of only `1` float for scores and `4` floats for coordinates. When the custom parser tried to loop over all 12,800 anchors, it accessed out-of-bounds memory on the GPU.
- **Fix**: Programmatically inserted a dynamic batch dimension into all model outputs: `['batch_size', 12800, 1]`, `['batch_size', 12800, 4]`, etc. TensorRT was then forced to retain the full buffer size at runtime.

### 3. Created a C++ Custom Bounding Box Parser for SCRFD

- **Problem**: The original config file referenced `NvDsInferParseYolo` from the default library, which does not exist in DeepStream 7.0 and would have decoded the coordinates incorrectly (since SCRFD has a different stride/anchor mechanism than YOLO).
- **Fix**: Wrote a custom C++ bounding box parser (`custom_parser/nvdsinfer_custom_parser_scrfd.cpp`) matching the anchor-based multi-stride decoding scheme of the original Python code. We compiled it into a shared object (`libnvdsinfer_custom_impl_scrfd.so`) inside the container.

---

## Configuration File Structure

- **`ha_meem_master_config.txt`**: The orchestration file configuring sources, tile displays, secondary classifiers, the tracker, and fakesinks.
- **`config_infer_primary.txt`**: Properties for the primary GIE (SCRFD detector). Configured to load the compiled C++ parser library and map layers `"448"`, `"451"`, `"471"`, `"474"`, `"494"`, `"497"` (scores and bounding boxes).
- **`config_infer_secondary.txt`**: Properties for the secondary GIE (AdaFace face recognizer).
- **`custom_parser/`**:
  - `nvdsinfer_custom_parser_scrfd.cpp`: C++ decoding logic.
  - `libnvdsinfer_custom_impl_scrfd.so`: Compiled shared library linked in `config_infer_primary.txt`.

---

## What Does the PERF Score Mean?

The performance tracker periodically outputs lines like:

```text
**PERF:  19.68 (6.94)
**PERF:  0.67 (6.63)
**PERF:  0.00 (6.33)
```

- **Current FPS (e.g., `19.68` / `0.67`)**: The instantaneous processing speed (Frames Per Second) of the pipeline.
- **Average FPS (e.g., `6.94`)**: The overall average processing speed since the pipeline transitioned to the `PLAYING` state.
- **Why did the FPS fluctuate in your run?**
  1. **Network Packet Loss/Lag**: The warnings `Could not receive any UDP packets for 5.0000 seconds` indicate that the RTSP connection over UDP was blocked or lagged.
  2. **TCP Fallback**: When the connection fell back to TCP, frames were buffered and delivered in bursts. This caused the processing rate to alternate between very high rates (when processing buffered bursts) and `0.00` (when waiting for new packets).
  3. **Stability**: Once the network transmission stabilizes, the FPS will consistently match your RTSP stream's output rate (usually 20 or 25 FPS).

---

## Build and Run Instructions

docker run --gpus all -it --rm --net=host -v "/home/ajmunna/Workspace/TDI Workspace/Munna/ha_meem_ai_surveillance:/app" nvcr.io/nvidia/deepstream:7.0-triton-multiarch bash

### 1. Compile the Parser (Inside Container)

If you modify the C++ parser code, recompile it using the following command inside the container:

```bash
g++ -shared -fPIC -o /app/deepstream-sdk-map/custom_parser/libnvdsinfer_custom_impl_scrfd.so \
    /app/deepstream-sdk-map/custom_parser/nvdsinfer_custom_parser_scrfd.cpp \
    -I/opt/nvidia/deepstream/deepstream/sources/includes \
    -I/usr/local/cuda/include \
    -O3 -std=c++11
```

### 2. Run the Application

Start the pipeline headlessly inside the configs directory:

```bash
cd /app/deepstream-sdk-map/configs
deepstream-app -c ha_meem_master_config.txt
```
