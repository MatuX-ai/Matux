#!/usr/bin/env python3
"""
多租户功能演示脚本
展示多租户架构的核心功能和使用方法
"""

import asyncio
import json
from typing import Dict, Any
import requests
from datetime import datetime

class MultitenantDemo:
    """多租户功能演示类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.organizations = {}
        self.users = {}
        
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "="*60)
        print(f"🎯 {title}")
        print("="*60)
    
    def print_step(self, step: str):
        """打印步骤"""
        print(f"\n📝 {step}")
        print("-" * 40)
    
    def print_result(self, result: Any):
        """打印结果"""
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
    
    def demo_organization_management(self):
        """演示组织管理功能"""
        self.print_header("组织管理演示")
        
        # 创建两个教育机构
        orgs_data = [
            {
                "name": "北京大学计算机学院",
                "contact_email": "cs@pku.edu.cn",
                "phone": "010-62751111",
                "address": "北京市海淀区颐和园路5号",
                "website": "https://cs.pku.edu.cn",
                "max_users": 2000
            },
            {
                "name": "清华大学软件学院",
                "contact_email": "software@tsinghua.edu.cn",
                "phone": "010-62782000",
                "address": "北京市海淀区清华园1号",
                "website": "https://www.thss.tsinghua.edu.cn",
                "max_users": 1500
            }
        ]
        
        for i, org_data in enumerate(orgs_data, 1):
            self.print_step(f"创建组织 {i}: {org_data['name']}")
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/organizations",
                    json=org_data
                )
                
                if response.status_code == 200:
                    org = response.json()
                    self.organizations[org['id']] = org
                    self.print_result({
                        "状态": "✅ 创建成功",
                        "组织ID": org['id'],
                        "名称": org['name'],
                        "联系邮箱": org['contact_email']
                    })
                else:
                    self.print_result({
                        "状态": "❌ 创建失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
    
    def demo_course_management(self):
        """演示课程管理功能"""
        self.print_header("课程管理演示")
        
        if not self.organizations:
            print("⚠️  请先创建组织")
            return
        
        # 为每个组织创建课程
        courses_data = {
            1: [  # 北京大学
                {
                    "title": "Python程序设计基础",
                    "code": "CS101-PKU",
                    "description": "面向初学者的Python编程课程",
                    "difficulty": "beginner",
                    "max_students": 100,
                    "duration_hours": 48,
                    "credit_hours": 3,
                    "price": 0,  # 免费课程
                    "is_free": True
                },
                {
                    "title": "数据结构与算法",
                    "code": "CS201-PKU",
                    "description": "经典数据结构和算法分析",
                    "difficulty": "intermediate",
                    "max_students": 80,
                    "duration_hours": 64,
                    "credit_hours": 4,
                    "price": 800,
                    "is_free": False
                }
            ],
            2: [  # 清华大学
                {
                    "title": "机器学习导论",
                    "code": "ML101-THU",
                    "description": "机器学习基础理论与实践",
                    "difficulty": "advanced",
                    "max_students": 60,
                    "duration_hours": 56,
                    "credit_hours": 3,
                    "price": 1200,
                    "is_free": False
                },
                {
                    "title": "Web开发实战",
                    "code": "WEB201-THU",
                    "description": "现代Web应用开发技术",
                    "difficulty": "intermediate",
                    "max_students": 120,
                    "duration_hours": 40,
                    "credit_hours": 2,
                    "price": 600,
                    "is_free": False
                }
            ]
        }
        
        for org_id, courses in courses_data.items():
            org_name = self.organizations[org_id]['name']
            self.print_step(f"为 {org_name} 创建课程")
            
            headers = {"X-Org-ID": str(org_id)}
            
            for course_data in courses:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/v1/org/{org_id}/courses",
                        json=course_data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        course = response.json()
                        self.print_result({
                            "状态": "✅ 课程创建成功",
                            "课程代码": course['code'],
                            "课程名称": course['title'],
                            "所属机构": org_name,
                            "学费": f"¥{course['price']}" if not course['is_free'] else "免费"
                        })
                    else:
                        self.print_result({
                            "状态": "❌ 课程创建失败",
                            "错误": response.text
                        })
                        
                except Exception as e:
                    self.print_result({
                        "状态": "❌ 请求异常",
                        "错误": str(e)
                    })
    
    def demo_tenant_isolation(self):
        """演示租户数据隔离"""
        self.print_header("租户数据隔离演示")
        
        if len(self.organizations) < 2:
            print("⚠️  需要至少两个组织来演示隔离")
            return
        
        org_ids = list(self.organizations.keys())
        org1_id, org2_id = org_ids[0], org_ids[1]
        org1_name = self.organizations[org1_id]['name']
        org2_name = self.organizations[org2_id]['name']
        
        self.print_step(f"验证 {org1_name} 只能看到自己的课程")
        
        try:
            # 用组织1的上下文查询课程
            headers = {"X-Org-ID": str(org1_id)}
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org1_id}/courses",
                headers=headers
            )
            
            if response.status_code == 200:
                courses = response.json()
                self.print_result({
                    "状态": "✅ 查询成功",
                    "组织": org1_name,
                    "课程数量": len(courses),
                    "课程列表": [course['code'] for course in courses]
                })
            else:
                self.print_result({
                    "状态": "❌ 查询失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
        
        self.print_step(f"验证 {org2_name} 只能看到自己的课程")
        
        try:
            # 用组织2的上下文查询课程
            headers = {"X-Org-ID": str(org2_id)}
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org2_id}/courses",
                headers=headers
            )
            
            if response.status_code == 200:
                courses = response.json()
                self.print_result({
                    "状态": "✅ 查询成功",
                    "组织": org2_name,
                    "课程数量": len(courses),
                    "课程列表": [course['code'] for course in courses]
                })
            else:
                self.print_result({
                    "状态": "❌ 查询失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
    
    def demo_tenant_config(self):
        """演示租户配置管理"""
        self.print_header("租户配置管理演示")
        
        if not self.organizations:
            print("⚠️  请先创建组织")
            return
        
        org_id = list(self.organizations.keys())[0]
        org_name = self.organizations[org_id]['name']
        
        self.print_step(f"为 {org_name} 初始化配置")
        
        try:
            headers = {"X-Org-ID": str(org_id)}
            response = self.session.post(
                f"{self.base_url}/api/v1/org/{org_id}/config/initialize",
                headers=headers
            )
            
            if response.status_code == 200:
                self.print_result({
                    "状态": "✅ 配置初始化成功",
                    "组织": org_name
                })
            else:
                self.print_result({
                    "状态": "❌ 配置初始化失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
        
        self.print_step(f"查看 {org_name} 的配置概览")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org_id}/config/overview",
                headers=headers
            )
            
            if response.status_code == 200:
                overview = response.json()
                self.print_result({
                    "状态": "✅ 获取配置概览成功",
                    "配置统计": overview.get('configs', {}),
                    "功能开关": overview.get('features', {}),
                    "资源配额": overview.get('quotas', {})
                })
            else:
                self.print_result({
                    "状态": "❌ 获取配置概览失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
    
    def demo_search_functionality(self):
        """演示搜索功能"""
        self.print_header("课程搜索功能演示")
        
        if not self.organizations:
            print("⚠️  请先创建组织和课程")
            return
        
        org_id = list(self.organizations.keys())[0]
        org_name = self.organizations[org_id]['name']
        
        self.print_step(f"在 {org_name} 中搜索Python相关课程")
        
        try:
            headers = {"X-Org-ID": str(org_id)}
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org_id}/courses/search",
                params={"query": "Python"},
                headers=headers
            )
            
            if response.status_code == 200:
                courses = response.json()
                self.print_result({
                    "状态": "✅ 搜索成功",
                    "关键词": "Python",
                    "找到课程数": len(courses),
                    "课程详情": [
                        {
                            "代码": course['code'],
                            "名称": course['title'],
                            "难度": course['difficulty']
                        }
                        for course in courses
                    ]
                })
            else:
                self.print_result({
                    "状态": "❌ 搜索失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
    
    def demo_statistics(self):
        """演示统计功能"""
        self.print_header("课程统计功能演示")
        
        if not self.organizations:
            print("⚠️  请先创建组织和课程")
            return
        
        org_id = list(self.organizations.keys())[0]
        org_name = self.organizations[org_id]['name']
        
        self.print_step(f"获取 {org_name} 的课程统计数据")
        
        try:
            headers = {"X-Org-ID": str(org_id)}
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org_id}/courses/statistics",
                headers=headers
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.print_result({
                    "状态": "✅ 统计获取成功",
                    "总课程数": stats.get('total_courses', 0),
                    "已发布课程": stats.get('published_courses', 0),
                    "草稿课程": stats.get('draft_courses', 0),
                    "总选课人数": stats.get('total_enrollments', 0),
                    "热门课程": stats.get('popular_courses', [])
                })
            else:
                self.print_result({
                    "状态": "❌ 统计获取失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })

def main():
    """主函数"""
    print("🎓 多租户架构功能演示")
    print("="*60)
    print("本演示将展示多租户系统的核心功能:")
    print("• 组织管理")
    print("• 课程管理")
    print("• 租户数据隔离")
    print("• 配置管理")
    print("• 搜索功能")
    print("• 统计分析")
    print("="*60)
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未正常运行，请先启动服务")
            return
        print("✅ 后端服务运行正常")
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("请确保服务在 http://localhost:8000 运行")
        return
    
    # 开始演示
    demo = MultitenantDemo()
    
    try:
        demo.demo_organization_management()
        demo.demo_course_management()
        demo.demo_tenant_isolation()
        demo.demo_tenant_config()
        demo.demo_search_functionality()
        demo.demo_statistics()
        
        print("\n" + "="*60)
        print("🎉 演示完成!")
        print("="*60)
        print("总结:")
        print(f"• 创建了 {len(demo.organizations)} 个教育机构")
        print("• 实现了完整的租户数据隔离")
        print("• 展示了多租户配置管理")
        print("• 验证了搜索和统计功能")
        print("\n现在您可以:")
        print("• 访问 http://localhost:8000/docs 查看完整API文档")
        print("• 使用不同的org_id测试租户隔离")
        print("• 配置不同的租户功能开关")
        
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")

if __name__ == "__main__":
    main()