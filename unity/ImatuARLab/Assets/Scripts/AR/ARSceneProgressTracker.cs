using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// AR场景进度跟踪器
/// 跟踪AR场景中任务的完成进度和状态
/// </summary>
public class ARSceneProgressTracker : MonoBehaviour
{
    [Header("场景配置")]
    [SerializeField] private float sceneStartTime;
    [SerializeField] private List<string> requiredComponents;
    [SerializeField] private int totalPoints = 500;

    private ARInteractionManager arManager;
    private Dictionary<string, bool> componentStatus;
    private HashSet<string> placedComponents;
    private float completionTime;

    // 场景完成状态结构
    public struct SceneCompletionStatus
    {
        public bool isCompleted;
        public float overallAccuracy;
        public int componentsPlaced;
        public int totalComponents;
        public float completionTime;
        public int earnedPoints;
        public List<string> missingComponents;
        public List<string> extraComponents;
    }

    void Awake()
    {
        InitializeSceneRequirements();
    }

    public void Initialize(ARInteractionManager manager)
    {
        arManager = manager;
        InitializeSceneRequirements();
        sceneStartTime = Time.time;

        // 订阅AR交互事件
        if (arManager != null)
        {
            arManager.OnARInteraction += HandleARInteraction;
        }
    }

    private void InitializeSceneRequirements()
    {
        requiredComponents = new List<string> { "ESP32", "LED", "Resistor", "Button" };
        componentStatus = new Dictionary<string, bool>();
        placedComponents = new HashSet<string>();

        foreach (string component in requiredComponents)
        {
            componentStatus[component] = false;
        }
    }

    private void HandleARInteraction(ARInteractionManager.ARInteractionType type, object data)
    {
        switch (type)
        {
            case ARInteractionManager.ARInteractionType.ObjectPlaced:
                if (data is GameObject placedObject)
                {
                    string componentType = IdentifyComponentType(placedObject);
                    if (!string.IsNullOrEmpty(componentType))
                    {
                        placedComponents.Add(componentType);
                        componentStatus[componentType] = true;
                        Debug.Log($"组件放置: {componentType}");
                    }
                }
                break;

            case ARInteractionManager.ARInteractionType.ComponentValidated:
                // 可以在这里处理验证通过的组件
                break;
        }
    }

    /// <summary>
    /// 检查场景完成状态
    /// </summary>
    public SceneCompletionStatus CheckSceneCompletion()
    {
        var status = new SceneCompletionStatus
        {
            isCompleted = false,
            overallAccuracy = 0f,
            componentsPlaced = placedComponents.Count,
            totalComponents = requiredComponents.Count,
            completionTime = Time.time - sceneStartTime,
            earnedPoints = 0,
            missingComponents = new List<string>(),
            extraComponents = new List<string>()
        };

        // 检查必需组件是否都已放置
        bool allRequiredPlaced = true;
        foreach (string requiredComponent in requiredComponents)
        {
            if (!placedComponents.Contains(requiredComponent))
            {
                status.missingComponents.Add(requiredComponent);
                allRequiredPlaced = false;
            }
        }

        // 检查是否有额外组件
        foreach (string placedComponent in placedComponents)
        {
            if (!requiredComponents.Contains(placedComponent))
            {
                status.extraComponents.Add(placedComponent);
            }
        }

        // 如果所有必需组件都已放置，计算准确度
        if (allRequiredPlaced)
        {
            // 获取放置验证器计算的整体准确度
            var placementValidator = GetComponent<ARPlacementValidator>();
            if (placementValidator != null)
            {
                status.overallAccuracy = placementValidator.CalculateOverallAccuracy();
            }

            // 计算获得的积分
            status.earnedPoints = CalculateEarnedPoints(status);

            // 如果准确度达到要求，则标记为完成
            if (status.overallAccuracy >= 70f)
            {
                status.isCompleted = true;
                completionTime = status.completionTime;
                Debug.Log($"场景完成！用时: {status.completionTime:F1}秒, 准确度: {status.overallAccuracy:F1}%");
            }
        }

        return status;
    }

    /// <summary>
    /// 计算获得的积分
    /// </summary>
    private int CalculateEarnedPoints(SceneCompletionStatus status)
    {
        int points = 0;

        // 基础积分：每放置一个必需组件
        points += status.componentsPlaced * 50;

        // 准确度奖励
        if (status.overallAccuracy >= 95f) points += 150;
        else if (status.overallAccuracy >= 90f) points += 100;
        else if (status.overallAccuracy >= 85f) points += 50;
        else if (status.overallAccuracy >= 80f) points += 25;

        // 速度奖励
        if (status.completionTime <= 120f) points += 100; // 2分钟内
        else if (status.completionTime <= 180f) points += 50;  // 3分钟内
        else if (status.completionTime <= 240f) points += 25;  // 4分钟内

        // 完整性奖励
        if (status.componentsPlaced >= status.totalComponents) points += 100;

        // 额外组件奖励
        points += status.extraComponents.Count * 20;

        return Mathf.Min(points, totalPoints); // 不超过总分
    }

    /// <summary>
    /// 识别组件类型
    /// </summary>
    private string IdentifyComponentType(GameObject component)
    {
        string name = component.name.ToLower();

        if (name.Contains("esp32") || name.Contains("开发板")) return "ESP32";
        if (name.Contains("led") || name.Contains("灯")) return "LED";
        if (name.Contains("resistor") || name.Contains("电阻")) return "Resistor";
        if (name.Contains("button") || name.Contains("按键")) return "Button";

        return "";
    }

    /// <summary>
    /// 获取当前进度信息
    /// </summary>
    public Dictionary<string, object> GetCurrentProgress()
    {
        var status = CheckSceneCompletion();

        return new Dictionary<string, object>
        {
            ["isCompleted"] = status.isCompleted,
            ["progressPercent"] = (float)status.componentsPlaced / status.totalComponents * 100f,
            ["accuracy"] = status.overallAccuracy,
            ["timeElapsed"] = status.completionTime,
            ["pointsEarned"] = status.earnedPoints,
            ["componentsPlaced"] = status.componentsPlaced,
            ["totalComponents"] = status.totalComponents,
            ["missingComponents"] = status.missingComponents,
            ["extraComponents"] = status.extraComponents
        };
    }

    /// <summary>
    /// 重置场景进度
    /// </summary>
    public void ResetProgress()
    {
        sceneStartTime = Time.time;
        placedComponents.Clear();

        foreach (string component in requiredComponents)
        {
            componentStatus[component] = false;
        }

        completionTime = 0f;
        Debug.Log("场景进度已重置");
    }

    /// <summary>
    /// 添加自定义必需组件
    /// </summary>
    public void AddRequiredComponent(string componentType)
    {
        if (!requiredComponents.Contains(componentType))
        {
            requiredComponents.Add(componentType);
            componentStatus[componentType] = false;
            Debug.Log($"添加必需组件: {componentType}");
        }
    }

    /// <summary>
    /// 移除必需组件
    /// </summary>
    public void RemoveRequiredComponent(string componentType)
    {
        if (requiredComponents.Contains(componentType))
        {
            requiredComponents.Remove(componentType);
            componentStatus.Remove(componentType);
            placedComponents.Remove(componentType);
            Debug.Log($"移除必需组件: {componentType}");
        }
    }

    void OnDestroy()
    {
        if (arManager != null)
        {
            arManager.OnARInteraction -= HandleARInteraction;
        }
    }
}

/// <summary>
/// 场景奖励数据结构
/// </summary>
[System.Serializable]
public struct SceneRewardData
{
    public float accuracy;
    public int componentsPlaced;
    public float totalTime;
    public int bonusPoints;

    public int TotalPoints => 200 + bonusPoints; // 基础200分 + 奖励分
}
