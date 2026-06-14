#!/usr/bin/env python3
"""
DeepStream Python hybrid pipeline with SCRFD Face Detection, NvDCF Tracking,
and AdaFace Recognition embedding matching against FAISS gallery database.
"""

import sys
import os
import time
import ctypes
import numpy as np
import cv2
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from datetime import datetime

# Append workspace path to import core libraries
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.config import load_config, load_merged_configs
from core.database.face_database import FaceDatabase
from core.fusion.aggregator import EmbeddingAggregator
from core.pipeline_state import PipelineState
from core.events.event_emitter import EventEmitter
from core.events.snapshot_writer import SnapshotWriter
from core.io_worker import AsyncIOWorker

# Import DeepStream python bindings
try:
    import pyds
except ImportError:
    print("[ERROR] DeepStream Python bindings (pyds) not found. Please run this script inside the DeepStream container.")
    sys.exit(1)

# Helper Class for EmbeddingAggregator
class DeepStreamFace:
    def __init__(self, track_id, embedding, quality_score=1.0):
        self.track_id = track_id
        self.embedding = embedding
        self.quality_score = quality_score

def on_pad_added(src, new_pad, depay):
    """Dynamic link callback for RTSP source pads."""
    sink_pad = depay.get_static_pad("sink")
    if not sink_pad.is_linked():
        new_pad.link(sink_pad)

def bus_call(bus, message, loop):
    """Callback for GStreamer bus messages."""
    t = message.type
    if t == Gst.MessageType.EOS:
        print("[INFO] End of stream reached. Exiting main loop...")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"[ERROR] {err}: {debug}")
        loop.quit()
    return True

def sgie_src_pad_probe(pad, info, u_data):
    """
    Pad probe callback on SGIE (Secondary GIE) source pad.
    Extracts face embedding vectors from SGIE tensor metadata,
    computes temporal consensus, performs gallery matching via FAISS,
    and updates object text overlays and bounding box colors.
    """
    face_db = u_data["face_db"]
    aggregators = u_data["aggregators"]
    pipeline_states = u_data["pipeline_states"]
    io_workers = u_data["io_workers"]
    camera_id_map = u_data["camera_id_map"]
    similarity_threshold = u_data["similarity_threshold"]
    recognition_config = u_data["recognition_config"]

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    # Fetch batch metadata
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        # Map pad index to camera ID
        pad_idx = frame_meta.pad_index
        camera_id = camera_id_map.get(pad_idx, f"camera_{pad_idx+1:02d}")

        # Auto-expire stale aggregator track entries
        aggregator = aggregators.get(camera_id)
        pipeline_state = pipeline_states.get(camera_id)
        if aggregator and pipeline_state:
            expired_tids = aggregator.expire_stale_tracks()
            for tid in expired_tids:
                pipeline_state.release_track(tid)

        l_obj = frame_meta.obj_meta_list
        frame_surface_np = None  # Lazy numpy surface loading

        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            # Parse user metadata to extract output tensors from SGIE
            l_user = obj_meta.obj_user_meta_list
            embedding = None

            while l_user is not None:
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                except StopIteration:
                    break

                # Check for tensor output metadata
                if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA_DS_INFER_TENSOR_OUTPUT_META"):
                    tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                    layer_info = pyds.get_nvds_LayerInfo(tensor_meta, 0)
                    
                    # Read embedding values
                    ptr = ctypes.cast(layer_info.buffer, ctypes.POINTER(ctypes.c_float))
                    embedding = np.ctypeslib.as_array(ptr, shape=(512,))
                    embedding = np.copy(embedding)  # Ensure data is safely copied out of buffer scope
                    break

                try:
                    l_user = l_user.next
                except StopIteration:
                    break

            if embedding is not None:
                # Normalise embedding vector
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                # Retrieve hardware tracking ID (NvDCF tracker output)
                track_id = obj_meta.object_id
                
                # Consensus aggregation
                if aggregator:
                    face_obj = DeepStreamFace(track_id, embedding)
                    aggregator.add_face(face_obj)
                    consensus_emb = aggregator.get_aggregated_embedding(track_id)
                else:
                    consensus_emb = embedding

                if consensus_emb is not None:
                    # Match query consensus against the gallery
                    identity, score = face_db.match(
                        consensus_emb,
                        similarity_threshold,
                        match_margin=recognition_config.get('match_margin', 0.05),
                        match_top_k=recognition_config.get('match_top_k', 10)
                    )

                    # Trigger alert and save snapshot if needed
                    if pipeline_state and pipeline_state.can_alert(identity, track_id):
                        io_worker = io_workers.get(camera_id)
                        if io_worker:
                            # Lazy-load frame buffer as standard NumPy BGR surface
                            if frame_surface_np is None:
                                try:
                                    n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
                                    frame_copy = np.array(n_frame, copy=True, order='C')
                                    frame_surface_np = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGR)
                                except Exception as e:
                                    print(f"[WARNING] Failed to extract buffer surface: {e}")

                            if frame_surface_np is not None:
                                event_time = datetime.now()
                                x1 = int(obj_meta.rect_params.left)
                                y1 = int(obj_meta.rect_params.top)
                                x2 = int(x1 + obj_meta.rect_params.width)
                                y2 = int(y1 + obj_meta.rect_params.height)

                                event_data = {
                                    "timestamp": event_time.isoformat(),
                                    "camera_id": camera_id,
                                    "track_id": track_id,
                                    "identity": identity,
                                    "score": float(score),
                                    "event": "AUTHORIZED" if identity else "UNKNOWN",
                                    "bbox": [x1, y1, x2, y2]
                                }

                                # Annotate snapshot image
                                snapshot_frame = np.copy(frame_surface_np)
                                cv2.rectangle(snapshot_frame, (x1, y1), (x2, y2), (0, 255, 0) if identity else (0, 0, 255), 2)
                                cv2.putText(snapshot_frame, f"{identity or 'UNKNOWN'} ({score:.2f})", (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if identity else (0, 0, 255), 2)

                                # Submit snapshot writing asynchronously
                                io_worker.submit(snapshot_frame, event_data, identity, event_time)

                        # Record alert decision state
                        pipeline_state.mark_decided(track_id, identity)

                    # Update display label
                    label = f"{identity} ({score:.2f})" if identity else f"UNKNOWN ({score:.2f})"
                    obj_meta.text_params.display_text = label

                    # Set box border color: Green for Authorized, Red for Unknown
                    if identity:
                        obj_meta.rect_params.border_color.set(0.0, 1.0, 0.0, 1.0)  # Green
                    else:
                        obj_meta.rect_params.border_color.set(1.0, 0.0, 0.0, 1.0)  # Red

                    # Set text layout styling
                    obj_meta.text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
                    obj_meta.text_params.text_bg_clr.set(0.0, 0.0, 0.0, 0.6)
                    obj_meta.text_params.font_params.font_size = 12

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def main():
    Gst.init(None)

    # 1. Load Configurations
    config = load_merged_configs([
        'configs/default.yaml',
        'configs/thresholds.yaml',
        'configs/tensorrt.yaml'
    ])
    camera_cfg = load_config('configs/cameras.yaml')

    active_cameras = [cam for cam in camera_cfg.get('cameras', []) if cam.get('enabled', True)]
    if not active_cameras:
        print("[ERROR] No active cameras found in configs/cameras.yaml")
        return

    num_sources = len(active_cameras)
    print(f"[INFO] Initializing DeepStream pipeline with {num_sources} active cameras...")

    # 2. Initialize GStreamer Pipeline Elements
    pipeline = Gst.Pipeline.new("deepstream-surveillance-pipeline")
    
    streammux = Gst.ElementFactory.make("nvstreammux", "stream-muxer")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-nvinfer")
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    sgie = Gst.ElementFactory.make("nvinfer", "secondary-nvinfer")
    tiler = Gst.ElementFactory.make("nvmultistreamtiler", "tiler")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "nvvideo-converter")
    nvosd = Gst.ElementFactory.make("nvdsosd", "nv-onscreendisplay")
    
    if os.environ.get("DISPLAY"):
        print("[INFO] DISPLAY variable detected. Using hardware-accelerated GUI output (nveglglessink).")
        sink = Gst.ElementFactory.make("nveglglessink", "egl-sink")
    else:
        print("[INFO] Headless environment. Defaulting to fakesink output.")
        sink = Gst.ElementFactory.make("fakesink", "fake-sink")

    if not all([streammux, pgie, tracker, sgie, tiler, nvvidconv, nvosd, sink]):
        print("[ERROR] Failed to create one or more GStreamer elements")
        return

    # 3. Configure GStreamer Properties
    streammux.set_property("width", 1920)
    streammux.set_property("height", 1080)
    streammux.set_property("batch-size", num_sources)
    streammux.set_property("batched-push-timeout", 40000)
    streammux.set_property("live-source", 1)
    streammux.set_property("gpu-id", 0)
    streammux.set_property("nvbuf-memory-type", 0)  # CUDA Device memory (NVMM)

    pgie.set_property("config-file-path", os.path.abspath("python_deepstream_pipeline/configs/config_infer_primary.txt"))
    pgie.set_property("unique-id", 1)
    pgie.set_property("gpu-id", 0)

    sgie.set_property("config-file-path", os.path.abspath("python_deepstream_pipeline/configs/config_infer_secondary.txt"))
    sgie.set_property("process-mode", 2)  # Secondary Mode
    sgie.set_property("unique-id", 2)
    sgie.set_property("gpu-id", 0)

    tracker.set_property("tracker-width", 640)
    tracker.set_property("tracker-height", 384)
    tracker.set_property("ll-lib-file", "/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so")
    tracker.set_property("ll-config-file", os.path.abspath("python_deepstream_pipeline/configs/config_tracker_NvDCF_perf.yml"))
    tracker.set_property("gpu-id", 0)

    # Configure grid layout inside tiler
    import math
    grid_cols = math.ceil(math.sqrt(num_sources))
    grid_rows = math.ceil(num_sources / grid_cols)
    tiler.set_property("rows", grid_rows)
    tiler.set_property("columns", grid_cols)
    tiler.set_property("width", 1920)
    tiler.set_property("height", 1080)
    tiler.set_property("gpu-id", 0)
    tiler.set_property("nvbuf-memory-type", 0)

    # 4. Add Elements to Pipeline
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(sgie)
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)

    # 5. Dynamically link RTSP Sources to Streammux
    camera_id_map = {}
    
    for idx, cam_info in enumerate(active_cameras):
        cam_id = cam_info['id']
        url = cam_info['url']
        
        # Build individual stream elements
        source = Gst.ElementFactory.make("rtspsrc", f"rtsp-source-{idx}")
        depay = Gst.ElementFactory.make("rtph264depay", f"rtp-depay-{idx}")
        parser = Gst.ElementFactory.make("h264parse", f"h264-parser-{idx}")
        decoder = Gst.ElementFactory.make("nvv4l2decoder", f"nvv4l2-decoder-{idx}")
        
        if not all([source, depay, parser, decoder]):
            print(f"[ERROR] Failed to create RTSP source elements for stream: {cam_id}")
            return
            
        source.set_property("location", url)
        source.set_property("protocols", 0x4)  # TCP
        source.set_property("latency", 200)
        decoder.set_property("gpu-id", 0)
        
        pipeline.add(source)
        pipeline.add(depay)
        pipeline.add(parser)
        pipeline.add(decoder)
        
        # Dynamic pad link
        source.connect("pad-added", on_pad_added, depay)
        depay.link(parser)
        parser.link(decoder)
        
        # Connect decoder source pad to requested sink pad on streammux
        sink_pad = streammux.get_request_pad(f"sink_{idx}")
        src_pad = decoder.get_static_pad("src")
        if src_pad.link(sink_pad) != Gst.PadLinkReturn.OK:
            print(f"[ERROR] Failed to link decoder for {cam_id} to streammux")
            return
            
        camera_id_map[idx] = cam_id

    # 6. Link Remaining Elements
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(sgie)
    sgie.link(tiler)
    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(sink)

    # 7. Initialize Face Recognition Databases & Per-Camera Pipeline States
    gallery_path = config['dataset']['gallery_embeddings']
    print(f"[INFO] Loading gallery embeddings from: {gallery_path}")
    gallery_embeddings = None
    if os.path.exists(gallery_path) and gallery_path.endswith('.npy'):
        try:
            gallery_embeddings = np.load(gallery_path, allow_pickle=True).item()
        except Exception as e:
            print(f"[WARNING] Failed to load .npy gallery: {e}")
            
    if gallery_embeddings is None:
        txt_paths = [
            "python_deepstream_pipeline/configs/gallery_embeddings.txt",
            "configs/gallery_embeddings.txt",
            "gallery_embeddings.txt",
            "/app/python_deepstream_pipeline/configs/gallery_embeddings.txt",
            "/app/cpp_deepstream_pipeline/configs/gallery_embeddings.txt",
            "/app/configs/gallery_embeddings.txt"
        ]
        if gallery_path.endswith('.npy'):
            txt_paths.insert(0, gallery_path[:-4] + '.txt')
            
        for path in txt_paths:
            if os.path.exists(path):
                print(f"[INFO] Loading gallery embeddings from text file fallback: {path}")
                try:
                    gallery_embeddings = {}
                    with open(path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split()
                            person_id = parts[0]
                            emb = np.array([float(x) for x in parts[1:]], dtype=np.float32)
                            if emb.shape[0] == 512:
                                if person_id not in gallery_embeddings:
                                    gallery_embeddings[person_id] = []
                                gallery_embeddings[person_id].append(emb)
                    if gallery_embeddings:
                        print(f"[SUCCESS] Loaded {len(gallery_embeddings)} identities from text database.")
                        break
                except Exception as e:
                    print(f"[WARNING] Failed to parse text gallery {path}: {e}")
                    gallery_embeddings = None
                    
    if not gallery_embeddings:
        print("[ERROR] Could not load any gallery embeddings database (.npy or .txt).")
        return

    face_db = FaceDatabase(gallery_embeddings)

    aggregators = {}
    pipeline_states = {}
    io_workers = {}
    
    tracking_config = config.get('tracking', {})
    fusion_config = config.get('fusion', {})
    recognition_config = config.get('recognition', {})
    similarity_threshold = recognition_config.get('similarity_threshold', 0.80)

    for cam_info in active_cameras:
        cam_id = cam_info['id']
        aggregators[cam_id] = EmbeddingAggregator(
            buffer_size=fusion_config.get('buffer_size', 10),
            min_frames=fusion_config.get('min_frames', 6),
            min_decision_seconds=fusion_config.get('min_decision_seconds', 0.3),
            recency_decay=fusion_config.get('recency_decay', 0.95),
            expire_after_seconds=fusion_config.get('expire_after_seconds', 5.0)
        )
        pipeline_states[cam_id] = PipelineState(
            camera_id=cam_id,
            cooldown_seconds=recognition_config.get('cooldown_seconds', 6)
        )
        emitter = EventEmitter(camera_id=cam_id, log_file="logs/events.jsonl")
        writer = SnapshotWriter(base_dir="snapshots", camera_id=cam_id)
        io_workers[cam_id] = AsyncIOWorker(emitter, writer)

    # 8. Attach Custom Python Pad Probe to Secondary GIE (SGIE)
    sgie_src_pad = sgie.get_static_pad("src")
    if not sgie_src_pad:
        print("[ERROR] Failed to attach probe: src pad on secondary-nvinfer not found")
        return

    probe_data = {
        "face_db": face_db,
        "aggregators": aggregators,
        "pipeline_states": pipeline_states,
        "io_workers": io_workers,
        "camera_id_map": camera_id_map,
        "similarity_threshold": similarity_threshold,
        "recognition_config": recognition_config
    }
    
    sgie_src_pad.add_probe(Gst.PadProbeType.BUFFER, sgie_src_pad_probe, probe_data)
    print("[SUCCESS] Attached custom Python face recognition pad probe.")

    # 9. Register Pipeline Signals & Start GLib Event Loop
    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    print("[INFO] Starting DeepStream Python Pipeline. Press Ctrl+C to stop.")
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("[ERROR] Failed to start pipeline playing state.")
        return

    try:
        loop.run()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user command.")
    finally:
        print("[INFO] Transitioning pipeline to NULL state...")
        pipeline.set_state(Gst.State.NULL)
        
        print("[INFO] Terminating background event writing threads...")
        for worker in io_workers.values():
            worker.stop()
            
        print("[SUCCESS] Pipeline shutdown completed.")

if __name__ == "__main__":
    main()
