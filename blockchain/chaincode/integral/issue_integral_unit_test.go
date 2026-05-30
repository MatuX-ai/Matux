package main

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// TestIssueIntegral 核心功能测试 - 符合用户要求的测试用例格式
func TestIssueIntegral(t *testing.T) {
	// 模拟教育局客户端
	clientOrg := "EducationBureauMSP"
	
	// 部署链码
	stub := shim.NewMockStub("integral_cc", new(IntegralChaincode))
	
	// 初始化链码
	initArgs := [][]byte{}
	response := stub.MockInit("init", initArgs)
	assert.Equal(t, int32(shim.OK), response.Status, "链码初始化应该成功")
	
	// 设置教育局MSP ID
	stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", clientOrg))
	
	// 执行发行积分
	result := stub.MockInvoke("tx1", [][]byte{[]byte("IssueIntegral"), []byte("stu001"), []byte("100")})
	
	// 验证结果
	assert.Equal(t, int32(shim.OK), result.Status, "IssueIntegral调用应该成功")
	
	// 验证余额是否正确更新
	queryResult := stub.MockInvoke("query1", [][]byte{[]byte("GetStudentBalance"), []byte("stu001")})
	assert.Equal(t, int32(shim.OK), queryResult.Status, "查询余额应该成功")
	
	var balance StudentBalance
	err := json.Unmarshal(queryResult.Payload, &balance)
	assert.NoError(t, err, "反序列化余额数据应该成功")
	assert.Equal(t, 100, balance.TotalAmount, "余额应该是100")
	assert.Equal(t, "stu001", balance.StudentID, "学生ID应该匹配")
}

// TestIssueIntegralComprehensive 全面的功能测试
func TestIssueIntegralComprehensive(t *testing.T) {
	fmt.Println("=== 开始IssueIntegral全面测试 ===")
	
	chaincode := new(IntegralChaincode)
	
	// 测试用例设计
	testCases := []struct {
		name           string
		studentID      string
		amount         int
		callerMSP      string
		expectSuccess  bool
		expectedError  string
		description    string
	}{
		{
			name:          "教育局正常发行积分",
			studentID:     "student_normal",
			amount:        500,
			callerMSP:     EducationBureauMSP,
			expectSuccess: true,
			description:   "教育局向普通学生发行500积分",
		},
		{
			name:          "教育局发行大额积分",
			studentID:     "student_large",
			amount:        10000,
			callerMSP:     EducationBureauMSP,
			expectSuccess: true,
			description:   "教育局发行大额积分测试",
		},
		{
			name:          "学校组织无权限发行",
			studentID:     "student_school",
			amount:        100,
			callerMSP:     SchoolMSP,
			expectSuccess: false,
			expectedError: "权限不足",
			description:   "学校组织尝试发行积分应该被拒绝",
		},
		{
			name:          "企业组织无权限发行",
			studentID:     "student_enterprise",
			amount:        100,
			callerMSP:     EnterpriseMSP,
			expectSuccess: false,
			expectedError: "权限不足",
			description:   "企业组织尝试发行积分应该被拒绝",
		},
		{
			name:          "空学生ID参数",
			studentID:     "",
			amount:        100,
			callerMSP:     EducationBureauMSP,
			expectSuccess: false,
			expectedError: "学生ID不能为空",
			description:   "空学生ID应该被拒绝",
		},
		{
			name:          "零积分发行",
			studentID:     "student_zero",
			amount:        0,
			callerMSP:     EducationBureauMSP,
			expectSuccess: false,
			expectedError: "积分数量必须大于0",
			description:   "零积分发行应该被拒绝",
		},
		{
			name:          "负积分发行",
			studentID:     "student_negative",
			amount:        -50,
			callerMSP:     EducationBureauMSP,
			expectSuccess: false,
			expectedError: "积分数量必须大于0",
			description:   "负积分发行应该被拒绝",
		},
		{
			name:          "多次发行同一学生",
			studentID:     "student_multiple",
			amount:        200,
			callerMSP:     EducationBureauMSP,
			expectSuccess: true,
			description:   "多次发行测试第一笔",
		},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			fmt.Printf("--- 测试用例: %s ---\n", tc.description)
			
			// 创建模拟上下文
			mockClientIdentity := new(MockClientIdentity)
			mockClientIdentity.On("GetMSPID").Return(tc.callerMSP, nil)
			
			mockCtx := new(MockTransactionContext)
			mockCtx.clientIdentity = mockClientIdentity
			
			// 模拟stub
			mockStub := new(shim.MockStub)
			mockCtx.On("GetStub").Return(mockStub)
			
			// 执行测试
			err := chaincode.IssueIntegral(mockCtx, tc.studentID, tc.amount)
			
			// 验证结果
			if tc.expectSuccess {
				assert.NoError(t, err, "测试用例应该成功: %s", tc.name)
				fmt.Printf("✓ 测试用例 '%s' 通过\n", tc.name)
			} else {
				assert.Error(t, err, "测试用例应该失败: %s", tc.name)
				assert.Contains(t, err.Error(), tc.expectedError, 
					"错误信息应该包含期望的内容: %s", tc.name)
				fmt.Printf("✓ 测试用例 '%s' 正确拒绝\n", tc.name)
			}
			
			// 验证模拟调用
			mockClientIdentity.AssertExpectations(t)
		})
	}
	
	fmt.Println("=== IssueIntegral全面测试完成 ===")
}

// TestIssueIntegralMultipleIssuance 多次发行测试
func TestIssueIntegralMultipleIssuance(t *testing.T) {
	fmt.Println("=== 开始多次发行测试 ===")
	
	chaincode := new(IntegralChaincode)
	studentID := "student_multi_test"
	
	// 创建模拟上下文（教育局权限）
	mockClientIdentity := new(MockClientIdentity)
	mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
	
	mockCtx := new(MockTransactionContext)
	mockCtx.clientIdentity = mockClientIdentity
	
	// 模拟stub
	mockStub := new(shim.MockStub)
	mockCtx.On("GetStub").Return(mockStub)
	
	// 多次发行积分
	issuanceAmounts := []int{100, 200, 150, 50}
	totalExpected := 500
	
	for i, amount := range issuanceAmounts {
		fmt.Printf("第%d次发行: %d积分\n", i+1, amount)
		err := chaincode.IssueIntegral(mockCtx, studentID, amount)
		assert.NoError(t, err, "第%d次发行应该成功", i+1)
	}
	
	// 验证最终余额
	queryArgs := [][]byte{[]byte("GetStudentBalance"), []byte(studentID)}
	queryResult := mockStub.MockInvoke("final_query", queryArgs)
	
	if queryResult.Status == shim.OK {
		var balance StudentBalance
		err := json.Unmarshal(queryResult.Payload, &balance)
		assert.NoError(t, err, "反序列化余额应该成功")
		assert.Equal(t, totalExpected, balance.TotalAmount, 
			"最终余额应该等于累计发行总额")
		fmt.Printf("✓ 最终余额验证通过: %d积分\n", balance.TotalAmount)
	}
	
	fmt.Println("=== 多次发行测试完成 ===")
}

// TestIssueIntegralDataPersistence 数据持久化测试
func TestIssueIntegralDataPersistence(t *testing.T) {
	fmt.Println("=== 开始数据持久化测试 ===")
	
	// 使用真实链码进行测试
	stub := shim.NewMockStub("integral_cc", new(IntegralChaincode))
	
	// 初始化链码
	initArgs := [][]byte{}
	response := stub.MockInit("init", initArgs)
	assert.Equal(t, int32(shim.OK), response.Status, "链码初始化应该成功")
	
	// 设置教育局权限
	stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))
	
	// 发行积分
	studentID := "student_persistence"
	amount := 300
	
	invokeArgs := [][]byte{[]byte("IssueIntegral"), []byte(studentID), []byte(fmt.Sprintf("%d", amount))}
	result := stub.MockInvoke("persistence_test", invokeArgs)
	assert.Equal(t, int32(shim.OK), result.Status, "发行积分应该成功")
	
	// 验证余额数据持久化
	queryArgs := [][]byte{[]byte("GetStudentBalance"), []byte(studentID)}
	queryResult := stub.MockInvoke("persistence_query", queryArgs)
	assert.Equal(t, int32(shim.OK), queryResult.Status, "查询余额应该成功")
	
	var balance StudentBalance
	err := json.Unmarshal(queryResult.Payload, &balance)
	assert.NoError(t, err, "反序列化余额应该成功")
	assert.Equal(t, amount, balance.TotalAmount, "余额应该正确持久化")
	assert.Equal(t, studentID, balance.StudentID, "学生ID应该匹配")
	
	// 验证积分记录持久化
	recordPrefix := fmt.Sprintf("issue_%s_", studentID)
	recordExists := false
	
	// 遍历所有状态检查积分记录
	for i := 0; i < 1000; i++ { // 限制搜索范围
		key := fmt.Sprintf("%s%d", recordPrefix, i)
		recordBytes, err := stub.GetState(key)
		if err == nil && recordBytes != nil {
			var record Integral
			err := json.Unmarshal(recordBytes, &record)
			if err == nil && record.StudentID == studentID && record.Amount == amount {
				recordExists = true
				break
			}
		}
	}
	
	assert.True(t, recordExists, "积分发行记录应该被持久化")
	fmt.Println("✓ 数据持久化验证通过")
	
	fmt.Println("=== 数据持久化测试完成 ===")
}

// TestIssueIntegralEdgeCases 边界条件测试
func TestIssueIntegralEdgeCases(t *testing.T) {
	fmt.Println("=== 开始边界条件测试 ===")
	
	chaincode := new(IntegralChaincode)
	
	// 边界测试用例
	edgeCases := []struct {
		name          string
		studentID     string
		amount        int
		description   string
		shouldSucceed bool
	}{
		{
			name:          "最小正整数积分",
			studentID:     "student_min_positive",
			amount:        1,
			description:   "发行最小正整数积分",
			shouldSucceed: true,
		},
		{
			name:          "超长学生ID",
			studentID:     "student_with_very_long_id_that_exceeds_typical_length_limits_and_tests_the_system_boundaries",
			amount:        100,
			description:   "测试超长学生ID处理",
			shouldSucceed: true,
		},
		{
			name:          "特殊字符学生ID",
			studentID:     "student_special_chars_123@#$%",
			amount:        100,
			description:   "测试特殊字符学生ID",
			shouldSucceed: true,
		},
	}
	
	for _, ec := range edgeCases {
		t.Run(ec.name, func(t *testing.T) {
			fmt.Printf("--- 边界测试: %s ---\n", ec.description)
			
			// 创建模拟上下文
			mockClientIdentity := new(MockClientIdentity)
			mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
			
			mockCtx := new(MockTransactionContext)
			mockCtx.clientIdentity = mockClientIdentity
			
			// 模拟stub
			mockStub := new(shim.MockStub)
			mockCtx.On("GetStub").Return(mockStub)
			
			// 执行测试
			err := chaincode.IssueIntegral(mockCtx, ec.studentID, ec.amount)
			
			if ec.shouldSucceed {
				assert.NoError(t, err, "边界测试应该成功: %s", ec.name)
				fmt.Printf("✓ 边界测试 '%s' 通过\n", ec.name)
			} else {
				assert.Error(t, err, "边界测试应该失败: %s", ec.name)
				fmt.Printf("✓ 边界测试 '%s' 正确处理\n", ec.name)
			}
		})
	}
	
	fmt.Println("=== 边界条件测试完成 ===")
}

// BenchmarkIssueIntegral 性能基准测试
func BenchmarkIssueIntegral(b *testing.B) {
	chaincode := new(IntegralChaincode)
	
	// 创建模拟上下文
	mockClientIdentity := new(MockClientIdentity)
	mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
	
	mockCtx := new(MockTransactionContext)
	mockCtx.clientIdentity = mockClientIdentity
	
	// 模拟stub
	mockStub := new(shim.MockStub)
	mockCtx.On("GetStub").Return(mockStub)
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		studentID := fmt.Sprintf("benchmark_student_%d", i)
		err := chaincode.IssueIntegral(mockCtx, studentID, 100)
		if err != nil {
			b.Errorf("基准测试失败: %v", err)
		}
	}
}