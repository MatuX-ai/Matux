#!/usr/bin/env python3
"""
AI-Edu-for-Kids 资源批量导入工具

使用方法:
    python scripts/import_ai_edu_resources.py --path /path/to/resources --dry-run
    python scripts/import_ai_edu_resources.py --path /path/to/resources --execute
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.database import get_sync_db
from services.ai_edu_import_service import AIEduResourceImporter


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI-Edu 课程资源导入工具')

    parser.add_argument(
        '--path', '-p',
        type=str,
        required=True,
        help='资源目录路径'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅预演，不实际写入数据库'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 验证路径
    resource_path = Path(args.path)
    if not resource_path.exists():
        print(f"❌ 错误：资源目录不存在：{resource_path}")
        sys.exit(1)

    print("=" * 60)
    print("AI-Edu-for-Kids 课程资源导入工具")
    print("=" * 60)
    print(f"\n资源路径：{resource_path}")
    print(f"模式：{'预演' if args.dry_run else '执行'}")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    try:
        # 创建数据库会话
        print("\n正在连接数据库...")
        db = next(get_sync_db())
        print("✅ 数据库连接成功")

        # 创建导入器
        importer = AIEduResourceImporter(
            base_path=str(resource_path),
            db_session=db
        )

        # 执行导入
        print(f"\n{'【预演】' if args.dry_run else ''}开始导入资源...")
        stats = importer.import_all(dry_run=args.dry_run)

        # 输出统计信息
        print("\n" + "=" * 60)
        print("导入统计")
        print("=" * 60)
        print(f"模块数量：{stats['modules']}")
        print(f"课时数量：{stats['lessons']}")
        print(f"规则数量：{stats['rules']}")
        print(f"资源文件：{stats['resources']}")
        print(f"成功总数：{stats['total_imported']}")
        print(f"失败总数：{stats['total_failed']}")
        print(f"跳过总数：{stats['total_skipped']}")

        if stats['errors']:
            print(f"\n错误列表:")
            for error in stats['errors']:
                print(f"  - {error}")

        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        print(f"\n耗时：{duration:.2f}秒")
        print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 生成报告
        report_file = generate_report(stats, args.dry_run)
        print(f"\n📄 报告已生成：{report_file}")

        return 0

    except Exception as e:
        print(f"\n❌ 导入过程中出错：{e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    finally:
        db.close()


def generate_report(stats: dict, dry_run: bool) -> str:
    """生成导入报告"""
    from models.ai_edu_rewards import AIEduModule, AIEduLesson, AIEduRewardRule

    report_data = {
        'import_type': 'dry_run' if dry_run else 'execution',
        'start_time': stats['start_time'].isoformat(),
        'end_time': stats['end_time'].isoformat(),
        'duration_seconds': (stats['end_time'] - stats['start_time']).total_seconds(),
        'statistics': {
            'modules': stats['modules'],
            'lessons': stats['lessons'],
            'rules': stats['rules'],
            'resources': stats['resources'],
            'total_imported': stats['total_imported'],
            'total_failed': stats['total_failed'],
            'total_skipped': stats['total_skipped']
        },
        'errors': stats['errors']
    }

    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = Path(__file__).parent.parent / 'backtest_reports'
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f'ai_edu_import_{timestamp}.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    return str(report_file)


if __name__ == '__main__':
    sys.exit(main())
