import sys
import os
import ctypes
import numpy as np
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Append workspace path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.config import load_config, load_merged_configs
from core.database.face_database import FaceDatabase
from core.pipeline_state import PipelineState

import pyds

def on_pad_added(src, new_pad, depay):
    print("Dynamic pad added, linking to depayloader...")
    sink_pad = depay.get_static_pad("sink")
    if not sink_pad.is_linked():
        new_pad.link(sink_pad)

def sgie_src_pad_probe(pad, info, u_data):
    return Gst.PadProbeReturn.OK

def main():
    Gst.init(None)
    
    # Load and merge configurations
    config = load_merged_configs([
        'configs/default.yaml',
        'configs/thresholds.yaml',
        'configs/tensorrt.yaml'
    ])
    camera_cfg = load_config('configs/cameras.yaml')
    
    # Identify the active camera URL
    active_cameras = [cam for cam in camera_cfg.get('cameras', []) if cam.get('enabled', True)]
    if not active_cameras:
        print("No active camera configuration found")
        return
    
    camera_info = active_cameras[0]
    camera_id = camera_info['id']
    camera_url = camera_info['url']
    
    print(f"Loading gallery embeddings from {config['dataset']['gallery_embeddings']}...")
    gallery_path = config['dataset']['gallery_embeddings']
    gallery_embeddings = np.load(gallery_path, allow_pickle=True).item()
    
    # Initialize shared components
    face_db = FaceDatabase(gallery_embeddings)
    pipeline_state = PipelineState(camera_id=camera_id)
    
    print(f"Creating GStreamer pipeline for RTSP input: {camera_url}")
    pipeline = Gst.Pipeline.new("deepstream-surveillance-pipeline")
    
    # Create GStreamer Elements
    source = Gst.ElementFactory.make("rtspsrc", "rtsp-source")
    depay = Gst.ElementFactory.make("rtph264depay", "rtp-depay")
    parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    streammux = Gst.ElementFactory.make("nvstreammux", "stream-muxer")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-nvinfer")
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    sgie = Gst.ElementFactory.make("nvinfer", "secondary-nvinfer")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "nvvideo-converter")
    nvosd = Gst.ElementFactory.make("nvdsosd", "nv-onscreendisplay")
    sink = Gst.ElementFactory.make("fakesink", "fake-sink") # Use fakesink for headless test
    
    if not all([source, depay, parser, decoder, streammux, pgie, tracker, sgie, nvvidconv, nvosd, sink]):
        print("Failed to create one or more GStreamer elements")
        return
        
    # Configure Properties
    source.set_property("location", camera_url)
    source.set_property("protocols", 0x4)  # TCP
    source.set_property("latency", 200)
    
    streammux.set_property("width", 1920)
    streammux.set_property("height", 1080)
    streammux.set_property("batch-size", 1)
    streammux.set_property("batched-push-timeout", 40000)
    streammux.set_property("live-source", 1)
    
    pgie.set_property("unique-id", 1)
    pgie.set_property("config-file-path", os.path.abspath("cpp_deepstream_pipeline/configs/config_infer_primary.txt"))
    
    sgie.set_property("process-mode", 2) # Secondary
    sgie.set_property("unique-id", 2)
    sgie.set_property("config-file-path", os.path.abspath("cpp_deepstream_pipeline/configs/config_infer_secondary.txt"))
    
    tracker.set_property("tracker-width", 640)
    tracker.set_property("tracker-height", 384)
    tracker.set_property("ll-lib-file", "/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so")
    tracker.set_property("ll-config-file", os.path.abspath("cpp_deepstream_pipeline/configs/config_tracker_NvDCF_perf.yml"))
    tracker.set_property("gpu-id", 0)
    
    # Add Elements to Pipeline
    pipeline.add(source)
    pipeline.add(depay)
    pipeline.add(parser)
    pipeline.add(decoder)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(sgie)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    
    # Link RTSP Source dynamically since pads are created at runtime
    source.connect("pad-added", on_pad_added, depay)
    
    # Link static elements
    depay.link(parser)
    parser.link(decoder)
    
    # Link decoder output (static src pad) to streammux input (request pad)
    sinkpad = streammux.get_request_pad("sink_0")
    srcpad = decoder.get_static_pad("src")
    if srcpad.link(sinkpad) != Gst.PadLinkReturn.OK:
        print("Failed to link decoder to streammux")
        return
        
    # Link remaining elements sequentially
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(sgie)
    sgie.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(sink)
    
    print("Transitioning pipeline to PLAYING state...")
    ret = pipeline.set_state(Gst.State.PLAYING)
    print(f"Set state PLAYING returned: {ret}")
    
    # Wait for 10 seconds to verify it stays running
    import time
    time.sleep(10)
    
    print("Stopping pipeline...")
    pipeline.set_state(Gst.State.NULL)
    print("Done")

if __name__ == "__main__":
    main()
