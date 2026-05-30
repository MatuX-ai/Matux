# 企业赞助管理平台操作手册

## 目录
1. [平台概述](#平台概述)
2. [快速入门](#快速入门)
3. [功能详解](#功能详解)
4. [积分体系](#积分体系)
5. [API接口文档](#api接口文档)
6. [常见问题](#常见问题)
7. [技术支持](#技术支持)

## 平台概述

企业赞助管理平台是iMatu教育平台的重要组成部分，专为企业客户设计，提供品牌曝光统计与公益积分转换的一站式服务。

### 核心价值
- **品牌推广**：多元化曝光渠道，精准触达目标用户群体
- **社会责任**：积分转换公益项目，践行企业社会责任
- **数据驱动**：实时数据分析，优化营销投资回报率
- **透明公正**：完整的数据追踪和审计机制

### 适用场景
- 教育科技企业品牌推广
- 企业CSR（企业社会责任）项目
- 行业峰会和会议赞助
- 教育公益项目合作

## 快速入门

### 1. 账户准备
联系平台管理员获取企业账户权限：
- 企业管理员账号
- 组织ID分配
- API访问密钥（如需要）

### 2. 创建首个赞助活动
1. 登录管理后台
2. 进入"赞助管理"模块
3. 点击"新建赞助活动"
4. 填写基本信息：
   - 活动名称
   - 赞助金额
   - 活动周期
   - 目标受众
5. 选择曝光渠道组合
6. 提交审核

### 3. 监控活动效果
1. 查看仪表板实时数据
2. 分析曝光量和互动率
3. 跟踪积分获取情况
4. 优化投放策略

### 4. 积分转换公益
1. 积累足够积分后
2. 选择合适的公益项目
3. 提交转换申请
4. 跟踪项目执行进展

## 功能详解

### 赞助活动管理

#### 创建赞助活动
```json
{
  "name": "2026年度教育科技赞助计划",
  "description": "支持教育科技创新发展的年度赞助",
  "sponsor_amount": 50000,
  "currency": "CNY",
  "start_date": "2026-03-01T00:00:00",
  "end_date": "2027-02-28T23:59:59",
  "exposure_types": ["banner", "sidebar", "content_integration"],
  "target_audience": {
    "age_range": "15-25",
    "interests": ["programming", "ai", "technology"],
    "geography": ["China"]
  }
}
```

#### 活动状态说明
- **ACTIVE**：活动中，正常产生曝光和积分
- **PAUSED**：已暂停，暂时停止曝光统计
- **COMPLETED**：已完成，活动周期结束
- **CANCELLED**：已取消，提前终止活动

### 品牌曝光管理

#### 曝光类型
| 类型 | 英文标识 | 积分系数 | 适用场景 |
|------|----------|----------|----------|
| 横幅广告 | banner | 1.0 | 首页、频道页顶部 |
| 侧边栏 | sidebar | 0.8 | 页面侧边栏位置 |
| 弹窗 | popup | 1.2 | 用户交互触发 |
| 邮件推广 | email | 1.5 | EDM邮件营销 |
| 社交媒体 | social_media | 1.3 | 平台社交分享 |
| 内容植入 | content_integration | 2.0 | 课程内容融合 |

#### 曝光数据统计维度
- **展示次数**：广告被展示的总次数
- **点击次数**：用户点击广告的次数
- **互动次数**：点赞、分享、评论等互动行为
- **转化次数**：最终达成目标的行为次数
- **点击率(CTR)**：点击次数/展示次数 × 100%
- **互动率**：互动次数/展示次数 × 100%

### 积分体系

#### 积分获取规则
积分基于曝光质量和效果计算：

```
基础积分 = 展示次数 × 0.1

类型系数调整：
- 横幅广告：×1.0
- 侧边栏：×0.8
- 弹窗：×1.2
- 邮件推广：×1.5
- 社交媒体：×1.3
- 内容植入：×2.0

效果加成：
- 点击率 > 5%：额外 ×1.5
- 高互动：每互动 +0.5积分
```

#### 积分转换规则

##### 教育资源捐赠
```
所需积分：1000分
转换内容：在线课程50个名额
单个价值：200元
适用类别：教育、科技
最低赞助：10000元
有效期：365天
个人限额：5次
```

##### 环保公益项目
```
所需积分：2000分
转换内容：植树造林项目
树木数量：每分0.1棵
项目地点：中国北方地区
适用类别：环保
最低赞助：20000元
有效期：730天
个人限额：3次
```

##### 科技教育基金
```
所需积分：5000分
转换内容：奖学金基金
资助人数：10名学生
资助金额：每人500元
适用类别：教育、科技
最低赞助：50000元
有效期：1095天
个人限额：2次
```

#### 积分使用限制
- 积分有效期：自获得之日起2年内有效
- 不同活动积分不可合并使用
- 转换后不可撤销
- 每个转换规则有个人使用次数限制

## API接口文档

### 基础信息
- **基础URL**：`https://api.imatu.com/api/v1/sponsorship`
- **认证方式**：JWT Token
- **数据格式**：JSON
- **字符编码**：UTF-8

### 认证请求头
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

### 核心API接口

#### 1. 创建赞助活动
```
POST /organizations/{org_id}/sponsorships

请求参数：
{
  "name": "string",
  "description": "string",
  "sponsor_amount": "number",
  "currency": "string",
  "start_date": "datetime",
  "end_date": "datetime",
  "exposure_types": ["string"],
  "target_audience": {}
}

响应示例：
{
  "id": 123,
  "org_id": 456,
  "name": "2026年度赞助计划",
  "status": "active",
  "total_exposures": 0,
  "total_points_earned": 0.0,
  "created_at": "2026-03-01T10:00:00Z"
}
```

#### 2. 获取赞助活动列表
```
GET /organizations/{org_id}/sponsorships?status=active&skip=0&limit=50

响应示例：
[
  {
    "id": 123,
    "name": "2026年度赞助计划",
    "sponsor_amount": 50000,
    "status": "active",
    "total_exposures": 150000,
    "total_points_earned": 1500,
    "conversion_rate": 3.2
  }
]
```

#### 3. 记录品牌曝光
```
POST /sponsorships/{sponsorship_id}/exposures

请求参数：
{
  "exposure_type": "banner",
  "platform": "主网站",
  "placement": "首页顶部横幅",
  "view_count": 10000,
  "click_count": 300,
  "engagement_count": 150
}

响应示例：
{
  "exposure_id": 789,
  "points_earned": 1200.5,
  "message": "品牌曝光记录成功"
}
```

#### 4. 获取积分余额
```
GET /sponsorships/{sponsorship_id}/points/balance

响应示例：
{
  "available_points": 2500.0
}
```

#### 5. 获取转换规则
```
GET /points/conversion-rules?is_active=true&category=education

响应示例：
[
  {
    "id": 1,
    "name": "教育资源捐赠",
    "points_required": 1000,
    "reward_type": "educational_resources",
    "reward_value": {
      "type": "online_courses",
      "quantity": 50,
      "value_per_unit": 200
    },
    "is_active": true
  }
]
```

#### 6. 转换积分
```
POST /sponsorships/{sponsorship_id}/points/convert

请求参数：
{
  "rule_id": 1,
  "quantity": 2
}

响应示例：
{
  "success": true,
  "transactions_count": 2,
  "message": "成功转换 2 次积分"
}
```

#### 7. 获取分析数据
```
GET /organizations/{org_id}/analytics?start_date=2026-01-01&end_date=2026-02-28

响应示例：
{
  "period_start": "2026-01-01T00:00:00Z",
  "period_end": "2026-02-28T23:59:59Z",
  "summary": {
    "total_sponsorships": 12,
    "active_sponsorships": 8,
    "total_amount": 150000,
    "total_exposures": 250000,
    "total_points_earned": 15000,
    "average_conversion_rate": 3.2
  },
  "trends": [...],
  "top_performing": [...]
}
```

## 常见问题

### 账户与权限
**Q: 如何申请企业账户？**
A: 联系平台商务团队，提供企业营业执照和相关资质文件。

**Q: 单个账户可以管理多个赞助活动吗？**
A: 可以，一个企业账户可同时管理多个赞助活动。

### 积分相关
**Q: 积分何时到账？**
A: 曝光数据经系统验证后，积分通常在24小时内到账。

**Q: 积分可以转让给其他企业吗？**
A: 不可以，积分仅限于本企业账户内使用。

**Q: 积分过期了怎么办？**
A: 过期积分无法恢复，请及时使用有效期内的积分。

### 技术问题
**Q: API调用频率有限制吗？**
A: 默认限制每分钟100次调用，如有更高需求请联系技术支持。

**Q: 如何处理API返回错误？**
A: 请检查错误码和错误信息，常见问题包括认证失效、参数错误等。

### 合规与安全
**Q: 平台如何保护企业数据安全？**
A: 采用企业级加密标准，通过ISO 27001安全认证。

**Q: 曝光数据的真实性如何保证？**
A: 建立多重验证机制，包括第三方监测和人工审核。

## 技术支持

### 联系方式
- **技术支持邮箱**：support@imatu.com
- **商务合作**：biz@imatu.com
- **客服热线**：400-123-4567
- **在线客服**：平台内即时聊天

### 服务时间
- 工作日：9:00-18:00
- 紧急故障：7×24小时响应

### 文档资源
- [API参考文档](https://docs.imatu.com/api/sponsorship)
- [开发者社区](https://community.imatu.com)
- [视频教程](https://learn.imatu.com/sponsorship)

---

*文档版本：v1.0*  
*最后更新：2026年2月28日*  
*适用于平台版本：≥2.5.0*