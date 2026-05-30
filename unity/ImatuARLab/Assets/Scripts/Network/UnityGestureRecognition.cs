using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

/// <summary>
/// Unity MediaPipe手势识别集成
/// 与后端MediaPipe服务通信，实现实时手势识别
/// </summary>
public class UnityGestureRecognition : MonoBehaviour
{
    [Header("手势识别配置")]
    [SerializeField] private float recognitionInterval = 0.1f;
    [SerializeField] private int maxGestureHistory = 20;
    [SerializeField] private float gestureConfidenceThreshold = 0.7f;

    // 组件引用
    private ARCameraManager arCameraManager;
    private Camera arCamera;

    // 手势数据
    private List<GestureData> gestureHistory;
    private float lastRecognitionTime;

    // 事件委托
    public delegate void GestureRecognizedHandler(GestureType gestureType, float confidence, Vector3 position);
    public event GestureRecognizedHandler OnGestureRecognized;

    public delegate void ComplexSequenceHandler(string sequenceName, float confidence);
    public event ComplexSequenceHandler OnComplexSequenceDetected;

    // 手势类型枚举
    public enum GestureType
    {
        Unknown,
        Tap,
        SwipeLeft,
        SwipeRight,
        SwipeUp,
        SwipeDown,
        PinchIn,
        PinchOut,
        RotateClockwise,
        RotateCounterClockwise,
        Circle,
        VShape,
        OkSign,
        ThumbsUp,
        PalmOpen,
        Fist,
        SecretGesture1,
        SecretGesture2
    }

    // 手势数据结构
    [System.Serializable]
    public struct GestureData
    {
        public GestureType gestureType;
        public float confidence;
        public Vector3 position;
        public float timestamp;
        public string metadata;
    }

    void Awake()
    {
        InitializeComponents();
        InitializeGestureSystem();
    }

    void Start()
    {
        StartGestureRecognition();
    }

    private void InitializeComponents()
    {
        // 获取AR相机组件
        arCameraManager = FindObjectOfType<ARCameraManager>();
        var sessionOrigin = FindObjectOfType<ARSessionOrigin>();
        if (sessionOrigin != null)
        {
            arCamera = sessionOrigin.camera;
        }

        if (arCameraManager == null || arCamera == null)
        {
            Debug.LogWarning("AR相机组件未找到，请确保场景中有AR Session Origin");
        }
    }

    private void InitializeGestureSystem()
    {
        gestureHistory = new List<GestureData>();
        lastRecognitionTime = 0f;

        Debug.Log("手势识别系统初始化完成");
    }

    private void StartGestureRecognition()
    {
        StartCoroutine(GestureRecognitionLoop());
    }

    private IEnumerator GestureRecognitionLoop()
    {
        while (enabled)
        {
            if (Time.time - lastRecognitionTime >= recognitionInterval)
            {
                yield return ProcessGestureFrame();
                lastRecognitionTime = Time.time;
            }
            yield return null;
        }
    }

    private IEnumerator ProcessGestureFrame()
    {
        if (arCamera == null) yield break;

        // 捕获当前帧
        Texture2D frameTexture = CaptureCameraFrame();
        if (frameTexture == null) yield break;

        // 发送到后端进行手势识别
        yield return StartCoroutine(SendFrameToBackend(frameTexture));

        // 清理纹理资源
        Destroy(frameTexture);
    }

    private Texture2D CaptureCameraFrame()
    {
        try
        {
            RenderTexture renderTexture = new RenderTexture(Screen.width, Screen.height, 24);
            arCamera.targetTexture = renderTexture;
            arCamera.Render();

            RenderTexture.active = renderTexture;
            Texture2D texture = new Texture2D(renderTexture.width, renderTexture.height, TextureFormat.RGB24, false);
            texture.ReadPixels(new Rect(0, 0, renderTexture.width, renderTexture.height), 0, 0);
            texture.Apply();

            // 恢复相机设置
            arCamera.targetTexture = null;
            RenderTexture.active = null;
            Destroy(renderTexture);

            return texture;
        }
        catch (System.Exception e)
        {
            Debug.LogError($"捕获相机帧失败: {e.Message}");
            return null;
        }
    }

    private IEnumerator SendFrameToBackend(Texture2D frameTexture)
    {
        // 将纹理编码为JPEG
        byte[] imageData = frameTexture.EncodeToJPG(80);

        // 构造POST请求
        WWWForm form = new WWWForm();
        form.AddBinaryData("image", imageData, "frame.jpg", "image/jpeg");
        form.AddField("timestamp", System.DateTime.Now.ToString("o"));

        using (UnityEngine.Networking.UnityWebRequest request = UnityEngine.Networking.UnityWebRequest.Post(
            "http://localhost:8000/api/v1/gesture/recognize", form))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
            {
                ProcessGestureResponse(request.downloadHandler.text);
            }
            else
            {
                Debug.LogError($"手势识别请求失败: {request.error}");
            }
        }
    }

    private void ProcessGestureResponse(string jsonResponse)
    {
        try
        {
            GestureRecognitionResponse response = JsonUtility.FromJson<GestureRecognitionResponse>(jsonResponse);

            if (response.success && response.data != null)
            {
                // 处理识别到的手势
                foreach (var gesture in response.data.recognized_gestures)
                {
                    ProcessRecognizedGesture(gesture);
                }

                // 处理复杂手势序列
                foreach (var sequence in response.data.complex_sequences)
                {
                    ProcessComplexSequence(sequence);
                }
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"处理手势识别响应失败: {e.Message}");
        }
    }

    private void ProcessRecognizedGesture(GestureRecognitionData gestureData)
    {
        GestureType gestureType = ParseGestureType(gestureData.type);
        float confidence = gestureData.confidence;

        if (confidence >= gestureConfidenceThreshold)
        {
            Vector3 gesturePosition = Vector3.zero; // 可以从数据中解析位置信息

            // 添加到历史记录
            GestureData gesture = new GestureData
            {
                gestureType = gestureType,
                confidence = confidence,
                position = gesturePosition,
                timestamp = Time.time,
                metadata = gestureData.metadata
            };

            gestureHistory.Add(gesture);
            if (gestureHistory.Count > maxGestureHistory)
            {
                gestureHistory.RemoveAt(0);
            }

            // 触发事件
            OnGestureRecognized?.Invoke(gestureType, confidence, gesturePosition);

            Debug.Log($"识别到手势: {gestureType}, 置信度: {confidence:F2}");

            // 特殊手势处理
            HandleSpecialGestures(gestureType, confidence);
        }
    }

    private void ProcessComplexSequence(ComplexSequenceData sequenceData)
    {
        string sequenceName = sequenceData.sequence_name;
        float confidence = sequenceData.confidence;

        OnComplexSequenceDetected?.Invoke(sequenceName, confidence);

        Debug.Log($"检测到复杂手势序列: {sequenceName}, 置信度: {confidence:F2}");

        // 触发隐藏任务
        TriggerHiddenTask(sequenceName, confidence);
    }

    private GestureType ParseGestureType(string typeString)
    {
        switch (typeString.ToLower())
        {
            case "tap": return GestureType.Tap;
            case "swipe_left": return GestureType.SwipeLeft;
            case "swipe_right": return GestureType.SwipeRight;
            case "swipe_up": return GestureType.SwipeUp;
            case "swipe_down": return GestureType.SwipeDown;
            case "pinch_in": return GestureType.PinchIn;
            case "pinch_out": return GestureType.PinchOut;
            case "rotate_clockwise": return GestureType.RotateClockwise;
            case "rotate_counterclockwise": return GestureType.RotateCounterClockwise;
            case "circle": return GestureType.Circle;
            case "v_shape": return GestureType.VShape;
            case "ok_sign": return GestureType.OkSign;
            case "thumbs_up": return GestureType.ThumbsUp;
            case "palm_open": return GestureType.PalmOpen;
            case "fist": return GestureType.Fist;
            case "secret_gesture_1": return GestureType.SecretGesture1;
            case "secret_gesture_2": return GestureType.SecretGesture2;
            default: return GestureType.Unknown;
        }
    }

    private void HandleSpecialGestures(GestureType gestureType, float confidence)
    {
        switch (gestureType)
        {
            case GestureType.ThumbsUp:
                Debug.Log("👍 点赞手势识别！");
                // 可以触发点赞相关的奖励
                break;

            case GestureType.VShape:
                Debug.Log("✌️ V字胜利手势识别！");
                // 可以触发特殊效果
                break;

            case GestureType.OkSign:
                Debug.Log("👌 OK手势识别！");
                // 可以确认操作
                break;
        }
    }

    private void TriggerHiddenTask(string sequenceName, float confidence)
    {
        switch (sequenceName)
        {
            case "secret_task_1":
                Debug.Log("🔓 隐藏任务1已触发！");
                // 实现隐藏任务1的逻辑
                StartCoroutine(ExecuteSecretTask1());
                break;

            case "secret_task_2":
                Debug.Log("🔓 隐藏任务2已触发！");
                // 实现隐藏任务2的逻辑
                StartCoroutine(ExecuteSecretTask2());
                break;

            case "secret_task_3":
                Debug.Log("🔓 隐藏任务3已触发！");
                // 实现隐藏任务3的逻辑
                StartCoroutine(ExecuteSecretTask3());
                break;
        }
    }

    private IEnumerator ExecuteSecretTask1()
    {
        // 隐藏任务1：给予额外积分奖励
        yield return StartCoroutine(SendHiddenTaskReward("secret_task_1", 100));
        Debug.Log("🎁 隐藏任务1奖励已发放：100积分");
    }

    private IEnumerator ExecuteSecretTask2()
    {
        // 隐藏任务2：解锁特殊徽章
        yield return StartCoroutine(SendHiddenTaskReward("secret_task_2", 150));
        Debug.Log("🏆 隐藏任务2奖励已发放：150积分 + 特殊徽章");
    }

    private IEnumerator ExecuteSecretTask3()
    {
        // 隐藏任务3：高级功能解锁
        yield return StartCoroutine(SendHiddenTaskReward("secret_task_3", 200));
        Debug.Log("🔑 隐藏任务3奖励已发放：200积分 + 功能解锁");
    }

    private IEnumerator SendHiddenTaskReward(string taskName, int points)
    {
        var rewardData = new HiddenTaskRewardData
        {
            task_name = taskName,
            points = points,
            timestamp = System.DateTime.Now.ToString("o")
        };

        string jsonData = JsonUtility.ToJson(rewardData);

        using (UnityEngine.Networking.UnityWebRequest request = new UnityEngine.Networking.UnityWebRequest(
            "http://localhost:8000/api/v1/gesture/hidden-task-reward", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UnityEngine.Networking.UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new UnityEngine.Networking.DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result != UnityEngine.Networking.UnityWebRequest.Result.Success)
            {
                Debug.LogError($"隐藏任务奖励发送失败: {request.error}");
            }
        }
    }

    public List<GestureData> GetGestureHistory()
    {
        return new List<GestureData>(gestureHistory);
    }

    public void ClearGestureHistory()
    {
        gestureHistory.Clear();
        Debug.Log("手势历史已清空");
    }

    void OnDestroy()
    {
        StopAllCoroutines();
    }

    // 数据结构定义
    [System.Serializable]
    private struct GestureRecognitionResponse
    {
        public bool success;
        public string message;
        public RecognitionData data;
    }

    [System.Serializable]
    private struct RecognitionData
    {
        public GestureRecognitionData[] recognized_gestures;
        public ComplexSequenceData[] complex_sequences;
        public bool frame_processed;
        public string timestamp;
    }

    [System.Serializable]
    private struct GestureRecognitionData
    {
        public string type;
        public float confidence;
        public float duration;
        public string metadata;
    }

    [System.Serializable]
    private struct ComplexSequenceData
    {
        public string sequence_name;
        public float confidence;
    }

    [System.Serializable]
    private struct HiddenTaskRewardData
    {
        public string task_name;
        public int points;
        public string timestamp;
    }
}
