using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 传感器模块基类
/// 所有传感器模块继承此类，实现通用的传感器功能
/// </summary>
[System.Serializable]
public abstract class SensorModule : MonoBehaviour
{
    [Header("传感器基本信息")]
    [SerializeField] protected string sensorName = "Generic Sensor";
    [SerializeField] protected string sensorType = "Unknown";
    [SerializeField] protected float minValue = 0f;
    [SerializeField] protected float maxValue = 100f;
    [SerializeField] protected float currentValue = 0f;
    
    [Header("物理属性")]
    [SerializeField] protected float mass = 0.01f;
    [SerializeField] protected Vector3 size = new Vector3(0.02f, 0.01f, 0.02f);
    
    [Header("连接配置")]
    [SerializeField] protected Transform[] connectionPoints;
    [SerializeField] protected Material activeMaterial;
    [SerializeField] protected Material inactiveMaterial;
    
    // 保护字段
    protected bool isActive = false;
    protected bool isConnected = false;
    protected Renderer sensorRenderer;
    protected Rigidbody sensorRigidbody;
    protected Collider sensorCollider;
    
    // 事件系统
    public delegate void SensorEventHandler(SensorModule sender, SensorEventType eventType, float value);
    public event SensorEventHandler OnSensorEvent;
    
    public enum SensorEventType
    {
        Activated,
        Deactivated,
        ValueChanged,
        Connected,
        Disconnected,
        Error
    }
    
    protected virtual void Awake()
    {
        InitializeSensor();
    }
    
    protected virtual void Start()
    {
        SetupPhysics();
    }
    
    /// <summary>
    /// 初始化传感器组件
    /// </summary>
    protected virtual void InitializeSensor()
    {
        sensorRenderer = GetComponent<Renderer>();
        sensorRigidbody = GetComponent<Rigidbody>();
        sensorCollider = GetComponent<Collider>();
        
        // 查找连接点
        FindConnectionPoints();
        
        // 设置初始状态
        SetInactive();
    }
    
    /// <summary>
    /// 设置物理属性
    /// </summary>
    protected virtual void SetupPhysics()
    {
        if (sensorRigidbody == null)
        {
            sensorRigidbody = gameObject.AddComponent<Rigidbody>();
        }
        
        sensorRigidbody.mass = mass;
        sensorRigidbody.drag = 0.8f;
        sensorRigidbody.angularDrag = 0.8f;
        sensorRigidbody.useGravity = true;
        sensorRigidbody.isKinematic = true; // 初始为运动学
        
        // 设置碰撞体
        if (sensorCollider == null)
        {
            BoxCollider boxCollider = gameObject.AddComponent<BoxCollider>();
            boxCollider.size = size;
        }
    }
    
    /// <summary>
    /// 查找连接点
    /// </summary>
    protected virtual void FindConnectionPoints()
    {
        List<Transform> points = new List<Transform>();
        
        foreach (Transform child in transform)
        {
            if (child.name.Contains("Pin") || child.name.Contains("Connector"))
            {
                points.Add(child);
            }
        }
        
        connectionPoints = points.ToArray();
    }
    
    /// <summary>
    /// 激活传感器
    /// </summary>
    public virtual void Activate()
    {
        if (isActive) return;
        
        isActive = true;
        SetActiveVisual();
        OnSensorEvent?.Invoke(this, SensorEventType.Activated, currentValue);
        Debug.Log($"{sensorName} 已激活");
    }
    
    /// <summary>
    /// 停用传感器
    /// </summary>
    public virtual void Deactivate()
    {
        if (!isActive) return;
        
        isActive = false;
        SetInactiveVisual();
        OnSensorEvent?.Invoke(this, SensorEventType.Deactivated, currentValue);
        Debug.Log($"{sensorName} 已停用");
    }
    
    /// <summary>
    /// 更新传感器数值
    /// </summary>
    protected virtual void UpdateSensorValue(float newValue)
    {
        float clampedValue = Mathf.Clamp(newValue, minValue, maxValue);
        currentValue = clampedValue;
        OnSensorEvent?.Invoke(this, SensorEventType.ValueChanged, currentValue);
    }
    
    /// <summary>
    /// 设置激活状态的视觉效果
    /// </summary>
    protected virtual void SetActiveVisual()
    {
        if (sensorRenderer != null && activeMaterial != null)
        {
            sensorRenderer.material = activeMaterial;
        }
    }
    
    /// <summary>
    /// 设置非激活状态的视觉效果
    /// </summary>
    protected virtual void SetInactiveVisual()
    {
        if (sensorRenderer != null && inactiveMaterial != null)
        {
            sensorRenderer.material = inactiveMaterial;
        }
    }
    
    /// <summary>
    /// 连接到主控板
    /// </summary>
    public virtual void ConnectTo(ESP32Model controller)
    {
        if (isConnected) return;
        
        isConnected = true;
        sensorRigidbody.isKinematic = false;
        OnSensorEvent?.Invoke(this, SensorEventType.Connected, currentValue);
        Debug.Log($"{sensorName} 已连接到控制器");
    }
    
    /// <summary>
    /// 断开连接
    /// </summary>
    public virtual void Disconnect()
    {
        if (!isConnected) return;
        
        isConnected = false;
        sensorRigidbody.isKinematic = true;
        Deactivate();
        OnSensorEvent?.Invoke(this, SensorEventType.Disconnected, currentValue);
        Debug.Log($"{sensorName} 连接已断开");
    }
    
    /// <summary>
    /// 获取传感器数据
    /// </summary>
    public virtual SensorData GetSensorData()
    {
        return new SensorData
        {
            SensorName = sensorName,
            SensorType = sensorType,
            Value = currentValue,
            IsActive = isActive,
            IsConnected = isConnected,
            Timestamp = Time.time
        };
    }
    
    /// <summary>
    /// 模拟传感器读数
    /// </summary>
    public abstract void SimulateReading();
    
    /// <summary>
    /// 传感器数据结构
    /// </summary>
    [System.Serializable]
    public struct SensorData
    {
        public string SensorName;
        public string SensorType;
        public float Value;
        public bool IsActive;
        public bool IsConnected;
        public float Timestamp;
    }
}

/// <summary>
/// 温湿度传感器 (DHT22)
/// </summary>
public class DHT22Sensor : SensorModule
{
    [Header("DHT22特定配置")]
    [SerializeField] private float temperatureOffset = 0f;
    [SerializeField] private float humidityOffset = 0f;
    
    private float temperature = 25f;
    private float humidity = 50f;
    
    protected override void InitializeSensor()
    {
        sensorName = "DHT22温湿度传感器";
        sensorType = "Temperature/Humidity";
        minValue = -40f;
        maxValue = 80f;
        base.InitializeSensor();
    }
    
    public override void SimulateReading()
    {
        // 模拟温度变化
        temperature += Random.Range(-0.5f, 0.5f);
        temperature = Mathf.Clamp(temperature, -40f, 80f);
        
        // 模拟湿度变化
        humidity += Random.Range(-2f, 2f);
        humidity = Mathf.Clamp(humidity, 0f, 100f);
        
        // 更新传感器值（使用温度值）
        UpdateSensorValue(temperature + temperatureOffset);
    }
    
    /// <summary>
    /// 获取温度值
    /// </summary>
    public float GetTemperature()
    {
        return temperature + temperatureOffset;
    }
    
    /// <summary>
    /// 获取湿度值
    /// </summary>
    public float GetHumidity()
    {
        return humidity + humidityOffset;
    }
}

/// <summary>
/// 光敏电阻传感器
/// </summary>
public class LightSensor : SensorModule
{
    [Header("光敏电阻特定配置")]
    [SerializeField] private AnimationCurve lightResponseCurve = AnimationCurve.Linear(0, 0, 1, 1);
    [SerializeField] private float ambientLightLevel = 0.5f;
    
    protected override void InitializeSensor()
    {
        sensorName = "光敏电阻传感器";
        sensorType = "Light Intensity";
        minValue = 0f;
        maxValue = 1023f;
        base.InitializeSensor();
    }
    
    public override void SimulateReading()
    {
        // 基于环境光模拟读数
        float simulatedValue = ambientLightLevel * maxValue;
        simulatedValue += Random.Range(-50f, 50f); // 添加噪声
        simulatedValue = Mathf.Clamp(simulatedValue, minValue, maxValue);
        
        UpdateSensorValue(simulatedValue);
    }
    
    /// <summary>
    /// 设置环境光强度
    /// </summary>
    public void SetAmbientLight(float intensity)
    {
        ambientLightLevel = Mathf.Clamp01(intensity);
    }
}

/// <summary>
/// 超声波传感器 (HC-SR04)
/// </summary>
public class UltrasonicSensor : SensorModule
{
    [Header("超声波传感器特定配置")]
    [SerializeField] private float minDistance = 2f;   // cm
    [SerializeField] private float maxDistance = 400f; // cm
    [SerializeField] private Transform triggerPin;
    [SerializeField] private Transform echoPin;
    
    private float distance = 100f;
    
    protected override void InitializeSensor()
    {
        sensorName = "HC-SR04超声波传感器";
        sensorType = "Distance";
        minValue = minDistance;
        maxValue = maxDistance;
        base.InitializeSensor();
    }
    
    public override void SimulateReading()
    {
        // 模拟距离测量
        distance += Random.Range(-5f, 5f);
        distance = Mathf.Clamp(distance, minDistance, maxDistance);
        
        UpdateSensorValue(distance);
    }
    
    /// <summary>
    /// 获取测量距离
    /// </summary>
    public float GetDistance()
    {
        return distance;
    }
    
    /// <summary>
    /// 模拟触发测量
    /// </summary>
    public void TriggerMeasurement()
    {
        SimulateReading();
        Debug.Log($"{sensorName} 触发测量，距离: {distance:F2}cm");
    }
}

/// <summary>
/// OLED显示屏
/// </summary>
public class OLedDisplay : SensorModule
{
    [Header("OLED显示配置")]
    [SerializeField] private int width = 128;
    [SerializeField] private int height = 64;
    [TextArea(3, 10)]
    [SerializeField] private string displayText = "Hello World!";
    
    protected override void InitializeSensor()
    {
        sensorName = "OLED显示屏";
        sensorType = "Display";
        minValue = 0f;
        maxValue = 1f;
        base.InitializeSensor();
    }
    
    public override void SimulateReading()
    {
        // 显示屏通常不产生模拟读数，但可以表示显示状态
        UpdateSensorValue(isActive ? 1f : 0f);
    }
    
    /// <summary>
    /// 设置显示文本
    /// </summary>
    public void SetDisplayText(string text)
    {
        displayText = text;
        Debug.Log($"{sensorName} 显示: {displayText}");
    }
    
    /// <summary>
    /// 清空显示
    /// </summary>
    public void ClearDisplay()
    {
        displayText = "";
        Debug.Log($"{sensorName} 显示已清空");
    }
}