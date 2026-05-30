using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Mirror;

/// <summary>
/// 数字孪生实验室网络管理器
/// 负责管理多人协作会话和网络同步
/// </summary>
public class DigitalTwinNetworkManager : NetworkManager
{
    [Header("数字孪生配置")]
    [Tooltip("最大同时在线用户数")]
    public int maxConcurrentUsers = 10;

    [Tooltip("网络同步间隔(秒)")]
    public float syncInterval = 0.1f;

    [Tooltip("是否启用主机优先模式")]
    public bool isMasterPriority = true;

    private static DigitalTwinNetworkManager _instance;
    public static DigitalTwinNetworkManager Instance => _instance;

    // 网络会话状态
    public enum SessionState
    {
        Disconnected,
        Connecting,
        Connected,
        Hosting,
        Client
    }

    public SessionState CurrentState { get; private set; } = SessionState.Disconnected;

    // 事件回调
    public System.Action OnSessionStarted;
    public System.Action OnSessionEnded;
    public System.Action<NetworkConnection> OnClientConnected;
    public System.Action<NetworkConnection> OnClientDisconnected;

    private void Awake()
    {
        if (_instance != null && _instance != this)
        {
            Destroy(gameObject);
            return;
        }

        _instance = this;
        DontDestroyOnLoad(gameObject);

        // 设置网络配置
        spawnPrefabs.Clear();
        spawnPrefabs.Add(Resources.Load<GameObject>("Prefabs/CircuitElement"));
        spawnPrefabs.Add(Resources.Load<GameObject>("Prefabs/MeasuringInstrument"));
    }

    public override void OnStartServer()
    {
        base.OnStartServer();
        CurrentState = SessionState.Hosting;
        Debug.Log("数字孪生实验室服务器已启动");
        OnSessionStarted?.Invoke();
    }

    public override void OnStartClient()
    {
        base.OnStartClient();
        CurrentState = SessionState.Client;
        Debug.Log("已连接到数字孪生实验室服务器");
        OnSessionStarted?.Invoke();
    }

    public override void OnStopServer()
    {
        base.OnStopServer();
        CurrentState = SessionState.Disconnected;
        Debug.Log("数字孪生实验室服务器已停止");
        OnSessionEnded?.Invoke();
    }

    public override void OnStopClient()
    {
        base.OnStopClient();
        CurrentState = SessionState.Disconnected;
        Debug.Log("已断开数字孪生实验室连接");
        OnSessionEnded?.Invoke();
    }

    public override void OnServerConnect(NetworkConnection conn)
    {
        base.OnServerConnect(conn);
        Debug.Log($"新客户端连接: {conn.connectionId}");
        OnClientConnected?.Invoke(conn);
    }

    public override void OnServerDisconnect(NetworkConnection conn)
    {
        base.OnServerDisconnect(conn);
        Debug.Log($"客户端断开连接: {conn.connectionId}");
        OnClientDisconnected?.Invoke(conn);
    }

    /// <summary>
    /// 启动主机模式
    /// </summary>
    public void StartHostMode()
    {
        if (CurrentState != SessionState.Disconnected) return;

        CurrentState = SessionState.Connecting;
        StartCoroutine(StartHostCoroutine());
    }

    private IEnumerator StartHostCoroutine()
    {
        yield return null;
        StartHost();
    }

    /// <summary>
    /// 连接到主机
    /// </summary>
    /// <param name="ipAddress">主机IP地址</param>
    public void ConnectToHost(string ipAddress)
    {
        if (CurrentState != SessionState.Disconnected) return;

        networkAddress = ipAddress;
        CurrentState = SessionState.Connecting;
        StartCoroutine(ConnectCoroutine());
    }

    private IEnumerator ConnectCoroutine()
    {
        yield return null;
        StartClient();
    }

    /// <summary>
    /// 断开连接
    /// </summary>
    public void Disconnect()
    {
        if (CurrentState == SessionState.Hosting)
        {
            StopHost();
        }
        else if (CurrentState == SessionState.Client)
        {
            StopClient();
        }
    }

    /// <summary>
    /// 获取当前连接的客户端数量
    /// </summary>
    /// <returns>客户端数量</returns>
    public int GetConnectedClientCount()
    {
        if (CurrentState != SessionState.Hosting) return 0;
        return NetworkServer.connections.Count;
    }
}
