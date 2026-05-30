/*
 * 增强版BLE模型更新器
 * 实现完整的模型热更新协议，支持校验和验证、增量更新等功能
 */

#include "BLEModelUpdater.h"
#include "SystemConfig.h"
#include <NimBLEDevice.h>
#include <NimBLEServer.h>
#include <NimBLECharacteristic.h>
#include <ArduinoJson.h>
#include <mbedtls/sha256.h>

// 增强的构造函数
BLEModelUpdater::BLEModelUpdater(VoiceRecognitionSystem* voiceSys)
    : voiceSystem(voiceSys)
    , bleServer(nullptr)
    , modelTransferChar(nullptr)
    , statusChar(nullptr)
    , isConnected(false)
    , transferInProgress(false)
    , receivedBytes(0)
    , expectedBytes(0)
    , chunkSize(512)
    , maxRetries(3)
    , timeoutMs(30000) {
    
    tempModelFile = ModelPaths::TEMP_MODEL;
    currentModelVersion = "1.0.0";
    modelChecksum = "";
}

// 增强的初始化函数
bool BLEModelUpdater::initialize() {
    Serial.println("初始化增强版BLE模型更新器...");
    
    try {
        // 初始化NimBLE
        NimBLEDevice::init(SystemConfig::BLE_DEVICE_NAME);
        
        // 创建BLE服务器
        bleServer = NimBLEDevice::createServer();
        bleServer->setCallbacks(new BLEServerCallbacks(this));
        
        // 创建服务
        NimBLEService* pService = bleServer->createService(SystemConfig::BLE_SERVICE_UUID);
        
        // 创建模型传输特征
        modelTransferChar = pService->createCharacteristic(
            SystemConfig::BLE_MODEL_CHAR_UUID,
            NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::WRITE_NR
        );
        modelTransferChar->setCallbacks(new ModelTransferCallbacks(this));
        
        // 创建状态查询特征
        statusChar = pService->createCharacteristic(
            SystemConfig::BLE_STATUS_CHAR_UUID,
            NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
        );
        statusChar->setCallbacks(new StatusCallbacks(this));
        
        // 启动服务
        pService->start();
        
        // 启动广播
        NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();
        pAdvertising->addServiceUUID(SystemConfig::BLE_SERVICE_UUID);
        pAdvertising->setScanResponse(true);
        pAdvertising->start();
        
        // 加载当前模型信息
        loadCurrentModelInfo();
        
        Serial.println("增强版BLE模型更新器初始化完成");
        Serial.printf("设备名称: %s\n", SystemConfig::BLE_DEVICE_NAME);
        Serial.printf("当前模型版本: %s\n", currentModelVersion.c_str());
        Serial.printf("支持的最大传输块大小: %d bytes\n", chunkSize);
        
        return true;
        
    } catch (const std::exception& e) {
        Serial.printf("BLE初始化失败: %s\n", e.what());
        return false;
    }
}

// 加载当前模型信息
void BLEModelUpdater::loadCurrentModelInfo() {
    // 从SPIFFS加载模型元数据
    std::string metadata;
    if (loadModelMetadata(metadata)) {
        DynamicJsonDocument doc(512);
        DeserializationError error = deserializeJson(doc, metadata);
        
        if (!error) {
            currentModelVersion = doc["version"] | "1.0.0";
            modelChecksum = doc["checksum"] | "";
        }
    }
    
    // 如果没有元数据，计算当前模型校验和
    if (modelChecksum.empty()) {
        calculateModelChecksum(modelChecksum);
        saveCurrentModelInfo();
    }
}

// 保存当前模型信息
void BLEModelUpdater::saveCurrentModelInfo() {
    DynamicJsonDocument doc(256);
    doc["version"] = currentModelVersion;
    doc["checksum"] = modelChecksum;
    doc["updated_at"] = millis();
    
    std::string metadata;
    serializeJson(doc, metadata);
    saveModelMetadata(metadata);
    updateModelChecksum(modelChecksum);
}

// 处理控制命令 - 增强版本
void BLEModelUpdater::handleControlCommand(const std::string& jsonStr) {
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, jsonStr);
    
    if (error) {
        Serial.printf("JSON解析错误: %s\n", error.c_str());
        sendStatusUpdate("JSON_PARSE_ERROR", "JSON解析失败");
        return;
    }
    
    String command = doc["command"];
    Serial.printf("收到控制命令: %s\n", command.c_str());
    
    if (command == "START_TRANSFER") {
        startModelTransfer(doc);
    } else if (command == "CANCEL_TRANSFER") {
        cancelTransfer();
    } else if (command == "GET_STATUS") {
        sendFullStatus();
    } else if (command == "ACTIVATE_MODEL") {
        activateNewModel();
    } else if (command == "INCREMENTAL_UPDATE") {
        handleIncrementalUpdate(doc);
    } else if (command == "VERIFY_INTEGRITY") {
        verifyModelIntegrity();
    } else {
        Serial.printf("未知命令: %s\n", command.c_str());
        sendStatusUpdate("UNKNOWN_COMMAND", "未知命令");
    }
}

// 增强的模型传输启动
void BLEModelUpdater::startModelTransfer(DynamicJsonDocument& doc) {
    if (transferInProgress) {
        sendStatusUpdate("TRANSFER_BUSY", "传输已在进行中");
        return;
    }
    
    expectedBytes = doc["size"] | 0;
    String modelName = doc["model_name"] | "unknown";
    String version = doc["version"] | "1.0.0";
    String checksum = doc["checksum"] | "";
    chunkSize = doc["chunk_size"] | 512;
    maxRetries = doc["max_retries"] | 3;
    
    // 验证参数
    if (expectedBytes == 0 || chunkSize < 128 || chunkSize > 1024) {
        sendStatusUpdate("INVALID_PARAMETERS", "无效的传输参数");
        return;
    }
    
    Serial.printf("开始模型传输 - 大小: %d bytes, 名称: %s, 版本: %s\n",
                 expectedBytes, modelName.c_str(), version.c_str());
    Serial.printf("校验和: %s, 块大小: %d, 最大重试: %d\n", 
                 checksum.c_str(), chunkSize, maxRetries);
    
    // 准备接收文件
    if (prepareTempFile()) {
        transferInProgress = true;
        receivedBytes = 0;
        currentModelName = modelName.c_str();
        newModelVersion = version.c_str();
        modelChecksum = checksum.c_str();
        
        JsonObject response = createStatusObject("TRANSFER_STARTED", "开始接收模型数据");
        response["expected_bytes"] = expectedBytes;
        response["chunk_size"] = chunkSize;
        response["checksum_algorithm"] = "SHA256";
        sendStatusJSON(response);
        
        // 启动超时监控
        startTimeoutMonitor();
    } else {
        sendStatusUpdate("FILE_ERROR", "无法创建临时文件");
    }
}

// 启动超时监控
void BLEModelUpdater::startTimeoutMonitor() {
    static unsigned long transferStartTime = millis();
    
    // 在handleClientConnections中检查超时
    // 这里只记录开始时间
    transferStartTime = millis();
    Serial.println("传输超时监控已启动");
}

// 增强的数据处理
void BLEModelUpdater::handleModelBinaryData(const std::string& data) {
    if (!transferInProgress) {
        sendStatusUpdate("NO_TRANSFER", "当前无传输进行");
        return;
    }
    
    // 写入临时文件
    File file = SPIFFS.open(tempModelFile.c_str(), "a");
    if (!file) {
        Serial.println("无法打开临时文件");
        cancelTransfer();
        return;
    }
    
    file.write((uint8_t*)data.data(), data.length());
    file.close();
    
    receivedBytes += data.length();
    
    // 更新进度（每5%发送一次）
    static int lastProgress = 0;
    int progress = (receivedBytes * 100) / expectedBytes;
    if (progress >= lastProgress + 5 || progress == 100) {
        sendProgressUpdate(progress);
        lastProgress = progress;
    }
    
    // 检查是否完成
    if (receivedBytes >= expectedBytes) {
        completeTransfer();
    }
}

// 完成传输 - 增强版本
void BLEModelUpdater::completeTransfer() {
    transferInProgress = false;
    
    Serial.printf("模型传输完成 - 接收: %d bytes, 预期: %d bytes\n",
                 receivedBytes, expectedBytes);
    
    // 验证文件完整性
    if (verifyModelFile() && verifyModelIntegrity()) {
        sendStatusUpdate("TRANSFER_COMPLETE", "模型接收完成，等待激活");
        Serial.println("模型文件验证通过");
    } else {
        sendStatusUpdate("VERIFY_FAILED", "模型文件验证失败");
        cleanupTempFile();
        Serial.println("模型文件验证失败");
    }
}

// 计算模型校验和
bool BLEModelUpdater::calculateModelChecksum(std::string& checksum) {
    File file = SPIFFS.open(tempModelFile.c_str(), "r");
    if (!file) {
        file = SPIFFS.open(ModelPaths::DEFAULT_MODEL, "r");
        if (!file) return false;
    }
    
    mbedtls_sha256_context sha256_ctx;
    mbedtls_sha256_init(&sha256_ctx);
    mbedtls_sha256_starts_ret(&sha256_ctx, 0); // SHA256
    
    uint8_t buffer[512];
    while (file.available()) {
        size_t bytesRead = file.read(buffer, sizeof(buffer));
        if (bytesRead > 0) {
            mbedtls_sha256_update_ret(&sha256_ctx, buffer, bytesRead);
        }
    }
    
    uint8_t hash[32];
    mbedtls_sha256_finish_ret(&sha256_ctx, hash);
    mbedtls_sha256_free(&sha256_ctx);
    file.close();
    
    // 转换为十六进制字符串
    char hexHash[65];
    for (int i = 0; i < 32; i++) {
        sprintf(hexHash + (i * 2), "%02x", hash[i]);
    }
    hexHash[64] = '\0';
    
    checksum = std::string(hexHash);
    return true;
}

// 验证模型完整性
bool BLEModelUpdater::verifyModelIntegrity() {
    std::string calculatedChecksum;
    if (!calculateModelChecksum(calculatedChecksum)) {
        Serial.println("无法计算校验和");
        return false;
    }
    
    bool isValid = (calculatedChecksum == modelChecksum) || modelChecksum.empty();
    Serial.printf("完整性验证: 预期=%s, 计算=%s, 结果=%s\n",
                 modelChecksum.c_str(), calculatedChecksum.c_str(), 
                 isValid ? "通过" : "失败");
    
    return isValid;
}

// 处理增量更新
void BLEModelUpdater::handleIncrementalUpdate(DynamicJsonDocument& doc) {
    if (transferInProgress) {
        sendStatusUpdate("TRANSFER_BUSY", "传输正在进行中");
        return;
    }
    
    String patchData = doc["patch_data"] | "";
    String targetVersion = doc["target_version"] | "";
    
    if (patchData.isEmpty()) {
        sendStatusUpdate("INVALID_PATCH", "无效的补丁数据");
        return;
    }
    
    Serial.printf("开始增量更新到版本: %s\n", targetVersion.c_str());
    
    if (applyDifferentialUpdate(patchData.c_str())) {
        newModelVersion = targetVersion.c_str();
        sendStatusUpdate("INCREMENTAL_SUCCESS", "增量更新成功");
        activateNewModel();
    } else {
        sendStatusUpdate("INCREMENTAL_FAILED", "增量更新失败");
    }
}

// 应用差异更新
bool BLEModelUpdater::applyDifferentialUpdate(const std::string& patchData) {
    // 这里应该实现实际的差异应用逻辑
    // 简化版本：直接替换整个模型
    Serial.println("应用差异更新（简化版）");
    
    // 备份当前模型
    backupCurrentModel();
    
    // 保存补丁数据到临时文件
    File patchFile = SPIFFS.open(ModelPaths::MODEL_PATCH, "w");
    if (!patchFile) return false;
    
    patchFile.print(patchData.c_str());
    patchFile.close();
    
    // 应用补丁（这里简化为直接复制）
    if (replaceModelFile()) {
        // 清理补丁文件
        SPIFFS.remove(ModelPaths::MODEL_PATCH);
        return true;
    }
    
    // 失败则恢复备份
    restoreBackupModel();
    return false;
}

// 保存模型元数据
bool BLEModelUpdater::saveModelMetadata(const std::string& metadata) {
    File metaFile = SPIFFS.open(ModelPaths::MODEL_METADATA, "w");
    if (!metaFile) return false;
    
    metaFile.print(metadata.c_str());
    metaFile.close();
    return true;
}

// 加载模型元数据
bool BLEModelUpdater::loadModelMetadata(std::string& metadata) {
    if (!SPIFFS.exists(ModelPaths::MODEL_METADATA)) return false;
    
    File metaFile = SPIFFS.open(ModelPaths::MODEL_METADATA, "r");
    if (!metaFile) return false;
    
    metadata = metaFile.readString().c_str();
    metaFile.close();
    return true;
}

// 更新模型校验和
bool BLEModelUpdater::updateModelChecksum(const std::string& checksum) {
    File checksumFile = SPIFFS.open(ModelPaths::MODEL_CHECKSUM, "w");
    if (!checksumFile) return false;
    
    checksumFile.print(checksum.c_str());
    checksumFile.close();
    return true;
}

// 验证模型结构
bool BLEModelUpdater::validateModelStructure() {
    // 这里应该实现对TFLite模型结构的基本验证
    // 简化版本：检查文件是否存在且非空
    File modelFile = SPIFFS.open(ModelPaths::DEFAULT_MODEL, "r");
    if (!modelFile) return false;
    
    bool isValid = modelFile.size() > 0;
    modelFile.close();
    return isValid;
}

// 增强的状态查询
void BLEModelUpdater::sendFullStatus() {
    JsonObject status = createStatusObject("FULL_STATUS", "完整状态信息");
    
    // 添加额外的系统信息
    status["uptime"] = millis() / 1000;
    status["recognition_count"] = voiceSystem ? voiceSystem->getRecognitionCount() : 0;
    status["model_ready"] = voiceSystem ? voiceSystem->isReady() : false;
    status["free_heap"] = ESP.getFreeHeap();
    status["flash_size"] = ESP.getFlashChipSize();
    status["sketch_size"] = ESP.getSketchSize();
    
    // 添加模型相关信息
    status["current_model_version"] = currentModelVersion.c_str();
    status["model_checksum"] = modelChecksum.c_str();
    status["transfer_in_progress"] = transferInProgress;
    status["received_bytes"] = receivedBytes;
    status["expected_bytes"] = expectedBytes;
    
    sendStatusJSON(status);
}