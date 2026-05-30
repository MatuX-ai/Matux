using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;

/// <summary>
/// 数字孪生后端通信客户端
/// 负责与FastAPI后端进行HTTP和WebSocket通信
/// </summary>
public class DigitalTwinBackendClient : MonoBehaviour
{
    [Header("后端配置")]
    [Tooltip("后端API基础URL")]
    public string baseUrl = "http://localhost:8000/api/v1";

    [Tooltip("会话ID")]
    public string sessionId = "";

    [Tooltip("用户ID")]
    public string userId = "user_1";

    [Tooltip("心跳间隔(秒)")]
    public float heartbeatInterval = 30f;

    // WebSocket连接
    private WebSocketClient webSocketClient;
    private bool isConnected = false;
    private float lastHeartbeatTime = 0f;

    // 本地状态缓存
    private Dictionary<string, CircuitElementState> localElementStates = new Dictionary<string, CircuitElementState>();
    private Dictionary<string, DeviceState> localDeviceStates = new Dictionary<string, DeviceState>();

    // 事件系统
    public Action<CircuitState> OnCircuitStateReceived;
    public Action<string, DeviceState> OnDeviceStateReceived;
    public Action<bool> OnConnectionStatusChanged;
    public Action<string> OnError;

    [Serializable]
    public class CircuitElementState
    {
        public string element_id;
        public string element_type;
        public float voltage;
        public float current;
        public float power;
        public string node1;
        public string node2;
        public float parameter_value;
        public string timestamp;
    }

    [Serializable]
    public class CircuitState
    {
        public string session_id;
        public CircuitElementState[] elements;
        public float total_power;
        public float total_current;
        public float simulation_time;
        public string timestamp;
    }

    [Serializable]
    public class DeviceState
    {
        public string device_id;
        public string device_type;
        public float voltage;
        public float current;
        public float temperature;
        public bool is_connected;
        public Dictionary<string, object> custom_properties;
        public string timestamp;
    }

    [Serializable]
    public class SessionInfo
    {
        public string session_id;
        public int host_user_id;
        public int participant_count;
        public string created_at;
        public bool is_active;
    }

    private void Start()
    {
        if (string.IsNullOrEmpty(sessionId))
        {
            sessionId = Guid.NewGuid().ToString();
        }

        ConnectToBackend();
    }

    private void Update()
    {
        // 心跳检测
        if (isConnected && Time.time - lastHeartbeatTime >= heartbeatInterval)
        {
            SendHeartbeat();
            lastHeartbeatTime = Time.time;
        }
    }

    /// <summary>
    /// 连接到后端服务
    /// </summary>
    public void ConnectToBackend()
    {
        StartCoroutine(ConnectCoroutine());
    }

    private IEnumerator ConnectCoroutine()
    {
        // 首先尝试创建会话
        yield return StartCoroutine(CreateSession());

        // 然后建立WebSocket连接
        string wsUrl = baseUrl.Replace("http", "ws").Replace("/api/v1", "") + $"/digital-twin/ws/session/{sessionId}?user_id={userId}";
        webSocketClient = new WebSocketClient(wsUrl);
        webSocketClient.OnConnected += OnWebSocketConnected;
        webSocketClient.OnDisconnected += OnWebSocketDisconnected;
        webSocketClient.OnMessageReceived += OnWebSocketMessageReceived;
        webSocketClient.OnError += OnWebSocketError;

        webSocketClient.Connect();
    }

    /// <summary>
    /// 创建会话
    /// </summary>
    private IEnumerator CreateSession()
    {
        string url = $"{baseUrl}/digital-twin/sessions";

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            request.SetRequestHeader("Content-Type", "application/json");

            // 添加认证头（这里简化处理）
            request.SetRequestHeader("Authorization", "Bearer your-jwt-token");

            string jsonData = JsonUtility.ToJson(new { }); // 空对象，让后端生成session_id
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string response = request.downloadHandler.text;
                var sessionInfo = JsonUtility.FromJson<SessionInfo>(response);
                sessionId = sessionInfo.session_id;
                Debug.Log($"会话创建成功: {sessionId}");
            }
            else
            {
                Debug.LogError($"创建会话失败: {request.error}");
                OnError?.Invoke($"创建会话失败: {request.error}");
            }
        }
    }

    /// <summary>
    /// WebSocket连接成功
    /// </summary>
    private void OnWebSocketConnected()
    {
        isConnected = true;
        OnConnectionStatusChanged?.Invoke(true);
        Debug.Log("成功连接到数字孪生后端");

        // 发送初始同步请求
        RequestInitialSync();
    }

    /// <summary>
    /// WebSocket断开连接
    /// </summary>
    private void OnWebSocketDisconnected()
    {
        isConnected = false;
        OnConnectionStatusChanged?.Invoke(false);
        Debug.Log("与数字孪生后端断开连接");
    }

    /// <summary>
    /// WebSocket错误
    /// </summary>
    private void OnWebSocketError(string error)
    {
        Debug.LogError($"WebSocket错误: {error}");
        OnError?.Invoke(error);
    }

    /// <summary>
    /// WebSocket消息接收
    /// </summary>
    private void OnWebSocketMessageReceived(string message)
    {
        try
        {
            var data = JsonConvert.DeserializeObject<Dictionary<string, object>>(message);
            string messageType = data["type"].ToString();

            switch (messageType)
            {
                case "circuit_state_broadcast":
                    HandleCircuitStateBroadcast(data);
                    break;

                case "device_state_broadcast":
                    HandleDeviceStateBroadcast(data);
                    break;

                case "sync_response":
                    HandleSyncResponse(data);
                    break;

                case "pong":
                    // 心跳响应
                    break;

                case "error":
                    string errorMsg = data["message"].ToString();
                    Debug.LogError($"后端错误: {errorMsg}");
                    OnError?.Invoke(errorMsg);
                    break;
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"解析WebSocket消息失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 处理电路状态广播
    /// </summary>
    private void HandleCircuitStateBroadcast(Dictionary<string, object> data)
    {
        try
        {
            string stateJson = JsonConvert.SerializeObject(data["state"]);
            var circuitState = JsonConvert.DeserializeObject<CircuitState>(stateJson);

            // 更新本地缓存
            if (circuitState.elements != null)
            {
                foreach (var element in circuitState.elements)
                {
                    localElementStates[element.element_id] = element;
                }
            }

            OnCircuitStateReceived?.Invoke(circuitState);
            Debug.Log($"接收到电路状态更新，元件数: {circuitState.elements?.Length ?? 0}");
        }
        catch (Exception ex)
        {
            Debug.LogError($"处理电路状态广播失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 处理设备状态广播
    /// </summary>
    private void HandleDeviceStateBroadcast(Dictionary<string, object> data)
    {
        try
        {
            string deviceId = data["device_id"].ToString();
            string stateJson = JsonConvert.SerializeObject(data["state"]);
            var deviceState = JsonConvert.DeserializeObject<DeviceState>(stateJson);

            localDeviceStates[deviceId] = deviceState;
            OnDeviceStateReceived?.Invoke(deviceId, deviceState);

            Debug.Log($"设备状态更新: {deviceId} - V:{deviceState.voltage}V, I:{deviceState.current}A");
        }
        catch (Exception ex)
        {
            Debug.LogError($"处理设备状态广播失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 处理同步响应
    /// </summary>
    private void HandleSyncResponse(Dictionary<string, object> data)
    {
        try
        {
            // 处理电路状态
            if (data.ContainsKey("circuit_state") && data["circuit_state"] != null)
            {
                string circuitJson = JsonConvert.SerializeObject(data["circuit_state"]);
                var circuitState = JsonConvert.DeserializeObject<CircuitState>(circuitJson);
                OnCircuitStateReceived?.Invoke(circuitState);
            }

            // 处理设备状态
            if (data.ContainsKey("device_states"))
            {
                var deviceStates = JsonConvert.DeserializeObject<List<Dictionary<string, object>>>(
                    JsonConvert.SerializeObject(data["device_states"]));

                foreach (var deviceData in deviceStates)
                {
                    string deviceJson = JsonConvert.SerializeObject(deviceData);
                    var deviceState = JsonConvert.DeserializeObject<DeviceState>(deviceJson);
                    localDeviceStates[deviceState.device_id] = deviceState;
                    OnDeviceStateReceived?.Invoke(deviceState.device_id, deviceState);
                }
            }

            Debug.Log("初始同步完成");
        }
        catch (Exception ex)
        {
            Debug.LogError($"处理同步响应失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 发送电路状态更新
    /// </summary>
    public void SendCircuitStateUpdate(CircuitState state)
    {
        if (!isConnected) return;

        var message = new Dictionary<string, object>
        {
            ["type"] = "circuit_state_update",
            ["session_id"] = sessionId,
            ["state"] = state,
            ["sender"] = userId
        };

        string jsonMessage = JsonConvert.SerializeObject(message);
        webSocketClient.SendMessage(jsonMessage);

        // 同时通过HTTP备份发送
        StartCoroutine(SendCircuitStateHttp(state));
    }

    /// <summary>
    /// 通过HTTP发送电路状态
    /// </summary>
    private IEnumerator SendCircuitStateHttp(CircuitState state)
    {
        string url = $"{baseUrl}/digital-twin/sessions/{sessionId}/states";

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("Authorization", "Bearer your-jwt-token");

            string jsonData = JsonConvert.SerializeObject(state);
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning($"HTTP发送电路状态失败: {request.error}");
            }
        }
    }

    /// <summary>
    /// 发送设备状态更新
    /// </summary>
    public void SendDeviceStateUpdate(DeviceState state)
    {
        if (!isConnected) return;

        var message = new Dictionary<string, object>
        {
            ["type"] = "device_state_update",
            ["session_id"] = sessionId,
            ["state"] = state
        };

        string jsonMessage = JsonConvert.SerializeObject(message);
        webSocketClient.SendMessage(jsonMessage);
    }

    /// <summary>
    /// 请求初始同步
    /// </summary>
    private void RequestInitialSync()
    {
        var message = new Dictionary<string, object>
        {
            ["type"] = "sync_request",
            ["session_id"] = sessionId
        };

        string jsonMessage = JsonConvert.SerializeObject(message);
        webSocketClient.SendMessage(jsonMessage);
    }

    /// <summary>
    /// 发送心跳
    /// </summary>
    private void SendHeartbeat()
    {
        if (!isConnected) return;

        var message = new Dictionary<string, object>
        {
            ["type"] = "ping",
            ["timestamp"] = DateTime.UtcNow.ToString("o")
        };

        string jsonMessage = JsonConvert.SerializeObject(message);
        webSocketClient.SendMessage(jsonMessage);
    }

    /// <summary>
    /// 获取本地电路状态
    /// </summary>
    public CircuitState GetLocalCircuitState()
    {
        return new CircuitState
        {
            session_id = sessionId,
            elements = new List<CircuitElementState>(localElementStates.Values).ToArray(),
            total_power = 0f, // 需要计算
            total_current = 0f, // 需要计算
            simulation_time = Time.time,
            timestamp = DateTime.UtcNow.ToString("o")
        };
    }

    /// <summary>
    /// 获取本地设备状态
    /// </summary>
    public DeviceState GetLocalDeviceState(string deviceId)
    {
        return localDeviceStates.ContainsKey(deviceId) ? localDeviceStates[deviceId] : null;
    }

    /// <summary>
    /// 获取所有本地设备状态
    /// </summary>
    public Dictionary<string, DeviceState> GetAllLocalDeviceStates()
    {
        return new Dictionary<string, DeviceState>(localDeviceStates);
    }

    private void OnDestroy()
    {
        if (webSocketClient != null)
        {
            webSocketClient.Close();
        }
    }

    /// <summary>
    /// 简化的WebSocket客户端
    /// </summary>
    public class WebSocketClient
    {
        private string url;
        private System.Net.WebSockets.ClientWebSocket webSocket;
        private bool isConnected = false;

        public Action OnConnected;
        public Action OnDisconnected;
        public Action<string> OnMessageReceived;
        public Action<string> OnError;

        public WebSocketClient(string url)
        {
            this.url = url;
        }

        public async void Connect()
        {
            try
            {
                webSocket = new System.Net.WebSockets.ClientWebSocket();
                await webSocket.ConnectAsync(new Uri(url), System.Threading.CancellationToken.None);
                isConnected = true;
                OnConnected?.Invoke();

                // 启动接收循环
                ReceiveLoop();
            }
            catch (Exception ex)
            {
                OnError?.Invoke(ex.Message);
            }
        }

        public async void SendMessage(string message)
        {
            if (!isConnected || webSocket.State != System.Net.WebSockets.WebSocketState.Open)
                return;

            try
            {
                byte[] bytes = System.Text.Encoding.UTF8.GetBytes(message);
                await webSocket.SendAsync(
                    new ArraySegment<byte>(bytes),
                    System.Net.WebSockets.WebSocketMessageType.Text,
                    true,
                    System.Threading.CancellationToken.None);
            }
            catch (Exception ex)
            {
                OnError?.Invoke(ex.Message);
            }
        }

        public async void Close()
        {
            if (webSocket != null && webSocket.State == System.Net.WebSockets.WebSocketState.Open)
            {
                await webSocket.CloseAsync(
                    System.Net.WebSockets.WebSocketCloseStatus.NormalClosure,
                    "Client closing",
                    System.Threading.CancellationToken.None);
            }
            isConnected = false;
            OnDisconnected?.Invoke();
        }

        private async void ReceiveLoop()
        {
            byte[] buffer = new byte[1024];
            while (isConnected && webSocket.State == System.Net.WebSockets.WebSocketState.Open)
            {
                try
                {
                    var result = await webSocket.ReceiveAsync(
                        new ArraySegment<byte>(buffer),
                        System.Threading.CancellationToken.None);

                    if (result.MessageType == System.Net.WebSockets.WebSocketMessageType.Text)
                    {
                        string message = System.Text.Encoding.UTF8.GetString(buffer, 0, result.Count);
                        OnMessageReceived?.Invoke(message);
                    }
                }
                catch (Exception ex)
                {
                    OnError?.Invoke(ex.Message);
                    break;
                }
            }

            isConnected = false;
            OnDisconnected?.Invoke();
        }
    }
}
