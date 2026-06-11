#include "nvdsinfer_custom_impl.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstring>

struct GalleryEntry {
    std::string person_id;
    std::vector<float> embedding;
};

static std::vector<GalleryEntry> g_gallery;
static bool g_gallery_loaded = false;

// Load the gallery embeddings from the text file
static bool load_gallery() {
    if (g_gallery_loaded) return true;
    
    std::vector<std::string> paths = {
        "gallery_embeddings.txt",
        "../configs/gallery_embeddings.txt",
        "/app/deepstream-sdk-map/configs/gallery_embeddings.txt"
    };
    
    std::ifstream file;
    std::string resolved_path = "";
    for (auto const &p : paths) {
        file.open(p);
        if (file.is_open()) {
            resolved_path = p;
            break;
        }
    }
    
    if (!file.is_open()) {
        std::cerr << "[ERROR] AdaFace C++ Parser: Could not open gallery_embeddings.txt" << std::endl;
        return false;
    }
    
    std::cout << "[INFO] AdaFace C++ Parser: Loading gallery embeddings from: " << resolved_path << std::endl;
    
    std::string line;
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string person_id;
        ss >> person_id;
        
        std::vector<float> emb;
        float val;
        while (ss >> val) {
            emb.push_back(val);
        }
        
        if (emb.size() == 512) {
            // Normalize embedding
            float norm = 0.0f;
            for (float v : emb) norm += v * v;
            norm = std::sqrt(norm);
            if (norm > 1e-6f) {
                for (float &v : emb) v /= norm;
            }
            g_gallery.push_back({person_id, emb});
        }
    }
    
    std::cout << "[SUCCESS] AdaFace C++ Parser: Loaded " << g_gallery.size() << " gallery embeddings." << std::endl;
    g_gallery_loaded = true;
    return true;
}

extern "C" bool NvDsInferClassifyCustomAdaFace(
    std::vector<NvDsInferLayerInfo> const &outputLayersInfo,
    NvDsInferNetworkInfo const &networkInfo,
    float classifierThreshold,
    std::vector<NvDsInferAttribute> &attrList,
    std::string &descString) {
    
    if (!g_gallery_loaded) {
        if (!load_gallery()) {
            return false;
        }
    }
    
    if (outputLayersInfo.empty()) {
        std::cerr << "[ERROR] AdaFace C++ Parser: Output layers are empty!" << std::endl;
        return false;
    }
    
    // Access output layer buffer (contains 512 floats representing embedding)
    const float *query = (const float *)outputLayersInfo[0].buffer;
    if (!query) {
        std::cerr << "[ERROR] AdaFace C++ Parser: Output layer buffer is null!" << std::endl;
        return false;
    }
    
    // Safely copy query embedding and normalize it
    std::vector<float> q_emb(512);
    float q_norm = 0.0f;
    for (int i = 0; i < 512; ++i) {
        q_emb[i] = query[i];
        q_norm += query[i] * query[i];
    }
    q_norm = std::sqrt(q_norm);
    if (q_norm > 1e-6f) {
        for (int i = 0; i < 512; ++i) {
            q_emb[i] /= q_norm;
        }
    }
    
    // Find best match in the gallery database
    float best_score = -1.0f;
    std::string best_id = "UNKNOWN";
    int best_index = -1;
    
    for (size_t i = 0; i < g_gallery.size(); ++i) {
        auto const &entry = g_gallery[i];
        float dot = 0.0f;
        for (int j = 0; j < 512; ++j) {
            dot += q_emb[j] * entry.embedding[j];
        }
        if (dot > best_score) {
            best_score = dot;
            best_id = entry.person_id;
            best_index = i;
        }
    }
    
    // Populate the attribute list
    NvDsInferAttribute attr;
    attr.attributeIndex = 0;
    attr.attributeConfidence = best_score;
    
    // Cosine similarity comparison with classifierThreshold (similarity threshold)
    if (best_score >= classifierThreshold) {
        attr.attributeValue = best_index;
        attr.attributeLabel = strdup(best_id.c_str());
        descString = best_id + " (" + std::to_string((int)(best_score * 100)) + "%)";
    } else {
        attr.attributeValue = -1;
        attr.attributeLabel = strdup("UNKNOWN");
        descString = "UNKNOWN (" + std::to_string((int)(best_score * 100)) + "%)";
    }
    
    attrList.push_back(attr);
    return true;
}

CHECK_CUSTOM_CLASSIFIER_PARSE_FUNC_PROTOTYPE(NvDsInferClassifyCustomAdaFace);
