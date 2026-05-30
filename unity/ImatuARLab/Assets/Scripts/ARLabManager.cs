using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// AR实验室主管理器
/// 整合所有AR实验室功能模块的核心控制器
/// </summary>
public class ARLabManager : MonoBehaviour
{
    [Header("系统组件")]
    [SerializeField] private ARInteractionManager arInteractionManager;
    [SerializeField] private HardwarePlacement hardwarePlacement;
    [SerializeField] private WiringGuide wiringGuide;
    [SerializeField] private UnityWebGLInterface webGLInterface;
    [SerializeField] private DataBridge dataBridge;
    
    [Header("实验室配置")]
    [SerializeField] private string labVersion = "1.0.0";
    [SerializeField] private bool autoInitialize = true;
    [SerializeField] private float initializationDelay = 1.0f;
    
    // 系统状态
    private LabState currentState = LabState.Initializing;
    private Dictionary<string, object> labConfiguration = new Dictionary<string, object>();
    
    // 事件委托
    public delegate void LabStateHandler(LabState newState, LabState oldState);
    public event LabStateHandler OnLabStateChanged;
    
    public enum LabState
    {
        Initializing,
        Ready,
        Active,
        Paused,
        Error
    }
    
    void Awake()
    {
        DontDestroyOnLoad(gameObject);
        InitializeLabConfiguration();
    }
    
    void Start()
    {
        if (autoInitialize)
        {
            StartCoroutine(InitializeLabSystem());
        }
    }
    
    /// <summary>
    /// 初始化实验室配置
    /// </summary>
    private void InitializeLabConfiguration()
    {
        labConfiguration["version"] = labVersion;
        labConfiguration["initialized"] = false;
        labConfiguration["startTime"] = Time.time;
        labConfiguration["supportedHardware"] = new List<string> { "ESP32", "DHT22", "LightSensor", "Ultrasonic", "OLED" };
    }
    
    /// <summary>
    /// 初始化实验室系统
    /// </summary>
    private IEnumerator InitializeLabSystem()
    {
        ChangeLabState(LabState.Initializing);
        
        // 等待初始化延迟
        yield return new WaitForSeconds(initializationDelay);
        
        try
        {
            // 按顺序初始化各个系统
            InitializeARSystem();
            InitializeHardwareSystem();
            InitializeWiringSystem();
            InitializeWebGLSystem();
            InitializeDataBridge();
            
            // 验证所有系统
            if (VerifySystemInitialization())
            {
                labConfiguration["initialized"] = true;
                ChangeLabState(LabState.Ready);
                Debug.Log("AR实验室系统初始化完成");
            }
            else
            {
                throw new System.Exception("系统验证失败");
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"实验室初始化失败: {e.Message}");
            ChangeLabState(LabState.Error);
        }
    }
    
    /// <summary>
    /// 初始化AR系统
    /// </summary>
    private void InitializeARSystem()
    {
        if (arInteractionManager == null)
        {
            arInteractionManager = FindObjectOfType<ARInteractionManager>();
            if (arInteractionManager == null)
            {
                GameObject arManagerObj = new GameObject("ARInteractionManager");
                arInteractionManager = arManagerObj.AddComponent<ARInteractionManager>();
            }
        }
        
        Debug.Log("AR系统初始化完成");
    }
    
    /// <summary>
    /// 初始化硬件系统
    /// </summary>
    private void InitializeHardwareSystem()
    {
        if (hardwarePlacement == null)
        {
            hardwarePlacement = FindObjectOfType<HardwarePlacement>();
            if (hardwarePlacement == null)
            {
                GameObject hardwareObj = new GameObject("HardwarePlacement");
                hardwarePlacement = hardwareObj.AddComponent<HardwarePlacement>();
                
                // 初始化硬件放置系统
                var arOrigin = arInteractionManager?.GetAROrigin();
                var raycastManager = arInteractionManager?.GetComponent<UnityEngine.XR.ARFoundation.ARRaycastManager>();
                if (arOrigin != null && raycastManager != null)
                {
                    hardwarePlacement.Initialize(arOrigin, raycastManager);
                }
            }
        }
        
        Debug.Log("硬件系统初始化完成");
    }
    
    /// <summary>
    /// 初始化接线系统
    /// </summary>
    private void InitializeWiringSystem()
    {
        if (wiringGuide == null)
        {
            wiringGuide = FindObjectOfType<WiringGuide>();
            if (wiringGuide == null)
            {
                GameObject wiringObj = new GameObject("WiringGuide");
                wiringGuide = wiringObj.AddComponent<WiringGuide>();
            }
        }
        
        Debug.Log("接线系统初始化完成");
    }
    
    /// <summary>
    /// 初始化WebGL接口
    /// </summary>
    private void InitializeWebGLSystem()
    {
        if (webGLInterface == null)
        {
            webGLInterface = FindObjectOfType<UnityWebGLInterface>();
            if (webGLInterface == null)
            {
                GameObject webGLObj = new GameObject("UnityWebGLInterface");
                webGLInterface = webGLObj.AddComponent<UnityWebGLInterface>();
            }
        }
        
        Debug.Log("WebGL接口初始化完成");
    }
    
    /// <summary>
    /// 初始化数据桥接器
    /// </summary>
    private void InitializeDataBridge()
    {
        if (dataBridge == null)
        {
            dataBridge = FindObjectOfType<DataBridge>();
            if (dataBridge == null)
            {
                GameObject bridgeObj = new GameObject("DataBridge");
                dataBridge = bridgeObj.AddComponent<DataBridge>();
            }
        }
        
        Debug.Log("数据桥接器初始化完成");
    }
    
    /// <summary>
    /// 验证系统初始化
    /// </summary>
    private bool VerifySystemInitialization()
    {
        return arInteractionManager != null &&
               hardwarePlacement != null &&
               wiringGuide != null &&
               webGLInterface != null &&
               dataBridge != null;
    }
    
    /// <summary>
    /// 改变实验室状态
    /// </summary>
    private void ChangeLabState(LabState newState)
    {
        LabState oldState = currentState;
        currentState = newState;
        
        OnLabStateChanged?.Invoke(newState, oldState);
        Debug.Log($"实验室状态变更: {oldState} -> {newState}");
    }
    
    /// <summary>
    /// 开始实验室活动
    /// </summary>
    public void StartLabActivity()
    {
        if (currentState != LabState.Ready && currentState != LabState.Paused)
        {
            Debug.LogWarning($"无法开始活动，当前状态: {currentState}");
            return;
        }
        
        ChangeLabState(LabState.Active);
        Debug.Log("实验室活动已开始");
    }
    
    /// <summary>
    /// 暂停实验室活动
    /// </summary>
    public void PauseLabActivity()
    {
        if (currentState == LabState.Active)
        {
            ChangeLabState(LabState.Paused);
            Debug.Log("实验室活动已暂停");
        }
    }
    
    /// <summary>
    /// 重置实验室
    /// </summary>
    public void ResetLab()
    {
        // 重置所有子系统
        if (arInteractionManager != null)
            arInteractionManager.ResetScene();
            
        if (hardwarePlacement != null)
            hardwarePlacement.ClearAllHardware();
            
        if (wiringGuide != null)
            wiringGuide.ClearAllConnections();
            
        // 重置状态
        ChangeLabState(LabState.Ready);
        Debug.Log("实验室已重置");
    }
    
    /// <summary>
    /// 获取实验室状态
    /// </summary>
    public LabStatus GetLabStatus()
    {
        return new LabStatus
        {
            CurrentState = currentState,
            IsInitialized = (bool)labConfiguration["initialized"],
            Version = labVersion,
            Uptime = Time.time - (float)labConfiguration["startTime"],
            HardwareStats = hardwarePlacement?.GetStatistics() ?? new HardwarePlacement.HardwareStatistics(),
            WiringStats = wiringGuide?.GetStatistics() ?? new WiringGuide.WiringStatistics(),
            ARStatus = arInteractionManager?.GetARStatus() ?? new ARInteractionManager.ARStatus()
        };
    }
    
    /// <summary>
    /// 获取实验室配置
    /// </summary>
    public Dictionary<string, object> GetLabConfiguration()
    {
        return new Dictionary<string, object>(labConfiguration);
    }
    
    /// <summary>
    /// 设置实验室配置
    /// </summary>
    public void SetLabConfiguration(string key, object value)
    {
        labConfiguration[key] = value;
        Debug.Log($"实验室配置已更新: {key} = {value}");
    }
    
    /// <summary>
    /// 获取系统组件引用
    /// </summary>
    public T GetSystemComponent<T>() where T : Component
    {
        if (typeof(T) == typeof(ARInteractionManager)) return arInteractionManager as T;
        if (typeof(T) == typeof(HardwarePlacement)) return hardwarePlacement as T;
        if (typeof(T) == typeof(WiringGuide)) return wiringGuide as T;
        if (typeof(T) == typeof(UnityWebGLInterface)) return webGLInterface as T;
        if (typeof(T) == typeof(DataBridge)) return dataBridge as T;
        
        return null;
    }
    
    /// <summary>
    /// 实验室状态信息结构体
    /// </summary>
    [System.Serializable]
    public struct LabStatus
    {
        public LabState CurrentState;
        public bool IsInitialized;
        public string Version;
        public float Uptime;
        public HardwarePlacement.HardwareStatistics HardwareStats;
        public WiringGuide.WiringStatistics WiringStats;
        public ARInteractionManager.ARStatus ARStatus;
    }
    
    /// <summary>
    /// 处理来自Web的命令
    /// </summary>
    public void HandleWebCommand(string command, string parameters)
    {
        Debug.Log($"接收到Web命令: {command} 参数: {parameters}");
        
        switch (command.ToLower())
        {
            case "startlab":
                StartLabActivity();
                break;
            case "pauselab":
                PauseLabActivity();
                break;
            case "resetlab":
                ResetLab();
                break;
            case "getstatus":
                var status = GetLabStatus();
                webGLInterface?.SendToJavaScript("labStatus", JsonUtility.ToJson(status));
                break;
            case "setconfig":
                // 解析配置参数
                try
                {
                    var configData = JsonUtility.FromJson<ConfigData>(parameters);
                    SetLabConfiguration(configData.key, configData.value);
                }
                catch (System.Exception e)
                {
                    Debug.LogError($"配置设置失败: {e.Message}");
                }
                break;
            default:
                Debug.LogWarning($"未知命令: {command}");
                break;
        }
    }
    
    /// <summary>
    /// 配置数据结构
    /// </summary>
    [System.Serializable]
    private class ConfigData
    {
        public string key;
        public string value;
    }
    
    void OnDestroy()
    {
        // 清理资源
        Debug.Log("AR实验室管理器正在销毁");
    }
}