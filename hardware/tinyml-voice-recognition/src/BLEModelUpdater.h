/*
 * BLE模型更新器头文件
 * 声明BLE通信和模型更新接口
 */

#ifndef BLE_MODEL_UPDATER_H
#define BLE_MODEL_UPDATER_H

#include <Arduino.h>
#include <string>
#include <ArduinoJson.h>
#include "VoiceRecognitionSystem.h"

// 前向声明
class NimBLEServer;
class NimBLECharacteristic;

class BLEModelUpdater {
private:
    VoiceRecognitionSystem* voiceSystem;
    
    // BLE相关
    NimBLEServer* bleServer;
    NimBLECharacteristic* modelTransferChar;
    NimBLECharacteristic* statusChar;
    bool isConnected;
    
    // 传输状态
    bool transferInProgress;
    size_t receivedBytes;
    size_t expectedBytes;
    std::string tempModelFile;
    
    // 模型信息
    std::string currentModelName;
    std::string currentModelVersion;
    std::string newModelVersion;
    std::string modelChecksum;
    
    // 传输配置
    size_t chunkSize;
    size_t maxRetries;
    unsigned long timeoutMs;
    
    // 私有方法
    void handleControlCommand(const std::string& jsonStr);
    void handleModelBinaryData(const std::string& data);
    void startModelTransfer(DynamicJsonDocument& doc);
    void completeTransfer();
    void cancelTransfer();
    void activateNewModel();
    
    // 增强功能
    bool calculateModelChecksum(std::string& checksum);
    bool verifyModelIntegrity();
    void handleIncrementalUpdate(DynamicJsonDocument& doc);
    bool applyDifferentialUpdate(const std::string& patchData);
    
    // 文件操作
    bool prepareTempFile();
    bool verifyModelFile();
    bool replaceModelFile();
    void backupCurrentModel();
    void restoreBackupModel();
    void cleanupTempFile();
    
    // 增强文件操作
    bool saveModelMetadata(const std::string& metadata);
    bool loadModelMetadata(std::string& metadata);
    bool updateModelChecksum(const std::string& checksum);
    bool validateModelStructure();
    
    // 状态管理
    JsonObject createStatusObject(const char* status, const char* message);
    void sendStatusJSON(JsonObject& status);
    std::string serializeStatus(JsonObject& status);
    void sendStatusUpdate(const char* status, const char* message);
    void sendProgressUpdate(int progress);
    void sendFullStatus();

public:
    BLEModelUpdater(VoiceRecognitionSystem* voiceSys);
    
    // 初始化
    bool initialize();
    
    // 主要接口
    void handleClientConnections();
    void handleModelData(const std::string& data);
    
    // 状态查询
    bool isConnected() const { return isConnected; }
    bool isTransferInProgress() const { return transferInProgress; }
    std::string getStatusJSON();
    void setConnectionStatus(bool connected);
    
    // 模型信息
    std::string getCurrentModelVersion() const { return currentModelVersion; }
    size_t getReceivedBytes() const { return receivedBytes; }
    size_t getExpectedBytes() const { return expectedBytes; }
};

#endif // BLE_MODEL_UPDATER_H