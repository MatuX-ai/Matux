package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// 组织MSP ID常量定义
const (
	EducationBureauMSP = "EducationBureauMSP" // 教育局组织MSP ID
	SchoolMSP          = "SchoolMSP"          // 学校组织MSP ID
	EnterpriseMSP      = "EnterpriseMSP"      // 企业组织MSP ID
)

// Integral 积分结构体定义
type Integral struct {
	StudentID string `json:"student_id"` // 学生唯一标识
	Amount    int    `json:"amount"`     // 积分数量
	Source    string `json:"source"`     // 积分来源（任务/兑换）
	Timestamp int64  `json:"timestamp"`  // 时间戳
}

// IntegralTransaction 积分交易记录
type IntegralTransaction struct {
	ID          string `json:"id"`          // 交易唯一标识
	StudentID   string `json:"student_id"`  // 学生ID
	Amount      int    `json:"amount"`      // 交易积分数量（正数为获得，负数为消耗）
	SourceType  string `json:"source_type"` // 来源类型（earn/spend）
	SourceID    string `json:"source_id"`   // 来源ID（任务ID或商品ID）
	Description string `json:"description"` // 交易描述
	Timestamp   int64  `json:"timestamp"`   // 交易时间戳
	Balance     int    `json:"balance"`     // 交易后余额
}

// IntegralRule 积分规则定义
type IntegralRule struct {
	ID          string `json:"id"`          // 规则ID
	Name        string `json:"name"`        // 规则名称
	Description string `json:"description"` // 规则描述
	EventType   string `json:"event_type"`  // 事件类型（task_complete, login_daily等）
	BaseAmount  int    `json:"base_amount"` // 基础积分数量
	MaxDaily    int    `json:"max_daily"`   // 每日上限
	IsActive    bool   `json:"is_active"`   // 是否启用
	CreatedAt   int64  `json:"created_at"`  // 创建时间
	UpdatedAt   int64  `json:"updated_at"`  // 更新时间
}

// StudentBalance 学生积分余额
type StudentBalance struct {
	StudentID   string `json:"student_id"`   // 学生ID
	TotalAmount int    `json:"total_amount"` // 总积分余额
	UpdatedAt   int64  `json:"updated_at"`   // 最后更新时间
}

// 积分衰减配置
type DecayConfig struct {
	DecayRate    float64 `json:"decay_rate"`    // 衰减率 (每日衰减百分比)
	MinThreshold int     `json:"min_threshold"` // 最小阈值 (低于此值不衰减)
	GracePeriod  int     `json:"grace_period"`  // 宽限期 (天数)
	IsActive     bool    `json:"is_active"`     // 是否启用衰减
	CreatedAt    int64   `json:"created_at"`    // 创建时间
	UpdatedAt    int64   `json:"updated_at"`    // 更新时间
}

// 任务状态跟踪
type TaskStatus struct {
	TaskID       string `json:"task_id"`       // 任务ID
	StudentID    string `json:"student_id"`    // 学生ID
	Status       string `json:"status"`        // 任务状态 (pending/completed/expired)
	AssignedAt   int64  `json:"assigned_at"`   // 分配时间
	CompletedAt  int64  `json:"completed_at"`  // 完成时间
	LastActivity int64  `json:"last_activity"` // 最后活动时间
	DecayApplied bool   `json:"decay_applied"` // 是否已应用衰减
}

// 多模态奖励记录
type MultimodalReward struct {
	RewardID     string `json:"reward_id"`     // 奖励ID
	StudentID    string `json:"student_id"`    // 学生ID
	RewardType   string `json:"reward_type"`   // 奖励类型 (voice/ar/gesture)
	Amount       int    `json:"amount"`        // 奖励积分
	Description  string `json:"description"`   // 奖励描述
	TriggerEvent string `json:"trigger_event"` // 触发事件
	Timestamp    int64  `json:"timestamp"`     // 时间戳
	IsValidated  bool   `json:"is_validated"`  // 是否已验证
}

// Validate 验证Integral结构体数据有效性
func (i *Integral) Validate() error {
	// 验证学生ID不能为空
	if i.StudentID == "" {
		return fmt.Errorf("student_id cannot be empty")
	}

	// 验证积分数量必须大于0
	if i.Amount <= 0 {
		return fmt.Errorf("amount must be greater than 0")
	}

	// 验证积分来源不能为空
	if i.Source == "" {
		return fmt.Errorf("source cannot be empty")
	}

	// 验证时间戳有效性
	if i.Timestamp <= 0 {
		return fmt.Errorf("timestamp must be greater than 0")
	}

	// 验证时间戳不超过当前时间
	currentTime := time.Now().Unix()
	if i.Timestamp > currentTime {
		return fmt.Errorf("timestamp cannot be in the future")
	}

	return nil
}

// ToJSON 将Integral结构体转换为JSON字符串
func (i *Integral) ToJSON() (string, error) {
	bytes, err := json.Marshal(i)
	if err != nil {
		return "", fmt.Errorf("failed to marshal integral to JSON: %v", err)
	}
	return string(bytes), nil
}

// FromJSON 从JSON字符串解析Integral结构体
func (i *Integral) FromJSON(jsonStr string) error {
	err := json.Unmarshal([]byte(jsonStr), i)
	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON to integral: %v", err)
	}
	return nil
}

// ValidateTransaction 验证积分交易数据有效性
func (t *IntegralTransaction) Validate() error {
	// 验证交易ID不能为空
	if t.ID == "" {
		return fmt.Errorf("transaction id cannot be empty")
	}

	// 验证学生ID不能为空
	if t.StudentID == "" {
		return fmt.Errorf("student_id cannot be empty")
	}

	// 验证金额不能为0
	if t.Amount == 0 {
		return fmt.Errorf("amount cannot be zero")
	}

	// 验证来源类型
	if t.SourceType != "earn" && t.SourceType != "spend" {
		return fmt.Errorf("source_type must be 'earn' or 'spend'")
	}

	// 验证来源ID不能为空
	if t.SourceID == "" {
		return fmt.Errorf("source_id cannot be empty")
	}

	// 验证描述不能为空
	if t.Description == "" {
		return fmt.Errorf("description cannot be empty")
	}

	// 验证时间戳
	if t.Timestamp <= 0 {
		return fmt.Errorf("timestamp must be greater than 0")
	}

	// 验证余额不能为负数
	if t.Balance < 0 {
		return fmt.Errorf("balance cannot be negative")
	}

	return nil
}

// ValidateRule 验证积分规则数据有效性
func (r *IntegralRule) Validate() error {
	// 验证规则ID不能为空
	if r.ID == "" {
		return fmt.Errorf("rule id cannot be empty")
	}

	// 验证规则名称不能为空
	if r.Name == "" {
		return fmt.Errorf("rule name cannot be empty")
	}

	// 验证事件类型不能为空
	if r.EventType == "" {
		return fmt.Errorf("event type cannot be empty")
	}

	// 验证基础积分数量必须大于0
	if r.BaseAmount <= 0 {
		return fmt.Errorf("base amount must be greater than 0")
	}

	// 验证每日上限不能为负数
	if r.MaxDaily < 0 {
		return fmt.Errorf("max daily cannot be negative")
	}

	// 如果设置了每日上限，必须大于等于基础积分
	if r.MaxDaily > 0 && r.MaxDaily < r.BaseAmount {
		return fmt.Errorf("max daily must be greater than or equal to base amount")
	}

	// 验证时间戳
	if r.CreatedAt <= 0 {
		return fmt.Errorf("created_at must be greater than 0")
	}

	if r.UpdatedAt <= 0 {
		return fmt.Errorf("updated_at must be greater than 0")
	}

	return nil
}

// ValidateBalance 验证学生余额数据有效性
func (b *StudentBalance) Validate() error {
	// 验证学生ID不能为空
	if b.StudentID == "" {
		return fmt.Errorf("student_id cannot be empty")
	}

	// 验证总积分不能为负数
	if b.TotalAmount < 0 {
		return fmt.Errorf("total_amount cannot be negative")
	}

	// 验证更新时间
	if b.UpdatedAt <= 0 {
		return fmt.Errorf("updated_at must be greater than 0")
	}

	return nil
}

// CheckEducationBureauPermission 检查调用者是否具有教育局权限
// 仅允许EducationBureauMSP组织调用特定敏感操作
func CheckEducationBureauPermission(ctx contractapi.TransactionContextInterface) error {
	// 获取客户端身份信息
	clientIdentity := ctx.GetClientIdentity()
	if clientIdentity == nil {
		return fmt.Errorf("无法获取客户端身份信息")
	}

	// 获取MSP ID
	mspID, err := clientIdentity.GetMSPID()
	if err != nil {
		return fmt.Errorf("获取MSP ID失败: %v", err)
	}

	// 验证是否为教育局组织
	if mspID != EducationBureauMSP {
		return fmt.Errorf("权限不足: 仅教育局组织可执行此操作，当前MSP ID: %s", mspID)
	}

	return nil
}

// GetCallerMSPID 获取调用者的MSP ID
func GetCallerMSPID(ctx contractapi.TransactionContextInterface) (string, error) {
	clientIdentity := ctx.GetClientIdentity()
	if clientIdentity == nil {
		return "", fmt.Errorf("无法获取客户端身份信息")
	}

	mspID, err := clientIdentity.GetMSPID()
	if err != nil {
		return "", fmt.Errorf("获取MSP ID失败: %v", err)
	}

	return mspID, nil
}

// ValidateDecayConfig 验证衰减配置数据有效性
func (dc *DecayConfig) Validate() error {
	// 验证衰减率范围 (0-100%)
	if dc.DecayRate < 0 || dc.DecayRate > 100 {
		return fmt.Errorf("decay_rate must be between 0 and 100")
	}

	// 验证最小阈值不能为负数
	if dc.MinThreshold < 0 {
		return fmt.Errorf("min_threshold cannot be negative")
	}

	// 验证宽限期不能为负数
	if dc.GracePeriod < 0 {
		return fmt.Errorf("grace_period cannot be negative")
	}

	// 验证时间戳
	if dc.CreatedAt <= 0 {
		return fmt.Errorf("created_at must be greater than 0")
	}

	if dc.UpdatedAt <= 0 {
		return fmt.Errorf("updated_at must be greater than 0")
	}

	return nil
}

// ValidateTaskStatus 验证任务状态数据有效性
func (ts *TaskStatus) Validate() error {
	// 验证任务ID不能为空
	if ts.TaskID == "" {
		return fmt.Errorf("task_id cannot be empty")
	}

	// 验证学生ID不能为空
	if ts.StudentID == "" {
		return fmt.Errorf("student_id cannot be empty")
	}

	// 验证状态值
	validStatuses := []string{"pending", "completed", "expired"}
	isValidStatus := false
	for _, status := range validStatuses {
		if ts.Status == status {
			isValidStatus = true
			break
		}
	}

	if !isValidStatus {
		return fmt.Errorf("invalid status: %s", ts.Status)
	}

	// 验证时间戳
	if ts.AssignedAt <= 0 {
		return fmt.Errorf("assigned_at must be greater than 0")
	}

	return nil
}

// ValidateMultimodalReward 验证多模态奖励数据有效性
func (mr *MultimodalReward) Validate() error {
	// 验证奖励ID不能为空
	if mr.RewardID == "" {
		return fmt.Errorf("reward_id cannot be empty")
	}

	// 验证学生ID不能为空
	if mr.StudentID == "" {
		return fmt.Errorf("student_id cannot be empty")
	}

	// 验证奖励类型
	validTypes := []string{"voice", "ar", "gesture", "multimodal"}
	isValidType := false
	for _, rewardType := range validTypes {
		if mr.RewardType == rewardType {
			isValidType = true
			break
		}
	}

	if !isValidType {
		return fmt.Errorf("invalid reward_type: %s", mr.RewardType)
	}

	// 验证奖励积分必须大于0
	if mr.Amount <= 0 {
		return fmt.Errorf("amount must be greater than 0")
	}

	// 验证描述不能为空
	if mr.Description == "" {
		return fmt.Errorf("description cannot be empty")
	}

	// 验证时间戳
	if mr.Timestamp <= 0 {
		return fmt.Errorf("timestamp must be greater than 0")
	}

	return nil
}

// CalculateDecayAmount 计算衰减积分数量
func (dc *DecayConfig) CalculateDecayAmount(currentAmount int, daysElapsed int) int {
	// 如果未启用衰减或在宽限期内，不衰减
	if !dc.IsActive || daysElapsed <= dc.GracePeriod {
		return 0
	}

	// 如果当前积分低于最小阈值，不衰减
	if currentAmount <= dc.MinThreshold {
		return 0
	}

	// 计算衰减后的积分
	decayMultiplier := 1.0 - (dc.DecayRate / 100.0)
	decayedAmount := float64(currentAmount) * decayMultiplier

	// 计算实际衰减数量
	decayAmount := currentAmount - int(decayedAmount)

	// 确保衰减后不低于最小阈值
	if currentAmount-decayAmount < dc.MinThreshold {
		decayAmount = currentAmount - dc.MinThreshold
	}

	return decayAmount
}
