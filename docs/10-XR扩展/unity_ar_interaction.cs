using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using System.Collections.Generic;

/// <summary>
/// Unity AR交互主控制器
/// 处理AR场景中的所有交互逻辑和硬件集成
/// </summary>
[RequireComponent(typeof(ARSessionOrigin))]
[RequireComponent(typeof(ARRaycastManager))]
public class ARInteraction : MonoBehaviour
{
    [Header("AR组件引用")]
    [SerializeField] private ARSessionOrigin arOrigin;
    [SerializeField] private ARRaycastManager raycastManager;
    [SerializeField] private ARPlaneManager planeManager;
    [SerializeField] private ARCameraManager cameraManager;

    [Header("交互设置")]
    [SerializeField] private float interactionDistance = 10f;
    [SerializeField] private LayerMask interactableLayer = 1 << 8; // 默认第8层为可交互对象
    [SerializeField] private Material highlightMaterial;

    [Header("硬件控制")]
    [SerializeField] private bool enableHardwareControl = true;
    [SerializeField] private string hardwareControllerName = "Arduino";

    private Camera arCamera;
    private GameObject selectedObject;
    private Material originalMaterial;
    private List<ARRaycastHit> raycastHits = new List<ARRaycastHit>();
    private Vector2 touchPosition;
    private bool isDragging = false;

    // 硬件控制相关
    private HardwareController hardwareController;
    
    void Awake()
    {
        // 获取AR组件
        if (arOrigin == null)
            arOrigin = GetComponent<ARSessionOrigin>();
            
        if (raycastManager == null)
            raycastManager = GetComponent<ARRaycastManager>();
            
        arCamera = arOrigin.camera;
        
        // 初始化硬件控制器
        if (enableHardwareControl)
        {
            InitializeHardwareController();
        }
    }

    void Start()
    {
        // 确保AR Session已启动
        StartCoroutine(StartARSession());
    }

    void Update()
    {
        HandleTouchInput();
        HandleGestures();
        UpdateHardwareState();
    }

    private System.Collections.IEnumerator StartARSession()
    {
        // 等待AR Session准备就绪
        yield return new WaitForSeconds(1f);
        
        // 启用平面检测
        if (planeManager != null)
        {
            planeManager.enabled = true;
        }
        
        Debug.Log("AR Session已启动");
    }

    /// <summary>
    /// 处理触摸输入
    /// </summary>
    private void HandleTouchInput()
    {
        if (Input.touchCount > 0)
        {
            Touch touch = Input.GetTouch(0);
            touchPosition = touch.position;

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
    }

    /// <summary>
    /// 处理触摸开始
    /// </summary>
    private void HandleTouchBegan(Touch touch)
    {
        // 执行AR射线检测
        if (raycastManager.Raycast(touchPosition, raycastHits, TrackableType.PlaneWithinPolygon))
        {
            TrackableHit hit = raycastHits[0];
            
            // 检测是否点击到可交互对象
            RaycastHit physicsHit;
            Ray ray = arCamera.ScreenPointToRay(touchPosition);
            
            if (Physics.Raycast(ray, out physicsHit, interactionDistance, interactableLayer))
            {
                SelectObject(physicsHit.collider.gameObject);
            }
            else
            {
                // 如果没有点击到对象，在点击位置放置新对象
                PlaceNewObject(hit.pose.position);
            }
        }
    }

    /// <summary>
    /// 处理触摸移动
    /// </summary>
    private void HandleTouchMoved(Touch touch)
    {
        if (isDragging && selectedObject != null)
        {
            // 拖拽对象
            if (raycastManager.Raycast(touchPosition, raycastHits, TrackableType.PlaneWithinPolygon))
            {
                Vector3 newPosition = raycastHits[0].pose.position;
                selectedObject.transform.position = Vector3.Lerp(selectedObject.transform.position, newPosition, 0.5f);
                
                // 发送位置更新到硬件
                if (hardwareController != null)
                {
                    hardwareController.SendObjectPosition(selectedObject.transform.position);
                }
            }
        }
    }

    /// <summary>
    /// 处理触摸结束
    /// </summary>
    private void HandleTouchEnded(Touch touch)
    {
        if (isDragging)
        {
            DeselectObject();
        }
    }

    /// <summary>
    /// 处理手势输入
    /// </summary>
    private void HandleGestures()
    {
        // 双指缩放手势
        if (Input.touchCount == 2)
        {
            Touch touch1 = Input.GetTouch(0);
            Touch touch2 = Input.GetTouch(1);

            if (touch1.phase == TouchPhase.Moved || touch2.phase == TouchPhase.Moved)
            {
                float currentDistance = Vector2.Distance(touch1.position, touch2.position);
                float previousDistance = Vector2.Distance(
                    touch1.position - touch1.deltaPosition,
                    touch2.position - touch2.deltaPosition
                );

                float deltaDistance = currentDistance - previousDistance;
                ScaleSelectedObject(deltaDistance * 0.01f);
            }
        }

        // 旋转手势（三指）
        if (Input.touchCount == 3)
        {
            Touch touch = Input.GetTouch(0);
            if (touch.phase == TouchPhase.Moved && selectedObject != null)
            {
                selectedObject.transform.Rotate(Vector3.up, touch.deltaPosition.x * 0.5f);
            }
        }
    }

    /// <summary>
    /// 选择对象
    /// </summary>
    private void SelectObject(GameObject obj)
    {
        if (selectedObject != null)
        {
            DeselectObject();
        }

        selectedObject = obj;
        isDragging = true;

        // 高亮显示
        Renderer renderer = selectedObject.GetComponent<Renderer>();
        if (renderer != null)
        {
            originalMaterial = renderer.material;
            renderer.material = highlightMaterial;
        }

        Debug.Log($"选择了对象: {selectedObject.name}");

        // 发送选择事件到硬件
        if (hardwareController != null)
        {
            hardwareController.ObjectSelected(selectedObject.name);
        }

        // 发送消息到Web端
        SendMessageToWeb("ObjectSelected", selectedObject.name);
    }

    /// <summary>
    /// 取消选择对象
    /// </summary>
    private void DeselectObject()
    {
        if (selectedObject != null)
        {
            // 恢复原始材质
            Renderer renderer = selectedObject.GetComponent<Renderer>();
            if (renderer != null && originalMaterial != null)
            {
                renderer.material = originalMaterial;
            }

            // 发送取消选择事件
            if (hardwareController != null)
            {
                hardwareController.ObjectDeselected(selectedObject.name);
            }

            SendMessageToWeb("ObjectDeselected", selectedObject.name);
            selectedObject = null;
        }

        isDragging = false;
    }

    /// <summary>
    /// 在指定位置放置新对象
    /// </summary>
    private void PlaceNewObject(Vector3 position)
    {
        // 创建默认的交互对象
        GameObject newObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
        newObject.transform.position = position + Vector3.up * 0.1f;
        newObject.transform.localScale = Vector3.one * 0.1f;
        
        // 添加碰撞体和刚体
        newObject.AddComponent<BoxCollider>();
        Rigidbody rb = newObject.AddComponent<Rigidbody>();
        rb.mass = 1f;
        
        // 设置为可交互对象
        newObject.layer = 8; // 使用第8层
        
        // 添加交互脚本
        newObject.AddComponent<ARInteractableObject>();
        
        Debug.Log($"放置新对象: {newObject.name} at {position}");
        
        // 发送放置事件
        SendMessageToWeb("ObjectPlaced", newObject.name);
    }

    /// <summary>
    /// 缩放选中的对象
    /// </summary>
    private void ScaleSelectedObject(float scaleFactor)
    {
        if (selectedObject != null)
        {
            Vector3 newScale = selectedObject.transform.localScale * (1 + scaleFactor);
            newScale = Vector3.Max(newScale, Vector3.one * 0.01f); // 最小缩放限制
            selectedObject.transform.localScale = newScale;
            
            // 发送缩放事件
            if (hardwareController != null)
            {
                hardwareController.ObjectScaled(selectedObject.name, newScale);
            }
            
            SendMessageToWeb("ObjectScaled", $"{selectedObject.name}:{newScale}");
        }
    }

    /// <summary>
    /// 初始化硬件控制器
    /// </summary>
    private void InitializeHardwareController()
    {
        try
        {
            hardwareController = new HardwareController(hardwareControllerName);
            hardwareController.OnHardwareEvent += HandleHardwareEvent;
            Debug.Log($"硬件控制器初始化成功: {hardwareControllerName}");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"硬件控制器初始化失败: {e.Message}");
            enableHardwareControl = false;
        }
    }

    /// <summary>
    /// 更新硬件状态
    /// </summary>
    private void UpdateHardwareState()
    {
        if (hardwareController != null && enableHardwareControl)
        {
            hardwareController.Update();
        }
    }

    /// <summary>
    /// 处理硬件事件
    /// </summary>
    private void HandleHardwareEvent(string eventType, string eventData)
    {
        switch (eventType)
        {
            case "BUTTON_PRESSED":
                HandleHardwareButtonPress(eventData);
                break;
            case "SENSOR_DATA":
                HandleHardwareSensorData(eventData);
                break;
            case "COMMAND_RECEIVED":
                HandleHardwareCommand(eventData);
                break;
        }
    }

    /// <summary>
    /// 处理硬件按钮按下事件
    /// </summary>
    private void HandleHardwareButtonPress(string buttonId)
    {
        Debug.Log($"硬件按钮按下: {buttonId}");
        
        switch (buttonId)
        {
            case "BTN_A":
                // 切换LED状态
                if (hardwareController != null)
                {
                    hardwareController.ToggleLED();
                }
                break;
            case "BTN_B":
                // 开始/停止电机
                if (hardwareController != null)
                {
                    hardwareController.ToggleMotor();
                }
                break;
            case "BTN_C":
                // 重置场景
                ResetScene();
                break;
        }
    }

    /// <summary>
    /// 处理硬件传感器数据
    /// </summary>
    private void HandleHardwareSensorData(string sensorData)
    {
        // 解析传感器数据并应用到AR场景
        // 例如：根据陀螺仪数据旋转对象
        Debug.Log($"接收到传感器数据: {sensorData}");
    }

    /// <summary>
    /// 处理硬件命令
    /// </summary>
    private void HandleHardwareCommand(string command)
    {
        Debug.Log($"接收到硬件命令: {command}");
        
        // 执行相应的AR操作
        switch (command.ToUpper())
        {
            case "TOGGLE_LED":
                if (selectedObject != null)
                {
                    ToggleObjectHighlight(selectedObject);
                }
                break;
            case "START_MOTOR":
                if (selectedObject != null)
                {
                    ApplyRotationForce(selectedObject, Vector3.up, 100f);
                }
                break;
        }
    }

    /// <summary>
    /// 切换对象高亮
    /// </summary>
    private void ToggleObjectHighlight(GameObject obj)
    {
        Renderer renderer = obj.GetComponent<Renderer>();
        if (renderer != null)
        {
            if (renderer.material == highlightMaterial)
            {
                renderer.material = originalMaterial ?? renderer.material;
            }
            else
            {
                originalMaterial = renderer.material;
                renderer.material = highlightMaterial;
            }
        }
    }

    /// <summary>
    /// 对对象施加旋转力
    /// </summary>
    private void ApplyRotationForce(GameObject obj, Vector3 axis, float force)
    {
        Rigidbody rb = obj.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.AddTorque(axis * force);
        }
    }

    /// <summary>
    /// 重置场景
    /// </summary>
    private void ResetScene()
    {
        // 清除所有放置的对象
        ARInteractableObject[] objects = FindObjectsOfType<ARInteractableObject>();
        foreach (ARInteractableObject obj in objects)
        {
            Destroy(obj.gameObject);
        }
        
        selectedObject = null;
        isDragging = false;
        
        Debug.Log("场景已重置");
        SendMessageToWeb("SceneReset", "");
    }

    /// <summary>
    /// 发送消息到Web端
    /// </summary>
    private void SendMessageToWeb(string messageType, string messageData)
    {
        // 通过Unity的WebGL接口发送消息到JavaScript
        #if UNITY_WEBGL && !UNITY_EDITOR
        Application.ExternalCall("unitySendMessage", messageType, messageData);
        #endif
        
        // 也可以通过WebSocket发送（如果已实现）
        Debug.Log($"发送到Web: {messageType} - {messageData}");
    }

    /// <summary>
    /// 从Web端接收消息
    /// </summary>
    public void ReceiveWebMessage(string messageType, string messageData)
    {
        Debug.Log($"从Web接收: {messageType} - {messageData}");
        
        switch (messageType)
        {
            case "SelectObject":
                // 选择指定对象
                GameObject obj = GameObject.Find(messageData);
                if (obj != null)
                {
                    SelectObject(obj);
                }
                break;
            case "PlaceObject":
                // 在当前位置放置对象
                if (raycastManager.Raycast(touchPosition, raycastHits, TrackableType.PlaneWithinPolygon))
                {
                    PlaceNewObject(raycastHits[0].pose.position);
                }
                break;
            case "ToggleHardware":
                // 切换硬件控制
                enableHardwareControl = !enableHardwareControl;
                if (enableHardwareControl && hardwareController == null)
                {
                    InitializeHardwareController();
                }
                break;
        }
    }

    void OnDestroy()
    {
        if (hardwareController != null)
        {
            hardwareController.Dispose();
        }
    }
}

/// <summary>
/// 可交互的AR对象组件
/// </summary>
public class ARInteractableObject : MonoBehaviour
{
    [Header("对象属性")]
    public string objectId;
    public float mass = 1f;
    public bool isGrabbable = true;
    public bool isScalable = true;
    public bool isRotatable = true;

    [Header("物理属性")]
    public PhysicMaterial physicMaterial;
    public float friction = 0.5f;
    public float bounciness = 0.2f;

    void Awake()
    {
        // 确保有碰撞体
        if (GetComponent<Collider>() == null)
        {
            gameObject.AddComponent<BoxCollider>();
        }

        // 确保有刚体
        if (GetComponent<Rigidbody>() == null)
        {
            Rigidbody rb = gameObject.AddComponent<Rigidbody>();
            rb.mass = mass;
        }

        // 设置物理材质
        if (physicMaterial == null)
        {
            physicMaterial = new PhysicMaterial();
            physicMaterial.dynamicFriction = friction;
            physicMaterial.staticFriction = friction;
            physicMaterial.bounciness = bounciness;
        }

        Collider collider = GetComponent<Collider>();
        if (collider != null)
        {
            collider.material = physicMaterial;
        }

        // 生成唯一ID
        if (string.IsNullOrEmpty(objectId))
        {
            objectId = $"ARObject_{GetInstanceID()}";
        }
    }

    void OnMouseDown()
    {
        // 鼠标点击事件（用于编辑器测试）
        #if UNITY_EDITOR
        Debug.Log($"对象被点击: {objectId}");
        #endif
    }
}

/// <summary>
/// 硬件控制器类
/// 处理与外部硬件设备的通信
/// </summary>
public class HardwareController : System.IDisposable
{
    public delegate void HardwareEventHandler(string eventType, string eventData);
    public event HardwareEventHandler OnHardwareEvent;

    private string deviceName;
    private bool isConnected = false;
    private System.IO.Ports.SerialPort serialPort;

    public HardwareController(string deviceName)
    {
        this.deviceName = deviceName;
        ConnectToDevice();
    }

    private void ConnectToDevice()
    {
        try
        {
            // 尝试连接到串口设备
            #if UNITY_EDITOR || UNITY_STANDALONE
            string[] ports = System.IO.Ports.SerialPort.GetPortNames();
            foreach (string port in ports)
            {
                try
                {
                    serialPort = new System.IO.Ports.SerialPort(port, 9600);
                    serialPort.Open();
                    serialPort.ReadTimeout = 1000;
                    isConnected = true;
                    Debug.Log($"已连接到硬件设备: {port}");
                    break;
                }
                catch (System.Exception)
                {
                    continue;
                }
            }
            #endif

            if (!isConnected)
            {
                Debug.LogWarning("未找到硬件设备，使用模拟模式");
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"硬件连接失败: {e.Message}");
        }
    }

    public void Update()
    {
        if (isConnected && serialPort != null && serialPort.IsOpen)
        {
            try
            {
                // 读取串口数据
                if (serialPort.BytesToRead > 0)
                {
                    string data = serialPort.ReadLine();
                    ProcessHardwareData(data);
                }
            }
            catch (System.Exception e)
            {
                Debug.LogError($"读取硬件数据失败: {e.Message}");
            }
        }
        else
        {
            // 模拟硬件输入（用于测试）
            SimulateHardwareInput();
        }
    }

    private void ProcessHardwareData(string data)
    {
        // 解析硬件数据
        if (data.StartsWith("BTN_"))
        {
            OnHardwareEvent?.Invoke("BUTTON_PRESSED", data.Trim());
        }
        else if (data.StartsWith("SENSOR_"))
        {
            OnHardwareEvent?.Invoke("SENSOR_DATA", data.Trim());
        }
        else if (data.StartsWith("CMD_"))
        {
            OnHardwareEvent?.Invoke("COMMAND_RECEIVED", data.Substring(4).Trim());
        }
    }

    private void SimulateHardwareInput()
    {
        // 模拟按键输入（仅用于测试）
        if (Input.GetKeyDown(KeyCode.Space))
        {
            OnHardwareEvent?.Invoke("BUTTON_PRESSED", "BTN_A");
        }
        if (Input.GetKeyDown(KeyCode.Return))
        {
            OnHardwareEvent?.Invoke("BUTTON_PRESSED", "BTN_B");
        }
    }

    public void ToggleLED()
    {
        SendCommand("TOGGLE_LED");
        Debug.Log("LED状态已切换");
    }

    public void ToggleMotor()
    {
        SendCommand("TOGGLE_MOTOR");
        Debug.Log("电机状态已切换");
    }

    public void ObjectSelected(string objectName)
    {
        SendCommand($"SELECT:{objectName}");
    }

    public void ObjectDeselected(string objectName)
    {
        SendCommand($"DESELECT:{objectName}");
    }

    public void ObjectScaled(string objectName, Vector3 scale)
    {
        SendCommand($"SCALE:{objectName}:{scale.x:F2},{scale.y:F2},{scale.z:F2}");
    }

    public void SendObjectPosition(Vector3 position)
    {
        SendCommand($"POSITION:{position.x:F2},{position.y:F2},{position.z:F2}");
    }

    private void SendCommand(string command)
    {
        if (isConnected && serialPort != null && serialPort.IsOpen)
        {
            try
            {
                serialPort.WriteLine(command);
            }
            catch (System.Exception e)
            {
                Debug.LogError($"发送命令失败: {e.Message}");
            }
        }
        else
        {
            // 模拟发送（用于测试）
            Debug.Log($"模拟发送命令: {command}");
        }
    }

    public void Dispose()
    {
        if (serialPort != null && serialPort.IsOpen)
        {
            serialPort.Close();
            serialPort.Dispose();
        }
    }
}