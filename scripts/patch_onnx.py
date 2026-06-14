import onnx
from onnx import numpy_helper
import numpy as np
import os

def patch_model():
    model_paths = ["models/scrfd_10g_bnkps.onnx"]
    
    for path in model_paths:
        if not os.path.exists(path):
            print(f"Path does not exist: {path}, skipping.")
            continue
            
        print(f"Patching model: {path}")
        model = onnx.load(path)
        
        # 1. Update Reshape shape initializers to output 3D tensors (adding batch dim of 1)
        for initializer in model.graph.initializer:
            if initializer.name == "446":
                arr = numpy_helper.to_array(initializer)
                print(f"  Updating initializer 446 (scores shape) from {arr} to [1, -1, 1]")
                new_arr = np.array([1, -1, 1], dtype=arr.dtype)
                new_tensor = numpy_helper.from_array(new_arr, name="446")
                initializer.CopyFrom(new_tensor)
            elif initializer.name == "450":
                arr = numpy_helper.to_array(initializer)
                print(f"  Updating initializer 450 (bboxes shape) from {arr} to [1, -1, 4]")
                new_arr = np.array([1, -1, 4], dtype=arr.dtype)
                new_tensor = numpy_helper.from_array(new_arr, name="450")
                initializer.CopyFrom(new_tensor)
            elif initializer.name == "453":
                arr = numpy_helper.to_array(initializer)
                print(f"  Updating initializer 453 (landmarks shape) from {arr} to [1, -1, 10]")
                new_arr = np.array([1, -1, 10], dtype=arr.dtype)
                new_tensor = numpy_helper.from_array(new_arr, name="453")
                initializer.CopyFrom(new_tensor)
        
        # 2. Update model output value info metadata shapes
        output_shapes = {
            "448": [1, 12800, 1],
            "471": [1, 3200, 1],
            "494": [1, 800, 1],
            "451": [1, 12800, 4],
            "474": [1, 3200, 4],
            "497": [1, 800, 4],
            "454": [1, 12800, 10],
            "477": [1, 3200, 10],
            "500": [1, 800, 10]
        }
        
        for output in model.graph.output:
            if output.name in output_shapes:
                shape = output_shapes[output.name]
                # Clear existing shape
                output.type.tensor_type.shape.Clear()
                # Add new dimensions
                for dim_val in shape:
                    dim = output.type.tensor_type.shape.dim.add()
                    dim.dim_value = dim_val
                print(f"  Updated output {output.name} shape to {shape}")
                
        # Save the patched model back
        onnx.save(model, path)
        print(f"Saved patched model to {path}\n")

if __name__ == "__main__":
    patch_model()
