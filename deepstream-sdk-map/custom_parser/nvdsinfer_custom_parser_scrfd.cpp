#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "nvdsinfer_custom_impl.h"

// Helper function to decode distances to bounding boxes
static inline void decode_bbox(float anchor_x, float anchor_y, const float* distance, float stride, float* x1, float* y1, float* x2, float* y2) {
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
    std::vector<NvDsInferObjectDetectionInfo> &objectList)
{
    const NvDsInferLayerInfo* score8 = nullptr;
    const NvDsInferLayerInfo* bbox8 = nullptr;
    const NvDsInferLayerInfo* score16 = nullptr;
    const NvDsInferLayerInfo* bbox16 = nullptr;
    const NvDsInferLayerInfo* score32 = nullptr;
    const NvDsInferLayerInfo* bbox32 = nullptr;

    for (auto const& layer : outputLayersInfo) {
        std::string name(layer.layerName);
        if (name == "448") score8 = &layer;
        else if (name == "451") bbox8 = &layer;
        else if (name == "471") score16 = &layer;
        else if (name == "474") bbox16 = &layer;
        else if (name == "494") score32 = &layer;
        else if (name == "497") bbox32 = &layer;
    }

    if (!score8 || !bbox8 || !score16 || !bbox16 || !score32 || !bbox32) {
        std::cerr << "SCRFD Custom Parser: Missing one or more required output layers" << std::endl;
        return false;
    }

    float thresh = detectionParams.perClassPreclusterThreshold[0];

    // Define strides and layers
    struct StrideConfig {
        float stride;
        const NvDsInferLayerInfo* scoreLayer;
        const NvDsInferLayerInfo* bboxLayer;
    };

    std::vector<StrideConfig> configs = {
        {8.0f, score8, bbox8},
        {16.0f, score16, bbox16},
        {32.0f, score32, bbox32}
    };

    int net_w = networkInfo.width; // 640
    int net_h = networkInfo.height; // 640

    for (auto const& cfg : configs) {
        float stride = cfg.stride;
        const float* scores = (const float*)cfg.scoreLayer->buffer;
        const float* bbox_preds = (const float*)cfg.bboxLayer->buffer;

        int grid_h = net_h / stride;
        int grid_w = net_w / stride;
        int num_anchors = 2; // SCRFD uses 2 anchors per scale step

        for (int y = 0; y < grid_h; ++y) {
            for (int x = 0; x < grid_w; ++x) {
                float anchor_x = x * stride;
                float anchor_y = y * stride;

                for (int a = 0; a < num_anchors; ++a) {
                    int idx = (y * grid_w + x) * num_anchors + a;
                    float score = scores[idx];

                    if (score >= thresh) {
                        float x1, y1, x2, y2;
                        decode_bbox(anchor_x, anchor_y, &bbox_preds[idx * 4], stride, &x1, &y1, &x2, &y2);

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
                        }
                    }
                }
            }
        }
    }

    return true;
}

CHECK_CUSTOM_PARSE_FUNC_PROTOTYPE(NvDsInferParseCustomSCRFD);
