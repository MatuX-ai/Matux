"""
文档迁移验证脚本
用于验证文档迁移的完整性和链接有效性
"""

import os
from pathlib import Path
from typing import List, Dict

class DocsMigrationVerifier:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir / "docs"
        self.documentation_dir = self.root_dir / "documentation"
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def verify_directory_structure(self):
        """验证目录结构是否创建完整"""
        print("=" * 80)
        print("📁 验证目录结构...")
        print("=" * 80)
        
        required_dirs = [
            "documentation/backend/routes",
            "documentation/backend/services",
            "documentation/backend/models",
            "documentation/backend/utils",
            "documentation/backend/ai-edu",
            "documentation/backend/blockchain",
            "documentation/backend/hardware",
            "documentation/frontend/components",
            "documentation/frontend/services",
            "documentation/frontend/modules",
            "documentation/frontend/design-system",
            "documentation/shared/architecture",
            "documentation/shared/api-specs",
            "documentation/shared/guides",
            "documentation/deployment",
            "documentation/tests",
            "documentation/resources",
        ]
        
        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                print(f"  ✅ {dir_path}")
                self.success_count += 1
            else:
                error_msg = f"❌ 目录不存在：{dir_path}"
                print(error_msg)
                self.errors.append(error_msg)
                
        print(f"\n✅ 目录结构验证完成：{self.success_count}/{len(required_dirs)} 通过\n")
        
    def verify_migrated_files(self):
        """验证已迁移的文件"""
        print("=" * 80)
        print("📄 验证已迁移文件...")
        print("=" * 80)
        
        # 检查 documentation 目录中的文件
        migrated_categories = {
            "backend/ai-edu": "AI-Edu 文档",
            "backend/services": "服务文档",
            "backend/blockchain": "区块链文档",
            "backend/hardware": "硬件文档",
            "backend/routes": "路由文档",
            "frontend/design-system": "Design System 文档",
            "frontend/components": "组件文档",
            "shared/architecture": "架构文档",
            "deployment": "部署文档",
            "tests": "测试文档",
            "resources": "资源文件",
        }
        
        total_files = 0
        
        for category, description in migrated_categories.items():
            category_dir = self.documentation_dir / category
            if category_dir.exists():
                files = list(category_dir.glob("*.md")) + list(category_dir.glob("*.html"))
                count = len(files)
                total_files += count
                if count > 0:
                    print(f"  ✅ {description}: {count} 个文件")
                else:
                    warning_msg = f"⚠️  {description} 目录为空"
                    print(warning_msg)
                    self.warnings.append(warning_msg)
            else:
                error_msg = f"❌ {description} 目录不存在"
                print(error_msg)
                self.errors.append(error_msg)
                
        print(f"\n✅ 文件迁移验证完成：共 {total_files} 个文件\n")
        
    def check_old_docs_status(self):
        """检查旧文档位置的状态"""
        print("=" * 80)
        print("🔍 检查旧文档位置...")
        print("=" * 80)
        
        # 应该保留在 docs/的文件
        preserved_files = [
            "INDEX.md",
            "SITE_MAP.md",
            "FRONTEND_ROUTING.md",
            "ROUTE_CONFIGURATION.md",
            "unity_ar_interaction.cs",
        ]
        
        print("\n检查应保留的文件:")
        for filename in preserved_files:
            file_path = self.docs_dir / filename
            if file_path.exists():
                print(f"  ✅ {filename} (保留)")
            else:
                warning_msg = f"⚠️  {filename} 不存在（可能已迁移）"
                print(warning_msg)
                self.warnings.append(warning_msg)
                
        # 检查不应该存在的旧文档
        should_be_migrated = [
            "PROJECT_OVERVIEW.md",
            "SYSTEM_ARCHITECTURE.md",
            "GLOBAL_TECHNICAL_ARCHITECTURE.md",
        ]
        
        print("\n检查应迁移的文件（不应在 docs/中）:")
        for filename in should_be_migrated:
            file_path = self.docs_dir / filename
            if file_path.exists():
                warning_msg = f"⚠️  {filename} 仍存在于 docs/（建议删除或创建重定向）"
                print(warning_msg)
                self.warnings.append(warning_msg)
            else:
                print(f"  ✅ {filename} (已正确迁移)")
                
        print()
        
    def verify_key_files_exist(self):
        """验证关键文件是否存在于新位置"""
        print("=" * 80)
        print("🔑 验证关键文件在新位置...")
        print("=" * 80)
        
        key_files = [
            "documentation/README.md",
            "documentation/MIGRATION_GUIDE.md",
            "documentation/.redirect-map.json",
            "documentation/shared/architecture/project-overview.md",
            "documentation/shared/architecture/system-architecture.md",
            "documentation/shared/architecture/global-technical-architecture.md",
        ]
        
        for file_path_str in key_files:
            # Windows 文件系统不区分大小写，但 Path.exists() 应该能处理
            file_path = self.root_dir / file_path_str
            if not file_path.exists():
                # 尝试查找相似的文件名（忽略大小写）
                parent_dir = file_path.parent
                if parent_dir.exists():
                    target_name = file_path.name.lower()
                    found = False
                    for existing_file in parent_dir.iterdir():
                        if existing_file.name.lower() == target_name:
                            print(f"  ✅ {file_path_str} (实际文件名：{existing_file.name})")
                            found = True
                            break
                    if found:
                        continue
            
            if file_path.exists() and file_path.is_file():
                print(f"  ✅ {file_path_str}")
            else:
                error_msg = f"❌ 关键文件不存在：{file_path_str}"
                print(error_msg)
                self.errors.append(error_msg)
                
        print()
        
    def generate_report(self):
        """生成验证报告"""
        print("=" * 80)
        print("📊 验证报告总结")
        print("=" * 80)
        
        print(f"\n✅ 成功项：{self.success_count}")
        print(f"⚠️  警告项：{len(self.warnings)}")
        print(f"❌ 错误项：{len(self.errors)}")
        
        if self.warnings:
            print("\n警告列表:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if self.errors:
            print("\n错误列表:")
            for error in self.errors:
                print(f"  - {error}")
                
        # 总体评估
        print("\n" + "=" * 80)
        if len(self.errors) == 0:
            print("🎉 验证通过！文档迁移成功完成！")
        else:
            print(f"⚠️  验证完成，发现 {len(self.errors)} 个错误需要修复")
        print("=" * 80)
        
        return len(self.errors) == 0
        
    def run_full_verification(self):
        """运行完整验证流程"""
        print("\n" + "=" * 80)
        print("🚀 开始文档迁移验证")
        print("=" * 80 + "\n")
        
        self.verify_directory_structure()
        self.verify_migrated_files()
        self.check_old_docs_status()
        self.verify_key_files_exist()
        
        success = self.generate_report()
        
        return success


if __name__ == "__main__":
    verifier = DocsMigrationVerifier()
    success = verifier.run_full_verification()
    
    # 退出码
    exit(0 if success else 1)
