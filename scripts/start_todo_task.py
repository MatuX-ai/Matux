# TODO 任务快速启动脚本
# 使用方式：python scripts/start_todo_task.py BACKEND-P1-001

import os
import sys
import json
from datetime import datetime

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def load_task_list():
    """加载任务清单"""
    task_file = "TODO_TASK_LIST_20260305.md"
    if not os.path.exists(task_file):
        print(f"❌ 任务清单文件不存在：{task_file}")
        return None

    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()

    return content

def parse_task_info(task_id):
    """解析任务信息"""
    task_list_content = load_task_list()
    if not task_list_content:
        return None

    # 简单的文本搜索
    lines = task_list_content.split('\n')
    task_start = None

    for i, line in enumerate(lines):
        # 支持多种格式：BACKEND-P1-001 或 BACKEND-P1-001:
        if task_id in line and ('**' in line or line.strip().startswith('###')):
            task_start = i
            break

    if task_start is None:
        return None

    # 提取任务信息（简化版）
    task_info = {
        'id': task_id,
        'title': '',
        'file': '',
        'hours': '',
        'difficulty': ''
    }

    # 查找后续的关键信息行
    for i in range(task_start, min(task_start + 20, len(lines))):
        line = lines[i]
        if '**位置**:' in line:
            task_info['file'] = line.split('**位置**:')[1].strip()
        elif '**预计工时**:' in line:
            task_info['hours'] = line.split('**预计工时**:')[1].strip()
        elif '**难度**:' in line:
            task_info['difficulty'] = line.split('**难度**:')[1].strip()
        elif '#### 任务描述' in line:
            # 提取任务描述
            desc_lines = []
            for j in range(i+1, min(i+5, len(lines))):
                if lines[j].strip() and not lines[j].startswith('####'):
                    desc_lines.append(lines[j].strip())
            task_info['description'] = ' '.join(desc_lines)
            break

    return task_info

def create_git_branch(task_id):
    """创建 Git 分支"""
    branch_name = f"feature/TODO-{task_id}"
    print(f"📝 建议创建的 Git 分支：{branch_name}")
    print(f"   命令：git checkout -b {branch_name}")
    return branch_name

def generate_checklist(task_info):
    """生成检查清单"""
    print("\n📋 任务检查清单:")
    print("-" * 60)

    checklist = [
        "准备阶段",
        "  □ 阅读任务详情（TODO_TASK_LIST_20260305.md）",
        "  □ 搜索相关代码，确认无重复实现",
        "  □ 查看现有文档，了解上下文",
        "  □ 创建 Git 分支",
        "",
        "实施阶段",
        f"  □ 按步骤编码（预计 {task_info.get('hours', '?')} 小时）",
        "  □ 遵循项目编码规范",
        "  □ 编写必要的注释",
        "  □ 实时 Git 提交（小步快跑）",
        "",
        "验证阶段",
        "  □ 运行快速回测脚本",
        "  □ 验证功能符合验收标准",
        "  □ 执行回归测试",
        "  □ 检查代码质量（lint/format）",
        "",
        "收尾阶段",
        "  □ 更新技术文档",
        "  □ 编写/更新单元测试",
        "  □ Git commit 并 push",
        "  □ 在任务清单中标记完成 ✅",
        "  □ 记录实际工时和经验教训"
    ]

    for item in checklist:
        print(item)

    print("-" * 60)

def show_task_details(task_info):
    """显示任务详情"""
    print_header(f"任务详情：{task_info['id']}")

    print(f"📌 任务ID: {task_info['id']}")
    print(f"📝 任务描述：{task_info.get('description', 'N/A')}")
    print(f"📁 目标文件：{task_info.get('file', 'N/A')}")
    print(f"⏱️  预计工时：{task_info.get('hours', 'N/A')}")
    print(f"⭐ 难度等级：{task_info.get('difficulty', 'N/A')}")

    print("\n💡 下一步行动:")
    print(f"  1. 打开文件：{task_info.get('file', 'N/A')}")
    print(f"  2. 搜索 TODO 标记，定位需要修改的位置")
    print(f"  3. 理解上下文，开始编码实现")

def main():
    """主函数"""
    print_header("TODO 任务启动助手")

    if len(sys.argv) < 2:
        print("❌ 请提供任务 ID")
        print("\n使用示例:")
        print("  python start_todo_task.py BACKEND-P1-001")
        print("  python start_todo_task.py FRONTEND-P2-001")
        print("\n可用任务列表请查看：TODO_TASK_LIST_20260305.md")
        sys.exit(1)

    task_id = sys.argv[1].upper()

    # 解析任务信息
    task_info = parse_task_info(task_id)
    if not task_info:
        print(f"❌ 未找到任务：{task_id}")
        print("\n请检查任务 ID 是否正确，或查看 TODO_TASK_LIST_20260305.md")
        sys.exit(1)

    # 显示任务详情
    show_task_details(task_info)

    # 创建 Git 分支
    branch_name = create_git_branch(task_id)

    # 生成检查清单
    generate_checklist(task_info)

    # 显示防重复开发提醒
    print_header("⚠️ 防重复开发提醒")
    print("在开始编码前，请务必:")
    print("  1. ✓ 搜索代码库，确认无现成实现")
    print("  2. ✓ 查看文档中心，了解相关信息")
    print("  3. ✓ 如有疑虑，及时与团队沟通")
    print("\n搜索建议:")
    print(f"  - 语义搜索：\"{task_info.get('description', '')[:50]}...\"")
    print(f"  - 文件搜索：查看 {task_info.get('file', 'N/A')} 的上下文")

    # 鼓励语
    print_header("🚀 开始行动吧！")
    print("祝你编码愉快！如有问题，及时寻求帮助。")
    print("\n记录开始时间：", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("\n提示：完成后记得运行回测验证并更新文档哦！")

if __name__ == "__main__":
    main()
