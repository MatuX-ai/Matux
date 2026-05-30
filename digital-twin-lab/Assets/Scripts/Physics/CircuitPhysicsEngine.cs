using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 电路仿真物理引擎
/// 负责电路元件的物理特性和电气行为仿真
/// </summary>
public class CircuitPhysicsEngine : MonoBehaviour
{
    [Header("仿真配置")]
    [Tooltip("仿真时间步长(秒)")]
    public float timeStep = 0.02f; // 50Hz

    [Tooltip("最大迭代次数")]
    public int maxIterations = 100;

    [Tooltip("收敛阈值")]
    public float convergenceThreshold = 0.001f;

    [Tooltip("是否启用实时仿真")]
    public bool enableRealtimeSimulation = true;

    // 电路网络
    private Dictionary<string, CircuitNode> nodes = new Dictionary<string, CircuitNode>();
    private List<CircuitElement> elements = new List<CircuitElement>();
    private List<VoltageSource> voltageSources = new List<VoltageSource>();
    private List<CurrentSource> currentSources = new List<CurrentSource>();

    // 仿真状态
    private bool isSimulating = false;
    private float simulationTimer = 0f;
    private int iterationCount = 0;

    // 事件系统
    public Action<CircuitState> OnCircuitStateChanged;
    public Action<string, float> OnElementValueChanged;

    [Serializable]
    public struct CircuitState
    {
        public float timestamp;
        public Dictionary<string, NodeState> nodeStates;
        public Dictionary<string, ElementState> elementStates;
        public float totalPower;
        public float totalCurrent;
    }

    [Serializable]
    public struct NodeState
    {
        public Vector3 position;
        public float voltage;
        public float charge;
    }

    [Serializable]
    public struct ElementState
    {
        public string type;
        public float voltage;
        public float current;
        public float power;
        public Vector3[] connectionPoints;
    }

    private void Start()
    {
        InitializeDefaultCircuit();
    }

    private void Update()
    {
        if (!enableRealtimeSimulation || !isSimulating) return;

        simulationTimer += Time.deltaTime;
        if (simulationTimer >= timeStep)
        {
            SimulateStep();
            simulationTimer = 0f;
        }
    }

    /// <summary>
    /// 初始化默认电路
    /// </summary>
    private void InitializeDefaultCircuit()
    {
        // 创建基本节点
        CreateNode("Node_GND", Vector3.zero, 0f); // 地节点
        CreateNode("Node_VCC", Vector3.right * 2, 5f); // 电源节点

        // 创建基本元件
        CreateResistor("R1", "Node_VCC", "Node_GND", 1000f); // 1kΩ电阻
        CreateCapacitor("C1", "Node_VCC", "Node_GND", 0.001f); // 1mF电容
    }

    /// <summary>
    /// 创建电路节点
    /// </summary>
    public void CreateNode(string nodeId, Vector3 position, float initialVoltage = 0f)
    {
        if (nodes.ContainsKey(nodeId))
        {
            Debug.LogWarning($"节点 {nodeId} 已存在");
            return;
        }

        var node = new CircuitNode
        {
            id = nodeId,
            position = position,
            voltage = initialVoltage,
            connections = new List<string>()
        };

        nodes[nodeId] = node;
        Debug.Log($"创建节点: {nodeId} 电压: {initialVoltage}V");
    }

    /// <summary>
    /// 创建电阻元件
    /// </summary>
    public void CreateResistor(string elementId, string node1, string node2, float resistance)
    {
        if (!nodes.ContainsKey(node1) || !nodes.ContainsKey(node2))
        {
            Debug.LogError($"节点不存在: {node1} 或 {node2}");
            return;
        }

        var resistor = new Resistor
        {
            id = elementId,
            node1 = node1,
            node2 = node2,
            resistance = resistance,
            voltage = 0f,
            current = 0f
        };

        elements.Add(resistor);
        nodes[node1].connections.Add(elementId);
        nodes[node2].connections.Add(elementId);

        Debug.Log($"创建电阻: {elementId} 阻值: {resistance}Ω");
    }

    /// <summary>
    /// 创建电容元件
    /// </summary>
    public void CreateCapacitor(string elementId, string node1, string node2, float capacitance)
    {
        if (!nodes.ContainsKey(node1) || !nodes.ContainsKey(node2))
        {
            Debug.LogError($"节点不存在: {node1} 或 {node2}");
            return;
        }

        var capacitor = new Capacitor
        {
            id = elementId,
            node1 = node1,
            node2 = node2,
            capacitance = capacitance,
            voltage = 0f,
            current = 0f,
            charge = 0f
        };

        elements.Add(capacitor);
        nodes[node1].connections.Add(elementId);
        nodes[node2].connections.Add(elementId);

        Debug.Log($"创建电容: {elementId} 容值: {capacitance}F");
    }

    /// <summary>
    /// 执行单步仿真
    /// </summary>
    public void SimulateStep()
    {
        if (nodes.Count == 0) return;

        iterationCount = 0;
        bool converged = false;

        while (iterationCount < maxIterations && !converged)
        {
            // 使用牛顿-拉夫森方法求解非线性电路
            converged = SolveCircuit();
            iterationCount++;
        }

        if (converged)
        {
            UpdateElementStates();
            CalculateTotalPower();
            BroadcastCircuitState();
        }
        else
        {
            Debug.LogWarning($"仿真未收敛，迭代次数: {iterationCount}");
        }
    }

    /// <summary>
    /// 求解电路方程
    /// </summary>
    private bool SolveCircuit()
    {
        // 构建节点电压方程组
        int nodeCount = nodes.Count;
        if (nodeCount <= 1) return true;

        // 简化的欧姆定律求解
        foreach (var element in elements)
        {
            var node1 = nodes[element.node1];
            var node2 = nodes[element.node2];
            float voltageDiff = node1.voltage - node2.voltage;

            switch (element)
            {
                case Resistor r:
                    r.current = voltageDiff / r.resistance;
                    r.voltage = voltageDiff;
                    break;

                case Capacitor c:
                    // 电容电流 = C * dV/dt
                    float dvdt = voltageDiff / timeStep;
                    c.current = c.capacitance * dvdt;
                    c.voltage = voltageDiff;
                    c.charge += c.current * timeStep;
                    break;
            }
        }

        // 检查收敛性
        float maxChange = 0f;
        foreach (var node in nodes.Values)
        {
            float oldVoltage = node.voltage;
            float newVoltage = CalculateNodeVoltage(node);
            float change = Mathf.Abs(newVoltage - oldVoltage);
            maxChange = Mathf.Max(maxChange, change);
            node.voltage = newVoltage;
        }

        return maxChange < convergenceThreshold;
    }

    /// <summary>
    /// 计算节点电压
    /// </summary>
    private float CalculateNodeVoltage(CircuitNode node)
    {
        if (node.id == "Node_GND") return 0f; // 地节点电压固定为0

        float totalCurrent = 0f;
        float totalConductance = 0f;

        foreach (string elementId in node.connections)
        {
            var element = elements.Find(e => e.id == elementId);
            if (element == null) continue;

            bool isConnectedToNode1 = element.node1 == node.id;
            string otherNode = isConnectedToNode1 ? element.node2 : element.node1;
            float otherVoltage = nodes[otherNode].voltage;

            switch (element)
            {
                case Resistor r:
                    float conductance = 1f / r.resistance;
                    totalConductance += conductance;
                    totalCurrent += conductance * otherVoltage;
                    break;

                case Capacitor c:
                    // 电容的瞬时导纳
                    float capacitiveConductance = c.capacitance / timeStep;
                    totalConductance += capacitiveConductance;
                    totalCurrent += capacitiveConductance * otherVoltage;
                    break;
            }
        }

        return totalConductance > 0 ? totalCurrent / totalConductance : 0f;
    }

    /// <summary>
    /// 更新元件状态
    /// </summary>
    private void UpdateElementStates()
    {
        foreach (var element in elements)
        {
            var node1 = nodes[element.node1];
            var node2 = nodes[element.node2];
            float voltageDiff = node1.voltage - node2.voltage;

            element.voltage = voltageDiff;

            switch (element)
            {
                case Resistor r:
                    r.current = voltageDiff / r.resistance;
                    break;

                case Capacitor c:
                    float dvdt = voltageDiff / timeStep;
                    c.current = c.capacitance * dvdt;
                    break;
            }
        }
    }

    /// <summary>
    /// 计算总功率
    /// </summary>
    private void CalculateTotalPower()
    {
        float totalPower = 0f;
        float totalCurrent = 0f;

        foreach (var element in elements)
        {
            float power = Mathf.Abs(element.voltage * element.current);
            totalPower += power;
            totalCurrent += Mathf.Abs(element.current);
        }

        // 触发功率变化事件
        OnElementValueChanged?.Invoke("TotalPower", totalPower);
        OnElementValueChanged?.Invoke("TotalCurrent", totalCurrent);
    }

    /// <summary>
    /// 广播电路状态
    /// </summary>
    private void BroadcastCircuitState()
    {
        var state = new CircuitState
        {
            timestamp = Time.time,
            nodeStates = new Dictionary<string, NodeState>(),
            elementStates = new Dictionary<string, ElementState>(),
            totalPower = 0f,
            totalCurrent = 0f
        };

        // 收集节点状态
        foreach (var kvp in nodes)
        {
            state.nodeStates[kvp.Key] = new NodeState
            {
                position = kvp.Value.position,
                voltage = kvp.Value.voltage,
                charge = 0f // 简化处理
            };
        }

        // 收集元件状态
        foreach (var element in elements)
        {
            state.elementStates[element.id] = new ElementState
            {
                type = element.GetType().Name,
                voltage = element.voltage,
                current = element.current,
                power = Mathf.Abs(element.voltage * element.current),
                connectionPoints = new Vector3[]
                {
                    nodes[element.node1].position,
                    nodes[element.node2].position
                }
            };
        }

        OnCircuitStateChanged?.Invoke(state);
    }

    /// <summary>
    /// 开始仿真
    /// </summary>
    public void StartSimulation()
    {
        isSimulating = true;
        simulationTimer = 0f;
        Debug.Log("电路仿真已启动");
    }

    /// <summary>
    /// 停止仿真
    /// </summary>
    public void StopSimulation()
    {
        isSimulating = false;
        Debug.Log("电路仿真已停止");
    }

    /// <summary>
    /// 重置电路状态
    /// </summary>
    public void ResetCircuit()
    {
        foreach (var node in nodes.Values)
        {
            node.voltage = node.id == "Node_GND" ? 0f : 5f;
        }

        foreach (var element in elements)
        {
            element.voltage = 0f;
            element.current = 0f;

            if (element is Capacitor c)
            {
                c.charge = 0f;
            }
        }

        Debug.Log("电路状态已重置");
    }

    // 电路元件基类
    public abstract class CircuitElement
    {
        public string id;
        public string node1;
        public string node2;
        public float voltage;
        public float current;
    }

    public class Resistor : CircuitElement
    {
        public float resistance;
    }

    public class Capacitor : CircuitElement
    {
        public float capacitance;
        public float charge;
    }

    public class CircuitNode
    {
        public string id;
        public Vector3 position;
        public float voltage;
        public List<string> connections;
    }

    public class VoltageSource
    {
        public string id;
        public string nodePositive;
        public string nodeNegative;
        public float voltage;
    }

    public class CurrentSource
    {
        public string id;
        public string nodeIn;
        public string nodeOut;
        public float current;
    }
}
