import sys
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

def main():
    Gst.init(None)
    pipeline = Gst.Pipeline.new("test-pipeline")
    
    pgie = Gst.ElementFactory.make("nvinfer", "primary-nvinfer")
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    sgie = Gst.ElementFactory.make("nvinfer", "secondary-nvinfer")
    
    if not all([pgie, tracker, sgie]):
        print("Failed to create elements")
        return
        
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(sgie)
    
    print("Setting pgie properties...")
    pgie.set_property("unique-id", 1)
    pgie.set_property("config-file-path", os.path.abspath("deepstream-sdk-map/configs/config_infer_primary.txt"))
    
    print("Setting tracker properties...")
    tracker.set_property("tracker-width", 640)
    tracker.set_property("tracker-height", 384)
    tracker.set_property("ll-lib-file", "/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so")
    tracker.set_property("ll-config-file", "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_tracker_NvDCF_perf.yml")
    
    print("Setting sgie properties...")
    # Test setting process-mode before config-file-path
    # sgie.set_property("process-mode", 2)
    sgie.set_property("unique-id", 2)
    sgie.set_property("config-file-path", os.path.abspath("deepstream-sdk-map/configs/config_infer_secondary.txt"))
    
    print("Transitioning pipeline to PLAYING state...")
    ret = pipeline.set_state(Gst.State.PLAYING)
    print(f"Set state PLAYING returned: {ret}")
    
    # Wait for 2 seconds to let things initialize or fail
    import time
    time.sleep(2)
    
    print("Transitioning pipeline to NULL state...")
    pipeline.set_state(Gst.State.NULL)
    print("Done")

if __name__ == "__main__":
    main()
