using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

/// <summary>
/// 硬件放置管理系统
/// 负责硬件对象的实例化、放置和管理
/// </summary>
public class HardwarePlacement : MonoBehaviour
{
    [Header("硬件预制体")]
    [SerializeField] private GameObject esp32Prefab;
    [SerializeField] private GameObject dht22Prefab;
    [SerializeField] private GameObject lightSensorPrefab;
    [SerializeField] private GameObject ultrasonicPrefab;
    [SerializeField] private GameObject oledPrefab;
    
    [Header("放置配置")]
    [SerializeField] private float minPlacementDistance = 0.5f;
    [SerializeField] private float maxPlacementDistance = 5.0f;
    [SerializeField] private LayerMask placementLayerMask = ~0;
    
    // 私有字段
    private ARSessionOrigin arOrigin;
    private ARRaycastManager raycastManager;
    private List<GameObject> placedHardware = new List<GameObject>();
    
    // 当前选中的硬件类型
    private HardwareType currentHardwareType = HardwareType.ESP32;
    
    public enum HardwareType
    {
        ESP32,
        DHT22,
        LightSensor,
        Ultrasonic,
        OLED
    }
    
    /// <summary>
    /// 初始化放置系统
    /// </summary>
    public void Initialize(ARSessionOrigin origin, ARRaycastManager raycastMgr)
    {
        arOrigin = origin;
        raycastManager = raycastMgr;
        
        // 验证预制体
        ValidatePrefabs();
    }
    
    /// <summary>
    /// 验证预制体是否存在
    /// </summary>
    private void ValidatePrefabs()
    {
        if (esp32Prefab == null)
        {
            Debug.LogWarning("ESP32预制体未分配，将在运行时创建默认立方体");
        }
    }
    
    /// <summary>
    /// 放置硬件对象
    /// </summary>
    public GameObject PlaceHardware(Vector3 position, Quaternion rotation)
    {
        GameObject prefab = GetPrefabForType(currentHardwareType);
        if (prefab == null)
        {
            prefab = CreateDefaultHardware();
        }
        
        // 实例化硬件
        GameObject hardwareObject = Instantiate(prefab, position, rotation);
        
        // 添加必要的组件
        SetupHardwareComponents(hardwareObject);
        
        // 添加到管理列表
        placedHardware.Add(hardwareObject);
        
        return hardwareObject;
    }
    
    /// <summary>
    /// 根据类型获取对应的预制体
    /// </summary>
    private GameObject GetPrefabForType(HardwareType type)
    {
        switch (type)
        {
            case HardwareType.ESP32: return esp32Prefab;
            case HardwareType.DHT22: return dht22Prefab;
            case HardwareType.LightSensor: return lightSensorPrefab;
            case HardwareType.Ultrasonic: return ultrasonicPrefab;
            case HardwareType.OLED: return oledPrefab;
            default: return null;
        }
    }
    
    /// <summary>
    /// 创建默认硬件对象（当没有预制体时）
    /// </summary>
    private GameObject CreateDefaultHardware()
    {
        GameObject defaultObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
        defaultObject.name = $"Hardware_{currentHardwareType}_{placedHardware.Count}";
        
        // 设置合适大小
        defaultObject.transform.localScale = GetDefaultScale(currentHardwareType);
        
        // 添加颜色标识
        Renderer renderer = defaultObject.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.material.color = GetHardwareColor(currentHardwareType);
        }
        
        return defaultObject;
    }
    
    /// <summary>
    /// 获取硬件类型的默认缩放
    /// </summary>
    private Vector3 GetDefaultScale(HardwareType type)
    {
        switch (type)
        {
            case HardwareType.ESP32: return new Vector3(0.05f, 0.01f, 0.08f); // 50mm x 10mm x 80mm
            case HardwareType.DHT22: return new Vector3(0.03f, 0.02f, 0.03f); // 30mm x 20mm x 30mm
            case HardwareType.LightSensor: return new Vector3(0.02f, 0.01f, 0.02f); // 20mm x 10mm x 20mm
            case HardwareType.Ultrasonic: return new Vector3(0.04f, 0.02f, 0.02f); // 40mm x 20mm x 20mm
            case HardwareType.OLED: return new Vector3(0.03f, 0.005f, 0.05f); // 30mm x 5mm x 50mm
            default: return Vector3.one * 0.1f;
        }
    }
    
    /// <summary>
    /// 获取硬件类型的颜色标识
    /// </summary>
    private Color GetHardwareColor(HardwareType type)
    {
        switch (type)
        {
            case HardwareType.ESP32: return Color.blue;
            case HardwareType.DHT22: return Color.green;
            case HardwareType.LightSensor: return Color.yellow;
            case HardwareType.Ultrasonic: return Color.red;
            case HardwareType.OLED: return Color.black;
            default: return Color.gray;
        }
    }
    
    /// <summary>
    /// 设置硬件组件
    /// </summary>
    private void SetupHardwareComponents(GameObject hardwareObject)
    {
        // 添加硬件控制脚本
        switch (currentHardwareType)
        {
            case HardwareType.ESP32:
                if (hardwareObject.GetComponent<ESP32Model>() == null)
                {
                    hardwareObject.AddComponent<ESP32Model>();
                }
                break;
                
            case HardwareType.DHT22:
                DHT22Sensor dht22 = hardwareObject.GetComponent<DHT22Sensor>() ?? hardwareObject.AddComponent<DHT22Sensor>();
                dht22.Activate();
                break;
                
            case HardwareType.LightSensor:
                LightSensor lightSensor = hardwareObject.GetComponent<LightSensor>() ?? hardwareObject.AddComponent<LightSensor>();
                lightSensor.Activate();
                break;
                
            case HardwareType.Ultrasonic:
                UltrasonicSensor ultrasonic = hardwareObject.GetComponent<UltrasonicSensor>() ?? hardwareObject.AddComponent<UltrasonicSensor>();
                ultrasonic.Activate();
                break;
                
            case HardwareType.OLED:
                OLedDisplay oled = hardwareObject.GetComponent<OLedDisplay>() ?? hardwareObject.AddComponent<OLedDisplay>();
                oled.Activate();
                break;
        }
        
        // 确保有碰撞体
        if (hardwareObject.GetComponent<Collider>() == null)
        {
            hardwareObject.AddComponent<BoxCollider>();
        }
        
        // 确保有刚体
        if (hardwareObject.GetComponent<Rigidbody>() == null)
        {
            Rigidbody rb = hardwareObject.AddComponent<Rigidbody>();
            rb.isKinematic = true; // 初始为运动学
        }
    }
    
    /// <summary>
    /// 设置当前要放置的硬件类型
    /// </summary>
    public void SetCurrentHardwareType(HardwareType type)
    {
        currentHardwareType = type;
        Debug.Log($"当前硬件类型设置为: {type}");
    }
    
    /// <summary>
    /// 获取当前硬件类型
    /// </summary>
    public HardwareType GetCurrentHardwareType()
    {
        return currentHardwareType;
    }
    
    /// <summary>
    /// 移除指定的硬件对象
    /// </summary>
    public void RemoveHardware(GameObject hardwareObject)
    {
        if (placedHardware.Contains(hardwareObject))
        {
            placedHardware.Remove(hardwareObject);
            Destroy(hardwareObject);
            Debug.Log("硬件对象已移除");
        }
    }
    
    /// <summary>
    /// 清除所有放置的硬件
    /// </summary>
    public void ClearAllHardware()
    {
        foreach (GameObject hardware in placedHardware)
        {
            if (hardware != null)
            {
                Destroy(hardware);
            }
        }
        placedHardware.Clear();
        Debug.Log("所有硬件对象已清除");
    }
    
    /// <summary>
    /// 获取所有放置的硬件
    /// </summary>
    public List<GameObject> GetAllPlacedHardware()
    {
        // 清理已被销毁的对象
        placedHardware.RemoveAll(obj => obj == null);
        return new List<GameObject>(placedHardware);
    }
    
    /// <summary>
    /// 获取特定类型的硬件
    /// </summary>
    public List<GameObject> GetHardwareByType(HardwareType type)
    {
        List<GameObject> result = new List<GameObject>();
        
        foreach (GameObject hardware in placedHardware)
        {
            if (hardware == null) continue;
            
            bool match = false;
            switch (type)
            {
                case HardwareType.ESP32:
                    match = hardware.GetComponent<ESP32Model>() != null;
                    break;
                case HardwareType.DHT22:
                    match = hardware.GetComponent<DHT22Sensor>() != null;
                    break;
                case HardwareType.LightSensor:
                    match = hardware.GetComponent<LightSensor>() != null;
                    break;
                case HardwareType.Ultrasonic:
                    match = hardware.GetComponent<UltrasonicSensor>() != null;
                    break;
                case HardwareType.OLED:
                    match = hardware.GetComponent<OLedDisplay>() != null;
                    break;
            }
            
            if (match)
            {
                result.Add(hardware);
            }
        }
        
        return result;
    }
    
    /// <summary>
    /// 检查放置位置是否有效
    /// </summary>
    public bool IsValidPlacement(Vector3 position)
    {
        // 检查距离范围
        float distance = Vector3.Distance(arOrigin.camera.transform.position, position);
        if (distance < minPlacementDistance || distance > maxPlacementDistance)
        {
            return false;
        }
        
        // 可以添加更多验证逻辑
        return true;
    }
    
    /// <summary>
    /// 获取硬件统计信息
    /// </summary>
    public HardwareStatistics GetStatistics()
    {
        return new HardwareStatistics
        {
            TotalHardware = placedHardware.Count,
            ESP32Count = GetHardwareByType(HardwareType.ESP32).Count,
            SensorCount = GetHardwareByType(HardwareType.DHT22).Count +
                         GetHardwareByType(HardwareType.LightSensor).Count +
                         GetHardwareByType(HardwareType.Ultrasonic).Count,
            DisplayCount = GetHardwareByType(HardwareType.OLED).Count
        };
    }
    
    /// <summary>
    /// 硬件统计信息结构体
    /// </summary>
    [System.Serializable]
    public struct HardwareStatistics
    {
        public int TotalHardware;
        public int ESP32Count;
        public int SensorCount;
        public int DisplayCount;
    }
}