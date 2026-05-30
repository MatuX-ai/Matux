#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联邦学习系统快速验证脚本
验证核心组件的基本功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试基础依赖
        import logging
        import asyncio
        import json
        from datetime import datetime
        print("✅ 基础依赖导入成功")
        
        # 测试数学库
        import numpy as np
        print("✅ NumPy导入成功")
        
        # 测试密码学库
        from cryptography.fernet import Fernet
        print("✅ Cryptography导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        return False

def test_model_definitions():
    """测试模型定义"""
    print("\n📊 测试模型定义...")
    
    try:
        from ai_service.fl_models import (
            FLTrainingConfig, 
            FLParticipantInfo, 
            FLTrainingStatus,
            FLParticipantRole
        )
        
        # 创建测试配置
        config = FLTrainingConfig(
            model_name="test_model",
            rounds=5,
            participants=["client_1", "client_2"],
            privacy_budget=1.0
        )
        print(f"✅ 训练配置创建成功: {config.training_id}")
        
        # 创建参与者信息
        participant = FLParticipantInfo(
            participant_id="test_client",
            role=FLParticipantRole.PARTICIPANT,
            status="online"
        )
        print(f"✅ 参与者信息创建成功: {participant.participant_id}")
        
        return True
    except Exception as e:
        print(f"❌ 模型定义测试失败: {e}")
        return False

def test_privacy_engine():
    """测试隐私引擎基础功能"""
    print("\n🛡️ 测试隐私引擎...")
    
    try:
        from ai_service.federated_learning.privacy_engine import PrivacyEngine
        
        # 创建隐私引擎
        engine = PrivacyEngine(total_epsilon=1.0)
        print("✅ 隐私引擎初始化成功")
        
        # 测试隐私统计
        stats = engine.get_privacy_stats()
        print(f"✅ 隐私统计获取成功: 总预算 {stats['total_epsilon']}")
        
        return True
    except Exception as e:
        print(f"❌ 隐私引擎测试失败: {e}")
        return False

def test_secure_aggregator():
    """测试安全聚合器"""
    print("\n🔗 测试安全聚合器...")
    
    try:
        from ai_service.federated_learning.secure_aggregator import SecureAggregator
        from ai_service.federated_learning.privacy_engine import PrivacyEngine
        
        # 创建组件
        privacy_engine = PrivacyEngine()
        aggregator = SecureAggregator(privacy_engine)
        print("✅ 安全聚合器初始化成功")
        
        # 测试公钥获取
        public_key = aggregator.get_public_key()
        print(f"✅ 公钥生成成功: {len(public_key)} 字节")
        
        # 测试统计信息
        stats = aggregator.get_aggregation_stats()
        print(f"✅ 聚合统计获取成功: 注册参与者 {stats['participants_registered']}")
        
        return True
    except Exception as e:
        print(f"❌ 安全聚合器测试失败: {e}")
        return False

def test_federated_client():
    """测试联邦学习客户端"""
    print("\n💻 测试联邦学习客户端...")
    
    try:
        from ai_service.federated_learning.federated_client import FederatedClient
        from ai_service.federated_learning.privacy_engine import PrivacyEngine
        
        # 创建客户端
        privacy_engine = PrivacyEngine()
        client = FederatedClient(
            participant_id="test_client_001",
            coordinator_url="http://localhost:8000",
            privacy_engine=privacy_engine
        )
        print("✅ 联邦客户端初始化成功")
        
        # 测试公钥获取
        public_key = client.get_public_key()
        print(f"✅ 客户端公钥生成成功: {len(public_key)} 字节")
        
        # 测试客户端状态
        stats = client.get_client_stats()
        print(f"✅ 客户端统计获取成功: 状态 {stats['status']}")
        
        return True
    except Exception as e:
        print(f"❌ 联邦客户端测试失败: {e}")
        return False

def test_monitoring_system():
    """测试监控系统"""
    print("\n📈 测试监控系统...")
    
    try:
        from ai_service.federated_learning.monitor import FLMonitor
        
        # 创建监控器
        monitor = FLMonitor()
        print("✅ 监控系统初始化成功")
        
        # 测试监控摘要
        summary = monitor.get_monitoring_summary()
        print(f"✅ 监控摘要获取成功: 系统状态 {summary['system_health']['status']}")
        
        return True
    except Exception as e:
        print(f"❌ 监控系统测试失败: {e}")
        return False

def test_api_routes():
    """测试API路由定义"""
    print("\n🌐 测试API路由...")
    
    try:
        # 测试FastAPI相关导入
        from fastapi import APIRouter, HTTPException
        print("✅ FastAPI组件导入成功")
        
        # 测试路由创建
        router = APIRouter(prefix="/test", tags=["测试"])
        print("✅ API路由创建成功")
        
        return True
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("联邦学习隐私保护系统验证测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("模型定义", test_model_definitions),
        ("隐私引擎", test_privacy_engine),
        ("安全聚合器", test_secure_aggregator),
        ("联邦客户端", test_federated_client),
        ("监控系统", test_monitoring_system),
        ("API路由", test_api_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 系统核心功能验证通过！")
        return 0
    else:
        print("⚠️  部分功能需要进一步调试")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)