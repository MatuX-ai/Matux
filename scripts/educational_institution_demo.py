#!/usr/bin/env python3
"""
教育机构完整功能演示脚本
展示教师、学生、教室、课时安排等核心功能
"""

import asyncio
import json
from typing import Dict, Any
import requests
from datetime import datetime, date, timedelta

class EducationalInstitutionDemo:
    """教育机构功能演示类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.organizations = {}
        self.users = {}
        self.teachers = {}
        self.students = {}
        self.classrooms = {}
        self.courses = {}
        
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "="*70)
        print(f"🏫 {title}")
        print("="*70)
    
    def print_step(self, step: str):
        """打印步骤"""
        print(f"\n📝 {step}")
        print("-" * 50)
    
    def print_result(self, result: Any):
        """打印结果"""
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print(result)
    
    def demo_organization_setup(self):
        """演示教育机构基础设置"""
        self.print_header("教育机构基础设置")
        
        # 创建教育机构
        org_data = {
            "name": "北京市第一中学",
            "contact_email": "admin@bj1school.edu.cn",
            "phone": "010-66668888",
            "address": "北京市朝阳区建国路1号",
            "website": "https://www.bj1school.edu.cn",
            "max_users": 2000
        }
        
        self.print_step("创建教育机构")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/organizations",
                json=org_data
            )
            
            if response.status_code == 200:
                org = response.json()
                self.organizations[org['id']] = org
                self.print_result({
                    "状态": "✅ 教育机构创建成功",
                    "机构ID": org['id'],
                    "机构名称": org['name'],
                    "联系方式": org['contact_email']
                })
            else:
                self.print_result({
                    "状态": "❌ 教育机构创建失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
    
    def demo_user_creation(self):
        """演示用户创建（教师和学生）"""
        self.print_header("用户账户创建")
        
        if not self.organizations:
            print("⚠️  请先创建教育机构")
            return
        
        org_id = list(self.organizations.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        # 创建教师用户
        teacher_users = [
            {
                "username": "zhanglaoshi",
                "email": "zhang@bj1school.edu.cn",
                "password": "Teacher123!",
                "role": "user"
            },
            {
                "username": "wanglaoshi",
                "email": "wang@bj1school.edu.cn",
                "password": "Teacher123!",
                "role": "user"
            }
        ]
        
        self.print_step("创建教师账户")
        for i, user_data in enumerate(teacher_users, 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data
                )
                
                if response.status_code == 200:
                    user = response.json()
                    self.users[f"teacher_{i}"] = user
                    self.print_result({
                        "状态": "✅ 教师账户创建成功",
                        "用户名": user['username'],
                        "邮箱": user['email']
                    })
                else:
                    self.print_result({
                        "状态": "❌ 教师账户创建失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
        
        # 创建学生用户
        student_users = [
            {
                "username": "xiaoming",
                "email": "xiaoming@student.bj1school.edu.cn",
                "password": "Student123!",
                "role": "user"
            },
            {
                "username": "xiaohong",
                "email": "xiaohong@student.bj1school.edu.cn",
                "password": "Student123!",
                "role": "user"
            }
        ]
        
        self.print_step("创建学生账户")
        for i, user_data in enumerate(student_users, 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data
                )
                
                if response.status_code == 200:
                    user = response.json()
                    self.users[f"student_{i}"] = user
                    self.print_result({
                        "状态": "✅ 学生账户创建成功",
                        "用户名": user['username'],
                        "邮箱": user['email']
                    })
                else:
                    self.print_result({
                        "状态": "❌ 学生账户创建失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
    
    def demo_teacher_management(self):
        """演示教师管理功能"""
        self.print_header("教师档案管理")
        
        if not self.organizations or len(self.users) < 2:
            print("⚠️  请先创建教育机构和用户")
            return
        
        org_id = list(self.organizations.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        # 创建教师档案
        teachers_data = [
            {
                "user_id": self.users["teacher_1"]["id"],
                "employee_id": "T001",
                "department": "数学教研组",
                "position": "高级教师",
                "hire_date": "2020-09-01",
                "specialization": "数学教育",
                "teaching_subjects": ["数学", "高等数学"],
                "max_classes": 6
            },
            {
                "user_id": self.users["teacher_2"]["id"],
                "employee_id": "T002",
                "department": "英语教研组",
                "position": "一级教师",
                "hire_date": "2021-03-15",
                "specialization": "英语语言文学",
                "teaching_subjects": ["英语", "商务英语"],
                "max_classes": 5
            }
        ]
        
        self.print_step("创建教师档案")
        for i, teacher_data in enumerate(teachers_data, 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/org/{org_id}/teachers",
                    json=teacher_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    teacher = response.json()
                    self.teachers[teacher['id']] = teacher
                    self.print_result({
                        "状态": "✅ 教师档案创建成功",
                        "工号": teacher['employee_id'],
                        "姓名": self.users[f"teacher_{i}"]['username'],
                        "部门": teacher['department'],
                        "专业": teacher['specialization']
                    })
                else:
                    self.print_result({
                        "状态": "❌ 教师档案创建失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
    
    def demo_student_management(self):
        """演示学生管理功能"""
        self.print_header("学生档案管理")
        
        if not self.organizations or len(self.users) < 4:
            print("⚠️  请先创建足够的用户")
            return
        
        org_id = list(self.organizations.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        # 创建学生档案
        students_data = [
            {
                "user_id": self.users["student_1"]["id"],
                "student_id": "S2024001",
                "grade": "高一",
                "class_name": "1班",
                "enrollment_date": "2024-09-01",
                "major": "理科",
                "parent_name": "张父",
                "parent_phone": "13800138001"
            },
            {
                "user_id": self.users["student_2"]["id"],
                "student_id": "S2024002",
                "grade": "高一",
                "class_name": "1班",
                "enrollment_date": "2024-09-01",
                "major": "文科",
                "parent_name": "王母",
                "parent_phone": "13800138002"
            }
        ]
        
        self.print_step("创建学生档案")
        for i, student_data in enumerate(students_data, 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/org/{org_id}/students",
                    json=student_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    student = response.json()
                    self.students[student['id']] = student
                    self.print_result({
                        "状态": "✅ 学生档案创建成功",
                        "学号": student['student_id'],
                        "姓名": self.users[f"student_{i}"]['username'],
                        "年级": student['grade'],
                        "班级": student['class_name']
                    })
                else:
                    self.print_result({
                        "状态": "❌ 学生档案创建失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
    
    def demo_classroom_management(self):
        """演示教室管理功能"""
        self.print_header("教室资源管理")
        
        if not self.organizations:
            print("⚠️  请先创建教育机构")
            return
        
        org_id = list(self.organizations.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        # 创建教室
        classrooms_data = [
            {
                "room_number": "A101",
                "building": "教学楼A",
                "floor": 1,
                "capacity": 40,
                "room_type": "普通教室",
                "has_projector": True,
                "has_computer": False,
                "has_audio_system": True,
                "has_whiteboard": True
            },
            {
                "room_number": "B205",
                "building": "实验楼B",
                "floor": 2,
                "capacity": 30,
                "room_type": "多媒体教室",
                "has_projector": True,
                "has_computer": True,
                "has_audio_system": True,
                "has_whiteboard": True
            }
        ]
        
        self.print_step("创建教室资源")
        for classroom_data in classrooms_data:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/org/{org_id}/classrooms",
                    json=classroom_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    classroom = response.json()
                    self.classrooms[classroom['id']] = classroom
                    self.print_result({
                        "状态": "✅ 教室创建成功",
                        "教室编号": classroom['room_number'],
                        "所在楼宇": classroom['building'],
                        "容量": classroom['capacity'],
                        "类型": classroom['room_type']
                    })
                else:
                    self.print_result({
                        "状态": "❌ 教室创建失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
    
    def demo_course_scheduling(self):
        """演示课程安排功能"""
        self.print_header("课程时间安排")
        
        if not self.organizations or not self.courses or not self.classrooms:
            print("⚠️  请先创建教育机构、课程和教室")
            return
        
        org_id = list(self.organizations.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        # 安排课程时间
        schedules_data = [
            {
                "classroom_id": list(self.classrooms.keys())[0],
                "course_id": list(self.courses.keys())[0],
                "teacher_id": list(self.teachers.keys())[0],
                "day_of_week": 1,  # 周一
                "start_time": "2024-03-04T08:00:00",
                "end_time": "2024-03-04T09:30:00",
                "recurrence_pattern": "weekly"
            }
        ]
        
        self.print_step("安排课程时间")
        for schedule_data in schedules_data:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/org/{org_id}/schedules",
                    json=schedule_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    schedule = response.json()
                    self.print_result({
                        "状态": "✅ 课程安排成功",
                        "教室": f"{self.classrooms[schedule_data['classroom_id']]['building']} {self.classrooms[schedule_data['classroom_id']]['room_number']}",
                        "课程": "待关联",
                        "教师": "待关联",
                        "时间": f"周{schedule['day_of_week']} {schedule['start_time'][:5]}-{schedule['end_time'][:5]}"
                    })
                else:
                    self.print_result({
                        "状态": "❌ 课程安排失败",
                        "错误": response.text
                    })
                    
            except Exception as e:
                self.print_result({
                    "状态": "❌ 请求异常",
                    "错误": str(e)
                })
    
    def demo_institution_overview(self):
        """演示机构概览功能"""
        self.print_header("教育机构综合概览")
        
        if not self.organizations:
            print("⚠️  请先创建教育机构")
            return
        
        org_id = list(self.organizations.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        self.print_step("获取机构综合信息")
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org_id}/overview",
                headers=headers
            )
            
            if response.status_code == 200:
                overview = response.json()
                self.print_result({
                    "状态": "✅ 获取概览成功",
                    "人员统计": overview.get('personnel', {}),
                    "资源统计": overview.get('resources', {}),
                    "教学统计": overview.get('academics', {})
                })
            else:
                self.print_result({
                    "状态": "❌ 获取概览失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
    
    def demo_teacher_schedule(self):
        """演示教师课表查询"""
        self.print_header("教师课表查询")
        
        if not self.organizations or not self.teachers:
            print("⚠️  请先创建教育机构和教师")
            return
        
        org_id = list(self.organizations.keys())[0]
        teacher_id = list(self.teachers.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        self.print_step("查询教师个人课表")
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org_id}/teachers/schedule/{teacher_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                schedule_data = response.json()
                self.print_result({
                    "状态": "✅ 课表查询成功",
                    "教师": self.teachers[teacher_id]['employee_id'],
                    "课程安排": schedule_data.get('schedule', [])
                })
            else:
                self.print_result({
                    "状态": "❌ 课表查询失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })
    
    def demo_student_schedule(self):
        """演示学生课表查询"""
        self.print_header("学生课表查询")
        
        if not self.organizations or not self.students:
            print("⚠️  请先创建教育机构和学生")
            return
        
        org_id = list(self.organizations.keys())[0]
        student_id = list(self.students.keys())[0]
        headers = {"X-Org-ID": str(org_id)}
        
        self.print_step("查询学生个人课表")
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/org/{org_id}/students/schedule/{student_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                schedule_data = response.json()
                self.print_result({
                    "状态": "✅ 课表查询成功",
                    "学生": self.students[student_id]['student_id'],
                    "课程安排": schedule_data.get('schedule', [])
                })
            else:
                self.print_result({
                    "状态": "❌ 课表查询失败",
                    "错误": response.text
                })
                
        except Exception as e:
            self.print_result({
                "状态": "❌ 请求异常",
                "错误": str(e)
            })

def main():
    """主函数"""
    print("🏫 教育机构完整功能演示")
    print("="*70)
    print("本演示将展示教育机构的核心管理功能:")
    print("• 教师档案管理")
    print("• 学生信息管理") 
    print("• 教室资源配置")
    print("• 课程时间安排")
    print("• 课表查询系统")
    print("• 综合统计分析")
    print("="*70)
    
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
    demo = EducationalInstitutionDemo()
    
    try:
        demo.demo_organization_setup()
        demo.demo_user_creation()
        demo.demo_teacher_management()
        demo.demo_student_management()
        demo.demo_classroom_management()
        demo.demo_course_scheduling()
        demo.demo_institution_overview()
        demo.demo_teacher_schedule()
        demo.demo_student_schedule()
        
        print("\n" + "="*70)
        print("🎉 教育机构功能演示完成!")
        print("="*70)
        print("总结:")
        print(f"• 创建了 {len(demo.organizations)} 个教育机构")
        print(f"• 管理了 {len(demo.teachers)} 名教师")
        print(f"• 管理了 {len(demo.students)} 名学生")
        print(f"• 配置了 {len(demo.classrooms)} 间教室")
        print("\n现在您可以:")
        print("• 访问教师管理API进行师资管理")
        print("• 使用学生信息系统管理学籍")
        print("• 通过教室管理系统调配教学资源")
        print("• 利用排课系统优化课程安排")
        
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")

if __name__ == "__main__":
    main()