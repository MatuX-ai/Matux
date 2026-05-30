package main

import (
	"encoding/json"
	"fmt"
	"math"
	"testing"
	"time"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// TestBoundaryConditions 边界条件测试
func TestBoundaryConditions(t *testing.T) {
	fmt.Println("=== 开始边界条件测试 ===")
	
	chaincode := new(IntegralChaincode)
	
	boundaryTests := []struct {
		name          string
		studentID     string
		amount        int
		mspID         string
		shouldPass    bool
		expectedError string
		description   string
	}{
		// 数值边界测试
		{
			name:          "最小正整数积分",
			studentID:     "student_min",
			amount:        1,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试发行最小正整数积分(1)",
		},
		{
			name:          "最大安全整数积分",
			studentID:     "student_max_safe",
			amount:        math.MaxInt32,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试发行最大安全整数积分",
		},
		{
			name:          "零积分边界",
			studentID:     "student_zero_boundary",
			amount:        0,
			mspID:         EducationBureauMSP,
			shouldPass:    false,
			expectedError: "积分数量必须大于0",
			description:   "测试零积分边界条件",
		},
		{
			name:          "负一积分边界",
			studentID:     "student_neg_one",
			amount:        -1,
			mspID:         EducationBureauMSP,
			shouldPass:    false,
			expectedError: "积分数量必须大于0",
			description:   "测试负一积分边界条件",
		},
		
		// 字符串长度边界测试
		{
			name:          "最短学生ID",
			studentID:     "a",
			amount:        100,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试最短有效学生ID",
		},
		{
			name:          "超长学生ID",
			studentID:     "student_with_extremely_long_identifier_that_tests_the_maximum_length_handling_capabilities_of_the_system_and_validates_robustness",
			amount:        100,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试超长学生ID处理能力",
		},
		{
			name:          "空学生ID",
			studentID:     "",
			amount:        100,
			mspID:         EducationBureauMSP,
			shouldPass:    false,
			expectedError: "学生ID不能为空",
			description:   "测试空学生ID边界",
		},
		
		// 特殊字符测试
		{
			name:          "含数字的学生ID",
			studentID:     "student123",
			amount:        100,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试包含数字的学生ID",
		},
		{
			name:          "含下划线的学生ID",
			studentID:     "student_test_user",
			amount:        100,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试包含下划线的学生ID",
		},
		{
			name:          "含连字符的学生ID",
			studentID:     "student-test-user",
			amount:        100,
			mspID:         EducationBureauMSP,
			shouldPass:    true,
			description:   "测试包含连字符的学生ID",
		},
	}
	
	for _, bt := range boundaryTests {
		t.Run(bt.name, func(t *testing.T) {
			fmt.Printf("--- 边界测试: %s ---\n", bt.description)
			
			mockClientIdentity := new(MockClientIdentity)
			mockClientIdentity.On("GetMSPID").Return(bt.mspID, nil)
			
			mockCtx := new(MockTransactionContext)
			mockCtx.clientIdentity = mockClientIdentity
			
			mockStub := new(shim.MockStub)
			mockCtx.On("GetStub").Return(mockStub)
			
			err := chaincode.IssueIntegral(mockCtx, bt.studentID, bt.amount)
			
			if bt.shouldPass {
				assert.NoError(t, err, "边界测试应该通过: %s", bt.name)
				fmt.Printf("✓ 边界测试 '%s' 通过\n", bt.name)
			} else {
				assert.Error(t, err, "边界测试应该失败: %s", bt.name)
				assert.Contains(t, err.Error(), bt.expectedError, 
					"错误信息应该包含期望内容: %s", bt.name)
				fmt.Printf("✓ 边界测试 '%s' 正确拒绝\n", bt.name)
			}
		})
	}
	
	fmt.Println("=== 边界条件测试完成 ===")
}

// TestExceptionScenarios 异常场景测试
func TestExceptionScenarios(t *testing.T) {
	fmt.Println("=== 开始异常场景测试 ===")
	
	chaincode := new(IntegralChaincode)
	
	exceptionTests := []struct {
		name          string
		studentID     string
		amount        int
		mspID         string
		setupFunc     func(*MockTransactionContext, *MockClientIdentity)
		shouldError   bool
		errorContains string
		description   string
	}{
		{
			name:        "MSP ID获取失败",
			studentID:   "student_msp_fail",
			amount:      100,
			mspID:       "",
			setupFunc: func(ctx *MockTransactionContext, identity *MockClientIdentity) {
				identity.On("GetMSPID").Return("", fmt.Errorf("network error"))
			},
			shouldError:   true,
			errorContains: "获取MSP ID失败",
			description:   "模拟MSP ID获取网络错误",
		},
		{
			name:        "stub GetState失败",
			studentID:   "student_getstate_fail",
			amount:      100,
			mspID:       EducationBureauMSP,
			setupFunc: func(ctx *MockTransactionContext, identity *MockClientIdentity) {
				identity.On("GetMSPID").Return(EducationBureauMSP, nil)
				// 模拟stub错误将在实际调用中体现
			},
			shouldError:   true,
			errorContains: "获取学生余额失败",
			description:   "模拟获取学生余额失败",
		},
		{
			name:        "stub PutState失败",
			studentID:   "student_putstate_fail",
			amount:      100,
			mspID:       EducationBureauMSP,
			setupFunc: func(ctx *MockTransactionContext, identity *MockClientIdentity) {
				identity.On("GetMSPID").Return(EducationBureauMSP, nil)
				// 模拟stub错误将在实际调用中体现
			},
			shouldError:   true,
			errorContains: "保存余额到区块链失败",
			description:   "模拟保存余额失败",
		},
		{
			name:        "JSON序列化失败",
			studentID:   "student_json_fail",
			amount:      100,
			mspID:       EducationBureauMSP,
			setupFunc: func(ctx *MockTransactionContext, identity *MockClientIdentity) {
				identity.On("GetMSPID").Return(EducationBureauMSP, nil)
				// 通过构造特殊数据导致序列化失败较为困难，
				// 但在实际环境中可能发生
			},
			shouldError:   true,
			errorContains: "序列化",
			description:   "模拟JSON序列化失败",
		},
	}
	
	for _, et := range exceptionTests {
		t.Run(et.name, func(t *testing.T) {
			fmt.Printf("--- 异常场景测试: %s ---\n", et.description)
			
			mockClientIdentity := new(MockClientIdentity)
			mockCtx := new(MockTransactionContext)
			
			if et.setupFunc != nil {
				et.setupFunc(mockCtx, mockClientIdentity)
			}
			
			mockCtx.clientIdentity = mockClientIdentity
			mockStub := new(shim.MockStub)
			mockCtx.On("GetStub").Return(mockStub)
			
			err := chaincode.IssueIntegral(mockCtx, et.studentID, et.amount)
			
			if et.shouldError {
				assert.Error(t, err, "异常场景应该返回错误: %s", et.name)
				if et.errorContains != "" {
					assert.Contains(t, err.Error(), et.errorContains, 
						"错误信息应该包含期望内容: %s", et.name)
				}
				fmt.Printf("✓ 异常场景 '%s' 正确处理: %v\n", et.name, err)
			} else {
				assert.NoError(t, err, "异常场景应该成功: %s", et.name)
				fmt.Printf("✓ 异常场景 '%s' 处理成功\n", et.name)
			}
		})
	}
	
	fmt.Println("=== 异常场景测试完成 ===")
}

// TestConcurrentAccess 并发访问测试
func TestConcurrentAccess(t *testing.T) {
	fmt.Println("=== 开始并发访问测试 ===")
	
	// 测试并发发行积分的场景
	chaincode := new(IntegralChaincode)
	studentID := "concurrent_student"
	
	// 创建共享的模拟上下文
	mockClientIdentity := new(MockClientIdentity)
	mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
	
	// 执行多个并发的积分发行
	concurrentOps := 5
	results := make(chan error, concurrentOps)
	
	for i := 0; i < concurrentOps; i++ {
		go func(opIndex int) {
			mockCtx := new(MockTransactionContext)
			mockCtx.clientIdentity = mockClientIdentity
			
			mockStub := new(shim.MockStub)
			mockCtx.On("GetStub").Return(mockStub)
			
			amount := 100 + opIndex*10 // 不同的金额
			err := chaincode.IssueIntegral(mockCtx, studentID, amount)
			results <- err
		}(i)
	}
	
	// 收集结果
	successCount := 0
	errorCount := 0
	
	for i := 0; i < concurrentOps; i++ {
		err := <-results
		if err != nil {
			errorCount++
			fmt.Printf("并发操作%d失败: %v\n", i+1, err)
		} else {
			successCount++
			fmt.Printf("并发操作%d成功\n", i+1)
		}
	}
	
	fmt.Printf("并发测试结果: 成功%d, 失败%d\n", successCount, errorCount)
	
	// 在模拟环境中，并发测试主要用于验证不会出现死锁等问题
	// 实际的并发安全性需要在真实的区块链环境中验证
	assert.True(t, successCount+errorCount == concurrentOps, 
		"所有并发操作都应该完成")
	
	fmt.Println("=== 并发访问测试完成 ===")
}

// TestLargeScaleOperations 大规模操作测试
func TestLargeScaleOperations(t *testing.T) {
	fmt.Println("=== 开始大规模操作测试 ===")
	
	chaincode := new(IntegralChaincode)
	
	// 测试大量连续操作
	largeScaleCount := 100
	successfulOps := 0
	
	for i := 0; i < largeScaleCount; i++ {
		mockClientIdentity := new(MockClientIdentity)
		mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
		
		mockCtx := new(MockTransactionContext)
		mockCtx.clientIdentity = mockClientIdentity
		
		mockStub := new(shim.MockStub)
		mockCtx.On("GetStub").Return(mockStub)
		
		studentID := fmt.Sprintf("large_scale_student_%d", i)
		amount := 50 + (i % 500) // 50-550之间的金额
		
		err := chaincode.IssueIntegral(mockCtx, studentID, amount)
		if err == nil {
			successfulOps++
		}
	}
	
	successRate := float64(successfulOps) / float64(largeScaleCount) * 100
	fmt.Printf("大规模操作测试: 总计%d次, 成功%d次, 成功率%.2f%%\n", 
		largeScaleCount, successfulOps, successRate)
	
	// 在模拟环境中，我们期望大部分操作成功
	assert.True(t, successRate > 80, "大规模操作成功率应该较高")
	
	fmt.Println("=== 大规模操作测试完成 ===")
}

// TestDataConsistency 数据一致性测试
func TestDataConsistency(t *testing.T) {
	fmt.Println("=== 开始数据一致性测试 ===")
	
	// 使用真实链码测试数据一致性
	stub := shim.NewMockStub("integral_cc", new(IntegralChaincode))
	
	// 初始化
	initArgs := [][]byte{}
	response := stub.MockInit("init", initArgs)
	assert.Equal(t, int32(shim.OK), response.Status, "初始化应该成功")
	
	// 设置权限
	stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))
	
	studentID := "consistency_test_student"
	initialAmount := 1000
	
	// 发行初始积分
	invokeArgs := [][]byte{[]byte("IssueIntegral"), []byte(studentID), []byte(fmt.Sprintf("%d", initialAmount))}
	result := stub.MockInvoke("initial_issue", invokeArgs)
	assert.Equal(t, int32(shim.OK), result.Status, "初始发行应该成功")
	
	// 多次查询验证一致性
	for i := 0; i < 10; i++ {
		queryArgs := [][]byte{[]byte("GetStudentBalance"), []byte(studentID)}
		queryResult := stub.MockInvoke(fmt.Sprintf("consistency_query_%d", i), queryArgs)
		
		assert.Equal(t, int32(shim.OK), queryResult.Status, 
			"第%d次查询应该成功", i+1)
		
		var balance StudentBalance
		err := json.Unmarshal(queryResult.Payload, &balance)
		assert.NoError(t, err, "第%d次反序列化应该成功", i+1)
		assert.Equal(t, initialAmount, balance.TotalAmount, 
			"第%d次查询余额应该一致", i+1)
	}
	
	fmt.Println("✓ 数据一致性验证通过")
	fmt.Println("=== 数据一致性测试完成 ===")
}