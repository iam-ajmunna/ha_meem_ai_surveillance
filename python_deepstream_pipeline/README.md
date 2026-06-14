# Python DeepStream Surveillance Pipeline

This directory contains the custom, production-ready Python GStreamer bindings implementation of the Ha-Meem face surveillance pipeline (Face Detection + NvDCF Tracking + AdaFace Recognition).

It operates **100% independently** of the C++ Native pipeline folder and contains its own copy of configuration parameters and custom parsing source codes.

---

## 🚀 Step-by-Step Running Guide

Follow these steps from the root of your workspace (`/app`) inside your running DeepStream Triton container:

### Step 1: Compile the Custom Parsers
The Python pipeline utilizes specialized C++ parser libraries to decode model bounding boxes and embeddings at runtime. Run these commands inside the container to build them locally:

```bash
# 1. Navigate to the custom parser folder
cd /app/python_deepstream_pipeline/custom_parser

# 2. Compile the SCRFD Bounding Box Parser
g++ -shared -fPIC -o libnvdsinfer_custom_impl_scrfd.so \
    nvdsinfer_custom_parser_scrfd.cpp \
    -Iinclude \
    -I/opt/nvidia/deepstream/deepstream/sources/includes \
    -I/usr/local/cuda/include \
    -O3 -std=c++17

# 3. Compile the AdaFace Face Recognition/Matching Parser
g++ -shared -fPIC -o libnvdsinfer_custom_impl_adaface.so \
    nvdsinfer_custom_parser_adaface.cpp \
    -Iinclude \
    -I/opt/nvidia/deepstream/deepstream/sources/includes \
    -I/usr/local/cuda/include \
    -O3 -std=c++17
```

---

### Step 2: Run the Pipeline
Once the shared library parsers are built, start the Python process from the root directory:

```bash
# 1. Ensure Python dependencies are installed (first time only)
pip3 install opencv-python-headless faiss-cpu PyYAML python-dotenv

# 2. Launch the pipeline
python3 /app/python_deepstream_pipeline/main.py
```

---

## 📁 Independent Directory Layout

* `main.py`: Main python pipeline orchestrator.
* `configs/`: 
  * `config_infer_primary.txt`: Configures the face detector model properties and parser path.
  * `config_infer_secondary.txt`: Configures the face embedder model properties and parser path.
  * `config_tracker_NvDCF_perf.yml`: Configures tracking parameters.
  * `labels_primary.txt` & `labels_secondary.txt`: Output label definitions.
  * `gallery_embeddings.txt`: Output target names/embeddings database.
* `custom_parser/`: Custom C++ source files, headers, and the compiled `.so` output plugins.
