using System.Collections.Generic;
using UnityEngine;
using Mirror;

/// <summary>
/// 网络化电路元件同步器
/// 负责在网络中同步电路元件的物理状态
/// </summary>
public class NetworkedCircuitElement : NetworkSyncBehaviour
{
    [Header("电路元件配置")]
    [Tooltip("元件类型")]
    public ElementType elementType = ElementType.Resistor;

    [Tooltip("元件标识符")]
    public string elementId = "";

    [Tooltip("连接节点1")]
    public string node1 = "";

    [Tooltip("连接节点2")]
    public string node2 = "";

    [Tooltip("元件参数值")]
    public float parameterValue = 1000f; // 电阻值、电容值等

    [Header("可视化配置")]
    [Tooltip("元件模型")]
    public GameObject elementModel;

    [Tooltip("连接线预制体")]
    public LineRenderer connectionLinePrefab;

    // 本地物理引擎引用
    private CircuitPhysicsEngine physicsEngine;
    private LineRenderer connectionLine;

    // 网络同步变量
    [SyncVar(hook = nameof(OnVoltageChanged))]
    private float networkVoltage = 0f;

    [SyncVar(hook = nameof(OnCurrentChanged))]
    private float networkCurrent = 0f;

    [SyncVar(hook = nameof(OnParameterValueChanged))]
    private float networkParameterValue = 0f;

    public enum ElementType
    {
        Resistor,
        Capacitor,
        Inductor,
        VoltageSource,
        CurrentSource
    }

    protected override void Awake()
    {
        base.Awake();
        physicsEngine = FindObjectOfType<CircuitPhysicsEngine>();

        if (string.IsNullOrEmpty(elementId))
        {
            elementId = $"{elementType}_{GetInstanceID()}";
        }

        CreateVisualRepresentation();
    }

    public override void OnStartServer()
    {
        base.OnStartServer();
        RegisterWithPhysicsEngine();
    }

    public override void OnStartClient()
    {
        base.OnStartClient();
        CreateVisualConnections();
    }

    /// <summary>
    /// 创建视觉表示
    /// </summary>
    private void CreateVisualRepresentation()
    {
        if (elementModel == null) return;

        GameObject modelInstance = Instantiate(elementModel, transform);
        modelInstance.name = $"{elementType}_Model";

        // 根据元件类型设置材质颜色
        Renderer renderer = modelInstance.GetComponent<Renderer>();
        if (renderer != null)
        {
            Color elementColor = GetElementColor(elementType);
            renderer.material.color = elementColor;
        }
    }

    /// <summary>
    /// 获取元件颜色
    /// </summary>
    private Color GetElementColor(ElementType type)
    {
        switch (type)
        {
            case ElementType.Resistor: return Color.red;
            case ElementType.Capacitor: return Color.blue;
            case ElementType.Inductor: return Color.green;
            case ElementType.VoltageSource: return Color.yellow;
            case ElementType.CurrentSource: return Color.magenta;
            default: return Color.white;
        }
    }

    /// <summary>
    /// 注册到物理引擎
    /// </summary>
    [Server]
    private void RegisterWithPhysicsEngine()
    {
        if (physicsEngine == null) return;

        switch (elementType)
        {
            case ElementType.Resistor:
                physicsEngine.CreateResistor(elementId, node1, node2, parameterValue);
                break;
            case ElementType.Capacitor:
                physicsEngine.CreateCapacitor(elementId, node1, node2, parameterValue);
                break;
        }

        // 订阅物理引擎状态变化
        physicsEngine.OnCircuitStateChanged += OnCircuitStateChanged;
        physicsEngine.OnElementValueChanged += OnElementValueChanged;

        Debug.Log($"元件 {elementId} 已注册到物理引擎");
    }

    /// <summary>
    /// 创建连接线可视化
    /// </summary>
    private void CreateVisualConnections()
    {
        if (connectionLinePrefab == null) return;

        connectionLine = Instantiate(connectionLinePrefab, transform);
        connectionLine.name = "ConnectionLine";
        connectionLine.positionCount = 2;
        UpdateConnectionLine();
    }

    /// <summary>
    /// 更新连接线位置
    /// </summary>
    private void UpdateConnectionLine()
    {
        if (connectionLine == null) return;

        // 查找连接的节点对象
        var node1Obj = GameObject.Find(node1);
        var node2Obj = GameObject.Find(node2);

        if (node1Obj != null && node2Obj != null)
        {
            connectionLine.SetPosition(0, node1Obj.transform.position);
            connectionLine.SetPosition(1, node2Obj.transform.position);
        }
    }

    /// <summary>
    /// 电路状态变化回调
    /// </summary>
    [Server]
    private void OnCircuitStateChanged(CircuitPhysicsEngine.CircuitState state)
    {
        if (state.elementStates.ContainsKey(elementId))
        {
            var elementState = state.elementStates[elementId];
            networkVoltage = elementState.voltage;
            networkCurrent = elementState.current;
        }
    }

    /// <summary>
    /// 元件值变化回调
    /// </summary>
    [Server]
    private void OnElementValueChanged(string elementName, float value)
    {
        if (elementName == elementId)
        {
            networkParameterValue = value;
        }
    }

    /// <summary>
    /// 电压变化钩子
    /// </summary>
    private void OnVoltageChanged(float oldValue, float newValue)
    {
        UpdateVisualVoltage(newValue);
        if (isClientOnly)
        {
            Debug.Log($"[{elementId}] 电压更新: {newValue:F3}V");
        }
    }

    /// <summary>
    /// 电流变化钩子
    /// </summary>
    private void OnCurrentChanged(float oldValue, float newValue)
    {
        UpdateVisualCurrent(newValue);
        if (isClientOnly)
        {
            Debug.Log($"[{elementId}] 电流更新: {newValue:F3}A");
        }
    }

    /// <summary>
    /// 参数值变化钩子
    /// </summary>
    private void OnParameterValueChanged(float oldValue, float newValue)
    {
        parameterValue = newValue;
        UpdateVisualParameters();
        if (isClientOnly)
        {
            Debug.Log($"[{elementId}] 参数更新: {newValue}");
        }
    }

    /// <summary>
    /// 更新电压可视化
    /// </summary>
    private void UpdateVisualVoltage(float voltage)
    {
        // 更新发光效果强度
        Renderer renderer = elementModel?.GetComponent<Renderer>();
        if (renderer != null)
        {
            float intensity = Mathf.Clamp01(Mathf.Abs(voltage) / 10f); // 假设10V为满量程
            Color emissionColor = GetElementColor(elementType) * intensity;
            renderer.material.SetColor("_EmissionColor", emissionColor);
        }

        // 更新UI显示
        UpdateElementUI("Voltage", voltage);
    }

    /// <summary>
    /// 更新电流可视化
    /// </summary>
    private void UpdateVisualCurrent(float current)
    {
        // 更新连接线宽度表示电流大小
        if (connectionLine != null)
        {
            float lineWidth = Mathf.Clamp(Mathf.Abs(current) * 10f, 0.01f, 0.2f);
            connectionLine.startWidth = lineWidth;
            connectionLine.endWidth = lineWidth;

            // 根据电流方向设置颜色
            Color lineColor = current >= 0 ? Color.red : Color.blue;
            connectionLine.material.SetColor("_Color", lineColor);
        }

        UpdateElementUI("Current", current);
    }

    /// <summary>
    /// 更新参数可视化
    /// </summary>
    private void UpdateVisualParameters()
    {
        // 更新元件标签显示
        UpdateElementUI("Parameter", parameterValue);
    }

    /// <summary>
    /// 更新元件UI显示
    /// </summary>
    private void UpdateElementUI(string property, float value)
    {
        // 查找或创建UI标签
        var labelObj = transform.Find("UILabel");
        if (labelObj == null)
        {
            GameObject labelGO = new GameObject("UILabel");
            labelGO.transform.SetParent(transform);
            labelGO.transform.localPosition = Vector3.up * 0.5f;

            var textMesh = labelGO.AddComponent<TextMesh>();
            textMesh.fontSize = 12;
            textMesh.anchor = TextAnchor.MiddleCenter;
            labelObj = labelGO.transform;
        }

        var textMeshComp = labelObj.GetComponent<TextMesh>();
        if (textMeshComp != null)
        {
            string unit = GetUnitForProperty(property, elementType);
            textMeshComp.text = $"{property}: {value:F2}{unit}";
        }
    }

    /// <summary>
    /// 获取属性单位
    /// </summary>
    private string GetUnitForProperty(string property, ElementType type)
    {
        switch (property)
        {
            case "Voltage": return "V";
            case "Current": return "A";
            case "Parameter":
                switch (type)
                {
                    case ElementType.Resistor: return "Ω";
                    case ElementType.Capacitor: return "F";
                    case ElementType.Inductor: return "H";
                    default: return "";
                }
            default: return "";
        }
    }

    /// <summary>
    /// 修改元件参数
    /// </summary>
    [Server]
    public void ModifyParameter(float newValue)
    {
        parameterValue = newValue;
        networkParameterValue = newValue;

        // 通知物理引擎参数变更
        // 这里可以调用物理引擎的相应方法
        Debug.Log($"元件 {elementId} 参数已修改为: {newValue}");
    }

    /// <summary>
    /// 获取当前状态
    /// </summary>
    public CircuitPhysicsEngine.ElementState GetCurrentState()
    {
        return new CircuitPhysicsEngine.ElementState
        {
            type = elementType.ToString(),
            voltage = networkVoltage,
            current = networkCurrent,
            power = Mathf.Abs(networkVoltage * networkCurrent),
            connectionPoints = new Vector3[2] // 简化处理
        };
    }

    protected override void OnCustomDataReceived(string jsonData)
    {
        base.OnCustomDataReceived(jsonData);
        // 处理自定义同步数据
    }

    private void OnDestroy()
    {
        if (physicsEngine != null)
        {
            physicsEngine.OnCircuitStateChanged -= OnCircuitStateChanged;
            physicsEngine.OnElementValueChanged -= OnElementValueChanged;
        }
    }
}
