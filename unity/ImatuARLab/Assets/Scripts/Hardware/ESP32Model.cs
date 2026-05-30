using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// ESP32开发板模型控制脚本
/// 管理ESP32硬件模型的显示、交互和物理行为
/// </summary>
public class ESP32Model : MonoBehaviour
{
    [Header("硬件配置")]
    [SerializeField] private string modelName = "ESP32-DevKitC";
    [SerializeField] private string firmwareVersion = "1.0.0";
    
    [Header("物理属性")]
    [SerializeField] private float mass = 0.05f; // 50克
    [SerializeField] private float sizeScale = 1.0f;
    
    [Header("连接点配置")]
    [SerializeField] private Transform[] connectionPoints; // 连接点引用
    [SerializeField] private Material highlightMaterial; // 高亮材质
    
    // 私有字段
    private Rigidbody rigidbody;
    private Collider collider;
    private Renderer renderer;
    private Material originalMaterial;
    private bool isSelected = false;
    private bool isPlaced = false;
    
    // 事件委托
    public delegate void HardwareEventHandler(ESP32Model sender, HardwareEventType eventType);
    public event HardwareEventHandler OnHardwareEvent;
    
    public enum HardwareEventType
    {
        Selected,
        Deselected,
        Placed,
        Removed,
        Connected,
        Disconnected
    }
    
    void Awake()
    {
        InitializeComponents();
        SetupPhysics();
    }
    
    void Start()
    {
        // 初始状态设置
        SetInitialState();
    }
    
    /// <summary>
    /// 初始化组件引用
    /// </summary>
    private void InitializeComponents()
    {
        rigidbody = GetComponent<Rigidbody>();
        collider = GetComponent<Collider>();
        renderer = GetComponent<Renderer>();
        
        if (renderer != null)
        {
            originalMaterial = renderer.material;
        }
        
        // 查找连接点（如果没有手动指定）
        if (connectionPoints == null || connectionPoints.Length == 0)
        {
            FindConnectionPoints();
        }
    }
    
    /// <summary>
    /// 设置物理属性
    /// </summary>
    private void SetupPhysics()
    {
        if (rigidbody == null)
        {
            rigidbody = gameObject.AddComponent<Rigidbody>();
        }
        
        rigidbody.mass = mass;
        rigidbody.drag = 0.5f;
        rigidbody.angularDrag = 0.5f;
        rigidbody.useGravity = true;
        
        // 设置碰撞体
        if (collider == null)
        {
            BoxCollider boxCollider = gameObject.AddComponent<BoxCollider>();
            boxCollider.size = new Vector3(0.05f, 0.02f, 0.08f); // 大约50mm x 20mm x 80mm
        }
    }
    
    /// <summary>
    /// 查找连接点子对象
    /// </summary>
    private void FindConnectionPoints()
    {
        List<Transform> points = new List<Transform>();
        
        // 查找名为"ConnectionPoint"的子对象
        foreach (Transform child in transform)
        {
            if (child.name.Contains("Connection") || child.name.Contains("Pin"))
            {
                points.Add(child);
            }
        }
        
        connectionPoints = points.ToArray();
        Debug.Log($"找到 {connectionPoints.Length} 个连接点");
    }
    
    /// <summary>
    /// 设置初始状态
    /// </summary>
    private void SetInitialState()
    {
        // 禁用物理直到放置
        if (rigidbody != null)
        {
            rigidbody.isKinematic = true;
        }
        
        // 设置合适的层级
        gameObject.layer = LayerMask.NameToLayer("Hardware");
    }
    
    /// <summary>
    /// 选中硬件模型
    /// </summary>
    public void Select()
    {
        if (isSelected) return;
        
        isSelected = true;
        Highlight(true);
        OnHardwareEvent?.Invoke(this, HardwareEventType.Selected);
        Debug.Log($"{modelName} 已选中");
    }
    
    /// <summary>
    /// 取消选中硬件模型
    /// </summary>
    public void Deselect()
    {
        if (!isSelected) return;
        
        isSelected = false;
        Highlight(false);
        OnHardwareEvent?.Invoke(this, HardwareEventType.Deselected);
        Debug.Log($"{modelName} 已取消选中");
    }
    
    /// <summary>
    /// 放置硬件模型到场景中
    /// </summary>
    public void Place(Vector3 position, Quaternion rotation)
    {
        transform.position = position;
        transform.rotation = rotation;
        
        // 启用物理
        if (rigidbody != null)
        {
            rigidbody.isKinematic = false;
        }
        
        isPlaced = true;
        OnHardwareEvent?.Invoke(this, HardwareEventType.Placed);
        Debug.Log($"{modelName} 已放置到场景中");
    }
    
    /// <summary>
    /// 从场景中移除硬件模型
    /// </summary>
    public void Remove()
    {
        isPlaced = false;
        Deselect();
        OnHardwareEvent?.Invoke(this, HardwareEventType.Removed);
        
        // 销毁游戏对象
        Destroy(gameObject);
        Debug.Log($"{modelName} 已从场景中移除");
    }
    
    /// <summary>
    /// 高亮显示硬件模型
    /// </summary>
    private void Highlight(bool enable)
    {
        if (renderer == null) return;
        
        if (enable && highlightMaterial != null)
        {
            renderer.material = highlightMaterial;
        }
        else
        {
            renderer.material = originalMaterial;
        }
    }
    
    /// <summary>
    /// 检查是否可以连接到指定连接点
    /// </summary>
    public bool CanConnectTo(Transform targetPoint)
    {
        // 检查距离
        float distance = Vector3.Distance(transform.position, targetPoint.position);
        return distance < 0.1f; // 10cm内认为可以连接
    }
    
    /// <summary>
    /// 连接到另一个硬件组件
    /// </summary>
    public void ConnectTo(Transform targetPoint)
    {
        if (!CanConnectTo(targetPoint)) return;
        
        // 创建物理连接（例如关节）
        FixedJoint joint = gameObject.AddComponent<FixedJoint>();
        joint.connectedBody = targetPoint.GetComponent<Rigidbody>();
        
        OnHardwareEvent?.Invoke(this, HardwareEventType.Connected);
        Debug.Log($"{modelName} 已连接到目标组件");
    }
    
    /// <summary>
    /// 断开连接
    /// </summary>
    public void Disconnect()
    {
        FixedJoint joint = GetComponent<FixedJoint>();
        if (joint != null)
        {
            Destroy(joint);
            OnHardwareEvent?.Invoke(this, HardwareEventType.Disconnected);
            Debug.Log($"{modelName} 连接已断开");
        }
    }
    
    /// <summary>
    /// 获取连接点信息
    /// </summary>
    public Transform[] GetConnectionPoints()
    {
        return connectionPoints;
    }
    
    /// <summary>
    /// 获取硬件信息
    /// </summary>
    public HardwareInfo GetHardwareInfo()
    {
        return new HardwareInfo
        {
            ModelName = modelName,
            FirmwareVersion = firmwareVersion,
            Mass = mass,
            Position = transform.position,
            Rotation = transform.rotation,
            IsSelected = isSelected,
            IsPlaced = isPlaced
        };
    }
    
    /// <summary>
    /// 硬件信息结构体
    /// </summary>
    public struct HardwareInfo
    {
        public string ModelName;
        public string FirmwareVersion;
        public float Mass;
        public Vector3 Position;
        public Quaternion Rotation;
        public bool IsSelected;
        public bool IsPlaced;
    }
    
    /// <summary>
    /// 响应点击事件
    /// </summary>
    void OnMouseDown()
    {
        if (!isPlaced) return;
        
        if (isSelected)
        {
            Deselect();
        }
        else
        {
            Select();
        }
    }
    
    /// <summary>
    /// 响应鼠标悬停
    /// </summary>
    void OnMouseEnter()
    {
        if (!isPlaced || isSelected) return;
        Highlight(true);
    }
    
    void OnMouseExit()
    {
        if (!isPlaced || isSelected) return;
        Highlight(false);
    }
}