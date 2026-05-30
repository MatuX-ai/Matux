using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

/// <summary>
/// AR交互管理器
/// 处理AR基础功能、手势识别和平面检测
/// </summary>
[RequireComponent(typeof(ARSessionOrigin))]
public class ARInteractionManager : MonoBehaviour
{
    [Header("AR组件引用")]
    [SerializeField] private ARSession arSession;
    [SerializeField] private ARPlaneManager planeManager;
    [SerializeField] private ARRaycastManager raycastManager;
    [SerializeField] private ARCameraManager cameraManager;
    [SerializeField] private Camera arCamera;

    [Header("交互配置")]
    [SerializeField] private float placementDistance = 2.0f;
    [SerializeField] private LayerMask placementLayerMask = ~0; // 默认所有层
    [SerializeField] private bool enablePlaneDetection = true;
    [SerializeField] private bool enableGestureRecognition = true;

    // 私有字段
    private ARSessionOrigin arOrigin;
    private List<ARRaycastHit> raycastHits = new List<ARRaycastHit>();
    private TouchScreenKeyboard touchKeyboard;

    // 硬件管理
    private HardwarePlacement hardwarePlacement;

    // 奖励系统
    private ARPlacementValidator placementValidator;
    private ARSceneProgressTracker sceneProgressTracker;
    private ARElementPositionDetector positionDetector;

    // 事件委托
    public delegate void ARInteractionHandler(ARInteractionType type, object data);
    public event ARInteractionHandler OnARInteraction;

    public enum ARInteractionType
    {
        PlaneDetected,
        ObjectPlaced,
        GestureRecognized,
        TrackingLost,
        TrackingRestored,
        ComponentValidated,
        PlacementCompleted,
        SceneCompleted,
        AchievementUnlocked,
        RewardEarned
    }

    void Awake()
    {
        InitializeARComponents();
        InitializeHardwareSystem();
    }

    void Start()
    {
        StartARSession();
    }

    void Update()
    {
        if (enableGestureRecognition)
        {
            HandleTouchInput();
        }
    }

    /// <summary>
    /// 初始化AR组件
    /// </summary>
    private void InitializeARComponents()
    {
        arOrigin = GetComponent<ARSessionOrigin>();

        // 获取或创建AR组件
        if (arSession == null)
            arSession = FindObjectOfType<ARSession>();

        if (planeManager == null)
            planeManager = FindObjectOfType<ARPlaneManager>();

        if (raycastManager == null)
            raycastManager = FindObjectOfType<ARRaycastManager>();

        if (cameraManager == null)
            cameraManager = FindObjectOfType<ARCameraManager>();

        if (arCamera == null)
            arCamera = arOrigin.camera;

        // 配置平面管理器
        if (planeManager != null)
        {
            planeManager.planesChanged += OnPlanesChanged;
        }
    }

    /// <summary>
    /// 初始化硬件放置系统
    /// </summary>
    private void InitializeHardwareSystem()
    {
        hardwarePlacement = gameObject.AddComponent<HardwarePlacement>();
        hardwarePlacement.Initialize(arOrigin, raycastManager);

        // 初始化奖励系统组件
        placementValidator = gameObject.AddComponent<ARPlacementValidator>();
        sceneProgressTracker = gameObject.AddComponent<ARSceneProgressTracker>();
        positionDetector = gameObject.AddComponent<ARElementPositionDetector>();

        // 初始化验证器
        placementValidator.Initialize(this);
        sceneProgressTracker.Initialize(this);
        positionDetector.Initialize(arOrigin, raycastManager);
    }

    /// <summary>
    /// 启动AR会话
    /// </summary>
    private void StartARSession()
    {
        StartCoroutine(StartARSessionCoroutine());
    }

    private IEnumerator StartARSessionCoroutine()
    {
        // 等待AR会话准备就绪
        yield return new WaitForSeconds(1f);

        if (arSession != null)
        {
            arSession.enabled = true;
        }

        if (planeManager != null && enablePlaneDetection)
        {
            planeManager.enabled = true;
        }

        Debug.Log("AR会话已启动");
        OnARInteraction?.Invoke(ARInteractionType.TrackingRestored, null);
    }

    /// <summary>
    /// 处理触摸输入
    /// </summary>
    private void HandleTouchInput()
    {
        if (Input.touchCount == 0) return;

        Touch touch = Input.GetTouch(0);

        switch (touch.phase)
        {
            case TouchPhase.Began:
                HandleTouchBegan(touch);
                break;
            case TouchPhase.Moved:
                HandleTouchMoved(touch);
                break;
            case TouchPhase.Ended:
                HandleTouchEnded(touch);
                break;
        }
    }

    /// <summary>
    /// 处理触摸开始
    /// </summary>
    private void HandleTouchBegan(Touch touch)
    {
        // 执行射线检测
        if (raycastManager.Raycast(touch.position, raycastHits, TrackableType.PlaneWithinPolygon))
        {
            if (raycastHits.Count > 0)
            {
                var hit = raycastHits[0];

                // 检查是否点击到已放置的硬件
                Ray ray = arCamera.ScreenPointToRay(touch.position);
                RaycastHit physicsHit;

                if (Physics.Raycast(ray, out physicsHit, 100f, placementLayerMask))
                {
                    ESP32Model hardware = physicsHit.collider.GetComponent<ESP32Model>();
                    if (hardware != null)
                    {
                        // 选中硬件
                        hardware.Select();
                        OnARInteraction?.Invoke(ARInteractionType.GestureRecognized, "HardwareSelected");
                        return;
                    }
                }

                // 放置新硬件
                PlaceNewHardware(hit.pose.position, hit.pose.rotation);
            }
        }
    }

    /// <summary>
    /// 处理触摸移动
    /// </summary>
    private void HandleTouchMoved(Touch touch)
    {
        // 可以实现拖拽、旋转等手势
        if (touch.deltaPosition.magnitude > 2f)
        {
            OnARInteraction?.Invoke(ARInteractionType.GestureRecognized, "Drag");
        }
    }

    /// <summary>
    /// 处理触摸结束
    /// </summary>
    private void HandleTouchEnded(Touch touch)
    {
        // 手势结束处理
        OnARInteraction?.Invoke(ARInteractionType.GestureRecognized, "TouchEnded");
    }

    /// <summary>
    /// 放置新的硬件对象
    /// </summary>
    private void PlaceNewHardware(Vector3 position, Quaternion rotation)
    {
        if (hardwarePlacement != null)
        {
            GameObject placedObject = hardwarePlacement.PlaceHardware(position, rotation);
            if (placedObject != null)
            {
                OnARInteraction?.Invoke(ARInteractionType.ObjectPlaced, placedObject);
                Debug.Log($"硬件已放置在位置: {position}");

                // 触发放置验证
                StartCoroutine(ValidatePlacementAfterDelay(placedObject, 1.0f));
            }
        }
    }

    /// <summary>
    /// 延迟验证放置结果
    /// </summary>
    private IEnumerator ValidatePlacementAfterDelay(GameObject placedObject, float delay)
    {
        yield return new WaitForSeconds(delay);

        if (placedObject != null && placementValidator != null)
        {
            var validation = placementValidator.ValidateComponentPlacement(placedObject);
            if (validation.isValid)
            {
                OnARInteraction?.Invoke(ARInteractionType.ComponentValidated, validation);
                Debug.Log($"元件放置验证通过: {validation.componentType} - 准确度: {validation.accuracy:F2}");

                // 检查场景完成状态
                CheckSceneCompletion();
            }
        }
    }

    /// <summary>
    /// 检查场景完成状态
    /// </summary>
    private void CheckSceneCompletion()
    {
        if (sceneProgressTracker != null)
        {
            var completionStatus = sceneProgressTracker.CheckSceneCompletion();
            if (completionStatus.isCompleted)
            {
                OnARInteraction?.Invoke(ARInteractionType.SceneCompleted, completionStatus);
                Debug.Log($"场景完成！准确度: {completionStatus.overallAccuracy:F2}%");

                // 触发奖励
                TriggerSceneCompletionReward(completionStatus);
            }
        }
    }

    /// <summary>
    /// 触发场景完成奖励
    /// </summary>
    private void TriggerSceneCompletionReward(SceneCompletionStatus status)
    {
        var rewardData = new SceneRewardData
        {
            accuracy = status.overallAccuracy,
            componentsPlaced = status.componentsPlaced,
            totalTime = status.completionTime,
            bonusPoints = CalculateBonusPoints(status)
        };

        OnARInteraction?.Invoke(ARInteractionType.RewardEarned, rewardData);
        Debug.Log($"获得奖励: 基础积分 + {rewardData.bonusPoints} 额外奖励");

        // 发送奖励事件到后端
        SendRewardEventToBackend(rewardData);
    }

    /// <summary>
    /// 发送奖励事件到后端
    /// </summary>
    private void SendRewardEventToBackend(SceneRewardData rewardData)
    {
        // 构造奖励事件数据
        var eventData = new System.Collections.Generic.Dictionary<string, object>
        {
            ["event_type"] = "ar_scene_completed",
            ["accuracy"] = rewardData.accuracy,
            ["components_placed"] = rewardData.componentsPlaced,
            ["total_time"] = rewardData.totalTime,
            ["bonus_points"] = rewardData.bonusPoints,
            ["scene_id"] = "default_scene", // 可以根据实际情况动态设置
            ["timestamp"] = System.DateTime.Now.ToString("o")
        };

        // 发送到后端WebSocket或HTTP API
        StartCoroutine(SendEventDataToBackend(eventData));
    }

    /// <summary>
    /// 发送事件数据到后端
    /// </summary>
    private IEnumerator SendEventDataToBackend(System.Collections.Generic.Dictionary<string, object> eventData)
    {
        string jsonData = UnityEngine.JsonUtility.ToJson(new EventDataWrapper(eventData));

        // 这里应该替换为实际的后端API地址
        string apiUrl = "http://localhost:8000/api/ar/rewards";

        using (UnityEngine.Networking.UnityWebRequest request = new UnityEngine.Networking.UnityWebRequest(apiUrl, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UnityEngine.Networking.UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new UnityEngine.Networking.DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
            {
                Debug.Log("奖励事件发送成功: " + request.downloadHandler.text);
            }
            else
            {
                Debug.LogError("奖励事件发送失败: " + request.error);
            }
        }
    }

    /// <summary>
    /// 事件数据包装类
    /// </summary>
    [System.Serializable]
    private class EventDataWrapper
    {
        public string event_type;
        public float accuracy;
        public int components_placed;
        public float total_time;
        public int bonus_points;
        public string scene_id;
        public string timestamp;

        public EventDataWrapper(System.Collections.Generic.Dictionary<string, object> data)
        {
            event_type = data["event_type"].ToString();
            accuracy = System.Convert.ToSingle(data["accuracy"]);
            components_placed = System.Convert.ToInt32(data["components_placed"]);
            total_time = System.Convert.ToSingle(data["total_time"]);
            bonus_points = System.Convert.ToInt32(data["bonus_points"]);
            scene_id = data["scene_id"].ToString();
            timestamp = data["timestamp"].ToString();
        }
    }

    /// <summary>
    /// 计算额外奖励积分
    /// </summary>
    private int CalculateBonusPoints(SceneCompletionStatus status)
    {
        int bonus = 0;

        // 准确度奖励
        if (status.overallAccuracy >= 95f) bonus += 50;
        else if (status.overallAccuracy >= 90f) bonus += 30;
        else if (status.overallAccuracy >= 85f) bonus += 10;

        // 速度奖励
        if (status.completionTime <= 120f) bonus += 20; // 2分钟内完成
        else if (status.completionTime <= 180f) bonus += 10; // 3分钟内完成

        // 完整性奖励
        if (status.componentsPlaced >= status.totalComponents) bonus += 30;

        return bonus;
    }

    /// <summary>
    /// 平面变化回调
    /// </summary>
    private void OnPlanesChanged(ARPlanesChangedEventArgs eventArgs)
    {
        foreach (var plane in eventArgs.added)
        {
            OnARInteraction?.Invoke(ARInteractionType.PlaneDetected, plane);
            Debug.Log($"检测到新平面: {plane.trackableId}");
        }
    }

    /// <summary>
    /// 重置AR场景
    /// </summary>
    public void ResetScene()
    {
        // 清除所有放置的硬件
        ESP32Model[] placedHardware = FindObjectsOfType<ESP32Model>();
        foreach (var hardware in placedHardware)
        {
            hardware.Remove();
        }

        // 重新启用平面检测
        if (planeManager != null)
        {
            planeManager.enabled = true;
        }

        Debug.Log("AR场景已重置");
    }

    /// <summary>
    /// 切换平面检测
    /// </summary>
    public void TogglePlaneDetection()
    {
        if (planeManager != null)
        {
            planeManager.enabled = !planeManager.enabled;
            Debug.Log($"平面检测已{(planeManager.enabled ? "启用" : "禁用")}");
        }
    }

    /// <summary>
    /// 获取AR状态信息
    /// </summary>
    public ARStatus GetARStatus()
    {
        return new ARStatus
        {
            IsTracking = arSession != null && arSession.enabled,
            PlaneDetectionEnabled = planeManager != null && planeManager.enabled,
            DetectedPlanes = planeManager != null ? planeManager.trackables.count : 0,
            PlacedObjects = FindObjectsOfType<ESP32Model>().Length
        };
    }

    /// <summary>
    /// AR状态信息结构体
    /// </summary>
    [System.Serializable]
    public struct ARStatus
    {
        public bool IsTracking;
        public bool PlaneDetectionEnabled;
        public int DetectedPlanes;
        public int PlacedObjects;
    }

    /// <summary>
    /// 获取AR相机引用
    /// </summary>
    public Camera GetARCamera()
    {
        return arCamera;
    }

    /// <summary>
    /// 获取会话原点
    /// </summary>
    public ARSessionOrigin GetAROrigin()
    {
        return arOrigin;
    }

    void OnDestroy()
    {
        // 清理事件监听
        if (planeManager != null)
        {
            planeManager.planesChanged -= OnPlanesChanged;
        }
    }
}
