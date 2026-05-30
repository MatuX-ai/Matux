using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 数据桥接器
/// 实现Unity内部各系统间的数据传递和同步
/// </summary>
public class DataBridge : MonoBehaviour
{
    [Header("数据同步配置")]
    [SerializeField] private float syncInterval = 0.05f; // 50ms同步间隔
    [SerializeField] private bool enableRealTimeSync = true;
    
    // 组件引用
    private UnityWebGLInterface webGLInterface;
    private ARInteractionManager arManager;
    private HardwarePlacement hardwarePlacement;
    private WiringGuide wiringGuide;
    
    // 数据缓存
    private Dictionary<string, object> sharedData = new Dictionary<string, object>();
    private float lastSyncTime = 0f;
    
    void Awake()
    {
        InitializeSystems();
    }
    
    void Start()
    {
        if (enableRealTimeSync)
        {
            StartDataSynchronization();
        }
    }
    
    /// <summary>
    /// 初始化系统组件
    /// </summary>
    private void InitializeSystems()
    {
        webGLInterface = FindObjectOfType<UnityWebGLInterface>();
        arManager = FindObjectOfType<ARInteractionManager>();
        hardwarePlacement = FindObjectOfType<HardwarePlacement>();
        wiringGuide = FindObjectOfType<WiringGuide>();
        
        // 初始化共享数据字典
        InitializeSharedData();
    }
    
    /// <summary>
    /// 初始化共享数据结构
    /// </summary>
    private void InitializeSharedData()
    {
        sharedData["hardwareList"] = new List<object>();
        sharedData["sensorReadings"] = new Dictionary<string, float>();
        sharedData["arState"] = new Dictionary<string, object>();
        sharedData["connectionStatus"] = new Dictionary<string, object>();
    }
    
    /// <summary>
    /// 开始数据同步
    /// </summary>
    private void StartDataSynchronization()
    {
        StartCoroutine(SyncDataCoroutine());
    }
    
    /// <summary>
    /// 数据同步协程
    /// </summary>
    private IEnumerator SyncDataCoroutine()
    {
        while (enableRealTimeSync)
        {
            if (Time.time - lastSyncTime >= syncInterval)
            {
                SynchronizeAllData();
                lastSyncTime = Time.time;
            }
            yield return null;
        }
    }
    
    /// <summary>
    /// 同步所有数据
    /// </summary>
    private void SynchronizeAllData()
    {
        UpdateHardwareList();
        UpdateSensorReadings();
        UpdateARState();
        UpdateConnectionStatus();
        
        // 通知WebGL接口数据更新
        if (webGLInterface != null)
        {
            // 数据已经通过UnityWebGLInterface的定时器自动发送
        }
    }
    
    /// <summary>
    /// 更新硬件列表
    /// </summary>
    private void UpdateHardwareList()
    {
        if (hardwarePlacement == null) return;
        
        List<object> hardwareList = new List<object>();
        var allHardware = hardwarePlacement.GetAllPlacedHardware();
        
        foreach (var hardwareObj in allHardware)
        {
            if (hardwareObj == null) continue;
            
            // 获取硬件类型和状态
            string hardwareType = GetHardwareType(hardwareObj);
            var hardwareInfo = GetHardwareInfo(hardwareObj);
            
            hardwareList.Add(new
            {
                id = hardwareObj.GetInstanceID(),
                name = hardwareObj.name,
                type = hardwareType,
                position = new
                {
                    x = hardwareInfo.Position.x,
                    y = hardwareInfo.Position.y,
                    z = hardwareInfo.Position.z
                },
                rotation = new
                {
                    x = hardwareInfo.Rotation.eulerAngles.x,
                    y = hardwareInfo.Rotation.eulerAngles.y,
                    z = hardwareInfo.Rotation.eulerAngles.z
                },
                isActive = hardwareInfo.IsSelected,
                isConnected = hardwareInfo.IsPlaced
            });
        }
        
        sharedData["hardwareList"] = hardwareList;
    }
    
    /// <summary>
    /// 获取硬件类型
    /// </summary>
    private string GetHardwareType(GameObject hardwareObj)
    {
        if (hardwareObj.GetComponent<ESP32Model>() != null) return "ESP32";
        if (hardwareObj.GetComponent<DHT22Sensor>() != null) return "DHT22";
        if (hardwareObj.GetComponent<LightSensor>() != null) return "LightSensor";
        if (hardwareObj.GetComponent<UltrasonicSensor>() != null) return "Ultrasonic";
        if (hardwareObj.GetComponent<OLedDisplay>() != null) return "OLED";
        return "Unknown";
    }
    
    /// <summary>
    /// 获取硬件信息
    /// </summary>
    private ESP32Model.HardwareInfo GetHardwareInfo(GameObject hardwareObj)
    {
        ESP32Model esp32 = hardwareObj.GetComponent<ESP32Model>();
        if (esp32 != null)
        {
            return esp32.GetHardwareInfo();
        }
        
        // 对于其他类型的硬件，返回默认信息
        return new ESP32Model.HardwareInfo
        {
            ModelName = hardwareObj.name,
            Position = hardwareObj.transform.position,
            Rotation = hardwareObj.transform.rotation,
            IsSelected = false,
            IsPlaced = true
        };
    }
    
    /// <summary>
    /// 更新传感器读数
    /// </summary>
    private void UpdateSensorReadings()
    {
        Dictionary<string, float> readings = new Dictionary<string, float>();
        
        // DHT22传感器读数
        DHT22Sensor[] dhtSensors = FindObjectsOfType<DHT22Sensor>();
        foreach (var sensor in dhtSensors)
        {
            readings[$"{sensor.name}_temperature"] = sensor.GetTemperature();
            readings[$"{sensor.name}_humidity"] = sensor.GetHumidity();
        }
        
        // 光敏电阻读数
        LightSensor[] lightSensors = FindObjectsOfType<LightSensor>();
        foreach (var sensor in lightSensors)
        {
            readings[$"{sensor.name}_light"] = sensor.GetSensorData().Value;
        }
        
        // 超声波传感器读数
        UltrasonicSensor[] ultrasonicSensors = FindObjectsOfType<UltrasonicSensor>();
        foreach (var sensor in ultrasonicSensors)
        {
            readings[$"{sensor.name}_distance"] = sensor.GetDistance();
        }
        
        sharedData["sensorReadings"] = readings;
    }
    
    /// <summary>
    /// 更新AR状态
    /// </summary>
    private void UpdateARState()
    {
        if (arManager == null) return;
        
        var arStatus = arManager.GetARStatus();
        var arState = new Dictionary<string, object>
        {
            ["isTracking"] = arStatus.IsTracking,
            ["planeDetectionEnabled"] = arStatus.PlaneDetectionEnabled,
            ["detectedPlanes"] = arStatus.DetectedPlanes,
            ["placedObjects"] = arStatus.PlacedObjects,
            ["cameraPosition"] = arManager.GetARCamera()?.transform.position,
            ["cameraRotation"] = arManager.GetARCamera()?.transform.rotation.eulerAngles
        };
        
        sharedData["arState"] = arState;
    }
    
    /// <summary>
    /// 更新连接状态
    /// </summary>
    private void UpdateConnectionStatus()
    {
        if (wiringGuide == null) return;
        
        var wiringStats = wiringGuide.GetStatistics();
        var connectionStatus = new Dictionary<string, object>
        {
            ["totalConnections"] = wiringStats.TotalConnections,
            ["validConnections"] = wiringStats.ValidConnections,
            ["invalidConnections"] = wiringStats.InvalidConnections,
            ["successRate"] = wiringStats.SuccessRate
        };
        
        sharedData["connectionStatus"] = connectionStatus;
    }
    
    /// <summary>
    /// 获取共享数据
    /// </summary>
    public Dictionary<string, object> GetSharedData()
    {
        return new Dictionary<string, object>(sharedData);
    }
    
    /// <summary>
    /// 获取特定类型的数据
    /// </summary>
    public T GetData<T>(string key)
    {
        if (sharedData.ContainsKey(key))
        {
            return (T)sharedData[key];
        }
        return default(T);
    }
    
    /// <summary>
    /// 设置数据
    /// </summary>
    public void SetData(string key, object value)
    {
        sharedData[key] = value;
    }
    
    /// <summary>
    /// 清除数据
    /// </summary>
    public void ClearData(string key)
    {
        if (sharedData.ContainsKey(key))
        {
            sharedData.Remove(key);
        }
    }
    
    /// <summary>
    /// 强制立即同步数据
    /// </summary>
    public void ForceDataSync()
    {
        SynchronizeAllData();
    }
    
    /// <summary>
    /// 获取数据快照（用于调试）
    /// </summary>
    public string GetDataSnapshot()
    {
        return JsonUtility.ToJson(new DataSnapshot
        {
            timestamp = Time.time,
            hardwareCount = GetData<List<object>>("hardwareList")?.Count ?? 0,
            sensorCount = GetData<Dictionary<string, float>>("sensorReadings")?.Count ?? 0,
            arTracking = GetData<Dictionary<string, object>>("arState")?["isTracking"]?.ToString() ?? "Unknown"
        });
    }
    
    /// <summary>
    /// 数据快照结构
    /// </summary>
    [System.Serializable]
    private class DataSnapshot
    {
        public float timestamp;
        public int hardwareCount;
        public int sensorCount;
        public string arTracking;
    }
}