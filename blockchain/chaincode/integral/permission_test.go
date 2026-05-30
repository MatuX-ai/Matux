package main

import (
	"testing"
	
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockClientIdentity 模拟客户端身份接口
type MockClientIdentity struct {
	mock.Mock
}

func (m *MockClientIdentity) GetID() (string, error) {
	args := m.Called()
	return args.String(0), args.Error(1)
}

func (m *MockClientIdentity) GetMSPID() (string, error) {
	args := m.Called()
	return args.String(0), args.Error(1)
}

func (m *MockClientIdentity) GetAttributeValue(attrName string) (string, bool, error) {
	args := m.Called(attrName)
	return args.String(0), args.Bool(1), args.Error(2)
}

func (m *MockClientIdentity) AssertAttributeValue(attrName, attrValue string) error {
	args := m.Called(attrName, attrValue)
	return args.Error(0)
}

func (m *MockClientIdentity) GetX509Certificate() (*shim.X509Certificate, error) {
	args := m.Called()
	return args.Get(0).(*shim.X509Certificate), args.Error(1)
}

// MockTransactionContext 模拟交易上下文
type MockTransactionContext struct {
	mock.Mock
	contractapi.TransactionContextInterface
	clientIdentity *MockClientIdentity
}

func (m *MockTransactionContext) GetClientIdentity() contractapi.ClientIdentity {
	return m.clientIdentity
}

func (m *MockTransactionContext) GetStub() shim.ChaincodeStubInterface {
	args := m.Called()
	return args.Get(0).(shim.ChaincodeStubInterface)
}

// TestCheckEducationBureauPermission 测试教育局权限检查
func TestCheckEducationBureauPermission(t *testing.T) {
	tests := []struct {
		name           string
		mspID          string
		expectError    bool
		expectedErrMsg string
	}{
		{
			name:           "教育局组织应该有权限",
			mspID:          EducationBureauMSP,
			expectError:    false,
			expectedErrMsg: "",
		},
		{
			name:           "学校组织不应该有权限",
			mspID:          SchoolMSP,
			expectError:    true,
			expectedErrMsg: "权限不足: 仅教育局组织可执行此操作",
		},
		{
			name:           "企业组织不应该有权限",
			mspID:          EnterpriseMSP,
			expectError:    true,
			expectedErrMsg: "权限不足: 仅教育局组织可执行此操作",
		},
		{
			name:           "未知组织不应该有权限",
			mspID:          "UnknownMSP",
			expectError:    true,
			expectedErrMsg: "权限不足: 仅教育局组织可执行此操作",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// 创建模拟对象
			mockClientIdentity := new(MockClientIdentity)
			mockCtx := new(MockTransactionContext)
			
			// 设置期望调用
			mockClientIdentity.On("GetMSPID").Return(tt.mspID, nil)
			mockCtx.clientIdentity = mockClientIdentity
			
			// 执行测试
			err := CheckEducationBureauPermission(mockCtx)
			
			// 验证结果
			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.expectedErrMsg)
			} else {
				assert.NoError(t, err)
			}
			
			// 验证模拟调用
			mockClientIdentity.AssertExpectations(t)
		})
	}
}

// TestGetCallerMSPID 测试获取调用者MSP ID
func TestGetCallerMSPID(t *testing.T) {
	tests := []struct {
		name        string
		mspID       string
		hasError    bool
		expectedErr string
	}{
		{
			name:        "成功获取MSP ID",
			mspID:       EducationBureauMSP,
			hasError:    false,
			expectedErr: "",
		},
		{
			name:        "获取MSP ID失败",
			mspID:       "",
			hasError:    true,
			expectedErr: "获取MSP ID失败",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// 创建模拟对象
			mockClientIdentity := new(MockClientIdentity)
			mockCtx := new(MockTransactionContext)
			
			// 设置期望调用
			if tt.hasError {
				mockClientIdentity.On("GetMSPID").Return("", assert.AnError)
			} else {
				mockClientIdentity.On("GetMSPID").Return(tt.mspID, nil)
			}
			mockCtx.clientIdentity = mockClientIdentity
			
			// 执行测试
			result, err := GetCallerMSPID(mockCtx)
			
			// 验证结果
			if tt.hasError {
				assert.Error(t, err)
				assert.Empty(t, result)
				assert.Contains(t, err.Error(), tt.expectedErr)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.mspID, result)
			}
			
			// 验证模拟调用
			mockClientIdentity.AssertExpectations(t)
		})
	}
}

// TestIssueIntegralValidation 测试IssueIntegral函数的参数验证
func TestIssueIntegralValidation(t *testing.T) {
	chaincode := new(IntegralChaincode)
	
	// 创建有权调用的模拟上下文
	mockClientIdentity := new(MockClientIdentity)
	mockClientIdentity.On("GetMSPID").Return(EducationBureauMSP, nil)
	
	mockCtx := new(MockTransactionContext)
	mockCtx.clientIdentity = mockClientIdentity
	
	// 模拟stub
	mockStub := new(shim.MockStub)
	mockCtx.On("GetStub").Return(mockStub)
	
	tests := []struct {
		name        string
		studentID   string
		amount      int
		expectError bool
		errorMsg    string
	}{
		{
			name:        "有效参数",
			studentID:   "student_001",
			amount:      100,
			expectError: false,
			errorMsg:    "",
		},
		{
			name:        "空学生ID",
			studentID:   "",
			amount:      100,
			expectError: true,
			errorMsg:    "学生ID不能为空",
		},
		{
			name:        "零积分",
			studentID:   "student_001",
			amount:      0,
			expectError: true,
			errorMsg:    "积分数量必须大于0",
		},
		{
			name:        "负积分",
			studentID:   "student_001",
			amount:      -50,
			expectError: true,
			errorMsg:    "积分数量必须大于0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := chaincode.IssueIntegral(mockCtx, tt.studentID, tt.amount)
			
			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errorMsg)
			} else {
				// 对于有效参数，我们期望权限检查通过但可能因为其他原因失败
				// 这里主要是测试参数验证逻辑
				if err != nil {
					// 如果有错误，应该不是参数验证错误
					assert.NotContains(t, err.Error(), tt.errorMsg)
				}
			}
		})
	}
}

// TestConstants 测试常量定义
func TestConstants(t *testing.T) {
	assert.Equal(t, "EducationBureauMSP", EducationBureauMSP)
	assert.Equal(t, "SchoolMSP", SchoolMSP)
	assert.Equal(t, "EnterpriseMSP", EnterpriseMSP)
}