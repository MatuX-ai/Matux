/*
 * BLE模型更新器
 * 实现通过蓝牙低功耗进行模型热更新的功能
 */

#include "BLEModelUpdater.h"
#include "SystemConfig.h"
#include <NimBLEDevice.h>
#include <NimBLEServer.h>
#include <NimBLECharacteristic.h>
#include <ArduinoJson.h>

// BLE回调处理器
class BLEServerCallbacks : public NimBLEServerCallbacks {
private:
    BLEModelUpdater* updater;
    
public:
    BLEServerCallbacks(BLEModelUpdater* bleUpdater) : updater(bleUpdater) {}
    
    void onConnect(NimBLEServer* pServer, ble_gap_conn_desc* desc) override {
        Serial.println("BLE客户端已连接");
        if (updater) updater->setConnectionStatus(true);
    }
    
    void onDisconnect(NimBLEServer* pServer) override {
        Serial.println("BLE客户端已断开");
        if (updater) updater->setConnectionStatus(false);
        // 重新开始广播
        pServer->startAdvertising();
    }
};

class ModelTransferCallbacks : public NimBLECharacteristicCallbacks {
private:
    BLEModelUpdater* updater;
    
public:
    ModelTransferCallbacks(BLEModelUpdater* bleUpdater) : updater(bleUpdater) {}
    
    void onWrite(NimBLECharacteristic* pCharacteristic) override {
        std::string value = pCharacteristic->getValue();
        if (updater) {
            updater->handleModelData(value);
        }
    }
};

class StatusCallbacks : public NimBLECharacteristicCallbacks {
private:
    BLEModelUpdater* updater;
    
public:
    StatusCallbacks(BLEModelUpdater* bleUpdater) : updater(bleUpdater) {}
    
    void onRead(NimBLECharacteristic* pCharacteristic) override {
        if (updater) {
            std::string status = updater->getStatusJSON();
            pCharacteristic->setValue(status);
        }
    }
};

BLEModelUpdater::BLEModelUpdater(VoiceRecognitionSystem* voiceSys)
    : voiceSystem(voiceSys)
    , bleServer(nullptr)
    , modelTransferChar(nullptr)
    , statusChar(nullptr)
    , isConnected(false)
    , transferInProgress(false)
    , receivedBytes(0)
    , expectedBytes(0) {
    
    tempModelFile = ModelPaths::TEMP_MODEL;
    currentModelVersion = "1.0.0";
}

bool BLEModelUpdater::initialize() {
    Serial.println("初始化BLE模型更新器...");
    
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
            NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY
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
        
        Serial.println("BLE模型更新器初始化完成");
        Serial.printf("设备名称: %s\n", SystemConfig::BLE_DEVICE_NAME);
        Serial.printf("服务UUID: %s\n", SystemConfig::BLE_SERVICE_UUID);
        
        return true;
        
    } catch (const std::exception& e) {
        Serial.printf("BLE初始化失败: %s\n", e.what());
        return false;
    }
}

void BLEModelUpdater::handleClientConnections() {
    // NimBLE会自动处理连接事件
    // 这里主要用于处理传输状态更新
    if (transferInProgress) {
        // 检查传输超时
        static unsigned long lastActivity = millis();
        if (millis() - lastActivity > 30000) { // 30秒超时
            Serial.println("模型传输超时");
            cancelTransfer();
        }
    }
}

void BLEModelUpdater::handleModelData(const std::string& data) {
    if (data.empty()) return;
    
    // 检查是否是控制命令
    if (data[0] == '{') {
        // JSON控制命令
        handleControlCommand(data);
    } else {
        // 模型数据
        handleModelBinaryData(data);
    }
}

void BLEModelUpdater::handleControlCommand(const std::string& jsonStr) {
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, jsonStr);
    
    if (error) {
        Serial.printf("JSON解析错误: %s\n", error.c_str());
        sendStatusUpdate("JSON_PARSE_ERROR", "JSON解析失败");
        return;
    }
    
    String command = doc["command"];
    
    if (command == "START_TRANSFER") {
        startModelTransfer(doc);
    } else if (command == "CANCEL_TRANSFER") {
        cancelTransfer();
    } else if (command == "GET_STATUS") {
        sendFullStatus();
    } else if (command == "ACTIVATE_MODEL") {
        activateNewModel();
    } else {
        Serial.printf("未知命令: %s\n", command.c_str());
        sendStatusUpdate("UNKNOWN_COMMAND", "未知命令");
    }
}

void BLEModelUpdater::startModelTransfer(DynamicJsonDocument& doc) {
    if (transferInProgress) {
        sendStatusUpdate("TRANSFER_BUSY", "传输已在进行中");
        return;
    }
    
    expectedBytes = doc["size"] | 0;
    String modelName = doc["model_name"] | "unknown";
    String version = doc["version"] | "1.0.0";
    
    Serial.printf("开始模型传输 - 大小: %d bytes, 名称: %s, 版本: %s\n",
                 expectedBytes, modelName.c_str(), version.c_str());
    
    // 准备接收文件
    if (prepareTempFile()) {
        transferInProgress = true;
        receivedBytes = 0;
        currentModelName = modelName.c_str();
        newModelVersion = version.c_str();
        
        JsonObject response = createStatusObject("TRANSFER_STARTED", "开始接收模型数据");
        response["expected_bytes"] = expectedBytes;
        sendStatusJSON(response);
    } else {
        sendStatusUpdate("FILE_ERROR", "无法创建临时文件");
    }
}

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
    
    // 更新进度
    int progress = (receivedBytes * 100) / expectedBytes;
    sendProgressUpdate(progress);
    
    // 检查是否完成
    if (receivedBytes >= expectedBytes) {
        completeTransfer();
    }
}

void BLEModelUpdater::completeTransfer() {
    transferInProgress = false;
    
    Serial.printf("模型传输完成 - 接收: %d bytes, 预期: %d bytes\n",
                 receivedBytes, expectedBytes);
    
    // 验证文件完整性
    if (verifyModelFile()) {
        sendStatusUpdate("TRANSFER_COMPLETE", "模型接收完成，等待激活");
    } else {
        sendStatusUpdate("VERIFY_FAILED", "模型文件验证失败");
        cleanupTempFile();
    }
}

void BLEModelUpdater::cancelTransfer() {
    transferInProgress = false;
    receivedBytes = 0;
    expectedBytes = 0;
    
    cleanupTempFile();
    sendStatusUpdate("TRANSFER_CANCELLED", "传输已取消");
    Serial.println("模型传输已取消");
}

void BLEModelUpdater::activateNewModel() {
    if (transferInProgress) {
        sendStatusUpdate("TRANSFER_BUSY", "传输正在进行中");
        return;
    }
    
    if (!SPIFFS.exists(tempModelFile.c_str())) {
        sendStatusUpdate("NO_MODEL", "无待激活的模型文件");
        return;
    }
    
    Serial.println("激活新模型...");
    sendStatusUpdate("ACTIVATING", "正在激活新模型");
    
    // 备份当前模型
    backupCurrentModel();
    
    // 替换模型文件
    if (replaceModelFile()) {
        currentModelVersion = newModelVersion;
        sendStatusUpdate("ACTIVATION_SUCCESS", "模型激活成功");
        Serial.println("模型激活完成");
        
        // 清理临时文件
        cleanupTempFile();
        
        // 重启语音识别系统以加载新模型
        if (voiceSystem) {
            voiceSystem->cleanup();
            voiceSystem->initialize();
        }
    } else {
        sendStatusUpdate("ACTIVATION_FAILED", "模型激活失败");
        restoreBackupModel();
    }
}

bool BLEModelUpdater::prepareTempFile() {
    // 初始化SPIFFS
    if (!SPIFFS.begin(true)) {
        Serial.println("SPIFFS初始化失败");
        return false;
    }
    
    // 删除旧的临时文件
    if (SPIFFS.exists(tempModelFile.c_str())) {
        SPIFFS.remove(tempModelFile.c_str());
    }
    
    // 创建新文件
    File file = SPIFFS.open(tempModelFile.c_str(), "w");
    if (!file) {
        Serial.println("无法创建临时文件");
        return false;
    }
    file.close();
    
    return true;
}

bool BLEModelUpdater::verifyModelFile() {
    File file = SPIFFS.open(tempModelFile.c_str(), "r");
    if (!file) return false;
    
    size_t fileSize = file.size();
    file.close();
    
    bool isValid = (fileSize == expectedBytes) && (fileSize > 0);
    Serial.printf("模型文件验证: 大小=%d, 预期=%d, 有效=%s\n",
                 fileSize, expectedBytes, isValid ? "是" : "否");
    
    return isValid;
}

bool BLEModelUpdater::replaceModelFile() {
    String defaultModelPath = ModelPaths::DEFAULT_MODEL;
    
    // 删除旧模型
    if (SPIFFS.exists(defaultModelPath.c_str())) {
        SPIFFS.remove(defaultModelPath.c_str());
    }
    
    // 重命名临时文件
    return SPIFFS.rename(tempModelFile.c_str(), defaultModelPath.c_str());
}

void BLEModelUpdater::backupCurrentModel() {
    String defaultModelPath = ModelPaths::DEFAULT_MODEL;
    String backupPath = ModelPaths::BACKUP_MODEL;
    
    if (SPIFFS.exists(defaultModelPath.c_str())) {
        SPIFFS.rename(defaultModelPath.c_str(), backupPath.c_str());
    }
}

void BLEModelUpdater::restoreBackupModel() {
    String defaultModelPath = ModelPaths::DEFAULT_MODEL;
    String backupPath = ModelPaths::BACKUP_MODEL;
    
    if (SPIFFS.exists(backupPath.c_str())) {
        SPIFFS.remove(defaultModelPath.c_str());
        SPIFFS.rename(backupPath.c_str(), defaultModelPath.c_str());
    }
}

void BLEModelUpdater::cleanupTempFile() {
    if (SPIFFS.exists(tempModelFile.c_str())) {
        SPIFFS.remove(tempModelFile.c_str());
    }
}

std::string BLEModelUpdater::getStatusJSON() {
    JsonObject status = createStatusObject("STATUS_UPDATE", "系统状态");
    return serializeStatus(status);
}

JsonObject BLEModelUpdater::createStatusObject(const char* status, const char* message) {
    DynamicJsonDocument doc(512);
    JsonObject root = doc.to<JsonObject>();
    
    root["status"] = status;
    root["message"] = message;
    root["timestamp"] = millis();
    root["connected"] = isConnected;
    root["transfer_in_progress"] = transferInProgress;
    root["received_bytes"] = receivedBytes;
    root["expected_bytes"] = expectedBytes;
    root["current_model_version"] = currentModelVersion.c_str();
    root["free_heap"] = ESP.getFreeHeap();
    
    return root;
}

void BLEModelUpdater::sendStatusJSON(JsonObject& status) {
    std::string jsonStr = serializeStatus(status);
    if (statusChar) {
        statusChar->setValue(jsonStr);
        statusChar->notify();
    }
}

std::string BLEModelUpdater::serializeStatus(JsonObject& status) {
    std::string jsonStr;
    serializeJson(status, jsonStr);
    return jsonStr;
}

void BLEModelUpdater::sendStatusUpdate(const char* status, const char* message) {
    JsonObject statusObj = createStatusObject(status, message);
    sendStatusJSON(statusObj);
}

void BLEModelUpdater::sendProgressUpdate(int progress) {
    JsonObject status = createStatusObject("TRANSFER_PROGRESS", "传输进度");
    status["progress"] = progress;
    sendStatusJSON(status);
}

void BLEModelUpdater::sendFullStatus() {
    JsonObject status = createStatusObject("FULL_STATUS", "完整状态信息");
    
    // 添加额外的系统信息
    status["uptime"] = millis() / 1000;
    status["recognition_count"] = voiceSystem ? voiceSystem->getRecognitionCount() : 0;
    status["model_ready"] = voiceSystem ? voiceSystem->isReady() : false;
    
    sendStatusJSON(status);
}

void BLEModelUpdater::setConnectionStatus(bool connected) {
    isConnected = connected;
    sendStatusUpdate(connected ? "CONNECTED" : "DISCONNECTED", 
                    connected ? "客户端已连接" : "客户端已断开");
}