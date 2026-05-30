#!/usr/bin/env python3
"""
核心配置文件备份脚本

目的：在代码清理前备份所有关键配置文件，确保可回滚
执行时间：2026-03-06
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


def create_backup_directory():
    """创建备份目录"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f'backup_configs_{timestamp}')
    backup_dir.mkdir(exist_ok=True)

    # 创建子目录结构（使用 parent.mkdir）
    (backup_dir / 'backend').mkdir(exist_ok=True)
    (backup_dir / 'backend' / 'config').mkdir(exist_ok=True)
    (backup_dir / 'src').mkdir(exist_ok=True)
    (backup_dir / 'src' / 'environments').mkdir(exist_ok=True)

    print(f"✅ 创建备份目录：{backup_dir}")
    return backup_dir


def backup_file(src: str, dest: Path, required: bool = True):
    """备份单个文件"""
    src_path = Path(src)
    if not src_path.exists():
        if required:
            print(f"⚠️  警告：文件不存在 - {src}")
        return False

    try:
        # 保持目录结构
        dest_path = dest / src_path.as_posix().replace('/', '_').replace('\\', '_')

        # 如果是嵌套路径，创建对应目录
        if '/' in src or '\\' in src:
            dest_path = dest / src_path.as_posix().replace('/', os.sep).replace('\\', os.sep)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

        # 复制文件
        shutil.copy2(src_path, dest_path)
        print(f"✅ 备份：{src} -> {dest_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败：{src} - {e}")
        return False


def backup_core_configs():
    """备份核心配置文件"""
    print("=" * 60)
    print("🔄 开始备份核心配置文件...")
    print("=" * 60)

    backup_dir = create_backup_directory()
    success_count = 0
    total_count = 0

    # A. 根目录配置
    root_configs = [
        'angular.json',
        'package.json',
        'pyproject.toml',
        'tsconfig.json',
        'tsconfig.app.json',
        'tsconfig.spec.json',
        '.editorconfig',
        '.prettierrc',
        '.prettierrc.json',
        '.eslintrc.js',
        '.stylelintrc.js',
        'sonar-project.properties',
        '.env.production.example',
        '.env.vircadia.example',
        '.env.vircadia',  # 真实配置
        'Dockerfile',
        'docker-compose.yml',
        'Jenkinsfile',
    ]

    print("\n📋 A. 根目录配置备份:")
    for config in root_configs:
        total_count += 1
        if backup_file(config, backup_dir):
            success_count += 1

    # B. Backend 核心配置
    backend_configs = [
        'backend/.env.example',
        'backend/.env.edu_data',
        'backend/.env.enterprise',
        'backend/.env.apm.example',
        'backend/pyproject.toml',
        'backend/pytest.ini',
        'backend/.flake8',
        'backend/alembic.ini',
        'backend/requirements.txt',
        'backend/requirements.txt.backup',
        'backend/requirements.ml.txt',
        'backend/requirements.apm.txt',
        'backend/requirements.enterprise.txt',
    ]

    print("\n📋 B. Backend 配置备份:")
    for config in backend_configs:
        total_count += 1
        if backup_file(config, backup_dir):
            success_count += 1

    # C. Backend Config 目录（核心中的核心）
    backend_config_files = [
        'backend/config/settings.py',
        'backend/config/enterprise_settings.py',
        'backend/config/edu_data_config.py',
        'backend/config/license_config.py',
        'backend/config/sponsorship_config.py',
        'backend/config/transfer_learning_config.py',
        'backend/config/voice_reward_templates.py',
    ]

    print("\n📋 C. Backend Config 目录备份:")
    for config in backend_config_files:
        total_count += 1
        if backup_file(config, backup_dir):
            success_count += 1

    # D. 前端核心配置
    frontend_configs = [
        'src/environments/environment.ts',
        'src/environments/environment.prod.ts',
    ]

    print("\n📋 D. 前端配置备份:")
    for config in frontend_configs:
        total_count += 1
        if backup_file(config, backup_dir):
            success_count += 1

    # E. Docker 和部署配置
    docker_configs = [
        'Dockerfile.3d-model-python',
        'docker-compose.override.yml',
        'docker-compose.vircadia.yml',
        'docker-compose.openhydra.yml',
        'docker-compose.3d-model.dev.yml',
    ]

    print("\n📋 E. Docker 配置备份:")
    for config in docker_configs:
        total_count += 1
        if backup_file(config, backup_dir):
            success_count += 1

    # F. 代码质量配置
    quality_configs = [
        'config/sonar-quality-config.json',
        '.gitignore',
        '.eslintignore',
        '.prettierignore',
    ]

    print("\n📋 F. 代码质量配置备份:")
    for config in quality_configs:
        total_count += 1
        if backup_file(config, backup_dir):
            success_count += 1

    # 生成备份清单
    manifest_file = backup_dir / 'BACKUP_MANIFEST.txt'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write(f"# 核心配置备份清单\n")
        f.write(f"备份时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"成功备份：{success_count}/{total_count} 文件\n")
        f.write(f"备份目录：{backup_dir}\n")
        f.write("\n## 文件列表\n")
        f.write(f"总计：{total_count} 个文件\n")
        f.write(f"成功：{success_count} 个文件\n")
        f.write(f"失败：{total_count - success_count} 个文件\n")

    print(f"\n{'=' * 60}")
    print(f"✅ 备份完成！")
    print(f"   成功：{success_count}/{total_count} 文件")
    print(f"   备份目录：{backup_dir.absolute()}")
    print(f"   清单文件：{manifest_file}")
    print(f"{'=' * 60}")

    return backup_dir, success_count, total_count


def create_git_tag(backup_dir: Path):
    """创建 Git 标签以便回滚"""
    import subprocess

    tag_name = f'cleanup-backup-{datetime.now().strftime("%Y%m%d")}'

    try:
        # 检查是否在 Git 仓库中
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # 创建标签
            subprocess.run(['git', 'tag', tag_name], check=True)
            print(f"\n✅ 创建 Git 标签：{tag_name}")

            # 记录标签信息到备份清单
            manifest_file = backup_dir / 'BACKUP_MANIFEST.txt'
            with open(manifest_file, 'a', encoding='utf-8') as f:
                f.write(f"\n## Git 标签\n")
                f.write(f"标签名：{tag_name}\n")
                f.write(f"创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"回滚命令：git reset --hard {tag_name}\n")
        else:
            print(f"\n⚠️  不在 Git 仓库中，跳过标签创建")

    except Exception as e:
        print(f"\n❌ Git 标签创建失败：{e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🛡️  核心配置文件备份工具")
    print("📅 " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)

    # 执行备份
    backup_dir, success, total = backup_core_configs()

    # 创建 Git 标签
    create_git_tag(backup_dir)

    # 计算成功率
    success_rate = (success / total * 100) if total > 0 else 0

    print(f"\n{'=' * 60}")
    print(f"📊 备份统计:")
    print(f"   成功率：{success_rate:.1f}%")
    print(f"   备份大小：估算 ~{sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()) / 1024:.1f} KB")
    print(f"{'=' * 60}\n")

    if success_rate >= 95:
        print("✅ 备份成功！可以安全执行代码清理。")
        return 0
    else:
        print("⚠️  部分文件备份失败，请检查后再继续。")
        return 1


if __name__ == '__main__':
    exit(main())
