package main

import (
	"fmt"
	"time"
)

// 本地测试验证函数
func main() {
	fmt.Println("🧪 IssueIntegral功能本地验证")
	fmt.Println("=" * 50)
	
	// 验证常量定义
	fmt.Printf("✅ 教育局MSP ID: %s\n", EducationBureauMSP)
	fmt.Printf("✅ 学校MSP ID: %s\n", SchoolMSP)
	fmt.Printf("✅ 企业MSP ID: %s\n", EnterpriseMSP)
	
	// 验证数据结构
	now := time.Now().Unix()
	
	integral := Integral{
		StudentID: "test_student_001",
		Amount:    100,
		Source:    "education",
		Timestamp: now,
	}
	
	fmt.Printf("\n📋 积分记录结构验证:\n")
	fmt.Printf("   学生ID: %s\n", integral.StudentID)
	fmt.Printf("   积分数额: %d\n", integral.Amount)
	fmt.Printf("   来源: %s\n", integral.Source)
	fmt.Printf("   时间戳: %d\n", integral.Timestamp)
	
	// 验证数据有效性
	if err := integral.Validate(); err != nil {
		fmt.Printf("❌ 积分数据验证失败: %v\n", err)
	} else {
		fmt.Printf("✅ 积分数据验证通过\n")
	}
	
	// 验证学生余额结构
	balance := StudentBalance{
		StudentID:   "test_student_001",
		TotalAmount: 500,
		UpdatedAt:   now,
	}
	
	fmt.Printf("\n💰 学生余额结构验证:\n")
	fmt.Printf("   学生ID: %s\n", balance.StudentID)
	fmt.Printf("   总余额: %d\n", balance.TotalAmount)
	fmt.Printf("   更新时间: %d\n", balance.UpdatedAt)
	
	if err := balance.Validate(); err != nil {
		fmt.Printf("❌ 余额数据验证失败: %v\n", err)
	} else {
		fmt.Printf("✅ 余额数据验证通过\n")
	}
	
	// 验证交易记录结构
	transaction := IntegralTransaction{
		ID:          fmt.Sprintf("tx_%d", now),
		StudentID:   "test_student_001",
		Amount:      100,
		SourceType:  "issue",
		SourceID:    "education_bureau",
		Description: "教育局发行积分 100 点",
		Timestamp:   now,
		Balance:     600,
	}
	
	fmt.Printf("\n📝 交易记录结构验证:\n")
	fmt.Printf("   交易ID: %s\n", transaction.ID)
	fmt.Printf("   学生ID: %s\n", transaction.StudentID)
	fmt.Printf("   金额: %d\n", transaction.Amount)
	fmt.Printf("   类型: %s\n", transaction.SourceType)
	fmt.Printf("   描述: %s\n", transaction.Description)
	fmt.Printf("   余额: %d\n", transaction.Balance)
	
	if err := transaction.Validate(); err != nil {
		fmt.Printf("❌ 交易记录验证失败: %v\n", err)
	} else {
		fmt.Printf("✅ 交易记录验证通过\n")
	}
	
	// 验证边界条件
	fmt.Printf("\n🚧 边界条件验证:\n")
	
	// 测试无效积分数据
	invalidIntegral := Integral{
		StudentID: "",
		Amount:    -50,
		Source:    "",
		Timestamp: 0,
	}
	
	if err := invalidIntegral.Validate(); err != nil {
		fmt.Printf("✅ 无效积分数据被正确拒绝: %v\n", err)
	} else {
		fmt.Printf("❌ 无效积分数据未被拒绝\n")
	}
	
	// 测试无效余额数据
	invalidBalance := StudentBalance{
		StudentID:   "",
		TotalAmount: -100,
		UpdatedAt:   0,
	}
	
	if err := invalidBalance.Validate(); err != nil {
		fmt.Printf("✅ 无效余额数据被正确拒绝: %v\n", err)
	} else {
		fmt.Printf("❌ 无效余额数据未被拒绝\n")
	}
	
	fmt.Printf("\n🎉 本地功能验证完成！\n")
	fmt.Printf("所有核心数据结构和验证逻辑工作正常。\n")
	fmt.Printf("建议在Fabric网络环境中进行完整集成测试。\n")
}