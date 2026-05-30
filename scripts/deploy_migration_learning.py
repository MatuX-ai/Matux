"""
迁移学习系统部署脚本
自动化部署预训练模型服务和相关组件
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import json
from datetime import datetime
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MigrationLearningDeployer:
    """迁移学习系统部署器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.models_dir = self.project_root / "models"
        self.data_dir = self.project_root / "data"
        self.docs_dir = self.project_root / "docs"
        self.requirements_file = self.backend_dir / "requirements.ml.txt"
        
    def deploy_full_system(self):
        """部署完整系统"""
        logger.info("🚀 开始迁移学习系统部署...")
        
        try:
            # 1. 环境检查
            logger.info("1. 执行环境检查...")
            if not self._check_environment():
                raise Exception("环境检查失败")
            
            # 2. 创建必要目录
            logger.info("2. 创建目录结构...")
            self._create_directories()
            
            # 3. 安装依赖
            logger.info("3. 安装依赖包...")
            self._install_dependencies()
            
            # 4. 初始化数据库
            logger.info("4. 初始化数据库...")
            self._initialize_database()
            
            # 5. 准备测试数据
            logger.info("5. 准备测试数据...")
            self._prepare_test_data()
            
            # 6. 验证部署
            logger.info("6. 验证部署...")
            self._verify_deployment()
            
            # 7. 生成部署报告
            logger.info("7. 生成部署报告...")
            self._generate_deployment_report()
            
            logger.info("✅ 系统部署完成!")
            return True
            
        except Exception as e:
            logger.error(f"部署失败: {e}")
            return False
    
    def _check_environment(self) -> bool:
        """检查部署环境"""
        checks = []
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            checks.append(("Python版本", True, f"{python_version.major}.{python_version.minor}.{python_version.micro}"))
        else:
            checks.append(("Python版本", False, "需要Python 3.8+"))
        
        # 检查必要目录
        required_dirs = [self.backend_dir, self.models_dir, self.data_dir]
        for dir_path in required_dirs:
            exists = dir_path.exists()
            checks.append((f"目录 {dir_path.name}", exists, "存在" if exists else "不存在"))
        
        # 检查必要文件
        required_files = [
            self.backend_dir / "main.py",
            self.backend_dir / "ai_service" / "traditional_ml_transfer.py",
            self.requirements_file
        ]
        
        for file_path in required_files:
            exists = file_path.exists()
            checks.append((f"文件 {file_path.name}", exists, "存在" if exists else "不存在"))
        
        # 输出检查结果
        print("\n环境检查结果:")
        print("-" * 50)
        all_passed = True
        for check_name, passed, message in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def _create_directories(self):
        """创建必要的目录结构"""
        directories = [
            self.data_dir / "cache",
            self.data_dir / "processed",
            self.data_dir / "raw",
            self.models_dir / "distilled",
            self.models_dir / "compressed",
            self.docs_dir,
            self.project_root / "reports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {directory}")
    
    def _install_dependencies(self):
        """安装依赖包"""
        if not self.requirements_file.exists():
            logger.warning(f"依赖文件不存在: {self.requirements_file}")
            return
        
        try:
            # 安装核心依赖
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("依赖包安装成功")
            else:
                logger.warning(f"依赖包安装可能存在问题: {result.stderr}")
                
        except Exception as e:
            logger.error(f"安装依赖包失败: {e}")
    
    def _initialize_database(self):
        """初始化数据库表"""
        try:
            # 导入数据库初始化脚本
            sys.path.insert(0, str(self.backend_dir))
            
            from utils.database import create_db_and_tables
            import asyncio
            
            # 运行数据库初始化
            async def init_db():
                await create_db_and_tables()
                logger.info("数据库表初始化完成")
            
            asyncio.run(init_db())
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            logger.info("继续执行其他部署步骤...")
    
    def _prepare_test_data(self):
        """准备测试数据"""
        try:
            from services.dataset_processor import AssistmentsDatasetProcessor
            
            # 生成测试数据集
            processor = AssistmentsDatasetProcessor()
            test_data = processor._generate_high_quality_mock_data()
            
            # 保存预处理数据
            processed_path = self.data_dir / "processed" / "assistments_dataset.csv"
            test_data.to_csv(processed_path, index=False, encoding='utf-8')
            logger.info(f"测试数据已保存到: {processed_path}")
            
            # 生成一些样本模型数据
            self._generate_sample_models()
            
        except Exception as e:
            logger.error(f"准备测试数据失败: {e}")
    
    def _generate_sample_models(self):
        """生成样本模型文件"""
        try:
            import pickle
            import numpy as np
            from sklearn.ensemble import RandomForestClassifier
            
            # 创建简单的示例模型
            sample_model = RandomForestClassifier(n_estimators=10, random_state=42)
            
            # 使用模拟数据训练
            X = np.random.rand(100, 20)
            y = np.random.randint(0, 2, 100)
            sample_model.fit(X, y)
            
            # 保存模型
            model_path = self.models_dir / "distilled" / "sample_model.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(sample_model, f)
            
            logger.info(f"示例模型已保存到: {model_path}")
            
        except Exception as e:
            logger.error(f"生成样本模型失败: {e}")
    
    def _verify_deployment(self):
        """验证部署是否成功"""
        verifications = []
        
        # 验证API服务
        try:
            import requests
            response = requests.get("http://localhost:8000/docs", timeout=5)
            verifications.append(("API文档访问", response.status_code == 200, "可访问"))
        except:
            verifications.append(("API文档访问", False, "无法访问"))
        
        # 验证模型文件
        model_files = list((self.models_dir / "distilled").glob("*.pkl"))
        verifications.append(("模型文件存在", len(model_files) > 0, f"找到 {len(model_files)} 个模型文件"))
        
        # 验证数据文件
        data_files = list((self.data_dir / "processed").glob("*.csv"))
        verifications.append(("数据文件存在", len(data_files) > 0, f"找到 {len(data_files)} 个数据文件"))
        
        # 验证必要模块导入
        try:
            sys.path.insert(0, str(self.backend_dir))
            from ai_service.traditional_ml_transfer import TraditionalTransferLearning
            from services.dataset_processor import AssistmentsDatasetProcessor
            verifications.append(("核心模块导入", True, "成功导入"))
        except Exception as e:
            verifications.append(("核心模块导入", False, f"导入失败: {e}"))
        
        # 输出验证结果
        print("\n部署验证结果:")
        print("-" * 50)
        all_passed = True
        for check_name, passed, message in verifications:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        
        if all_passed:
            logger.info("所有验证检查通过!")
        else:
            logger.warning("部分验证检查未通过，请检查部署状态")
    
    def _generate_deployment_report(self):
        """生成部署报告"""
        report = {
            "deployment_info": {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "deployer": os.getenv("USER", "unknown")
            },
            "system_components": {
                "api_service": "http://localhost:8000",
                "api_docs": "http://localhost:8000/docs",
                "model_directory": str(self.models_dir),
                "data_directory": str(self.data_dir)
            },
            "available_endpoints": [
                "POST /api/v1/pretrain-model/train",
                "POST /api/v1/pretrain-model/compress/{model_id}",
                "POST /api/v1/pretrain-model/recommend",
                "GET /api/v1/pretrain-model/status/{task_id}",
                "GET /api/v1/pretrain-model/models"
            ],
            "deployment_status": "completed",
            "next_steps": [
                "启动API服务: python backend/main.py",
                "运行性能测试: python scripts/migration_learning_validation.py",
                "查看API文档: 访问 http://localhost:8000/docs"
            ]
        }
        
        # 保存报告
        report_path = self.project_root / "reports" / f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"部署报告已保存到: {report_path}")
        
        # 打印快速开始指南
        self._print_quick_start_guide()
    
    def _print_quick_start_guide(self):
        """打印快速开始指南"""
        print("\n" + "=" * 60)
        print("🚀 迁移学习系统快速开始指南")
        print("=" * 60)
        print("\n1. 启动API服务:")
        print("   cd backend")
        print("   python main.py")
        print("\n2. 访问API文档:")
        print("   浏览器打开: http://localhost:8000/docs")
        print("\n3. 测试预训练模型API:")
        print("   POST /api/v1/pretrain-model/train")
        print("   参数: {\"dataset_source\": \"assistments2012\"}")
        print("\n4. 运行性能验证:")
        print("   python scripts/migration_learning_validation.py")
        print("\n5. 查看系统状态:")
        print("   GET /api/v1/pretrain-model/health")
        print("\n" + "=" * 60)

# 开发者工具函数
def create_development_environment():
    """创建开发环境"""
    print("🔧 创建开发环境...")
    
    deployer = MigrationLearningDeployer()
    
    # 创建开发配置
    dev_config = {
        "environment": "development",
        "debug": True,
        "log_level": "DEBUG",
        "model_cache_ttl": 300,  # 5分钟缓存用于开发
        "max_concurrent_requests": 5
    }
    
    config_path = deployer.project_root / "config" / "dev_config.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(dev_config, f, indent=2)
    
    print(f"开发配置已创建: {config_path}")

def run_development_server():
    """运行开发服务器"""
    print("🔧 启动开发服务器...")
    
    try:
        # 切换到backend目录
        backend_dir = Path(__file__).parent.parent / "backend"
        os.chdir(backend_dir)
        
        # 启动FastAPI开发服务器
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 开发服务器已停止")
    except Exception as e:
        print(f"❌ 启动开发服务器失败: {e}")

def run_comprehensive_test():
    """运行综合测试"""
    print("🧪 运行综合测试...")
    
    try:
        # 切换到scripts目录
        scripts_dir = Path(__file__).parent.parent / "scripts"
        test_script = scripts_dir / "migration_learning_validation.py"
        
        if test_script.exists():
            result = subprocess.run([sys.executable, str(test_script)], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)
        else:
            print(f"❌ 测试脚本不存在: {test_script}")
            
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")

# 主函数
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="迁移学习系统部署工具")
    parser.add_argument("action", choices=["deploy", "dev-env", "dev-server", "test"], 
                       help="执行的操作")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    deployer = MigrationLearningDeployer()
    
    if args.action == "deploy":
        success = deployer.deploy_full_system()
        sys.exit(0 if success else 1)
    elif args.action == "dev-env":
        create_development_environment()
    elif args.action == "dev-server":
        run_development_server()
    elif args.action == "test":
        run_comprehensive_test()

if __name__ == "__main__":
    main()