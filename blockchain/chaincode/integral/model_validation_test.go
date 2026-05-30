package main

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"
)

// TestDataModelValidation 数据模型验证测试
func TestDataModelValidation(t *testing.T) {
	fmt.Println("=== 开始数据模型验证测试 ===")

	// 测试Integral结构体验证
	testIntegralValidation(t)
	
	// 测试Transaction结构体验证
	testTransactionValidation(t)
	
	// 测试Rule结构体验证
	testRuleValidation(t)
	
	// 测试Balance结构体验证
	testBalanceValidation(t)
	
	fmt.Println("=== 数据模型验证测试完成 ===")
}

func testIntegralValidation(t *testing.T) {
	fmt.Println("--- 测试Integral结构体验证 ---")
	
	// 测试有效数据
	validIntegral := &Integral{
		StudentID: "student_001",
		Amount:    100,
		Source:    "task_completion",
		Timestamp: time.Now().Unix(),
	}
	
	err := validIntegral.Validate()
	if err != nil {
		t.Errorf("有效Integral数据验证失败: %v", err)
	} else {
		fmt.Println("✓ 有效Integral数据验证通过")
	}
	
	// 测试无效数据
	invalidCases := []struct {
		name  string
		data  *Integral
		error string
	}{
		{
			"空学生ID",
			&Integral{StudentID: "", Amount: 100, Source: "test", Timestamp: time.Now().Unix()},
			"student_id cannot be empty",
		},
		{
			"零积分",
			&Integral{StudentID: "student_001", Amount: 0, Source: "test", Timestamp: time.Now().Unix()},
			"amount must be greater than 0",
		},
		{
			"负积分",
			&Integral{StudentID: "student_001", Amount: -50, Source: "test", Timestamp: time.Now().Unix()},
			"amount must be greater than 0",
		},
		{
			"空来源",
			&Integral{StudentID: "student_001", Amount: 100, Source: "", Timestamp: time.Now().Unix()},
			"source cannot be empty",
		},
		{
			"零时间戳",
			&Integral{StudentID: "student_001", Amount: 100, Source: "test", Timestamp: 0},
			"timestamp must be greater than 0",
		},
		{
			"未来时间戳",
			&Integral{StudentID: "student_001", Amount: 100, Source: "test", Timestamp: time.Now().Unix() + 1000000},
			"timestamp cannot be in the future",
		},
	}
	
	for _, tc := range invalidCases {
		err := tc.data.Validate()
		if err == nil {
			t.Errorf("测试用例 '%s' 应该失败但通过了", tc.name)
		} else if err.Error() != tc.error {
			t.Errorf("测试用例 '%s' 错误信息不匹配: 期望 '%s', 实际 '%s'", 
				tc.name, tc.error, err.Error())
		} else {
			fmt.Printf("✓ 测试用例 '%s' 验证通过\n", tc.name)
		}
	}
}

func testTransactionValidation(t *testing.T) {
	fmt.Println("--- 测试IntegralTransaction结构体验证 ---")
	
	// 测试有效数据
	validTransaction := &IntegralTransaction{
		ID:          "tx_001",
		StudentID:   "student_001",
		Amount:      50,
		SourceType:  "earn",
		SourceID:    "task_001",
		Description: "完成任务获得积分",
		Timestamp:   time.Now().Unix(),
		Balance:     150,
	}
	
	err := validTransaction.Validate()
	if err != nil {
		t.Errorf("有效Transaction数据验证失败: %v", err)
	} else {
		fmt.Println("✓ 有效Transaction数据验证通过")
	}
	
	// 测试无效数据
	invalidTransactions := []struct {
		name  string
		data  *IntegralTransaction
		error string
	}{
		{
			"空交易ID",
			&IntegralTransaction{ID: "", StudentID: "student_001", Amount: 50, SourceType: "earn", SourceID: "task_001", Description: "test", Timestamp: time.Now().Unix(), Balance: 100},
			"transaction id cannot be empty",
		},
		{
			"零金额",
			&IntegralTransaction{ID: "tx_001", StudentID: "student_001", Amount: 0, SourceType: "earn", SourceID: "task_001", Description: "test", Timestamp: time.Now().Unix(), Balance: 100},
			"amount cannot be zero",
		},
		{
			"无效来源类型",
			&IntegralTransaction{ID: "tx_001", StudentID: "student_001", Amount: 50, SourceType: "invalid", SourceID: "task_001", Description: "test", Timestamp: time.Now().Unix(), Balance: 100},
			"source_type must be 'earn' or 'spend'",
		},
		{
			"空来源ID",
			&IntegralTransaction{ID: "tx_001", StudentID: "student_001", Amount: 50, SourceType: "earn", SourceID: "", Description: "test", Timestamp: time.Now().Unix(), Balance: 100},
			"source_id cannot be empty",
		},
		{
			"空描述",
			&IntegralTransaction{ID: "tx_001", StudentID: "student_001", Amount: 50, SourceType: "earn", SourceID: "task_001", Description: "", Timestamp: time.Now().Unix(), Balance: 100},
			"description cannot be empty",
		},
		{
			"负余额",
			&IntegralTransaction{ID: "tx_001", StudentID: "student_001", Amount: 50, SourceType: "earn", SourceID: "task_001", Description: "test", Timestamp: time.Now().Unix(), Balance: -10},
			"balance cannot be negative",
		},
	}
	
	for _, tc := range invalidTransactions {
		err := tc.data.Validate()
		if err == nil {
			t.Errorf("Transaction测试用例 '%s' 应该失败但通过了", tc.name)
		} else if err.Error() != tc.error {
			t.Errorf("Transaction测试用例 '%s' 错误信息不匹配", tc.name)
		} else {
			fmt.Printf("✓ Transaction测试用例 '%s' 验证通过\n", tc.name)
		}
	}
}

func testRuleValidation(t *testing.T) {
	fmt.Println("--- 测试IntegralRule结构体验证 ---")
	
	// 测试有效数据
	now := time.Now().Unix()
	validRule := &IntegralRule{
		ID:          "rule_001",
		Name:        "每日登录奖励",
		Description: "每日登录获得积分",
		EventType:   "daily_login",
		BaseAmount:  10,
		MaxDaily:    50,
		IsActive:    true,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
	
	err := validRule.Validate()
	if err != nil {
		t.Errorf("有效Rule数据验证失败: %v", err)
	} else {
		fmt.Println("✓ 有效Rule数据验证通过")
	}
	
	// 测试无效数据
	invalidRules := []struct {
		name  string
		data  *IntegralRule
		error string
	}{
		{
			"空规则ID",
			&IntegralRule{ID: "", Name: "test", EventType: "test", BaseAmount: 10, MaxDaily: 50, IsActive: true, CreatedAt: now, UpdatedAt: now},
			"rule id cannot be empty",
		},
		{
			"空规则名称",
			&IntegralRule{ID: "rule_001", Name: "", EventType: "test", BaseAmount: 10, MaxDaily: 50, IsActive: true, CreatedAt: now, UpdatedAt: now},
			"rule name cannot be empty",
		},
		{
			"零基础积分",
			&IntegralRule{ID: "rule_001", Name: "test", EventType: "test", BaseAmount: 0, MaxDaily: 50, IsActive: true, CreatedAt: now, UpdatedAt: now},
			"base amount must be greater than 0",
		},
		{
			"负每日上限",
			&IntegralRule{ID: "rule_001", Name: "test", EventType: "test", BaseAmount: 10, MaxDaily: -10, IsActive: true, CreatedAt: now, UpdatedAt: now},
			"max daily cannot be negative",
		},
		{
			"每日上限小于基础积分",
			&IntegralRule{ID: "rule_001", Name: "test", EventType: "test", BaseAmount: 50, MaxDaily: 10, IsActive: true, CreatedAt: now, UpdatedAt: now},
			"max daily must be greater than or equal to base amount",
		},
	}
	
	for _, tc := range invalidRules {
		err := tc.data.Validate()
		if err == nil {
			t.Errorf("Rule测试用例 '%s' 应该失败但通过了", tc.name)
		} else if err.Error() != tc.error {
			t.Errorf("Rule测试用例 '%s' 错误信息不匹配", tc.name)
		} else {
			fmt.Printf("✓ Rule测试用例 '%s' 验证通过\n", tc.name)
		}
	}
}

func testBalanceValidation(t *testing.T) {
	fmt.Println("--- 测试StudentBalance结构体验证 ---")
	
	// 测试有效数据
	validBalance := &StudentBalance{
		StudentID:   "student_001",
		TotalAmount: 1000,
		UpdatedAt:   time.Now().Unix(),
	}
	
	err := validBalance.Validate()
	if err != nil {
		t.Errorf("有效Balance数据验证失败: %v", err)
	} else {
		fmt.Println("✓ 有效Balance数据验证通过")
	}
	
	// 测试无效数据
	invalidBalances := []struct {
		name  string
		data  *StudentBalance
		error string
	}{
		{
			"空学生ID",
			&StudentBalance{StudentID: "", TotalAmount: 1000, UpdatedAt: time.Now().Unix()},
			"student_id cannot be empty",
		},
		{
			"负积分余额",
			&StudentBalance{StudentID: "student_001", TotalAmount: -100, UpdatedAt: time.Now().Unix()},
			"total_amount cannot be negative",
		},
		{
			"零更新时间",
			&StudentBalance{StudentID: "student_001", TotalAmount: 1000, UpdatedAt: 0},
			"updated_at must be greater than 0",
		},
	}
	
	for _, tc := range invalidBalances {
		err := tc.data.Validate()
		if err == nil {
			t.Errorf("Balance测试用例 '%s' 应该失败但通过了", tc.name)
		} else if err.Error() != tc.error {
			t.Errorf("Balance测试用例 '%s' 错误信息不匹配", tc.name)
		} else {
			fmt.Printf("✓ Balance测试用例 '%s' 验证通过\n", tc.name)
		}
	}
}

// TestJSONOperations JSON操作测试
func TestJSONOperations(t *testing.T) {
	fmt.Println("=== 开始JSON操作测试 ===")
	
	// 测试Integral的JSON序列化和反序列化
	testIntegral := &Integral{
		StudentID: "student_001",
		Amount:    100,
		Source:    "task_completion",
		Timestamp: time.Now().Unix(),
	}
	
	// 测试ToJSON方法
	jsonStr, err := testIntegral.ToJSON()
	if err != nil {
		t.Errorf("Integral ToJSON失败: %v", err)
	} else {
		fmt.Printf("Integral序列化结果: %s\n", jsonStr)
	}
	
	// 测试FromJSON方法
	var deserializedIntegral Integral
	err = deserializedIntegral.FromJSON(jsonStr)
	if err != nil {
		t.Errorf("Integral FromJSON失败: %v", err)
	}
	
	// 验证数据一致性
	if testIntegral.StudentID != deserializedIntegral.StudentID ||
		testIntegral.Amount != deserializedIntegral.Amount ||
		testIntegral.Source != deserializedIntegral.Source ||
		testIntegral.Timestamp != deserializedIntegral.Timestamp {
		t.Errorf("Integral序列化/反序列化后数据不一致")
	} else {
		fmt.Println("✓ Integral JSON操作测试通过")
	}
	
	// 测试标准JSON库操作
	transaction := &IntegralTransaction{
		ID:          "tx_001",
		StudentID:   "student_001",
		Amount:      50,
		SourceType:  "earn",
		SourceID:    "task_001",
		Description: "测试交易",
		Timestamp:   time.Now().Unix(),
		Balance:     150,
	}
	
	// 标准JSON序列化
	transactionBytes, err := json.Marshal(transaction)
	if err != nil {
		t.Errorf("Transaction标准序列化失败: %v", err)
	}
	
	// 标准JSON反序列化
	var deserializedTransaction IntegralTransaction
	err = json.Unmarshal(transactionBytes, &deserializedTransaction)
	if err != nil {
		t.Errorf("Transaction标准反序列化失败: %v", err)
	}
	
	// 验证一致性
	if transaction.ID != deserializedTransaction.ID ||
		transaction.StudentID != deserializedTransaction.StudentID ||
		transaction.Amount != deserializedTransaction.Amount {
		t.Errorf("Transaction标准JSON操作后数据不一致")
	} else {
		fmt.Println("✓ Transaction标准JSON操作测试通过")
	}
	
	fmt.Println("=== JSON操作测试完成 ===")
}

// BenchmarkJSONSerialization JSON序列化性能基准测试
func BenchmarkJSONSerialization(b *testing.B) {
	integral := &Integral{
		StudentID: "student_001",
		Amount:    100,
		Source:    "benchmark_test",
		Timestamp: time.Now().Unix(),
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := integral.ToJSON()
		if err != nil {
			b.Errorf("序列化失败: %v", err)
		}
	}
}

func BenchmarkJSONDeserialization(b *testing.B) {
	jsonStr := `{"student_id":"student_001","amount":100,"source":"benchmark_test","timestamp":1234567890}`
	var integral Integral
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		err := integral.FromJSON(jsonStr)
		if err != nil {
			b.Errorf("反序列化失败: %v", err)
		}
	}
}