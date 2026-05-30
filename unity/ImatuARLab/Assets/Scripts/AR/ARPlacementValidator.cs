using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// AR元件放置验证器
/// 验证虚拟元件在AR场景中的放置准确性和合理性
/// </summary>
public class ARPlacementValidator : MonoBehaviour
{
    [Header("验证配置")]
    [SerializeField] private float positionTolerance = 0.1f;        // 位置容差(米)
    [SerializeField] private float rotationTolerance = 15f;         // 旋转容差(度)
    [SerializeField] private float scaleTolerance = 0.2f;           // 缩放容差
    [SerializeField] private LayerMask validationLayers = ~0;       // 验证层掩码

    private ARInteractionManager arManager;
    private Dictionary<string, ComponentTargetPosition> targetPositions;

    // 验证结果结构
    public struct ValidationReport
    {
        public bool isValid;
        public string componentType;
        public float accuracy;
        public Vector3 positionError;
        public float rotationError;
        public float scaleError;
        public string feedbackMessage;
    }

    // 元件目标位置定义
    private struct ComponentTargetPosition
    {
        public Vector3 idealPosition;
        public Quaternion idealRotation;
        public Vector3 idealScale;
        public string componentName;
        public int pointValue;
    }

    void Awake()
    {
        InitializeTargetPositions();
    }

    public void Initialize(ARInteractionManager manager)
    {
        arManager = manager;
        InitializeTargetPositions();
    }

    private void InitializeTargetPositions()
    {
        targetPositions = new Dictionary<string, ComponentTargetPosition>
        {
            ["ESP32"] = new ComponentTargetPosition
            {
                idealPosition = new Vector3(0, 0, 0),
                idealRotation = Quaternion.identity,
                idealScale = Vector3.one,
                componentName = "ESP32开发板",
                pointValue = 100
            },
            ["LED"] = new ComponentTargetPosition
            {
                idealPosition = new Vector3(0.1f, 0, 0),
                idealRotation = Quaternion.Euler(0, 0, 90),
                idealScale = Vector3.one * 0.5f,
                componentName = "LED指示灯",
                pointValue = 50
            },
            ["Resistor"] = new ComponentTargetPosition
            {
                idealPosition = new Vector3(-0.1f, 0, 0),
                idealRotation = Quaternion.identity,
                idealScale = Vector3.one,
                componentName = "限流电阻",
                pointValue = 30
            },
            ["Button"] = new ComponentTargetPosition
            {
                idealPosition = new Vector3(0, 0.1f, 0),
                idealRotation = Quaternion.identity,
                idealScale = Vector3.one * 0.8f,
                componentName = "按键开关",
                pointValue = 40
            }
        };
    }

    /// <summary>
    /// 验证元件放置
    /// </summary>
    public ValidationReport ValidateComponentPlacement(GameObject component)
    {
        if (component == null) return CreateInvalidReport("组件为空");

        string componentType = GetComponentType(component);
        if (string.IsNullOrEmpty(componentType))
        {
            return CreateInvalidReport("无法识别组件类型");
        }

        if (!targetPositions.ContainsKey(componentType))
        {
            return CreateInvalidReport($"未知组件类型: {componentType}");
        }

        var target = targetPositions[componentType];
        var report = CompareWithTarget(component, target);

        // 记录验证日志
        Debug.Log($"验证 {componentType}: 准确度 {report.accuracy:F2}%, 位置误差 {report.positionError.magnitude:F3}m");

        return report;
    }

    /// <summary>
    /// 比较组件与目标位置
    /// </summary>
    private ValidationReport CompareWithTarget(GameObject component, ComponentTargetPosition target)
    {
        Vector3 currentPosition = component.transform.position;
        Quaternion currentRotation = component.transform.rotation;
        Vector3 currentScale = component.transform.localScale;

        // 计算误差
        Vector3 posError = currentPosition - target.idealPosition;
        float rotError = Quaternion.Angle(currentRotation, target.idealRotation);
        Vector3 scaleErrorVec = currentScale - target.idealScale;
        float scaleError = scaleErrorVec.magnitude;

        // 归一化误差到0-1范围
        float normalizedPosError = Mathf.Clamp01(posError.magnitude / positionTolerance);
        float normalizedRotError = Mathf.Clamp01(rotError / rotationTolerance);
        float normalizedScaleError = Mathf.Clamp01(scaleError / scaleTolerance);

        // 计算综合准确度 (权重: 位置50%, 旋转30%, 缩放20%)
        float accuracy = 100f - (normalizedPosError * 50f + normalizedRotError * 30f + normalizedScaleError * 20f);
        accuracy = Mathf.Clamp(accuracy, 0f, 100f);

        bool isValid = accuracy >= 70f; // 70%以上认为有效

        string feedback = GenerateFeedback(accuracy, normalizedPosError, normalizedRotError, normalizedScaleError);

        return new ValidationReport
        {
            isValid = isValid,
            componentType = target.componentName,
            accuracy = accuracy,
            positionError = posError,
            rotationError = rotError,
            scaleError = scaleError,
            feedbackMessage = feedback
        };
    }

    /// <summary>
    /// 生成反馈消息
    /// </summary>
    private string GenerateFeedback(float accuracy, float posError, float rotError, float scaleError)
    {
        if (accuracy >= 95f) return "完美放置！非常准确！";
        if (accuracy >= 85f) return "放置很好！准确度很高";
        if (accuracy >= 75f) return "放置不错，还有改进空间";
        if (accuracy >= 70f) return "勉强合格，建议调整位置";

        string mainIssue = "";
        if (posError > rotError && posError > scaleError) mainIssue = "位置偏差较大";
        else if (rotError > scaleError) mainIssue = "角度偏差较大";
        else mainIssue = "大小不合适";

        return $"放置不准确 - {mainIssue}，请重新调整";
    }

    /// <summary>
    /// 创建无效报告
    /// </summary>
    private ValidationReport CreateInvalidReport(string reason)
    {
        return new ValidationReport
        {
            isValid = false,
            componentType = "Unknown",
            accuracy = 0f,
            positionError = Vector3.zero,
            rotationError = 0f,
            scaleError = 0f,
            feedbackMessage = reason
        };
    }

    /// <summary>
    /// 识别组件类型
    /// </summary>
    private string GetComponentType(GameObject component)
    {
        // 通过组件名称识别
        string name = component.name.ToLower();

        if (name.Contains("esp32") || name.Contains("开发板")) return "ESP32";
        if (name.Contains("led") || name.Contains("灯")) return "LED";
        if (name.Contains("resistor") || name.Contains("电阻")) return "Resistor";
        if (name.Contains("button") || name.Contains("按键")) return "Button";

        // 通过组件脚本识别
        if (component.GetComponent<ESP32Model>() != null) return "ESP32";

        return "";
    }

    /// <summary>
    /// 获取所有组件的验证状态
    /// </summary>
    public List<ValidationReport> ValidateAllComponents()
    {
        List<ValidationReport> reports = new List<ValidationReport>();

        ESP32Model[] components = FindObjectsOfType<ESP32Model>();
        foreach (var component in components)
        {
            var report = ValidateComponentPlacement(component.gameObject);
            reports.Add(report);
        }

        return reports;
    }

    /// <summary>
    /// 计算整体场景准确度
    /// </summary>
    public float CalculateOverallAccuracy()
    {
        var reports = ValidateAllComponents();
        if (reports.Count == 0) return 0f;

        float totalAccuracy = 0f;
        int validCount = 0;

        foreach (var report in reports)
        {
            if (report.isValid)
            {
                totalAccuracy += report.accuracy;
                validCount++;
            }
        }

        return validCount > 0 ? totalAccuracy / validCount : 0f;
    }
}
