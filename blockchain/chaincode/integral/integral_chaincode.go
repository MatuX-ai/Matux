package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// IntegralChaincode 积分智能合约
type IntegralChaincode struct {
	contractapi.Contract
}

// InitLedger 初始化账本
func (ic *IntegralChaincode) InitLedger(ctx contractapi.TransactionContextInterface) error {
	log.Println("初始化积分账本")

	// 创建初始积分规则示例
	rules := []IntegralRule{
		{
			ID:          "rule_daily_login",
			Name:        "每日登录奖励",
			Description: "用户每日首次登录系统获得积分",
			EventType:   "daily_login",
			BaseAmount:  10,
			MaxDaily:    10,
			IsActive:    true,
			CreatedAt:   time.Now().Unix(),
			UpdatedAt:   time.Now().Unix(),
		},
		{
			ID:          "rule_task_complete",
			Name:        "任务完成奖励",
			Description: "完成学习任务获得相应积分",
			EventType:   "task_complete",
			BaseAmount:  50,
			MaxDaily:    500,
			IsActive:    true,
			CreatedAt:   time.Now().Unix(),
			UpdatedAt:   time.Now().Unix(),
		},
		{
			ID:          "rule_course_finish",
			Name:        "课程完成奖励",
			Description: "完成整个课程学习获得积分",
			EventType:   "course_finish",
			BaseAmount:  200,
			MaxDaily:    1000,
			IsActive:    true,
			CreatedAt:   time.Now().Unix(),
			UpdatedAt:   time.Now().Unix(),
		},
	}

	// 存储初始规则
	for _, rule := range rules {
		ruleBytes, err := json.Marshal(rule)
		if err != nil {
			return fmt.Errorf("序列化规则失败: %v", err)
		}

		err = ctx.GetStub().PutState("rule_"+rule.ID, ruleBytes)
		if err != nil {
			return fmt.Errorf("存储规则失败: %v", err)
		}
	}

	// 创建初始衰减配置
	decayConfig := DecayConfig{
		DecayRate:    2.0,   // 每日衰减2%
		MinThreshold: 100,   // 最低保留100积分
		GracePeriod:  7,     // 7天宽限期
		IsActive:     false, // 默认不启用
		CreatedAt:    time.Now().Unix(),
		UpdatedAt:    time.Now().Unix(),
	}

	// 验证并存储衰减配置
	if err := decayConfig.Validate(); err != nil {
		return fmt.Errorf("衰减配置验证失败: %v", err)
	}

	decayConfigBytes, err := json.Marshal(decayConfig)
	if err != nil {
		return fmt.Errorf("序列化衰减配置失败: %v", err)
	}

	err = ctx.GetStub().PutState("config_decay", decayConfigBytes)
	if err != nil {
		return fmt.Errorf("存储衰减配置失败: %v", err)
	}

	// 创建一些示例学生余额用于测试
	balances := []StudentBalance{
		{
			StudentID:   "student_001",
			TotalAmount: 1000,
			UpdatedAt:   time.Now().Unix(),
		},
		{
			StudentID:   "student_002",
			TotalAmount: 500,
			UpdatedAt:   time.Now().Unix(),
		},
	}

	// 存储初始余额
	for _, balance := range balances {
		balanceBytes, err := json.Marshal(balance)
		if err != nil {
			return fmt.Errorf("序列化余额失败: %v", err)
		}

		err = ctx.GetStub().PutState("balance_"+balance.StudentID, balanceBytes)
		if err != nil {
			return fmt.Errorf("存储余额失败: %v", err)
		}
	}

	log.Println("积分账本初始化完成")
	return nil
}

// AddIntegral 为学生增加积分
func (ic *IntegralChaincode) AddIntegral(ctx contractapi.TransactionContextInterface, integralJSON string) (string, error) {
	log.Printf("增加积分: %s", integralJSON)

	var integral Integral
	err := integral.FromJSON(integralJSON)
	if err != nil {
		return "", fmt.Errorf("解析积分数据失败: %v", err)
	}

	// 验证数据有效性
	err = integral.Validate()
	if err != nil {
		return "", fmt.Errorf("积分数据验证失败: %v", err)
	}

	// 获取学生当前余额
	balanceKey := "balance_" + integral.StudentID
	balanceBytes, err := ctx.GetStub().GetState(balanceKey)
	if err != nil {
		return "", fmt.Errorf("获取学生余额失败: %v", err)
	}

	var studentBalance StudentBalance
	if balanceBytes == nil {
		// 如果不存在，则创建新的余额记录
		studentBalance = StudentBalance{
			StudentID:   integral.StudentID,
			TotalAmount: 0,
			UpdatedAt:   time.Now().Unix(),
		}
	} else {
		err = json.Unmarshal(balanceBytes, &studentBalance)
		if err != nil {
			return "", fmt.Errorf("解析学生余额失败: %v", err)
		}
	}

	// 更新余额
	studentBalance.TotalAmount += integral.Amount
	studentBalance.UpdatedAt = time.Now().Unix()

	// 保存更新后的余额
	balanceBytes, err = json.Marshal(studentBalance)
	if err != nil {
		return "", fmt.Errorf("序列化余额失败: %v", err)
	}

	err = ctx.GetStub().PutState(balanceKey, balanceBytes)
	if err != nil {
		return "", fmt.Errorf("保存余额失败: %v", err)
	}

	// 创建交易记录
	transaction := IntegralTransaction{
		ID:          fmt.Sprintf("tx_%d", time.Now().UnixNano()),
		StudentID:   integral.StudentID,
		Amount:      integral.Amount,
		SourceType:  "earn",
		SourceID:    integral.Source,
		Description: fmt.Sprintf("通过%s获得积分", integral.Source),
		Timestamp:   integral.Timestamp,
		Balance:     studentBalance.TotalAmount,
	}

	// 保存交易记录
	transactionBytes, err := json.Marshal(transaction)
	if err != nil {
		return "", fmt.Errorf("序列化交易记录失败: %v", err)
	}

	err = ctx.GetStub().PutState(transaction.ID, transactionBytes)
	if err != nil {
		return "", fmt.Errorf("保存交易记录失败: %v", err)
	}

	log.Printf("成功为学生 %s 增加 %d 积分，当前余额: %d",
		integral.StudentID, integral.Amount, studentBalance.TotalAmount)

	return transaction.ID, nil
}

// DeductIntegral 扣除学生积分
func (ic *IntegralChaincode) DeductIntegral(ctx contractapi.TransactionContextInterface, studentID string, amount int, reason string) (string, error) {
	log.Printf("扣除积分: studentID=%s, amount=%d, reason=%s", studentID, amount, reason)

	// 验证参数
	if studentID == "" {
		return "", fmt.Errorf("studentID不能为空")
	}
	if amount <= 0 {
		return "", fmt.Errorf("扣除积分数量必须大于0")
	}

	// 获取学生当前余额
	balanceKey := "balance_" + studentID
	balanceBytes, err := ctx.GetStub().GetState(balanceKey)
	if err != nil {
		return "", fmt.Errorf("获取学生余额失败: %v", err)
	}

	if balanceBytes == nil {
		return "", fmt.Errorf("学生 %s 的余额记录不存在", studentID)
	}

	var studentBalance StudentBalance
	err = json.Unmarshal(balanceBytes, &studentBalance)
	if err != nil {
		return "", fmt.Errorf("解析学生余额失败: %v", err)
	}

	// 检查余额是否充足
	if studentBalance.TotalAmount < amount {
		return "", fmt.Errorf("余额不足: 当前余额 %d, 需要扣除 %d",
			studentBalance.TotalAmount, amount)
	}

	// 扣除积分
	studentBalance.TotalAmount -= amount
	studentBalance.UpdatedAt = time.Now().Unix()

	// 保存更新后的余额
	balanceBytes, err = json.Marshal(studentBalance)
	if err != nil {
		return "", fmt.Errorf("序列化余额失败: %v", err)
	}

	err = ctx.GetStub().PutState(balanceKey, balanceBytes)
	if err != nil {
		return "", fmt.Errorf("保存余额失败: %v", err)
	}

	// 创建交易记录
	transaction := IntegralTransaction{
		ID:          fmt.Sprintf("tx_%d", time.Now().UnixNano()),
		StudentID:   studentID,
		Amount:      -amount, // 负数表示扣除
		SourceType:  "spend",
		SourceID:    "deduction",
		Description: reason,
		Timestamp:   time.Now().Unix(),
		Balance:     studentBalance.TotalAmount,
	}

	// 保存交易记录
	transactionBytes, err := json.Marshal(transaction)
	if err != nil {
		return "", fmt.Errorf("序列化交易记录失败: %v", err)
	}

	err = ctx.GetStub().PutState(transaction.ID, transactionBytes)
	if err != nil {
		return "", fmt.Errorf("保存交易记录失败: %v", err)
	}

	log.Printf("成功为学生 %s 扣除 %d 积分，当前余额: %d",
		studentID, amount, studentBalance.TotalAmount)

	return transaction.ID, nil
}

// GetStudentBalance 查询学生积分余额
func (ic *IntegralChaincode) GetStudentBalance(ctx contractapi.TransactionContextInterface, studentID string) (*StudentBalance, error) {
	log.Printf("查询学生余额: %s", studentID)

	if studentID == "" {
		return nil, fmt.Errorf("studentID不能为空")
	}

	balanceKey := "balance_" + studentID
	balanceBytes, err := ctx.GetStub().GetState(balanceKey)
	if err != nil {
		return nil, fmt.Errorf("获取学生余额失败: %v", err)
	}

	if balanceBytes == nil {
		// 返回零余额而不是错误
		return &StudentBalance{
			StudentID:   studentID,
			TotalAmount: 0,
			UpdatedAt:   time.Now().Unix(),
		}, nil
	}

	var studentBalance StudentBalance
	err = json.Unmarshal(balanceBytes, &studentBalance)
	if err != nil {
		return nil, fmt.Errorf("解析学生余额失败: %v", err)
	}

	return &studentBalance, nil
}

// GetTransactionHistory 查询学生积分交易历史
func (ic *IntegralChaincode) GetTransactionHistory(ctx contractapi.TransactionContextInterface, studentID string) ([]*IntegralTransaction, error) {
	log.Printf("查询交易历史: %s", studentID)

	if studentID == "" {
		return nil, fmt.Errorf("studentID不能为空")
	}

	// 使用富查询（需要CouchDB）
	queryString := fmt.Sprintf(`{
		"selector": {
			"student_id": "%s"
		},
		"sort": [{"timestamp": "desc"}]
	}`, studentID)

	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("查询交易记录失败: %v", err)
	}
	defer resultsIterator.Close()

	var transactions []*IntegralTransaction
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("遍历查询结果失败: %v", err)
		}

		var transaction IntegralTransaction
		err = json.Unmarshal(queryResponse.Value, &transaction)
		if err != nil {
			log.Printf("解析交易记录失败: %v", err)
			continue
		}

		transactions = append(transactions, &transaction)
	}

	return transactions, nil
}

// GetActiveRules 获取所有激活的积分规则
func (ic *IntegralChaincode) GetActiveRules(ctx contractapi.TransactionContextInterface) ([]*IntegralRule, error) {
	log.Println("获取激活的积分规则")

	// 查询所有规则
	resultsIterator, err := ctx.GetStub().GetStateByRange("rule_", "rule_~")
	if err != nil {
		return nil, fmt.Errorf("查询规则失败: %v", err)
	}
	defer resultsIterator.Close()

	var activeRules []*IntegralRule
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("遍历规则失败: %v", err)
		}

		var rule IntegralRule
		err = json.Unmarshal(queryResponse.Value, &rule)
		if err != nil {
			log.Printf("解析规则失败: %v", err)
			continue
		}

		// 只返回激活的规则
		if rule.IsActive {
			activeRules = append(activeRules, &rule)
		}
	}

	return activeRules, nil
}

// CreateRule 创建新的积分规则
func (ic *IntegralChaincode) CreateRule(ctx contractapi.TransactionContextInterface, ruleJSON string) error {
	log.Printf("创建积分规则: %s", ruleJSON)

	var rule IntegralRule
	err := json.Unmarshal([]byte(ruleJSON), &rule)
	if err != nil {
		return fmt.Errorf("解析规则数据失败: %v", err)
	}

	// 验证规则数据
	err = rule.Validate()
	if err != nil {
		return fmt.Errorf("规则数据验证失败: %v", err)
	}

	// 检查规则是否已存在
	ruleKey := "rule_" + rule.ID
	existingRuleBytes, err := ctx.GetStub().GetState(ruleKey)
	if err != nil {
		return fmt.Errorf("检查规则存在性失败: %v", err)
	}

	if existingRuleBytes != nil {
		return fmt.Errorf("规则 %s 已存在", rule.ID)
	}

	// 存储规则
	ruleBytes, err := json.Marshal(rule)
	if err != nil {
		return fmt.Errorf("序列化规则失败: %v", err)
	}

	err = ctx.GetStub().PutState(ruleKey, ruleBytes)
	if err != nil {
		return fmt.Errorf("存储规则失败: %v", err)
	}

	log.Printf("成功创建规则: %s", rule.Name)
	return nil
}

// IssueIntegral 发行积分给学生
// 仅教育局组织可以调用此函数
func (ic *IntegralChaincode) IssueIntegral(ctx contractapi.TransactionContextInterface, studentID string, amount int) error {
	log.Printf("发行积分: studentID=%s, amount=%d", studentID, amount)

	// 1. 检查调用者权限（仅教育局）
	if err := CheckEducationBureauPermission(ctx); err != nil {
		return fmt.Errorf("权限验证失败: %v", err)
	}

	// 2. 验证输入参数
	if studentID == "" {
		return fmt.Errorf("学生ID不能为空")
	}
	if amount <= 0 {
		return fmt.Errorf("积分数量必须大于0")
	}

	// 3. 获取学生当前余额
	balanceKey := "balance_" + studentID
	balanceBytes, err := ctx.GetStub().GetState(balanceKey)
	if err != nil {
		return fmt.Errorf("获取学生余额失败: %v", err)
	}

	var studentBalance StudentBalance
	if balanceBytes == nil {
		// 如果学生余额不存在，创建新的余额记录
		studentBalance = StudentBalance{
			StudentID:   studentID,
			TotalAmount: 0,
			UpdatedAt:   time.Now().Unix(),
		}
	} else {
		// 解析现有余额记录
		err = json.Unmarshal(balanceBytes, &studentBalance)
		if err != nil {
			return fmt.Errorf("解析学生余额失败: %v", err)
		}
	}

	// 4. 更新余额
	studentBalance.TotalAmount += amount
	studentBalance.UpdatedAt = time.Now().Unix()

	// 5. 验证更新后的余额数据
	if err := studentBalance.Validate(); err != nil {
		return fmt.Errorf("余额数据验证失败: %v", err)
	}

	// 6. 保存更新后的余额到区块链
	balanceBytes, err = json.Marshal(studentBalance)
	if err != nil {
		return fmt.Errorf("序列化余额失败: %v", err)
	}

	err = ctx.GetStub().PutState(balanceKey, balanceBytes)
	if err != nil {
		return fmt.Errorf("保存余额到区块链失败: %v", err)
	}

	// 7. 创建积分发行记录
	issueRecord := Integral{
		StudentID: studentID,
		Amount:    amount,
		Source:    "education", // 标识为教育局发行
		Timestamp: time.Now().Unix(),
	}

	// 8. 验证积分记录数据
	if err := issueRecord.Validate(); err != nil {
		return fmt.Errorf("积分记录验证失败: %v", err)
	}

	// 9. 生成唯一的积分记录键
	recordKey := fmt.Sprintf("issue_%s_%d", studentID, time.Now().UnixNano())

	// 10. 序列化积分记录
	recordBytes, err := json.Marshal(issueRecord)
	if err != nil {
		return fmt.Errorf("序列化积分记录失败: %v", err)
	}

	// 11. 保存积分记录到区块链
	err = ctx.GetStub().PutState(recordKey, recordBytes)
	if err != nil {
		return fmt.Errorf("保存积分记录到区块链失败: %v", err)
	}

	// 12. 创建交易记录
	transaction := IntegralTransaction{
		ID:          fmt.Sprintf("tx_issue_%d", time.Now().UnixNano()),
		StudentID:   studentID,
		Amount:      amount,
		SourceType:  "issue",
		SourceID:    "education_bureau",
		Description: fmt.Sprintf("教育局发行积分 %d 点", amount),
		Timestamp:   time.Now().Unix(),
		Balance:     studentBalance.TotalAmount,
	}

	// 13. 保存交易记录
	transactionBytes, err := json.Marshal(transaction)
	if err != nil {
		return fmt.Errorf("序列化交易记录失败: %v", err)
	}

	err = ctx.GetStub().PutState(transaction.ID, transactionBytes)
	if err != nil {
		return fmt.Errorf("保存交易记录失败: %v", err)
	}

	log.Printf("成功为学生 %s 发行 %d 积分，当前余额: %d",
		studentID, amount, studentBalance.TotalAmount)

	return nil
}

// UpdateRule 更新积分规则
func (ic *IntegralChaincode) UpdateRule(ctx contractapi.TransactionContextInterface, ruleJSON string) error {
	log.Printf("更新积分规则: %s", ruleJSON)

	var rule IntegralRule
	err := json.Unmarshal([]byte(ruleJSON), &rule)
	if err != nil {
		return fmt.Errorf("解析规则数据失败: %v", err)
	}

	// 验证规则数据
	err = rule.Validate()
	if err != nil {
		return fmt.Errorf("规则数据验证失败: %v", err)
	}

	// 检查规则是否存在
	ruleKey := "rule_" + rule.ID
	existingRuleBytes, err := ctx.GetStub().GetState(ruleKey)
	if err != nil {
		return fmt.Errorf("检查规则存在性失败: %v", err)
	}

	if existingRuleBytes == nil {
		return fmt.Errorf("规则 %s 不存在", rule.ID)
	}

	// 更新时间戳
	rule.UpdatedAt = time.Now().Unix()

	// 存储更新后的规则
	ruleBytes, err := json.Marshal(rule)
	if err != nil {
		return fmt.Errorf("序列化规则失败: %v", err)
	}

	err = ctx.GetStub().PutState(ruleKey, ruleBytes)
	if err != nil {
		return fmt.Errorf("存储规则失败: %v", err)
	}

	log.Printf("成功更新规则: %s", rule.Name)
	return nil
}

// ApplyDecay 应用积分衰减
func (ic *IntegralChaincode) ApplyDecay(ctx contractapi.TransactionContextInterface, studentID string) (int, error) {
	log.Printf("为学生 %s 应用积分衰减", studentID)

	// 1. 获取衰减配置
	configBytes, err := ctx.GetStub().GetState("config_decay")
	if err != nil {
		return 0, fmt.Errorf("获取衰减配置失败: %v", err)
	}

	if configBytes == nil {
		return 0, fmt.Errorf("衰减配置不存在")
	}

	var decayConfig DecayConfig
	err = json.Unmarshal(configBytes, &decayConfig)
	if err != nil {
		return 0, fmt.Errorf("解析衰减配置失败: %v", err)
	}

	// 2. 如果衰减未启用，直接返回
	if !decayConfig.IsActive {
		log.Printf("衰减功能未启用")
		return 0, nil
	}

	// 3. 获取学生余额
	balanceKey := "balance_" + studentID
	balanceBytes, err := ctx.GetStub().GetState(balanceKey)
	if err != nil {
		return 0, fmt.Errorf("获取学生余额失败: %v", err)
	}

	if balanceBytes == nil {
		log.Printf("学生 %s 无余额记录", studentID)
		return 0, nil
	}

	var studentBalance StudentBalance
	err = json.Unmarshal(balanceBytes, &studentBalance)
	if err != nil {
		return 0, fmt.Errorf("解析学生余额失败: %v", err)
	}

	// 4. 计算衰减天数
	currentTime := time.Now().Unix()
	daysElapsed := int((currentTime - studentBalance.UpdatedAt) / 86400) // 86400秒 = 1天

	// 5. 计算衰减积分
	decayAmount := decayConfig.CalculateDecayAmount(studentBalance.TotalAmount, daysElapsed)

	if decayAmount <= 0 {
		log.Printf("学生 %s 无需衰减，当前积分: %d", studentID, studentBalance.TotalAmount)
		return 0, nil
	}

	// 6. 应用衰减
	studentBalance.TotalAmount -= decayAmount
	studentBalance.UpdatedAt = currentTime

	// 7. 验证更新后余额
	if err := studentBalance.Validate(); err != nil {
		return 0, fmt.Errorf("余额验证失败: %v", err)
	}

	// 8. 保存更新后余额
	updatedBalanceBytes, err := json.Marshal(studentBalance)
	if err != nil {
		return 0, fmt.Errorf("序列化余额失败: %v", err)
	}

	err = ctx.GetStub().PutState(balanceKey, updatedBalanceBytes)
	if err != nil {
		return 0, fmt.Errorf("保存余额失败: %v", err)
	}

	// 9. 创建衰减交易记录
	transaction := IntegralTransaction{
		ID:          fmt.Sprintf("tx_decay_%d", time.Now().UnixNano()),
		StudentID:   studentID,
		Amount:      -decayAmount,
		SourceType:  "decay",
		SourceID:    "system_decay",
		Description: fmt.Sprintf("系统自动衰减 %d 积分 (%d天未活动)", decayAmount, daysElapsed),
		Timestamp:   currentTime,
		Balance:     studentBalance.TotalAmount,
	}

	transactionBytes, err := json.Marshal(transaction)
	if err != nil {
		return 0, fmt.Errorf("序列化交易记录失败: %v", err)
	}

	err = ctx.GetStub().PutState(transaction.ID, transactionBytes)
	if err != nil {
		return 0, fmt.Errorf("保存交易记录失败: %v", err)
	}

	log.Printf("成功为学生 %s 衰减 %d 积分，剩余: %d", studentID, decayAmount, studentBalance.TotalAmount)
	return decayAmount, nil
}

// GetDecayConfig 获取衰减配置
func (ic *IntegralChaincode) GetDecayConfig(ctx contractapi.TransactionContextInterface) (*DecayConfig, error) {
	configBytes, err := ctx.GetStub().GetState("config_decay")
	if err != nil {
		return nil, fmt.Errorf("获取衰减配置失败: %v", err)
	}

	if configBytes == nil {
		return nil, fmt.Errorf("衰减配置不存在")
	}

	var config DecayConfig
	err = json.Unmarshal(configBytes, &config)
	if err != nil {
		return nil, fmt.Errorf("解析衰减配置失败: %v", err)
	}

	return &config, nil
}

// UpdateDecayConfig 更新衰减配置
func (ic *IntegralChaincode) UpdateDecayConfig(ctx contractapi.TransactionContextInterface, configJSON string) error {
	log.Printf("更新衰减配置: %s", configJSON)

	// 验证权限（仅教育局可更新）
	if err := CheckEducationBureauPermission(ctx); err != nil {
		return fmt.Errorf("权限验证失败: %v", err)
	}

	var config DecayConfig
	err := json.Unmarshal([]byte(configJSON), &config)
	if err != nil {
		return fmt.Errorf("解析配置失败: %v", err)
	}

	// 验证配置
	if err := config.Validate(); err != nil {
		return fmt.Errorf("配置验证失败: %v", err)
	}

	// 更新时间戳
	config.UpdatedAt = time.Now().Unix()

	// 保存配置
	configBytes, err := json.Marshal(config)
	if err != nil {
		return fmt.Errorf("序列化配置失败: %v", err)
	}

	err = ctx.GetStub().PutState("config_decay", configBytes)
	if err != nil {
		return fmt.Errorf("保存配置失败: %v", err)
	}

	log.Printf("成功更新衰减配置，衰减率: %.2f%%", config.DecayRate)
	return nil
}

// RecordMultimodalReward 记录多模态奖励
func (ic *IntegralChaincode) RecordMultimodalReward(ctx contractapi.TransactionContextInterface, rewardJSON string) (string, error) {
	log.Printf("记录多模态奖励: %s", rewardJSON)

	var reward MultimodalReward
	err := json.Unmarshal([]byte(rewardJSON), &reward)
	if err != nil {
		return "", fmt.Errorf("解析奖励数据失败: %v", err)
	}

	// 验证奖励数据
	if err := reward.Validate(); err != nil {
		return "", fmt.Errorf("奖励数据验证失败: %v", err)
	}

	// 获取学生当前余额
	balanceKey := "balance_" + reward.StudentID
	balanceBytes, err := ctx.GetStub().GetState(balanceKey)
	if err != nil {
		return "", fmt.Errorf("获取学生余额失败: %v", err)
	}

	var studentBalance StudentBalance
	if balanceBytes == nil {
		// 创建新余额记录
		studentBalance = StudentBalance{
			StudentID:   reward.StudentID,
			TotalAmount: 0,
			UpdatedAt:   time.Now().Unix(),
		}
	} else {
		err = json.Unmarshal(balanceBytes, &studentBalance)
		if err != nil {
			return "", fmt.Errorf("解析学生余额失败: %v", err)
		}
	}

	// 更新余额
	studentBalance.TotalAmount += reward.Amount
	studentBalance.UpdatedAt = time.Now().Unix()

	// 保存更新后余额
	updatedBalanceBytes, err := json.Marshal(studentBalance)
	if err != nil {
		return "", fmt.Errorf("序列化余额失败: %v", err)
	}

	err = ctx.GetStub().PutState(balanceKey, updatedBalanceBytes)
	if err != nil {
		return "", fmt.Errorf("保存余额失败: %v", err)
	}

	// 创建交易记录
	transaction := IntegralTransaction{
		ID:          fmt.Sprintf("tx_reward_%d", time.Now().UnixNano()),
		StudentID:   reward.StudentID,
		Amount:      reward.Amount,
		SourceType:  "multimodal_reward",
		SourceID:    reward.RewardID,
		Description: fmt.Sprintf("%s: %s", reward.TriggerEvent, reward.Description),
		Timestamp:   reward.Timestamp,
		Balance:     studentBalance.TotalAmount,
	}

	transactionBytes, err := json.Marshal(transaction)
	if err != nil {
		return "", fmt.Errorf("序列化交易记录失败: %v", err)
	}

	err = ctx.GetStub().PutState(transaction.ID, transactionBytes)
	if err != nil {
		return "", fmt.Errorf("保存交易记录失败: %v", err)
	}

	// 保存奖励记录
	reward.IsValidated = true
	rewardBytes, err := json.Marshal(reward)
	if err != nil {
		return "", fmt.Errorf("序列化奖励记录失败: %v", err)
	}

	err = ctx.GetStub().PutState("reward_"+reward.RewardID, rewardBytes)
	if err != nil {
		return "", fmt.Errorf("保存奖励记录失败: %v", err)
	}

	log.Printf("成功为学生 %s 记录多模态奖励: %s (+%d积分)",
		reward.StudentID, reward.Description, reward.Amount)

	return transaction.ID, nil
}

// GetStudentRewards 获取学生多模态奖励记录
func (ic *IntegralChaincode) GetStudentRewards(ctx contractapi.TransactionContextInterface, studentID string) ([]*MultimodalReward, error) {
	queryString := fmt.Sprintf(`{
		"selector": {
			"student_id": "%s",
			"is_validated": true
		},
		"sort": [{"timestamp": "desc"}]
	}`, studentID)

	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("查询奖励记录失败: %v", err)
	}
	defer resultsIterator.Close()

	var rewards []*MultimodalReward
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("遍历查询结果失败: %v", err)
		}

		var reward MultimodalReward
		err = json.Unmarshal(queryResponse.Value, &reward)
		if err != nil {
			log.Printf("解析奖励记录失败: %v", err)
			continue
		}

		rewards = append(rewards, &reward)
	}

	return rewards, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&IntegralChaincode{})
	if err != nil {
		log.Panicf("创建积分链码失败: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("启动积分链码失败: %v", err)
	}
}
