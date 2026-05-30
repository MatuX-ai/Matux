using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

/// <summary>
/// AR元素位置检测器
/// 提供精确的3D空间位置检测和碰撞检测功能
/// </summary>
public class ARElementPositionDetector : MonoBehaviour
{
    [Header("检测配置")]
    [SerializeField] private float detectionRadius = 0.5f;
    [SerializeField] private LayerMask detectionLayers = ~0;
    [SerializeField] private float snapDistance = 0.1f;
    [SerializeField] private bool enableSnapToGrid = true;
    [SerializeField] private float gridSize = 0.05f;

    private ARSessionOrigin arOrigin;
    private ARRaycastManager raycastManager;
    private List<ARRaycastHit> raycastHits = new List<ARRaycastHit>();

    // 位置检测结果结构
    public struct PositionDetectionResult
    {
        public bool isValid;
        public Vector3 detectedPosition;
        public Quaternion detectedRotation;
        public Vector3 surfaceNormal;
        public string surfaceType;
        public float confidence;
        public List<GameObject> nearbyObjects;
        public string errorMessage;
    }

    // 碰撞检测结果结构
    public struct CollisionDetectionResult
    {
        public bool hasCollision;
        public List<GameObject> collidingObjects;
        public Vector3 collisionPoint;
        public float collisionDistance;
        public string collisionType;
    }

    public void Initialize(ARSessionOrigin origin, ARRaycastManager raycastMgr)
    {
        arOrigin = origin;
        raycastManager = raycastMgr;
    }

    /// <summary>
    /// 检测屏幕点击位置的3D世界坐标
    /// </summary>
    public PositionDetectionResult DetectWorldPosition(Vector2 screenPosition)
    {
        var result = new PositionDetectionResult
        {
            isValid = false,
            nearbyObjects = new List<GameObject>(),
            errorMessage = ""
        };

        if (raycastManager == null)
        {
            result.errorMessage = "射线投射管理器未初始化";
            return result;
        }

        // 执行AR射线投射
        if (raycastManager.Raycast(screenPosition, raycastHits, TrackableType.PlaneWithinPolygon))
        {
            if (raycastHits.Count > 0)
            {
                var hit = raycastHits[0];

                result.isValid = true;
                result.detectedPosition = hit.pose.position;
                result.detectedRotation = hit.pose.rotation;
                result.surfaceNormal = hit.normal;
                result.surfaceType = hit.hitType.ToString();
                result.confidence = hit.distance; // 使用距离作为置信度指标

                // 应用网格对齐
                if (enableSnapToGrid)
                {
                    result.detectedPosition = SnapToGrid(result.detectedPosition);
                }

                // 检测附近的对象
                result.nearbyObjects = DetectNearbyObjects(result.detectedPosition);

                Debug.Log($"位置检测成功: {result.detectedPosition}");
            }
        }
        else
        {
            result.errorMessage = "无法在AR平面上找到点击位置";
        }

        return result;
    }

    /// <summary>
    /// 网格对齐
    /// </summary>
    private Vector3 SnapToGrid(Vector3 position)
    {
        return new Vector3(
            Mathf.Round(position.x / gridSize) * gridSize,
            Mathf.Round(position.y / gridSize) * gridSize,
            Mathf.Round(position.z / gridSize) * gridSize
        );
    }

    /// <summary>
    /// 检测附近对象
    /// </summary>
    private List<GameObject> DetectNearbyObjects(Vector3 centerPosition)
    {
        List<GameObject> nearbyObjects = new List<GameObject>();

        Collider[] colliders = Physics.OverlapSphere(centerPosition, detectionRadius, detectionLayers);

        foreach (Collider collider in colliders)
        {
            GameObject obj = collider.gameObject;
            if (obj != gameObject) // 排除自身
            {
                nearbyObjects.Add(obj);
            }
        }

        return nearbyObjects;
    }

    /// <summary>
    /// 检测放置碰撞
    /// </summary>
    public CollisionDetectionResult DetectPlacementCollisions(Vector3 position, Bounds objectBounds)
    {
        var result = new CollisionDetectionResult
        {
            hasCollision = false,
            collidingObjects = new List<GameObject>(),
            collisionDistance = float.MaxValue
        };

        // 扩大检测范围以包含对象边界
        float expandedRadius = Mathf.Max(objectBounds.extents.magnitude, detectionRadius);
        Collider[] colliders = Physics.OverlapSphere(position, expandedRadius, detectionLayers);

        foreach (Collider collider in colliders)
        {
            GameObject obj = collider.gameObject;

            // 排除某些类型的对象（如AR平面可视化）
            if (obj.CompareTag("ARPlane") || obj == gameObject)
                continue;

            // 检查实际碰撞
            if (collider.bounds.Intersects(objectBounds))
            {
                result.hasCollision = true;
                result.collidingObjects.Add(obj);

                float distance = Vector3.Distance(position, collider.ClosestPoint(position));
                if (distance < result.collisionDistance)
                {
                    result.collisionDistance = distance;
                    result.collisionPoint = collider.ClosestPoint(position);
                }
            }
        }

        result.collisionType = result.collidingObjects.Count > 0 ?
            (result.collidingObjects[0].GetComponent<ESP32Model>() != null ? "HardwareCollision" : "GenericCollision") :
            "NoCollision";

        return result;
    }

    /// <summary>
    /// 预测最佳放置位置
    /// </summary>
    public Vector3 PredictBestPlacementPosition(Vector2 screenPosition, Vector3 objectSize)
    {
        var detectionResult = DetectWorldPosition(screenPosition);

        if (!detectionResult.isValid)
            return Vector3.zero;

        Vector3 candidatePosition = detectionResult.detectedPosition;

        // 检查当前位置是否有碰撞
        Bounds objectBounds = new Bounds(candidatePosition, objectSize);
        var collisionResult = DetectPlacementCollisions(candidatePosition, objectBounds);

        if (!collisionResult.hasCollision)
        {
            return candidatePosition; // 当前位置可用
        }

        // 尝试寻找附近无碰撞的位置
        Vector3[] offsetDirections = {
            Vector3.right, Vector3.left, Vector3.forward, Vector3.back,
            Vector3.right + Vector3.forward, Vector3.right + Vector3.back,
            Vector3.left + Vector3.forward, Vector3.left + Vector3.back
        };

        float searchRadius = 0.1f;
        float maxSearchRadius = 0.5f;

        while (searchRadius <= maxSearchRadius)
        {
            foreach (Vector3 direction in offsetDirections)
            {
                Vector3 testPosition = candidatePosition + direction.normalized * searchRadius;
                Bounds testBounds = new Bounds(testPosition, objectSize);

                if (!DetectPlacementCollisions(testPosition, testBounds).hasCollision)
                {
                    return testPosition;
                }
            }
            searchRadius += 0.05f;
        }

        // 如果找不到无碰撞位置，返回原始位置
        return candidatePosition;
    }

    /// <summary>
    /// 验证放置位置的有效性
    /// </summary>
    public bool ValidatePlacementPosition(Vector3 position, Vector3 objectSize, out string validationMessage)
    {
        validationMessage = "";

        // 检查是否在合理范围内
        if (Mathf.Abs(position.y) > 2f) // 高度过高或过低
        {
            validationMessage = "放置高度不合理，请选择更合适的表面";
            return false;
        }

        if (position.magnitude > 10f) // 距离过远
        {
            validationMessage = "放置位置过远，请靠近一些";
            return false;
        }

        // 检查碰撞
        Bounds bounds = new Bounds(position, objectSize);
        var collisionResult = DetectPlacementCollisions(position, bounds);

        if (collisionResult.hasCollision)
        {
            validationMessage = $"检测到 {collisionResult.collidingObjects.Count} 个碰撞对象，请调整位置";
            return false;
        }

        validationMessage = "位置验证通过";
        return true;
    }

    /// <summary>
    /// 获取可视化的调试信息
    /// </summary>
    public Dictionary<string, object> GetDebugInfo(Vector3 position)
    {
        return new Dictionary<string, object>
        {
            ["detectionRadius"] = detectionRadius,
            ["snapDistance"] = snapDistance,
            ["gridSize"] = gridSize,
            ["enableSnapToGrid"] = enableSnapToGrid,
            ["nearbyObjectCount"] = DetectNearbyObjects(position).Count,
            ["currentPosition"] = position
        };
    }

    /// <summary>
    /// 绘制调试可视化
    /// </summary>
    void OnDrawGizmosSelected()
    {
        if (Application.isPlaying)
        {
            // 绘制检测半径
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, detectionRadius);

            // 绘制网格对齐参考
            if (enableSnapToGrid)
            {
                Gizmos.color = Color.blue;
                Vector3 snappedPos = SnapToGrid(transform.position);
                Gizmos.DrawCube(snappedPos, Vector3.one * 0.02f);
            }
        }
    }
}
