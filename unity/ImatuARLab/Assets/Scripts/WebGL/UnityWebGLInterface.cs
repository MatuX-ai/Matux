using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Unity WebGL与JavaScript通信接口
/// 实现Unity与Angular前端的数据交换
/// </summary>
public class UnityWebGLInterface : MonoBehaviour
{
    [Header("通信配置")]
    [SerializeField] private bool enableWebGLMessaging = true;
    [SerializeField] private float dataUpdateInterval = 0.1f; // 100ms更新间隔
    
    // 私有字段
    private ARInteractionManager arManager;
    private HardwarePlacement hardwarePlacement;
    private WiringGuide wiringGuide;
    private float lastDataUpdateTime = 0f;
    
    // 数据缓存
    private Dictionary<string, object> cachedData = new Dictionary<string, object>();
    
    void Awake()
    {
        InitializeComponents();
    }
    
    void Start()
    {
        if (enableWebGLMessaging)
        {
            StartDataTransmission();
        }
    }
    
    /// <summary>
    /// 初始化组件引用
    /// </summary>
    private void InitializeComponents()
    {
        arManager = FindObjectOfType<ARInteractionManager>();
        hardwarePlacement = FindObjectOfType<HardwarePlacement>();
        wiringGuide = FindObjectOfType<WiringGuide>();
        
        // 注册事件监听
        if (arManager != null)
        {
            arManager.OnARInteraction += HandleARInteraction;
        }
    }
    
    /// <summary>
    /// 开始数据传输
    /// </summary>
    private void StartDataTransmission()
    {
        StartCoroutine(DataTransmissionCoroutine());
    }
    
    /// <summary>
    /// 数据传输协程
    /// </summary>
    private IEnumerator DataTransmissionCoroutine()
    {
        while (enableWebGLMessaging)
        {
            if (Time.time - lastDataUpdateTime >= dataUpdateInterval)
            {
                TransmitSensorData();
                lastDataUpdateTime = Time.time;
            }
            yield return null;
        }
    }
    
    /// <summary>
    /// 传输传感器数据到前端
    /// </summary>
    private void TransmitSensorData()
    {
        // 收集所有传感器数据
        Dictionary<string, object> sensorData = CollectSensorData();
        
        // 发送到JavaScript
        SendToJavaScript("sensorDataUpdate", JsonUtility.ToJson(sensorData));
    }
    
    /// <summary>
    /// 收集传感器数据
    /// </summary>
    private Dictionary<string, object> CollectSensorData()
    {
        Dictionary<string, object> data = new Dictionary<string, object>();
        
        // 收集DHT22传感器数据
        DHT22Sensor[] dhtSensors = FindObjectsOfType<DHT22Sensor>();
        List<object> dhtData = new List<object>();
        foreach (var sensor in dhtSensors)
        {
            dhtData.Add(new
            {
                name = sensor.name,
                temperature = sensor.GetTemperature(),
                humidity = sensor.GetHumidity(),
                isActive = sensor.isActive,
                isConnected = sensor.isConnected
            });
        }
        data["dht22"] = dhtData;
        
        // 收集光敏电阻数据
        LightSensor[] lightSensors = FindObjectsOfType<LightSensor>();
        List<object> lightData = new List<object>();
        foreach (var sensor in lightSensors)
        {
            lightData.Add(new
            {
                name = sensor.name,
                lightLevel = sensor.GetSensorData().Value,
                isActive = sensor.isActive,
                isConnected = sensor.isConnected
            });
        }
        data["lightSensors"] = lightData;
        
        // 收集超声波传感器数据
        UltrasonicSensor[] ultrasonicSensors = FindObjectsOfType<UltrasonicSensor>();
        List<object> ultrasonicData = new List<object>();
        foreach (var sensor in ultrasonicSensors)
        {
            ultrasonicData.Add(new
            {
                name = sensor.name,
                distance = sensor.GetDistance(),
                isActive = sensor.isActive,
                isConnected = sensor.isConnected
            });
        }
        data["ultrasonicSensors"] = ultrasonicData;
        
        // 添加AR状态信息
        if (arManager != null)
        {
            var arStatus = arManager.GetARStatus();
            data["arStatus"] = new
            {
                isTracking = arStatus.IsTracking,
                planeDetectionEnabled = arStatus.PlaneDetectionEnabled,
                detectedPlanes = arStatus.DetectedPlanes,
                placedObjects = arStatus.PlacedObjects
            };
        }
        
        // 添加接线统计信息
        if (wiringGuide != null)
        {
            var wiringStats = wiringGuide.GetStatistics();
            data["wiringStats"] = new
            {
                totalConnections = wiringStats.TotalConnections,
                validConnections = wiringStats.ValidConnections,
                invalidConnections = wiringStats.InvalidConnections,
                successRate = wiringStats.SuccessRate
            };
        }
        
        return data;
    }
    
    /// <summary>
    /// 处理AR交互事件
    /// </summary>
    private void HandleARInteraction(ARInteractionManager.ARInteractionType type, object data)
    {
        switch (type)
        {
            case ARInteractionManager.ARInteractionType.ObjectPlaced:
                SendToJavaScript("objectPlaced", data?.ToString() ?? "Unknown");
                break;
            case ARInteractionManager.ARInteractionType.GestureRecognized:
                SendToJavaScript("gestureRecognized", data?.ToString() ?? "Unknown");
                break;
            case ARInteractionManager.ARInteractionType.PlaneDetected:
                SendToJavaScript("planeDetected", "New plane detected");
                break;
        }
    }
    
    /// <summary>
    /// 发送消息到JavaScript
    /// </summary>
    private void SendToJavaScript(string messageType, string messageData)
    {
        #if UNITY_WEBGL && !UNITY_EDITOR
        Application.ExternalCall("unityMessageHandler", messageType, messageData);
        #else
        // 编辑器模式下输出到控制台
        Debug.Log($"[WebGL Interface] {messageType}: {messageData}");
        #endif
    }
    
    /// <summary>
    /// 从JavaScript接收消息
    /// </summary>
    public void ReceiveMessage(string messageType, string messageData)
    {
        Debug.Log($"[WebGL Interface] Received: {messageType} - {messageData}");
        
        switch (messageType.ToLower())
        {
            case "placehardware":
                PlaceHardwareFromWeb(messageData);
                break;
            case "selecthardwaretype":
                SelectHardwareType(messageData);
                break;
            case "resetscene":
                ResetScene();
                break;
            case "toggleplanedetection":
                TogglePlaneDetection();
                break;
            case "startconnection":
                StartConnectionFromWeb(messageData);
                break;
            case "completeconnection":
                CompleteConnectionFromWeb(messageData);
                break;
            default:
                Debug.LogWarning($"未知的消息类型: {messageType}");
                break;
        }
    }
    
    /// <summary>
    /// 从Web端放置硬件
    /// </summary>
    private void PlaceHardwareFromWeb(string data)
    {
        try
        {
            // 解析位置数据
            var positionData = JsonUtility.FromJson<PositionData>(data);
            Vector3 position = new Vector3(positionData.x, positionData.y, positionData.z);
            
            // 在指定位置放置硬件
            if (hardwarePlacement != null)
            {
                GameObject placedObject = hardwarePlacement.PlaceHardware(position, Quaternion.identity);
                if (placedObject != null)
                {
                    SendToJavaScript("hardwarePlaced", placedObject.name);
                }
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"放置硬件失败: {e.Message}");
            SendToJavaScript("error", $"Failed to place hardware: {e.Message}");
        }
    }
    
    /// <summary>
    /// 从Web端选择硬件类型
    /// </summary>
    private void SelectHardwareType(string type)
    {
        if (hardwarePlacement != null)
        {
            HardwarePlacement.HardwareType hardwareType;
            if (System.Enum.TryParse(type, true, out hardwareType))
            {
                hardwarePlacement.SetCurrentHardwareType(hardwareType);
                SendToJavaScript("hardwareTypeSelected", type);
            }
            else
            {
                Debug.LogWarning($"无效的硬件类型: {type}");
            }
        }
    }
    
    /// <summary>
    /// 重置场景
    /// </summary>
    private void ResetScene()
    {
        if (arManager != null)
        {
            arManager.ResetScene();
        }
        
        if (hardwarePlacement != null)
        {
            hardwarePlacement.ClearAllHardware();
        }
        
        if (wiringGuide != null)
        {
            wiringGuide.ClearAllConnections();
        }
        
        SendToJavaScript("sceneReset", "Scene has been reset");
    }
    
    /// <summary>
    /// 切换平面检测
    /// </summary>
    private void TogglePlaneDetection()
    {
        if (arManager != null)
        {
            arManager.TogglePlaneDetection();
            SendToJavaScript("planeDetectionToggled", "Plane detection toggled");
        }
    }
    
    /// <summary>
    /// 从Web端开始连接
    /// </summary>
    private void StartConnectionFromWeb(string data)
    {
        // 这里应该实现具体的连接逻辑
        SendToJavaScript("connectionStarted", "Connection process initiated");
    }
    
    /// <summary>
    /// 从Web端完成连接
    /// </summary>
    private void CompleteConnectionFromWeb(string data)
    {
        // 这里应该实现具体的连接完成逻辑
        SendToJavaScript("connectionCompleted", "Connection completed");
    }
    
    /// <summary>
    /// 请求当前场景状态
    /// </summary>
    public void RequestSceneState()
    {
        Dictionary<string, object> sceneState = new Dictionary<string, object>();
        
        // 硬件统计
        if (hardwarePlacement != null)
        {
            var stats = hardwarePlacement.GetStatistics();
            sceneState["hardwareStats"] = new
            {
                totalHardware = stats.TotalHardware,
                esp32Count = stats.ESP32Count,
                sensorCount = stats.SensorCount,
                displayCount = stats.DisplayCount
            };
        }
        
        // AR状态
        if (arManager != null)
        {
            var arStatus = arManager.GetARStatus();
            sceneState["arStatus"] = arStatus;
        }
        
        // 接线统计
        if (wiringGuide != null)
        {
            var wiringStats = wiringGuide.GetStatistics();
            sceneState["wiringStats"] = wiringStats;
        }
        
        SendToJavaScript("sceneState", JsonUtility.ToJson(sceneState));
    }
    
    /// <summary>
    /// 位置数据结构
    /// </summary>
    [System.Serializable]
    private class PositionData
    {
        public float x;
        public float y;
        public float z;
    }
    
    void OnDestroy()
    {
        // 清理事件监听
        if (arManager != null)
        {
            arManager.OnARInteraction -= HandleARInteraction;
        }
    }
}