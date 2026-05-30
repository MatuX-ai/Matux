using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 虚实结合接线指引系统
/// 实现AR虚拟连线与实际硬件的对应关系
/// </summary>
public class WiringGuide : MonoBehaviour
{
    [Header("接线配置")]
    [SerializeField] private Material wireMaterial;
    [SerializeField] private Color correctConnectionColor = Color.green;
    [SerializeField] private Color incorrectConnectionColor = Color.red;
    [SerializeField] private float wireThickness = 0.005f;
    
    [Header("检测设置")]
    [SerializeField] private float connectionDistanceThreshold = 0.05f;
    [SerializeField] private bool enableRealHardwareDetection = true;
    
    // 私有字段
    private List<WireConnection> activeConnections = new List<WireConnection>();
    private Dictionary<Transform, List<WireConnection>> connectionMap = new Dictionary<Transform, List<WireConnection>>();
    
    // 事件委托
    public delegate void WiringEventHandler(WiringEventType type, WireConnection connection);
    public event WiringEventHandler OnWiringEvent;
    
    public enum WiringEventType
    {
        ConnectionStarted,
        ConnectionCompleted,
        ConnectionValidated,
        ConnectionRemoved,
        ErrorDetected
    }
    
    /// <summary>
    /// 连接信息结构
    /// </summary>
    [System.Serializable]
    public class WireConnection
    {
        public Transform startPoint;
        public Transform endPoint;
        public GameObject wireObject;
        public LineRenderer lineRenderer;
        public bool isValid;
        public string connectionType;
        public float length;
        
        public WireConnection(Transform start, Transform end, string type = "Generic")
        {
            startPoint = start;
            endPoint = end;
            connectionType = type;
            isValid = false;
        }
    }
    
    void Start()
    {
        // 初始化材质
        if (wireMaterial == null)
        {
            CreateDefaultWireMaterial();
        }
    }
    
    /// <summary>
    /// 创建默认连线材质
    /// </summary>
    private void CreateDefaultWireMaterial()
    {
        wireMaterial = new Material(Shader.Find("Standard"));
        wireMaterial.color = Color.yellow;
    }
    
    /// <summary>
    /// 开始创建连接
    /// </summary>
    public WireConnection StartConnection(Transform startPoint, string connectionType = "Generic")
    {
        WireConnection connection = new WireConnection(startPoint, null, connectionType);
        activeConnections.Add(connection);
        
        // 创建可视化的连线
        CreateWireVisualization(connection);
        
        OnWiringEvent?.Invoke(WiringEventType.ConnectionStarted, connection);
        Debug.Log($"开始连接: {startPoint.name} -> ?");
        
        return connection;
    }
    
    /// <summary>
    /// 完成连接
    /// </summary>
    public bool CompleteConnection(WireConnection connection, Transform endPoint)
    {
        if (connection == null || endPoint == null) return false;
        
        connection.endPoint = endPoint;
        connection.length = Vector3.Distance(connection.startPoint.position, endPoint.position);
        
        // 更新连线可视化
        UpdateWireVisualization(connection);
        
        // 验证连接
        bool isValid = ValidateConnection(connection);
        connection.isValid = isValid;
        
        // 设置颜色
        SetWireColor(connection, isValid);
        
        OnWiringEvent?.Invoke(WiringEventType.ConnectionCompleted, connection);
        Debug.Log($"连接完成: {connection.startPoint.name} -> {endPoint.name} ({(isValid ? "有效" : "无效")})");
        
        return true;
    }
    
    /// <summary>
    /// 验证连接是否正确
    /// </summary>
    private bool ValidateConnection(WireConnection connection)
    {
        if (connection.startPoint == null || connection.endPoint == null)
            return false;
        
        // 检查距离
        float distance = Vector3.Distance(connection.startPoint.position, connection.endPoint.position);
        if (distance > connectionDistanceThreshold)
        {
            return false;
        }
        
        // 检查连接点类型匹配
        string startType = GetConnectionPointType(connection.startPoint);
        string endType = GetConnectionPointType(connection.endPoint);
        
        return AreConnectionTypesCompatible(startType, endType, connection.connectionType);
    }
    
    /// <summary>
    /// 获取连接点类型
    /// </summary>
    private string GetConnectionPointType(Transform point)
    {
        // 可以通过标签、名称或其他方式确定连接点类型
        if (point.name.Contains("VCC") || point.name.Contains("Power"))
            return "Power";
        if (point.name.Contains("GND") || point.name.Contains("Ground"))
            return "Ground";
        if (point.name.Contains("DATA") || point.name.Contains("Signal"))
            return "Data";
        if (point.name.Contains("Pin"))
            return "Generic";
        
        return "Unknown";
    }
    
    /// <summary>
    /// 检查连接类型是否兼容
    /// </summary>
    private bool AreConnectionTypesCompatible(string type1, string type2, string connectionType)
    {
        // 基本的连接规则
        switch (connectionType)
        {
            case "Power":
                return (type1 == "Power" && type2 == "Power") ||
                       (type1 == "VCC" && type2 == "VCC");
            case "Ground":
                return (type1 == "Ground" && type2 == "Ground") ||
                       (type1 == "GND" && type2 == "GND");
            case "Data":
                return type1 == "Data" && type2 == "Data";
            default:
                return type1 != "Unknown" && type2 != "Unknown";
        }
    }
    
    /// <summary>
    /// 创建连线可视化
    /// </summary>
    private void CreateWireVisualization(WireConnection connection)
    {
        GameObject wireObj = new GameObject($"Wire_{connection.GetHashCode()}");
        connection.wireObject = wireObj;
        
        LineRenderer lineRenderer = wireObj.AddComponent<LineRenderer>();
        lineRenderer.material = wireMaterial;
        lineRenderer.widthMultiplier = wireThickness;
        lineRenderer.positionCount = 2;
        lineRenderer.useWorldSpace = true;
        
        connection.lineRenderer = lineRenderer;
        
        // 设置初始位置
        UpdateWireVisualization(connection);
    }
    
    /// <summary>
    /// 更新连线可视化
    /// </summary>
    private void UpdateWireVisualization(WireConnection connection)
    {
        if (connection.lineRenderer == null || connection.startPoint == null) return;
        
        Vector3 startPos = connection.startPoint.position;
        Vector3 endPos = connection.endPoint != null ? 
            connection.endPoint.position : 
            startPos + Vector3.forward * 0.1f; // 临时终点
            
        connection.lineRenderer.SetPosition(0, startPos);
        connection.lineRenderer.SetPosition(1, endPos);
    }
    
    /// <summary>
    /// 设置连线颜色
    /// </summary>
    private void SetWireColor(WireConnection connection, bool isValid)
    {
        if (connection.lineRenderer == null) return;
        
        Color color = isValid ? correctConnectionColor : incorrectConnectionColor;
        connection.lineRenderer.startColor = color;
        connection.lineRenderer.endColor = color;
    }
    
    /// <summary>
    /// 移除连接
    /// </summary>
    public void RemoveConnection(WireConnection connection)
    {
        if (activeConnections.Contains(connection))
        {
            activeConnections.Remove(connection);
            
            if (connection.wireObject != null)
            {
                Destroy(connection.wireObject);
            }
            
            OnWiringEvent?.Invoke(WiringEventType.ConnectionRemoved, connection);
            Debug.Log("连接已移除");
        }
    }
    
    /// <summary>
    /// 清除所有连接
    /// </summary>
    public void ClearAllConnections()
    {
        foreach (var connection in activeConnections)
        {
            if (connection.wireObject != null)
            {
                Destroy(connection.wireObject);
            }
        }
        activeConnections.Clear();
        Debug.Log("所有连接已清除");
    }
    
    /// <summary>
    /// 获取指定点的所有连接
    /// </summary>
    public List<WireConnection> GetConnectionsForPoint(Transform point)
    {
        List<WireConnection> connections = new List<WireConnection>();
        
        foreach (var connection in activeConnections)
        {
            if (connection.startPoint == point || connection.endPoint == point)
            {
                connections.Add(connection);
            }
        }
        
        return connections;
    }
    
    /// <summary>
    /// 检查两个点之间是否已有连接
    /// </summary>
    public bool HasConnectionBetween(Transform point1, Transform point2)
    {
        foreach (var connection in activeConnections)
        {
            bool isConnected = (connection.startPoint == point1 && connection.endPoint == point2) ||
                              (connection.startPoint == point2 && connection.endPoint == point1);
            if (isConnected)
            {
                return true;
            }
        }
        return false;
    }
    
    /// <summary>
    /// 获取连接统计信息
    /// </summary>
    public WiringStatistics GetStatistics()
    {
        int totalConnections = activeConnections.Count;
        int validConnections = activeConnections.Count(c => c.isValid);
        int invalidConnections = totalConnections - validConnections;
        
        return new WiringStatistics
        {
            TotalConnections = totalConnections,
            ValidConnections = validConnections,
            InvalidConnections = invalidConnections,
            SuccessRate = totalConnections > 0 ? (float)validConnections / totalConnections : 0f
        };
    }
    
    /// <summary>
    /// 连接统计信息结构体
    /// </summary>
    [System.Serializable]
    public struct WiringStatistics
    {
        public int TotalConnections;
        public int ValidConnections;
        public int InvalidConnections;
        public float SuccessRate;
    }
    
    /// <summary>
    /// 实时检测硬件连接状态
    /// </summary>
    void Update()
    {
        if (enableRealHardwareDetection)
        {
            UpdateConnectionValidation();
        }
    }
    
    /// <summary>
    /// 更新连接验证状态
    /// </summary>
    private void UpdateConnectionValidation()
    {
        foreach (var connection in activeConnections)
        {
            if (connection.endPoint != null)
            {
                bool currentValidity = ValidateConnection(connection);
                if (connection.isValid != currentValidity)
                {
                    connection.isValid = currentValidity;
                    SetWireColor(connection, currentValidity);
                    OnWiringEvent?.Invoke(WiringEventType.ConnectionValidated, connection);
                }
            }
        }
    }
    
    /// <summary>
    /// 高亮显示所有连接
    /// </summary>
    public void HighlightAllConnections(bool highlight)
    {
        foreach (var connection in activeConnections)
        {
            if (connection.lineRenderer != null)
            {
                Color color = highlight ? Color.white : 
                    (connection.isValid ? correctConnectionColor : incorrectConnectionColor);
                connection.lineRenderer.startColor = color;
                connection.lineRenderer.endColor = color;
            }
        }
    }
}