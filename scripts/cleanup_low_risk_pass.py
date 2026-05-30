"""
清理 14 处低风险 Python pass 占位符
按照 PASS_PLACEHOLDER_ANALYSIS_REPORT.md 中的 🟢 低风险清单执行
"""

import os
from pathlib import Path

# 低风险的 pass 占位符清单（来自分析报告）
LOW_RISK_FILES = {
    "backend/services/code_sandbox_service.py": [194],
    "backend/services/document_service.py": [201],
    "backend/services/hidden_task_reward_system.py": [395],
    "backend/services/learning_behavior_service.py": [309],
    "backend/services/three_d_service.py": [211],
    "backend/services/web_rtc_sensor_service.py": [207, 215, 283],
    "backend/tests/quick_test.py": [119],
    "backend/tests/quick_test_dynamic_course.py": [18],
    "backend/tests/test_apm_monitoring.py": [244],
    "backend/tests/test_xr_integration.py": [81],
    "backend/enterprise_gateway/tests/test_performance.py": [188],
}


def clean_pass_placeholder(file_path: Path, line_numbers: list) -> dict:
    """清理指定文件中的 pass 占位符"""
    result = {
        'file': str(file_path),
        'cleaned': 0,
        'skipped': 0,
        'errors': []
    }
    
    if not file_path.exists():
        result['errors'].append(f"文件不存在")
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 从后向前处理，避免行号偏移
        for line_num in reversed(line_numbers):
            idx = line_num - 1
            if 0 <= idx < len(lines):
                line = lines[idx].strip()
                
                # 确认是 pass 语句
                if line == 'pass':
                    # 检查上下文
                    prev_line = lines[idx - 1].strip() if idx > 0 else ''
                    next_line = lines[idx + 1].strip() if idx < len(lines) - 1 else ''
                    
                    # 如果是空函数的唯一内容，保留 docstring
                    if (prev_line.startswith('"""') or prev_line.startswith("'''")) and \
                       (not next_line or next_line.startswith('#')):
                        # 这是一个有 docstring 的空函数，保留 pass
                        print(f"  ⚠️  跳过 {file_path.name}:{line_num} (保留空函数)")
                        result['skipped'] += 1
                    else:
                        # 可以安全删除
                        lines[idx] = '\n'  # 替换为空行
                        print(f"  ✅ 清理 {file_path.name}:{line_num}")
                        result['cleaned'] += 1
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
    except Exception as e:
        result['errors'].append(str(e))
        print(f"  ❌ 错误：{file_path} - {e}")
    
    return result


def main():
    print("=" * 80)
    print("🔧 开始清理 14 处低风险 pass 占位符")
    print("=" * 80)
    print()
    
    total_cleaned = 0
    total_skipped = 0
    results = []
    
    for file_path_str, line_numbers in LOW_RISK_FILES.items():
        file_path = Path(file_path_str)
        print(f"\n📄 {file_path}:")
        
        result = clean_pass_placeholder(file_path, line_numbers)
        results.append(result)
        
        total_cleaned += result['cleaned']
        total_skipped += result['skipped']
    
    # 打印总结
    print("\n" + "=" * 80)
    print("📊 清理完成总结")
    print("=" * 80)
    print(f"✅ 成功清理：{total_cleaned} 处")
    print(f"⚠️  跳过保留：{total_skipped} 处")
    print(f"❌ 发生错误：{len([r for r in results if r['errors']])} 个文件")
    
    if any(r['errors'] for r in results):
        print("\n错误详情:")
        for result in results:
            if result['errors']:
                print(f"  - {result['file']}: {', '.join(result['errors'])}")
    
    print("\n" + "=" * 80)
    print(f"✨ 代码优化完成！共清理 {total_cleaned} 处占位符\n")


if __name__ == "__main__":
    main()
