package main

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/stretchr/testify/assert"
)

// TestIssueIntegralIntegration 集成测试IssueIntegral功能
func TestIssueIntegralIntegration(t *testing.T) {
	// 创建链码实例
	chaincode, err := contractapi.NewChaincode(&IntegralChaincode{})
	assert.NoError(t, err, "创建链码实例应该成功")

	// 创建模拟stub
	stub := shim.NewMockStub("integral", chaincode)
	assert.NotNil(t, stub, "创建mock stub应该成功")

	// 初始化账本
	initArgs := [][]byte{}
	response := stub.MockInit("init", initArgs)
	assert.Equal(t, int32(shim.OK), response.Status, "初始化账本应该成功")

	t.Run("教育局权限测试", func(t *testing.T) {
		// 设置教育局MSP ID
		stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))

		// 教育局应该能够成功发行积分
		args := [][]byte{
			[]byte("IssueIntegral"),
			[]byte("student_test_001"),
			[]byte("500"),
		}
		
		response := stub.MockInvoke("issue1", args)
		assert.Equal(t, int32(shim.OK), response.Status, "教育局发行积分应该成功")
	})

	t.Run("非教育局权限测试", func(t *testing.T) {
		// 设置学校MSP ID
		stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", SchoolMSP))

		// 学校不应该能够发行积分
		args := [][]byte{
			[]byte("IssueIntegral"),
			[]byte("student_test_002"),
			[]byte("300"),
		}
		
		response := stub.MockInvoke("issue2", args)
		assert.Equal(t, int32(shim.ERROR), response.Status, "非教育局发行积分应该失败")
		assert.Contains(t, response.Message, "权限不足", "错误消息应该包含权限不足")
	})

	t.Run("余额查询测试", func(t *testing.T) {
		// 先确保有教育局权限
		stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))

		// 发行积分给学生
		issueArgs := [][]byte{
			[]byte("IssueIntegral"),
			[]byte("student_balance_test"),
			[]byte("1000"),
		}
		
		response := stub.MockInvoke("issue3", issueArgs)
		assert.Equal(t, int32(shim.OK), response.Status, "发行积分应该成功")

		// 查询学生余额
		queryArgs := [][]byte{
			[]byte("GetStudentBalance"),
			[]byte("student_balance_test"),
		}
		
		response = stub.MockInvoke("query1", queryArgs)
		assert.Equal(t, int32(shim.OK), response.Status, "查询余额应该成功")
		
		// 解析响应数据
		var balance StudentBalance
		err := json.Unmarshal(response.Payload, &balance)
		assert.NoError(t, err, "解析余额数据应该成功")
		assert.Equal(t, "student_balance_test", balance.StudentID, "学生ID应该匹配")
		assert.Equal(t, 1000, balance.TotalAmount, "余额应该是1000")
	})

	t.Run("多次发行测试", func(t *testing.T) {
		stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))

		studentID := "student_multiple_test"
		
		// 第一次发行
		args1 := [][]byte{
			[]byte("IssueIntegral"),
			[]byte(studentID),
			[]byte("200"),
		}
		response1 := stub.MockInvoke("issue4", args1)
		assert.Equal(t, int32(shim.OK), response1.Status, "第一次发行应该成功")

		// 第二次发行
		args2 := [][]byte{
			[]byte("IssueIntegral"),
			[]byte(studentID),
			[]byte("300"),
		}
		response2 := stub.MockInvoke("issue5", args2)
		assert.Equal(t, int32(shim.OK), response2.Status, "第二次发行应该成功")

		// 查询最终余额
		queryArgs := [][]byte{
			[]byte("GetStudentBalance"),
			[]byte(studentID),
		}
		response := stub.MockInvoke("query2", queryArgs)
		assert.Equal(t, int32(shim.OK), response.Status, "查询余额应该成功")
		
		var balance StudentBalance
		err := json.Unmarshal(response.Payload, &balance)
		assert.NoError(t, err)
		assert.Equal(t, 500, balance.TotalAmount, "余额应该是500 (200+300)")
	})

	t.Run("边界条件测试", func(t *testing.T) {
		stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))

		testCases := []struct {
			name      string
			studentID string
			amount    string
			shouldFail bool
		}{
			{
				name:       "空学生ID",
				studentID:  "",
				amount:     "100",
				shouldFail: true,
			},
			{
				name:       "零积分",
				studentID:  "student_zero",
				amount:     "0",
				shouldFail: true,
			},
			{
				name:       "负积分",
				studentID:  "student_negative",
				amount:     "-50",
				shouldFail: true,
			},
			{
				name:       "极大数值",
				studentID:  "student_large",
				amount:     "1000000",
				shouldFail: false,
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				args := [][]byte{
					[]byte("IssueIntegral"),
					[]byte(tc.studentID),
					[]byte(tc.amount),
				}
				
				response := stub.MockInvoke("boundary_test_"+tc.name, args)
				
				if tc.shouldFail {
					assert.Equal(t, int32(shim.ERROR), response.Status, "应该失败")
				} else {
					assert.Equal(t, int32(shim.OK), response.Status, "应该成功")
				}
			})
		}
	})
}

// TestIntegralDataStructure 测试积分数据结构
func TestIntegralDataStructure(t *testing.T) {
	now := time.Now().Unix()
	
	integral := Integral{
		StudentID: "test_student",
		Amount:    100,
		Source:    "education",
		Timestamp: now,
	}

	// 测试验证
	err := integral.Validate()
	assert.NoError(t, err, "有效的积分数据应该通过验证")

	// 测试JSON序列化
	jsonData, err := integral.ToJSON()
	assert.NoError(t, err, "序列化应该成功")
	assert.NotEmpty(t, jsonData, "JSON数据不应该为空")

	// 测试JSON反序列化
	var parsedIntegral Integral
	err = parsedIntegral.FromJSON(jsonData)
	assert.NoError(t, err, "反序列化应该成功")
	assert.Equal(t, integral.StudentID, parsedIntegral.StudentID)
	assert.Equal(t, integral.Amount, parsedIntegral.Amount)
	assert.Equal(t, integral.Source, parsedIntegral.Source)
	assert.Equal(t, integral.Timestamp, parsedIntegral.Timestamp)
}

// TestStudentBalance 测试学生余额结构
func TestStudentBalance(t *testing.T) {
	balance := StudentBalance{
		StudentID:   "test_student",
		TotalAmount: 1000,
		UpdatedAt:   time.Now().Unix(),
	}

	// 测试验证
	err := balance.Validate()
	assert.NoError(t, err, "有效的余额数据应该通过验证")

	// 测试无效数据
	invalidBalance := StudentBalance{
		StudentID:   "",
		TotalAmount: -100,
		UpdatedAt:   0,
	}

	err = invalidBalance.Validate()
	assert.Error(t, err, "无效的余额数据应该验证失败")
	assert.Contains(t, err.Error(), "student_id cannot be empty")
	assert.Contains(t, err.Error(), "total_amount cannot be negative")
	assert.Contains(t, err.Error(), "updated_at must be greater than 0")
}

// BenchmarkIssueIntegral 性能基准测试
func BenchmarkIssueIntegral(b *testing.B) {
	// 创建链码实例
	chaincode, err := contractapi.NewChaincode(&IntegralChaincode{})
	if err != nil {
		b.Fatal(err)
	}

	stub := shim.NewMockStub("integral", chaincode)
	stub.MockInit("init", [][]byte{})
	
	// 设置教育局权限
	stub.Creator = []byte(fmt.Sprintf("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n%s", EducationBureauMSP))

	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		args := [][]byte{
			[]byte("IssueIntegral"),
			[]byte(fmt.Sprintf("benchmark_student_%d", i)),
			[]byte("100"),
		}
		
		response := stub.MockInvoke(fmt.Sprintf("bench_%d", i), args)
		if response.Status != shim.OK {
			b.Fatalf("Benchmark failed: %s", response.Message)
		}
	}
}