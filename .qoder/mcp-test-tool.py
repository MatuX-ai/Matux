#!/usr/bin/env python3
"""
MatuX MCP 自动化测试脚本
用于执行预定义的浏览器自动化测试场景
"""

import json
import time
import sys
from pathlib import Path


class MatuXMCPAutomation:
    """MatuX MCP 自动化测试工具"""

    def __init__(self, config_path: str = None):
        """初始化测试工具"""
        if config_path is None:
            config_path = Path(__file__).parent / "mcp-config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.test_accounts = self.config['projectConfig']['testAccounts']
        self.scenarios = self.config['automationScenarios']

    def get_test_account(self, role: str = 'student'):
        """获取测试账号信息"""
        return self.test_accounts.get(role, self.test_accounts['student'])

    def generate_mcp_commands(self, scenario_name: str):
        """生成 MCP 命令序列"""
        if scenario_name not in self.scenarios:
            print(f"❌ 未知场景: {scenario_name}")
            return

        scenario = self.scenarios[scenario_name]
        commands = []

        print(f"\n📝 场景: {scenario['description']}")
        print(f"🌐 起始URL: {scenario.get('url', '未指定')}")
        print("\n" + "="*60)
        print("MCP 命令序列:")
        print("="*60 + "\n")

        for i, action in enumerate(scenario['actions'], 1):
            cmd = self._format_action(action, i)
            commands.append(cmd)
            print(cmd)

        print("\n" + "="*60)
        print("✅ 生成完成！")
        print("="*60)

        return commands

    def _format_action(self, action: dict, index: int) -> str:
        """格式化单个动作"""
        action_type = action['type']

        # 定义格式化函数
        def fmt_navigate(a):
            url = a.get('url', '')
            return f'navigate_page({{url: "{url}"}})'

        def fmt_click(a):
            selector = a.get('selector', '')
            return f'click({{selector: "{selector}"}})'

        def fmt_screenshot(a):
            filename = a.get('filename', f'screenshot_{index}')
            return f'take_screenshot({{filename: "{filename}"}})'

        def fmt_wait(a):
            seconds = a.get('seconds', 3)
            return f'wait_for({{seconds: {seconds}}})'

        def fmt_fill(a):
            selector = a.get('selector', '')
            value = a.get('value', '')
            return f'fill({{selector: "{selector}", value: "{value}"}})'

        def fmt_snapshot(a):
            return 'take_snapshot()'

        def fmt_network(a):
            return 'list_network_requests()'

        def fmt_console(a):
            return 'list_console_messages()'

        def fmt_evaluate(a):
            script = a.get('script', '').replace('"', '\\"')
            return f'evaluate_script({{script: "{script}"}})'

        def fmt_dialog(a):
            accept = a.get('accept', True)
            return f'handle_dialog({{accept: {str(accept).lower()}}})'

        def fmt_default(a):
            return f'# 未知动作: {action_type}'

        format_handlers = {
            'navigate': fmt_navigate,
            'click': fmt_click,
            'screenshot': fmt_screenshot,
            'wait': fmt_wait,
            'fill': fmt_fill,
            'snapshot': fmt_snapshot,
            'network': fmt_network,
            'console': fmt_console,
            'evaluate': fmt_evaluate,
            'handle_dialog': fmt_dialog,
        }

        formatter = format_handlers.get(action_type, fmt_default)
        return f"{index}. {formatter(action)}"

    def print_test_accounts(self):
        """打印所有测试账号"""
        print("\n👥 可用的测试账号:")
        print("="*60)

        for role, account in self.test_accounts.items():
            print(f"\n🎭 {account['description']} ({role.upper()})")
            print(f"   用户名: {account['username']}")
            print(f"   密  码: {account['password']}")

        print("\n" + "="*60)

    def print_quick_reference(self):
        """打印快速参考"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║              MatuX MCP 快速参考指南                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🔍 常用命令                                                  ║
║  ─────────────────────────────────────────────────────────  ║
║  导航: navigate_page({url: "http://localhost:4200/..."})    ║
║  点击: click({selector: ".class-name"})                       ║
║  截图: take_screenshot()                                    ║
║  等待: wait_for({seconds: 3})                              ║
║                                                              ║
║  📊 登录测试流程                                              ║
║  ─────────────────────────────────────────────────────────  ║
║  1. navigate_page("http://localhost:4200/auth/login")        ║
║  2. click(".test-login-button")  // 一键登录按钮             ║
║  3. wait_for({seconds: 3})                                 ║
║  4. navigate_page("http://localhost:4200/user/dashboard")     ║
║  5. take_screenshot()  // 验证 Dashboard                     ║
║                                                              ║
║  🎯 性能分析                                                  ║
║  ─────────────────────────────────────────────────────────  ║
║  1. list_network_requests()  // 开始监控                      ║
║  2. 执行登录操作                                             ║
║  3. 分析请求耗时                                             ║
║                                                              ║
║  💡 调试技巧                                                  ║
║  ─────────────────────────────────────────────────────────  ║
║  - 使用 take_snapshot() 获取高清 DOM 快照                     ║
║  - 使用 evaluate_script 检查 localStorage                     ║
║  - 使用 list_console_messages 检查错误                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

    def list_scenarios(self):
        """列出所有可用场景"""
        print("\n📋 可用的自动化场景:")
        print("="*60)

        for name, scenario in self.scenarios.items():
            print(f"\n🎯 {name}")
            print(f"   描述: {scenario['description']}")
            print(f"   步骤数: {len(scenario['actions'])}")

        print("\n" + "="*60)

    def interactive_mode(self):
        """交互模式"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║           MatuX MCP 自动化测试工具 - 交互模式                 ║
╚══════════════════════════════════════════════════════════════╝
        
可用命令:
  1. test <scenario>  - 运行指定场景
  2. accounts        - 显示测试账号
  3. scenarios       - 列出所有场景
  4. quick           - 显示快速参考
  5. help            - 显示帮助
  6. quit            - 退出
  
示例:
  > test login        # 运行登录测试
  > test performance  # 运行性能测试
  > accounts          # 查看测试账号
  > quit              # 退出
        """)

        while True:
            try:
                cmd = input("\n(matuxtest) ").strip().lower()

                if cmd == 'quit' or cmd == 'exit':
                    print("👋 再见!")
                    break
                elif cmd.startswith('test '):
                    scenario = cmd[5:].strip()
                    if scenario in self.scenarios:
                        self.generate_mcp_commands(scenario)
                    else:
                        print(f"❌ 未知场景: {scenario}")
                        print("使用 'scenarios' 查看所有可用场景")
                elif cmd == 'accounts':
                    self.print_test_accounts()
                elif cmd == 'scenarios':
                    self.list_scenarios()
                elif cmd == 'quick':
                    self.print_quick_reference()
                elif cmd == 'help':
                    print("帮助: 输入命令执行相应操作")
                else:
                    print("❌ 未知命令，使用 'help' 查看帮助")

            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


def main():
    """主入口"""
    tool = MatuXMCPAutomation()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'accounts' or command == '-a':
            tool.print_test_accounts()
        elif command == 'scenarios' or command == '-s':
            tool.list_scenarios()
        elif command == 'quick' or command == '-q':
            tool.print_quick_reference()
        elif command == 'interactive' or command == '-i':
            tool.interactive_mode()
        elif command == 'test' and len(sys.argv) > 2:
            tool.generate_mcp_commands(sys.argv[2])
        elif command == 'help' or command == '-h':
            print("""
用法: python mcp-test-tool.py [命令]

命令:
  accounts, -a        显示测试账号信息
  scenarios, -s      列出所有自动化场景
  quick, -q           显示快速参考指南
  interactive, -i     进入交互模式
  test <场景名>       生成指定场景的 MCP 命令
  help, -h           显示帮助信息

示例:
  python mcp-test-tool.py accounts
  python mcp-test-tool.py scenarios
  python mcp-test-tool.py test 一键登录验证
  python mcp-test-tool.py interactive
            """)
        else:
            print("❌ 无效命令，使用 'help' 查看帮助")
    else:
        tool.print_quick_reference()


if __name__ == "__main__":
    main()
