#include "nvdsinfer_custom_impl.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <string>
#include <vector>

// Helper function to decode distances to bounding boxes
static inline void decode_bbox(float anchor_x, float anchor_y,
                               const float *distance, float stride, float *x1,
                               float *y1, float *x2, float *y2) {
  float dx1 = distance[0] * stride;
  float dy1 = distance[1] * stride;
  float dx2 = distance[2] * stride;
  float dy2 = distance[3] * stride;

  *x1 = anchor_x - dx1;
  *y1 = anchor_y - dy1;
  *x2 = anchor_x + dx2;
  *y2 = anchor_y + dy2;
}

extern "C" bool NvDsInferParseCustomSCRFD(
    std::vector<NvDsInferLayerInfo> const &outputLayersInfo,
    NvDsInferNetworkInfo const &networkInfo,
    NvDsInferParseDetectionParams const &detectionParams,
    std::vector<NvDsInferObjectDetectionInfo> &objectList) {
  
  static bool printed_info = false;
  if (!printed_info) {
    std::cout << "\n=== SCRFD Parser Info ===\n";
    std::cout << "Network Info: " << networkInfo.width << "x" << networkInfo.height << "\n";
    std::cout << "Output Layers count: " << outputLayersInfo.size() << "\n";
    for (size_t i = 0; i < outputLayersInfo.size(); ++i) {
      auto const &layer = outputLayersInfo[i];
      std::cout << "  Layer " << i << ": name=" << layer.layerName 
                << ", dataType=" << layer.dataType 
                << ", buffer=" << layer.buffer;
      if (layer.inferDims.numDims > 0) {
        std::cout << ", dims=[";
        for (unsigned int d = 0; d < layer.inferDims.numDims; ++d) {
          std::cout << layer.inferDims.d[d] << (d == layer.inferDims.numDims - 1 ? "" : ",");
        }
        std::cout << "]";
      }
      std::cout << "\n";
    }
    std::cout << "Detection Params: preclusterThreshold=" 
              << (detectionParams.numClassesConfigured > 0 ? detectionParams.perClassPreclusterThreshold[0] : 0.0)
              << "\n=========================\n" << std::endl;
    printed_info = true;
  }

  const NvDsInferLayerInfo *score8 = nullptr;
  const NvDsInferLayerInfo *bbox8 = nullptr;
  const NvDsInferLayerInfo *score16 = nullptr;
  const NvDsInferLayerInfo *bbox16 = nullptr;
  const NvDsInferLayerInfo *score32 = nullptr;
  const NvDsInferLayerInfo *bbox32 = nullptr;

  for (auto const &layer : outputLayersInfo) {
    std::string name(layer.layerName);
    if (name == "448")
      score8 = &layer;
    else if (name == "451")
      bbox8 = &layer;
    else if (name == "471")
      score16 = &layer;
    else if (name == "474")
      bbox16 = &layer;
    else if (name == "494")
      score32 = &layer;
    else if (name == "497")
      bbox32 = &layer;
  }

  if (!score8 || !bbox8 || !score16 || !bbox16 || !score32 || !bbox32) {
    static int missing_counter = 0;
    if (missing_counter++ % 100 == 0) {
      std::cerr
          << "SCRFD Custom Parser: Missing one or more required output layers"
          << std::endl;
    }
    return false;
  }

  float thresh = detectionParams.perClassPreclusterThreshold[0];

  // Define strides and layers
  struct StrideConfig {
    float stride;
    const NvDsInferLayerInfo *scoreLayer;
    const NvDsInferLayerInfo *bboxLayer;
  };

  std::vector<StrideConfig> configs = {{8.0f, score8, bbox8},
                                       {16.0f, score16, bbox16},
                                       {32.0f, score32, bbox32}};

  int net_w = networkInfo.width;  // 640
  int net_h = networkInfo.height; // 640

  static int frame_counter = 0;
  bool print_frame = (frame_counter++ % 60 == 0);

  for (auto const &cfg : configs) {
    float stride = cfg.stride;
    const float *scores = (const float *)cfg.scoreLayer->buffer;
    const float *bbox_preds = (const float *)cfg.bboxLayer->buffer;

    int grid_h = net_h / stride;
    int grid_w = net_w / stride;
    int num_anchors = 2; // SCRFD uses 2 anchors per scale step

    float max_score_this_stride = -9999.0f;
    int detections_this_stride = 0;

    for (int y = 0; y < grid_h; ++y) {
      for (int x = 0; x < grid_w; ++x) {
        float anchor_x = x * stride;
        float anchor_y = y * stride;

        for (int a = 0; a < num_anchors; ++a) {
          int idx = (y * grid_w + x) * num_anchors + a;
          float score = scores[idx];

          if (score > max_score_this_stride) {
            max_score_this_stride = score;
          }

          if (score >= thresh) {
            float x1, y1, x2, y2;
            decode_bbox(anchor_x, anchor_y, &bbox_preds[idx * 4], stride, &x1,
                        &y1, &x2, &y2);

            // Clamp to image coordinates
            x1 = std::max(0.0f, std::min(x1, (float)(net_w - 1)));
            y1 = std::max(0.0f, std::min(y1, (float)(net_h - 1)));
            x2 = std::max(0.0f, std::min(x2, (float)(net_w - 1)));
            y2 = std::max(0.0f, std::min(y2, (float)(net_h - 1)));

            if (x2 > x1 && y2 > y1) {
              NvDsInferObjectDetectionInfo obj;
              obj.classId = 0; // Class 0: Face
              obj.left = x1;
              obj.top = y1;
              obj.width = x2 - x1;
              obj.height = y2 - y1;
              obj.detectionConfidence = score;
              objectList.push_back(obj);
              detections_this_stride++;
            }
          }
        }
      }
    }
    if (print_frame) {
      std::cout << "Stride " << stride << " max score: " << max_score_this_stride 
                << ", threshold: " << thresh 
                << ", detections parsed: " << detections_this_stride << std::endl;
    }
  }

  return true;
}

CHECK_CUSTOM_PARSE_FUNC_PROTOTYPE(NvDsInferParseCustomSCRFD);

