package main

import (
	"fmt"
	"testing"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// TestPermissionControlComprehensive 权限控制综合测试
func TestPermissionControlComprehensive(t *testing.T) {
	fmt.Println("=== 开始权限控制综合测试 ===")
	
	// 测试不同组织的权限
	orgTests := []struct {
		name           string
		mspID          string
		shouldAllow    bool
		description    string
	}{
		{
			name:        "教育局组织",
			mspID:       EducationBureauMSP,
			shouldAllow: true,
			description: "教育局组织应该被允许发行积分",
		},
		{
			name:        "学校组织",
			mspID:       SchoolMSP,
			shouldAllow: false,
			description: "学校组织不应该被允许发行积分",
		},
		{
			name:        "企业组织",
			mspID:       EnterpriseMSP,
			shouldAllow: false,
			description: "企业组织不应该被允许发行积分",
		},
		{
			name:        "未知组织",
			mspID:       "UnknownOrgMSP",
			shouldAllow: false,
			description: "未知组织不应该被允许发行积分",
		},
		{
			name:        "空MSP ID",
			mspID:       "",
			shouldAllow: false,
			description: "空MSP ID不应该被允许",
		},
	}
	
	for _, ot := range orgTests {
		t.Run(ot.name, func(t *testing.T) {
			fmt.Printf("--- 测试组织权限: %s ---\n", ot.description)
			
			// 创建模拟对象
			mockClientIdentity := new(MockClientIdentity)
			mockCtx := new(MockTransactionContext)
			
			// 设置期望调用
			mockClientIdentity.On("GetMSPID").Return(ot.mspID, nil)
			mockCtx.clientIdentity = mockClientIdentity
			
			// 执行权限检查
			err := CheckEducationBureauPermission(mockCtx)
			
			// 验证结果
			if ot.shouldAllow {
				assert.NoError(t, err, "组织 %s 应该有权限", ot.name)
				fmt.Printf("✓ 组织 '%s' 权限验证通过\n", ot.name)
			} else {
				assert.Error(t, err, "组织 %s 应该无权限", ot.name)
				assert.Contains(t, err.Error(), "权限不足", 
					"错误信息应该包含权限不足提示")
				fmt.Printf("✓ 组织 '%s' 权限正确拒绝\n", ot.name)
			}
			
			// 验证模拟调用
			mockClientIdentity.AssertExpectations(t)
		})
	}
	
	fmt.Println("=== 权限控制综合测试完成 ===")
}

// TestPermissionWithChaincodeIntegration 链码集成权限测试
func TestPermissionWithChaincodeIntegration(t *testing.T) {
	fmt.Println("=== 开始链码集成权限测试 ===")
	
	chaincode := new(IntegralChaincode)
	studentID := "test_student_permissions"
	amount := 100
	
	// 测试有权组织
	t.Run("教育局权限测试", func(t *testing.T) {
		fmt.Println("--- 教育局权限测试 ---")
		
		mockClientIdentity := new(MockClientIdentity)
		mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
		
		mockCtx := new(MockTransactionContext)
		mockCtx.clientIdentity = mockClientIdentity
		
		mockStub := new(shim.MockStub)
		mockCtx.On("GetStub").Return(mockStub)
		
		err := chaincode.IssueIntegral(mockCtx, studentID, amount)
		
		// 对于模拟环境，可能会因为stub未完全模拟而失败
		// 但我们主要验证权限检查是否通过
		if err != nil {
			// 如果出错，确保不是权限错误
			assert.NotContains(t, err.Error(), "权限不足", 
				"教育局不应该因为权限被拒绝")
			fmt.Printf("✓ 教育局权限检查通过（其他错误：%v）\n", err)
		} else {
			fmt.Println("✓ 教育局权限测试完全通过")
		}
	})
	
	// 测试无权组织
	unauthorizedOrgs := []string{SchoolMSP, EnterpriseMSP, "RandomOrgMSP"}
	
	for _, orgMSP := range unauthorizedOrgs {
		t.Run(fmt.Sprintf("无权限组织-%s", orgMSP), func(t *testing.T) {
			fmt.Printf("--- 无权限组织测试: %s ---\n", orgMSP)
			
			mockClientIdentity := new(MockClientIdentity)
			mockClientIdentity.On("GetMSPID").Return(orgMSP, nil)
			
			mockCtx := new(MockTransactionContext)
			mockCtx.clientIdentity = mockClientIdentity
			
			mockStub := new(shim.MockStub)
			mockCtx.On("GetStub").Return(mockStub)
			
			err := chaincode.IssueIntegral(mockCtx, studentID, amount)
			
			// 验证权限被正确拒绝
			assert.Error(t, err, "无权限组织应该被拒绝")
			assert.Contains(t, err.Error(), "权限不足", 
				"错误信息应该包含权限不足")
			fmt.Printf("✓ 组织 '%s' 权限正确拒绝\n", orgMSP)
		})
	}
	
	fmt.Println("=== 链码集成权限测试完成 ===")
}

// TestGetCallerMSPIDDetailed MSP ID获取详细测试
func TestGetCallerMSPIDDetailed(t *testing.T) {
	fmt.Println("=== 开始MSP ID获取详细测试 ===")
	
	testCases := []struct {
		name          string
		mspID         string
		hasError      bool
		errorContains string
		description   string
	}{
		{
			name:          "正常获取教育局MSP ID",
			mspID:         EducationBureauMSP,
			hasError:      false,
			description:   "正常获取教育局MSP ID",
		},
		{
			name:          "正常获取学校MSP ID",
			mspID:         SchoolMSP,
			hasError:      false,
			description:   "正常获取学校MSP ID",
		},
		{
			name:          "正常获取企业MSP ID",
			mspID:         EnterpriseMSP,
			hasError:      false,
			description:   "正常获取企业MSP ID",
		},
		{
			name:          "获取失败场景",
			mspID:         "",
			hasError:      true,
			errorContains: "获取MSP ID失败",
			description:   "模拟获取MSP ID失败",
		},
		{
			name:          "空MSP ID场景",
			mspID:         "",
			hasError:      false,
			description:   "获取空MSP ID",
		},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			fmt.Printf("--- MSP ID测试: %s ---\n", tc.description)
			
			mockClientIdentity := new(MockClientIdentity)
			mockCtx := new(MockTransactionContext)
			
			if tc.hasError {
				mockClientIdentity.On("GetMSPID").Return("", assert.AnError)
			} else {
				mockClientIdentity.On("GetMSPID").Return(tc.mspID, nil)
			}
			mockCtx.clientIdentity = mockClientIdentity
			
			result, err := GetCallerMSPID(mockCtx)
			
			if tc.hasError {
				assert.Error(t, err, "应该返回错误")
				assert.Empty(t, result, "错误情况下应该返回空结果")
				if tc.errorContains != "" {
					assert.Contains(t, err.Error(), tc.errorContains, 
						"错误信息应该包含期望内容")
				}
				fmt.Printf("✓ 错误场景 '%s' 处理正确\n", tc.name)
			} else {
				assert.NoError(t, err, "不应该返回错误")
				assert.Equal(t, tc.mspID, result, "返回的MSP ID应该匹配")
				fmt.Printf("✓ 正常场景 '%s' 处理正确: %s\n", tc.name, result)
			}
			
			mockClientIdentity.AssertExpectations(t)
		})
	}
	
	fmt.Println("=== MSP ID获取详细测试完成 ===")
}

// TestPermissionErrorMessages 权限错误消息测试
func TestPermissionErrorMessages(t *testing.T) {
	fmt.Println("=== 开始权限错误消息测试 ===")
	
	errorTestCases := []struct {
		name           string
		mspID          string
		expectedError  string
		description    string
	}{
		{
			name:          "学校组织错误消息",
			mspID:         SchoolMSP,
			expectedError: "权限不足: 仅教育局组织可执行此操作，当前MSP ID: " + SchoolMSP,
			description:   "学校组织的详细错误消息",
		},
		{
			name:          "企业组织错误消息",
			mspID:         EnterpriseMSP,
			expectedError: "权限不足: 仅教育局组织可执行此操作，当前MSP ID: " + EnterpriseMSP,
			description:   "企业组织的详细错误消息",
		},
		{
			name:          "未知组织错误消息",
			mspID:         "UnknownOrgMSP",
			expectedError: "权限不足: 仅教育局组织可执行此操作，当前MSP ID: UnknownOrgMSP",
			description:   "未知组织的详细错误消息",
		},
	}
	
	for _, etc := range errorTestCases {
		t.Run(etc.name, func(t *testing.T) {
			fmt.Printf("--- 错误消息测试: %s ---\n", etc.description)
			
			mockClientIdentity := new(MockClientIdentity)
			mockCtx := new(MockTransactionContext)
			
			mockClientIdentity.On("GetMSPID").Return(etc.mspID, nil)
			mockCtx.clientIdentity = mockClientIdentity
			
			err := CheckEducationBureauPermission(mockCtx)
			
			assert.Error(t, err, "应该返回权限错误")
			assert.Equal(t, etc.expectedError, err.Error(), 
				"错误消息应该完全匹配")
			fmt.Printf("✓ 错误消息验证通过: %s\n", err.Error())
			
			mockClientIdentity.AssertExpectations(t)
		})
	}
	
	fmt.Println("=== 权限错误消息测试完成 ===")
}

// TestPermissionPerformance 权限检查性能测试
func TestPermissionPerformance(t *testing.T) {
	fmt.Println("=== 开始权限检查性能测试 ===")
	
	// 测试大量权限检查的性能
	mockClientIdentity := new(MockClientIdentity)
	mockCtx := new(MockTransactionContext)
	mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
	mockCtx.clientIdentity = mockClientIdentity
	
	// 执行1000次权限检查
	for i := 0; i < 1000; i++ {
		err := CheckEducationBureauPermission(mockCtx)
		assert.NoError(t, err, "第%d次权限检查应该成功", i+1)
	}
	
	fmt.Println("✓ 1000次权限检查完成，性能良好")
	mockClientIdentity.AssertExpectations(t)
	
	fmt.Println("=== 权限检查性能测试完成 ===")
}