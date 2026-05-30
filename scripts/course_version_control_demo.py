"""
课程版本控制系统演示脚本
展示Git-like版本控制功能的实际使用场景
"""

import json
import time
from datetime import datetime
from typing import Dict, Any

class CourseVersionControlDemo:
    """课程版本控制演示类"""
    
    def __init__(self):
        self.course_data = {
            "title": "Python编程入门",
            "description": "面向初学者的Python编程课程",
            "version": "1.0.0",
            "chapters": [
                {
                    "id": 1,
                    "title": "Python基础语法",
                    "lessons": [
                        {"id": 1, "title": "变量和数据类型"},
                        {"id": 2, "title": "运算符和表达式"}
                    ]
                }
            ],
            "metadata": {
                "created_by": "teacher@example.com",
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
        }
        
        self.versions = []  # 存储版本历史
        self.branches = {"main": {"head": None}}  # 分支管理
        self.current_branch = "main"
        self.version_counter = 0
    
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f"{title:^60}")
        print(f"{'='*60}")
    
    def print_step(self, step: int, description: str):
        """打印步骤"""
        print(f"\n[{step}] {description}")
        print("-" * 40)
    
    def commit(self, message: str, branch: str = None) -> Dict[str, Any]:
        """模拟提交操作"""
        if branch is None:
            branch = self.current_branch
            
        self.version_counter += 1
        timestamp = int(time.time())
        
        # 创建版本快照
        snapshot = {
            "version": self.version_counter,
            "changes": [],  # 简化处理
            "author": "teacher@example.com",
            "timestamp": timestamp,
            "message": message,
            "branch": branch,
            "course_data": self.course_data.copy()
        }
        
        # 更新分支HEAD
        self.branches[branch] = {"head": snapshot}
        
        # 添加到版本历史
        self.versions.append(snapshot)
        
        print(f"✅ 提交成功!")
        print(f"   版本: v{self.version_counter}")
        print(f"   分支: {branch}")
        print(f"   消息: {message}")
        print(f"   时间: {datetime.fromtimestamp(timestamp)}")
        
        return snapshot
    
    def create_branch(self, name: str, from_branch: str = "main") -> bool:
        """创建新分支"""
        if name in self.branches:
            print(f"❌ 分支 '{name}' 已存在!")
            return False
        
        # 基于源分支创建新分支
        if from_branch in self.branches and self.branches[from_branch]["head"]:
            self.branches[name] = {"head": self.branches[from_branch]["head"].copy()}
            print(f"✅ 分支 '{name}' 创建成功，基于 '{from_branch}'")
            return True
        else:
            print(f"❌ 源分支 '{from_branch}' 不存在或为空!")
            return False
    
    def switch_branch(self, name: str) -> bool:
        """切换分支"""
        if name not in self.branches:
            print(f"❌ 分支 '{name}' 不存在!")
            return False
        
        self.current_branch = name
        print(f"✅ 切换到分支 '{name}'")
        return True
    
    def show_status(self):
        """显示当前状态"""
        print(f"\n📋 当前状态:")
        print(f"   当前分支: {self.current_branch}")
        print(f"   最新版本: v{self.version_counter}")
        print(f"   总版本数: {len(self.versions)}")
        print(f"   分支数量: {len(self.branches)}")
        
        print(f"\n🌳 分支列表:")
        for branch_name, branch_info in self.branches.items():
            head_version = branch_info["head"]["version"] if branch_info["head"] else "无"
            marker = " * " if branch_name == self.current_branch else "   "
            print(f"   {marker}{branch_name} (HEAD: v{head_version})")
    
    def show_history(self, branch: str = None, limit: int = 10):
        """显示版本历史"""
        if branch:
            history = [v for v in self.versions if v["branch"] == branch][-limit:]
        else:
            history = self.versions[-limit:]
        
        print(f"\n📜 版本历史 ({'全部分支' if not branch else branch}):")
        print("-" * 80)
        
        for version in reversed(history):
            timestamp = datetime.fromtimestamp(version["timestamp"])
            print(f"v{version['version']:2d} | {timestamp.strftime('%Y-%m-%d %H:%M')} | "
                  f"{version['branch']:10} | {version['message']}")
    
    def modify_course(self, modifications: Dict[str, Any]):
        """修改课程内容"""
        print(f"\n✏️  修改课程内容:")
        for key, value in modifications.items():
            old_value = self.course_data.get(key, "N/A")
            self.course_data[key] = value
            print(f"   {key}: {old_value} → {value}")
        
        # 更新最后修改时间
        self.course_data["metadata"]["last_modified"] = datetime.now().isoformat()
    
    def merge(self, source_branch: str, target_branch: str) -> bool:
        """模拟合并操作"""
        if source_branch not in self.branches or target_branch not in self.branches:
            print(f"❌ 分支不存在!")
            return False
        
        source_head = self.branches[source_branch]["head"]
        target_head = self.branches[target_branch]["head"]
        
        if not source_head:
            print(f"❌ 源分支 '{source_branch}' 为空!")
            return False
        
        if not target_head:
            # 目标分支为空，直接复制
            self.branches[target_branch]["head"] = source_head.copy()
            print(f"✅ 合并成功: '{source_branch}' → '{target_branch}' (快进合并)")
            return True
        
        # 检查是否有冲突（简化版）
        source_data = source_head["course_data"]
        target_data = target_head["course_data"]
        
        conflicts = []
        for key in set(source_data.keys()) | set(target_data.keys()):
            if (key in source_data and key in target_data and 
                source_data[key] != target_data[key]):
                conflicts.append(key)
        
        if conflicts:
            print(f"⚠️  发现冲突字段: {', '.join(conflicts)}")
            print("   自动解决冲突（保留源分支版本）...")
        
        # 执行合并
        merged_data = target_data.copy()
        merged_data.update(source_data)
        
        # 创建合并提交
        self.version_counter += 1
        merge_commit = {
            "version": self.version_counter,
            "changes": [{"type": "merge", "source": source_branch, "target": target_branch}],
            "author": "system",
            "timestamp": int(time.time()),
            "message": f"Merge branch '{source_branch}' into '{target_branch}'",
            "branch": target_branch,
            "course_data": merged_data
        }
        
        self.branches[target_branch]["head"] = merge_commit
        self.versions.append(merge_commit)
        
        print(f"✅ 合并成功!")
        print(f"   从 '{source_branch}' 合并到 '{target_branch}'")
        print(f"   创建合并提交: v{self.version_counter}")
        return True
    
    def revert(self, version_num: int) -> bool:
        """回滚到指定版本"""
        target_version = None
        for version in self.versions:
            if version["version"] == version_num:
                target_version = version
                break
        
        if not target_version:
            print(f"❌ 版本 v{version_num} 不存在!")
            return False
        
        # 创建回滚提交
        self.version_counter += 1
        revert_commit = {
            "version": self.version_counter,
            "changes": [{"type": "revert", "target_version": version_num}],
            "author": "teacher@example.com",
            "timestamp": int(time.time()),
            "message": f"Revert to version {version_num}",
            "branch": self.current_branch,
            "course_data": target_version["course_data"].copy()
        }
        
        self.branches[self.current_branch]["head"] = revert_commit
        self.versions.append(revert_commit)
        self.course_data = target_version["course_data"].copy()
        
        print(f"✅ 回滚成功!")
        print(f"   回滚到版本: v{version_num}")
        print(f"   创建回滚提交: v{self.version_counter}")
        return True
    
    def run_demo(self):
        """运行完整演示"""
        self.print_header("课程版本控制系统演示")
        
        # 步骤1: 初始化课程
        self.print_step(1, "初始化课程并创建第一个版本")
        self.commit("Initial commit: 创建基础课程结构")
        
        # 步骤2: 修改课程内容
        self.print_step(2, "修改课程内容 - 添加新章节")
        self.modify_course({
            "chapters": [
                {
                    "id": 1,
                    "title": "Python基础语法",
                    "lessons": [
                        {"id": 1, "title": "变量和数据类型"},
                        {"id": 2, "title": "运算符和表达式"},
                        {"id": 3, "title": "输入输出操作"}  # 新增
                    ]
                },
                {
                    "id": 2,  # 新增章节
                    "title": "控制结构",
                    "lessons": [
                        {"id": 4, "title": "条件语句"},
                        {"id": 5, "title": "循环语句"}
                    ]
                }
            ]
        })
        self.commit("Add control structures chapter")
        
        # 步骤3: 创建功能分支
        self.print_step(3, "创建功能分支进行实验性修改")
        self.create_branch("feature/advanced-topics")
        self.switch_branch("feature/advanced-topics")
        
        # 在功能分支上修改
        self.modify_course({
            "chapters": self.course_data["chapters"] + [
                {
                    "id": 3,
                    "title": "高级特性",
                    "lessons": [
                        {"id": 6, "title": "面向对象编程"},
                        {"id": 7, "title": "异常处理"}
                    ]
                }
            ]
        })
        self.commit("Add advanced topics chapter")
        
        # 步骤4: 切换回主分支继续开发
        self.print_step(4, "切换回主分支继续常规开发")
        self.switch_branch("main")
        self.modify_course({
            "description": "面向初学者的Python编程课程 - 基础版"
        })
        self.commit("Update course description")
        
        # 步骤5: 查看当前状态
        self.print_step(5, "查看当前状态和版本历史")
        self.show_status()
        self.show_history()
        
        # 步骤6: 创建合并请求
        self.print_step(6, "将功能分支合并到主分支")
        self.merge("feature/advanced-topics", "main")
        
        # 步骤7: 查看合并后的状态
        self.print_step(7, "查看合并后的状态")
        self.show_status()
        self.show_history(limit=5)
        
        # 步骤8: 演示回滚功能
        self.print_step(8, "演示版本回滚功能")
        print("回滚到版本2...")
        self.revert(2)
        self.show_history(limit=3)
        
        # 最终总结
        self.print_header("演示完成")
        print(f"🎉 课程版本控制系统演示完成!")
        print(f"\n主要功能展示:")
        print(f"  ✓ 版本提交和历史管理")
        print(f"  ✓ 分支创建和切换")
        print(f"  ✓ 分支合并")
        print(f"  ✓ 版本回滚")
        print(f"  ✓ 冲突检测和解决")
        print(f"\n总共创建了 {self.version_counter} 个版本")
        print(f"当前维护了 {len(self.branches)} 个分支")

def main():
    """主函数"""
    demo = CourseVersionControlDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()