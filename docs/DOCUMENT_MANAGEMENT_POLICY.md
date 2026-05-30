# 文档管理制度

## 概述

为确保iMatu项目文档的质量、一致性和时效性，特制定本文档管理制度。

## 文档分类与责任分工

### 文档类别及负责人

| 文档类别 | 负责人 | 审核人 | 更新频率 |
|----------|--------|--------|----------|
| 项目概述 | 项目经理 | 技术总监 | 季度 |
| 技术架构 | 架构师 | CTO | 月度 |
| 开发指南 | 技术负责人 | 架构师 | 双周 |
| API参考 | 后端主管 | 前端主管 | 每次发布 |
| 部署运维 | 运维工程师 | 技术总监 | 月度 |
| 测试质量 | QA主管 | 技术负责人 | 双周 |

## 文档生命周期管理

### 1. 文档创建流程

```
需求提出 → 内容撰写 → 内部评审 → 格式检查 → 正式发布
    ↓         ↓         ↓         ↓         ↓
  相关方    文档作者   技术专家   格式专员   全体可见
```

### 2. 文档更新流程

```
发现问题 → 提交修改 → 审核批准 → 更新发布 → 通知相关人员
    ↓        ↓        ↓        ↓         ↓
Issue单   PR请求    技术评审   合并主干    邮件通知
```

### 3. 文档废弃流程

```
评估必要性 → 标记废弃 → 归档备份 → 物理删除
    ↓         ↓         ↓         ↓
技术评审    添加标识    移至archive  30天后删除
```

## 质量控制标准

### 内容质量要求
- **准确性**: 技术描述必须准确无误
- **完整性**: 覆盖所有必要信息
- **时效性**: 内容与当前版本保持同步
- **可读性**: 语言简洁明了，逻辑清晰

### 格式规范检查
- [ ] 遵循标准文档模板
- [ ] 标题层级结构正确
- [ ] 代码示例可正常运行
- [ ] 链接地址有效可用
- [ ] 图表清晰标注完整

### 评审机制
- **技术评审**: 由相关领域专家审核技术内容
- **语言评审**: 由文档专员检查语言表达
- **格式评审**: 由QA检查格式规范性

## 自动化工具支持

### 文档检查脚本
```bash
#!/bin/bash
# docs_validator.sh

echo "开始文档质量检查..."

# 检查Markdown语法
find docs/ -name "*.md" -exec markdownlint {} \;

# 检查链接有效性
python scripts/check_links.py

# 检查图片引用
python scripts/check_images.py

# 生成文档索引
python scripts/generate_index.py

echo "文档检查完成"
```

### 链接检查工具
```python
# scripts/check_links.py
import os
import re
from pathlib import Path

def check_internal_links():
    """检查内部链接有效性"""
    docs_root = Path("docs")
    broken_links = []
    
    for md_file in docs_root.rglob("*.md"):
        content = md_file.read_text(encoding='utf-8')
        links = re.findall(r'\[.*?\]\((.*?)\)', content)
        
        for link in links:
            if link.startswith(('http', 'https')):
                continue  # 外部链接跳过
                
            # 检查相对链接
            target_path = (md_file.parent / link).resolve()
            if not target_path.exists():
                broken_links.append({
                    'file': str(md_file),
                    'link': link,
                    'target': str(target_path)
                })
    
    return broken_links

if __name__ == "__main__":
    broken = check_internal_links()
    if broken:
        print("发现无效链接:")
        for item in broken:
            print(f"  {item['file']} -> {item['link']}")
        exit(1)
    else:
        print("所有链接检查通过")
```

### 自动索引生成
```python
# scripts/generate_index.py
import os
from pathlib import Path

def generate_document_index():
    """自动生成文档索引"""
    docs_root = Path("docs")
    index_content = "# iMatu文档索引\n\n"
    
    # 按目录分类
    categories = {
        "01-项目概述": "项目基本信息和总体规划",
        "02-开发指南": "开发环境搭建和编码规范",
        "03-核心技术": "各技术模块详细说明",
        "04-API参考": "接口规范和使用示例",
        "05-部署运维": "部署配置和运维指南",
        "06-测试质量": "测试策略和质量报告"
    }
    
    for category_dir in sorted(docs_root.glob("[0-9]*-*")):
        if category_dir.is_dir():
            category_name = category_dir.name
            category_desc = categories.get(category_name, "")
            
            index_content += f"## {category_name} {category_desc}\n\n"
            
            # 列出该目录下所有文档
            for doc_file in sorted(category_dir.glob("*.md")):
                if doc_file.name != "README.md":
                    title = doc_file.stem.replace('-', ' ')
                    index_content += f"- [{title}]({category_dir.name}/{doc_file.name})\n"
            
            index_content += "\n"
    
    # 写入索引文件
    index_file = docs_root / "INDEX_AUTO.md"
    index_file.write_text(index_content, encoding='utf-8')
    print(f"索引已生成: {index_file}")

if __name__ == "__main__":
    generate_document_index()
```

## 版本控制策略

### Git分支管理
```bash
# 文档专用分支命名规范
docs/feature/new-api-docs      # 新增API文档
docs/fix/typo-correction       # 修正错别字
docs/update/architecture-refactor # 架构文档更新
```

### 提交信息规范
```
docs: 添加用户管理API文档
docs: 修正区块链部署指南中的配置错误
docs: 更新前端开发环境搭建步骤
```

### 发布管理
- **主版本**: 重大结构调整
- **次版本**: 新增重要文档
- **修订版**: 内容修正和完善

## 培训与知识传递

### 新员工培训
- 文档体系介绍 (1小时)
- 标准模板使用培训 (2小时)
- 贡献流程演练 (1小时)

### 定期分享会
- 月度文档质量回顾
- 最佳实践分享
- 工具使用技巧交流

## 持续改进机制

### KPI指标
- 文档更新及时率 > 95%
- 用户满意度 > 4.5/5
- 链接有效率 > 99%
- 格式规范符合率 > 98%

### 改进建议收集
- 用户反馈渠道
- 定期内部评审
- 外部专家咨询

### 定期审计
- 季度文档质量审计
- 年度体系架构评估
- 用户使用情况分析

## 应急处理预案

### 文档丢失处理
1. 从Git历史恢复
2. 从备份系统还原
3. 联系原作者重建

### 重大错误修正
1. 立即标记问题文档
2. 发布修正版本
3. 通知所有相关方
4. 更新影响分析

---

## 附录

### 相关文档
- [文档模板](TEMPLATE.md)
- [文档分类清单](DOCUMENT_CLASSIFICATION_INVENTORY.md)

### 联系方式
- 文档管理负责人: [待指定]
- 技术文档组邮箱: docs@imatu.com
- 紧急联系电话: [待指定]

---
*iMatu文档管理制度 | 版本 v1.0 | 最后更新 2026年3月*