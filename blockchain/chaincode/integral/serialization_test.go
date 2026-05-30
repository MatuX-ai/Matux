package main

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"
)

// SerializationValidator 序列化验证器
type SerializationValidator struct{}

// ValidateIntegralJSONSerialization 验证Integral结构体JSON序列化
func (sv *SerializationValidator) ValidateIntegralJSONSerialization() error {
	fmt.Println("开始验证Integral结构体JSON序列化...")
	
	// 创建测试数据
	testIntegral := &Integral{
		StudentID: "student_001",
		Amount:    100,
		Source:    "task_completion",
		Timestamp: time.Now().Unix(),
	}
	
	// 测试序列化
	jsonStr, err := testIntegral.ToJSON()
	if err != nil {
		return fmt.Errorf("序列化失败: %v", err)
	}
	
	fmt.Printf("序列化结果: %s\n", jsonStr)
	
	// 测试反序列化
	var deserializedIntegral Integral
	err = deserializedIntegral.FromJSON(jsonStr)
	if err != nil {
		return fmt.Errorf("反序列化失败: %v", err)
	}
	
	// 验证数据一致性
	if testIntegral.StudentID != deserializedIntegral.StudentID {
		return fmt.Errorf("StudentID不一致: 期望 %s, 实际 %s", 
			testIntegral.StudentID, deserializedIntegral.StudentID)
	}
	
	if testIntegral.Amount != deserializedIntegral.Amount {
		return fmt.Errorf("Amount不一致: 期望 %d, 实际 %d", 
			testIntegral.Amount, deserializedIntegral.Amount)
	}
	
	if testIntegral.Source != deserializedIntegral.Source {
		return fmt.Errorf("Source不一致: 期望 %s, 实际 %s", 
			testIntegral.Source, deserializedIntegral.Source)
	}
	
	if testIntegral.Timestamp != deserializedIntegral.Timestamp {
		return fmt.Errorf("Timestamp不一致: 期望 %d, 实际 %d", 
			testIntegral.Timestamp, deserializedIntegral.Timestamp)
	}
	
	fmt.Println("✓ Integral结构体JSON序列化验证通过")
	return nil
}

// ValidateTransactionJSONSerialization 验证Transaction结构体JSON序列化
func (sv *SerializationValidator) ValidateTransactionJSONSerialization() error {
	fmt.Println("开始验证IntegralTransaction结构体JSON序列化...")
	
	// 创建测试数据
	testTransaction := &IntegralTransaction{
		ID:          "tx_001",
		StudentID:   "student_001",
		Amount:      50,
		SourceType:  "earn",
		SourceID:    "task_001",
		Description: "完成学习任务获得积分",
		Timestamp:   time.Now().Unix(),
		Balance:     150,
	}
	
	// 转换为JSON
	transactionBytes, err := json.Marshal(testTransaction)
	if err != nil {
		return fmt.Errorf("Transaction序列化失败: %v", err)
	}
	
	fmt.Printf("Transaction序列化结果: %s\n", string(transactionBytes))
	
	// 反序列化
	var deserializedTransaction IntegralTransaction
	err = json.Unmarshal(transactionBytes, &deserializedTransaction)
	if err != nil {
		return fmt.Errorf("Transaction反序列化失败: %v", err)
	}
	
	// 验证数据一致性
	if testTransaction.ID != deserializedTransaction.ID ||
		testTransaction.StudentID != deserializedTransaction.StudentID ||
		testTransaction.Amount != deserializedTransaction.Amount ||
		testTransaction.SourceType != deserializedTransaction.SourceType ||
		testTransaction.SourceID != deserializedTransaction.SourceID ||
		testTransaction.Description != deserializedTransaction.Description ||
		testTransaction.Timestamp != deserializedTransaction.Timestamp ||
		testTransaction.Balance != deserializedTransaction.Balance {
		return fmt.Errorf("Transaction数据反序列化后不一致")
	}
	
	fmt.Println("✓ IntegralTransaction结构体JSON序列化验证通过")
	return nil
}

// ValidateRuleJSONSerialization 验证Rule结构体JSON序列化
func (sv *SerializationValidator) ValidateRuleJSONSerialization() error {
	fmt.Println("开始验证IntegralRule结构体JSON序列化...")
	
	now := time.Now().Unix()
	testRule := &IntegralRule{
		ID:          "rule_001",
		Name:        "每日登录奖励",
		Description: "用户每日登录系统可获得积分奖励",
		EventType:   "daily_login",
		BaseAmount:  10,
		MaxDaily:    50,
		IsActive:    true,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
	
	// 转换为JSON
	ruleBytes, err := json.Marshal(testRule)
	if err != nil {
		return fmt.Errorf("Rule序列化失败: %v", err)
	}
	
	fmt.Printf("Rule序列化结果: %s\n", string(ruleBytes))
	
	// 反序列化
	var deserializedRule IntegralRule
	err = json.Unmarshal(ruleBytes, &deserializedRule)
	if err != nil {
		return fmt.Errorf("Rule反序列化失败: %v", err)
	}
	
	// 验证数据一致性
	if testRule.ID != deserializedRule.ID ||
		testRule.Name != deserializedRule.Name ||
		testRule.Description != deserializedRule.Description ||
		testRule.EventType != deserializedRule.EventType ||
		testRule.BaseAmount != deserializedRule.BaseAmount ||
		testRule.MaxDaily != deserializedRule.MaxDaily ||
		testRule.IsActive != deserializedRule.IsActive ||
		testRule.CreatedAt != deserializedRule.CreatedAt ||
		testRule.UpdatedAt != deserializedRule.UpdatedAt {
		return fmt.Errorf("Rule数据反序列化后不一致")
	}
	
	fmt.Println("✓ IntegralRule结构体JSON序列化验证通过")
	return nil
}

// ValidateBalanceJSONSerialization 验证Balance结构体JSON序列化
func (sv *SerializationValidator) ValidateBalanceJSONSerialization() error {
	fmt.Println("开始验证StudentBalance结构体JSON序列化...")
	
	testBalance := &StudentBalance{
		StudentID:   "student_001",
		TotalAmount: 1000,
		UpdatedAt:   time.Now().Unix(),
	}
	
	// 转换为JSON
	balanceBytes, err := json.Marshal(testBalance)
	if err != nil {
		return fmt.Errorf("Balance序列化失败: %v", err)
	}
	
	fmt.Printf("Balance序列化结果: %s\n", string(balanceBytes))
	
	// 反序列化
	var deserializedBalance StudentBalance
	err = json.Unmarshal(balanceBytes, &deserializedBalance)
	if err != nil {
		return fmt.Errorf("Balance反序列化失败: %v", err)
	}
	
	// 验证数据一致性
	if testBalance.StudentID != deserializedBalance.StudentID ||
		testBalance.TotalAmount != deserializedBalance.TotalAmount ||
		testBalance.UpdatedAt != deserializedBalance.UpdatedAt {
		return fmt.Errorf("Balance数据反序列化后不一致")
	}
	
	fmt.Println("✓ StudentBalance结构体JSON序列化验证通过")
	return nil
}

// RunAllSerializationTests 运行所有序列化测试
func (sv *SerializationValidator) RunAllSerializationTests() error {
	fmt.Println("=== 开始JSON序列化验证测试 ===")
	
	tests := []func() error{
		sv.ValidateIntegralJSONSerialization,
		sv.ValidateTransactionJSONSerialization,
		sv.ValidateRuleJSONSerialization,
		sv.ValidateBalanceJSONSerialization,
	}
	
	for i, test := range tests {
		fmt.Printf("\n--- 测试 %d ---\n", i+1)
		if err := test(); err != nil {
			return fmt.Errorf("测试 %d 失败: %v", i+1, err)
		}
	}
	
	fmt.Println("\n=== 所有JSON序列化验证测试通过 ===")
	return nil
}

// 单元测试函数
func TestIntegralSerialization(t *testing.T) {
	validator := &SerializationValidator{}
	
	err := validator.RunAllSerializationTests()
	if err != nil {
		t.Errorf("序列化验证失败: %v", err)
	}
}

func TestIntegralValidation(t *testing.T) {
	// 测试有效的Integral数据
	validIntegral := &Integral{
		StudentID: "student_001",
		Amount:    100,
		Source:    "task_completion",
		Timestamp: time.Now().Unix(),
	}
	
	err := validIntegral.Validate()
	if err != nil {
		t.Errorf("有效数据验证失败: %v", err)
	}
	
	// 测试无效数据
	invalidIntegrals := []*Integral{
		{
			StudentID: "",
			Amount:    100,
			Source:    "task_completion",
			Timestamp: time.Now().Unix(),
		},
		{
			StudentID: "student_001",
			Amount:    0,
			Source:    "task_completion",
			Timestamp: time.Now().Unix(),
		},
		{
			StudentID: "student_001",
			Amount:    100,
			Source:    "",
			Timestamp: time.Now().Unix(),
		},
		{
			StudentID: "student_001",
			Amount:    100,
			Source:    "task_completion",
			Timestamp: 0,
		},
	}
	
	for i, invalidIntegral := range invalidIntegrals {
		err := invalidIntegral.Validate()
		if err == nil {
			t.Errorf("无效数据测试 %d 应该失败但通过了", i+1)
		}
	}
}