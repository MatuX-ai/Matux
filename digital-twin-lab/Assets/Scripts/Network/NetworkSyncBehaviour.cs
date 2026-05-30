using System.Collections.Generic;
using UnityEngine;
using Mirror;

/// <summary>
/// 网络同步基础行为类
/// 为所有需要网络同步的对象提供基础功能
/// </summary>
[RequireComponent(typeof(NetworkIdentity))]
public class NetworkSyncBehaviour : NetworkBehaviour
{
    [Header("同步配置")]
    [Tooltip("同步间隔(秒)")]
    public float syncInterval = 0.1f;

    [Tooltip("是否只在网络主机上运行")]
    public bool runOnServerOnly = false;

    [Tooltip("是否在网络客户端上运行")]
    public bool runOnClientOnly = false;

    protected float lastSyncTime = 0f;
    protected bool isInitialized = false;

    // 同步数据缓冲区
    protected Queue<SyncData> syncBuffer = new Queue<SyncData>();
    protected const int MAX_BUFFER_SIZE = 10;

    [System.Serializable]
    public struct SyncData
    {
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 scale;
        public float timestamp;

        public SyncData(Vector3 pos, Quaternion rot, Vector3 scl)
        {
            position = pos;
            rotation = rot;
            scale = scl;
            timestamp = Time.time;
        }
    }

    protected virtual void Awake()
    {
        // 确保有NetworkIdentity组件
        if (GetComponent<NetworkIdentity>() == null)
        {
            gameObject.AddComponent<NetworkIdentity>();
        }
    }

    public override void OnStartServer()
    {
        base.OnStartServer();
        isInitialized = true;
        lastSyncTime = Time.time;
        Debug.Log($"[{gameObject.name}] 网络服务器同步已启动");
    }

    public override void OnStartClient()
    {
        base.OnStartClient();
        isInitialized = true;
        lastSyncTime = Time.time;
        Debug.Log($"[{gameObject.name}] 网络客户端同步已启动");
    }

    protected virtual void Update()
    {
        if (!isInitialized) return;

        // 根据配置决定在哪种模式下运行
        if (runOnServerOnly && !isServer) return;
        if (runOnClientOnly && !isClient) return;

        // 定期同步
        if (Time.time - lastSyncTime >= syncInterval)
        {
            PerformSync();
            lastSyncTime = Time.time;
        }

        // 处理接收的数据
        ProcessReceivedData();
    }

    /// <summary>
    /// 执行同步操作
    /// </summary>
    protected virtual void PerformSync()
    {
        if (isServer)
        {
            // 服务器向所有客户端广播状态
            SyncData currentData = new SyncData(
                transform.position,
                transform.rotation,
                transform.localScale
            );

            CmdBroadcastSyncData(currentData);
        }
        else if (isClient)
        {
            // 客户端向服务器发送状态
            SyncData currentData = new SyncData(
                transform.position,
                transform.rotation,
                transform.localScale
            );

            CmdSendSyncData(currentData);
        }
    }

    /// <summary>
    /// 处理接收到的同步数据
    /// </summary>
    protected virtual void ProcessReceivedData()
    {
        while (syncBuffer.Count > 0)
        {
            SyncData data = syncBuffer.Dequeue();

            // 插值处理以获得平滑效果
            if (isClientOnly)
            {
                float interpolationFactor = Mathf.Clamp01((Time.time - data.timestamp) / syncInterval);
                transform.position = Vector3.Lerp(transform.position, data.position, interpolationFactor);
                transform.rotation = Quaternion.Slerp(transform.rotation, data.rotation, interpolationFactor);
                transform.localScale = Vector3.Lerp(transform.localScale, data.scale, interpolationFactor);
            }
            else
            {
                // 直接应用服务器数据
                transform.position = data.position;
                transform.rotation = data.rotation;
                transform.localScale = data.scale;
            }
        }
    }

    /// <summary>
    /// 服务器RPC：广播同步数据给所有客户端
    /// </summary>
    [Server]
    protected void CmdBroadcastSyncData(SyncData data)
    {
        RpcReceiveSyncData(data);
    }

    /// <summary>
    /// 客户端命令：发送同步数据到服务器
    /// </summary>
    [Command]
    protected void CmdSendSyncData(SyncData data)
    {
        // 服务器接收并转发给其他客户端
        RpcReceiveSyncData(data);
    }

    /// <summary>
    /// 客户端RPC：接收同步数据
    /// </summary>
    [ClientRpc]
    protected void RpcReceiveSyncData(SyncData data)
    {
        // 将数据加入缓冲区
        if (syncBuffer.Count >= MAX_BUFFER_SIZE)
        {
            syncBuffer.Dequeue(); // 移除最旧的数据
        }
        syncBuffer.Enqueue(data);
    }

    /// <summary>
    /// 添加自定义同步数据
    /// </summary>
    /// <param name="customData">自定义数据</param>
    [Server]
    protected void BroadcastCustomData<T>(T customData) where T : struct
    {
        RpcReceiveCustomData(JsonUtility.ToJson(customData));
    }

    /// <summary>
    /// 客户端接收自定义数据
    /// </summary>
    [ClientRpc]
    protected void RpcReceiveCustomData(string jsonData)
    {
        OnCustomDataReceived(jsonData);
    }

    /// <summary>
    /// 处理自定义数据接收
    /// </summary>
    /// <param name="jsonData">JSON格式的数据</param>
    protected virtual void OnCustomDataReceived(string jsonData)
    {
        // 子类重写此方法处理特定数据
    }

    /// <summary>
    /// 检查网络权限
    /// </summary>
    /// <returns>是否有权限执行操作</returns>
    protected bool HasAuthority()
    {
        NetworkIdentity identity = GetComponent<NetworkIdentity>();
        return identity != null && identity.hasAuthority;
    }

    /// <summary>
    /// 获取网络对象ID
    /// </summary>
    /// <returns>网络ID</returns>
    protected uint GetNetId()
    {
        NetworkIdentity identity = GetComponent<NetworkIdentity>();
        return identity != null ? identity.netId : 0;
    }
}
