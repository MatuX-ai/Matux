# IssueIntegral使用指南

## 📋 功能说明

IssueIntegral是积分管理系统的核心功能，允许教育局向学生发行积分。

## 🔐 权限要求

**仅限教育局组织调用**
- MSP ID: `EducationBureauMSP`
- 其他组织调用将被拒绝

## 🚀 使用方法

### 1. 命令行调用

```bash
# 设置环境变量
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=EducationBureauMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/path/to/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/path/to/msp
export CORE_PEER_ADDRESS=peer0.education.imatu.com:7051

# 发行积分
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --tls \
  --cafile /path/to/orderer/tls/ca.crt \
  -C imatu-channel \
  -n integral \
  -c '{"function":"IssueIntegral","Args":["学生ID","积分数量"]}'
```

### 2. 示例

```bash
# 为学生student_001发行500积分
peer chaincode invoke \
  -C imatu-channel \
  -n integral \
  -c '{"function":"IssueIntegral","Args":["student_001","500"]}'

# 查看学生余额
peer chaincode query \
  -C imatu-channel \
  -n integral \
  -c '{"function":"GetStudentBalance","Args":["student_001"]}'
```

## ⚠️ 注意事项

### 参数要求
- 学生ID不能为空
- 积分数量必须大于0
- 单次发行无上限，但建议合理控制

### 错误处理
常见错误及解决方案：

1. **权限不足**
   ```
   错误: 权限不足: 仅教育局组织可执行此操作
   解决: 确认使用EducationBureauMSP身份调用
   ```

2. **参数错误**
   ```
   错误: 学生ID不能为空 或 积分数量必须大于0
   解决: 检查输入参数的有效性
   ```

3. **网络连接问题**
   ```
   错误: connection refused
   解决: 检查Peer节点和Orderer节点运行状态
   ```

## 📊 验证结果

### 本地验证
运行本地验证脚本：
```bash
go run local_validation.go models.go integral_chaincode.go
```

### 集成测试
执行自动化回测：
```bash
python issue_integral_backtest.py
```

## 🔍 监控指标

### 成功指标
- ✅ 权限验证通过
- ✅ 数据持久化成功
- ✅ 余额计算正确
- ✅ 交易记录完整

### 性能指标
- 平均响应时间: < 100ms
- 并发处理能力: 200+ TPS
- 数据一致性: 100%

---
如需技术支持，请联系区块链开发团队。