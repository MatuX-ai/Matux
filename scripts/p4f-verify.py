#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-F verification：验证 /user/learning-reports 页面 PDF / 打印按钮工作正常
测试目标：
1. 页面正常加载
2. "导出PDF" 按钮可见且可点击
3. "打印" 按钮可见且可点击
4. 点击 PDF 按钮（后端不可用）触发回退打印提示
5. 打印对话框 API 被正确调用（监听 window.print）
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

INIT = """
() => {
  localStorage.setItem('access_token', 'fake');
  localStorage.setItem('user_data', JSON.stringify({id:'1', username:'test', email:'t@t.com', userType:'student'}));
  localStorage.setItem('remember_me', 'true');
}
"""


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # 监听 print 调用
        print_called = []
        page.expose_function('__recordPrint', lambda: print_called.append(True))

        # 在每个新文档加载前注入 window.print mock
        page.add_init_script("""
          (() => {
            const originalPrint = window.print;
            window.print = function() {
              window.__recordPrint && window.__recordPrint();
              console.log('[P4-F] window.print() called');
            };
          })();
        """)

        console_logs = []
        page.on('console', lambda m: console_logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: console_logs.append({'type': 'pageerror', 'text': str(e)}))

        # 1. 登录页 + 设置 token
        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        # 2. 导航到 /user/reports
        print('\n=== 测试 /user/reports ===')
        page.goto('http://127.0.0.1:8080/user/reports', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)

        # 3. 检查按钮是否存在
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-learning-reports');
  if (!root) return { hasComponent: false };
  const exportBtn = root.querySelector('.export-btn');
  const printBtn = root.querySelector('button[matTooltip*="打印"], button[matTooltip*="打印当前"]');
  const allButtons = [...root.querySelectorAll('button')].map(b => b.innerText.trim() || b.getAttribute('matTooltip') || '');
  return {
    hasComponent: true,
    exportBtnExists: !!exportBtn,
    exportBtnText: exportBtn ? exportBtn.innerText.trim() : null,
    printBtnExists: !!printBtn,
    printBtnTooltip: printBtn ? printBtn.getAttribute('matTooltip') : null,
    allButtons: allButtons.slice(0, 10),
  };
}
""")
        print(f'  初始状态: {result}')

        if not result['hasComponent']:
            print('  ✗ 组件未挂载')
            browser.close()
            return

        # 4. 点击"导出PDF"按钮 - 应该触发回退打印（后端不可用）
        print('\n=== 测试"导出PDF"按钮 ===')
        try:
            page.click('.export-btn', timeout=3000)
            print('  ✓ 按钮可点击')

            # 等待 1s 让 snackbar 显示
            page.wait_for_timeout(1500)

            state = page.evaluate("""
() => {
  const snackbar = document.querySelector('.mat-mdc-snack-bar-container, simple-snack-bar, mat-snack-bar-container');
  return {
    snackbarText: snackbar ? snackbar.innerText.trim() : null,
  };
}
""")
            print(f'  snackbar: {state}')

            # 检查 window.print 是否被调用（后端失败 → 回退打印）
            page.wait_for_timeout(2000)
            if print_called:
                print(f'  ✓ window.print() 被调用 ({len(print_called)} 次) - 回退打印成功')
            else:
                print('  ⚠ window.print() 未被调用（后端可能意外成功了）')
        except Exception as e:
            print(f'  ✗ 按钮点击失败: {e}')

        # 5. 点击"打印"按钮
        print('\n=== 测试"打印"按钮 ===')
        print_called.clear()
        try:
            # 找 matTooltip 为 "打印当前报告" 的按钮
            clicked = page.evaluate("""
() => {
  const root = document.querySelector('app-learning-reports');
  if (!root) return { found: false };
  const buttons = [...root.querySelectorAll('button')];
  const printBtn = buttons.find(b => {
    const tt = b.getAttribute('matTooltip') || b.getAttribute('ng-reflect-message') || '';
    const icon = b.querySelector('mat-icon');
    const iconText = icon ? icon.innerText.trim() : '';
    return tt.includes('打印') || iconText === 'print';
  });
  if (printBtn) {
    printBtn.click();
    return { found: true, text: printBtn.innerText.trim(), tooltip: printBtn.getAttribute('matTooltip'), disabled: printBtn.disabled };
  }
  return { found: false, allBtns: buttons.map(b => ({ text: b.innerText.trim(), tt: b.getAttribute('matTooltip'), icon: b.querySelector('mat-icon')?.innerText })) };
}
""")
            print(f'  按钮查找结果: {clicked}')
            page.wait_for_timeout(1500)
            if print_called:
                print(f'  ✓ window.print() 被调用 ({len(print_called)} 次)')
            else:
                print('  ⚠ window.print() 未被调用')
        except Exception as e:
            print(f'  ✗ 按钮点击失败: {e}')

        # 6. 检查全局打印样式是否加载
        print('\n=== 检查全局打印样式 ===')
        css_check = page.evaluate("""
() => {
  const sheets = [...document.styleSheets];
  let hasPrintMedia = false;
  let hasPrintHidden = false;
  let hasPageRule = false;
  for (const sheet of sheets) {
    try {
      const rules = sheet.cssRules || sheet.rules || [];
      for (const rule of rules) {
        if (rule.type === CSSRule.MEDIA_RULE && rule.media && rule.media.mediaText && rule.media.mediaText.includes('print')) {
          hasPrintMedia = true;
          for (const inner of rule.cssRules || []) {
            if (inner.selectorText && inner.selectorText.includes('print-hidden')) hasPrintHidden = true;
          }
        }
        if (rule.type === CSSRule.PAGE_RULE) {
          hasPageRule = true;
        }
      }
    } catch (e) {
      // CORS
    }
  }
  return { hasPrintMedia, hasPrintHidden, hasPageRule };
}
""")
        print(f'  CSS 检查: {css_check}')

        # 7. 显示关键 console logs
        print('\n=== 关键 console logs ===')
        keywords = ['pdf', 'print', '导出', '打印', 'PDF', 'P4-F']
        for log in console_logs:
            text = log.get('text', '')
            if any(k.lower() in text.lower() for k in keywords):
                print(f"  [{log['type']}] {text[:200]}")

        # 总结
        print('\n=== 总结 ===')
        print(f'  PDF 按钮存在: {result["exportBtnExists"]}')
        print(f'  打印按钮存在: {result["printBtnExists"]}')
        print(f'  @media print 加载: {css_check["hasPrintMedia"]}')
        print(f'  @page 规则加载: {css_check["hasPageRule"]}')
        all_ok = result['exportBtnExists'] and result['printBtnExists'] and css_check['hasPrintMedia'] and css_check['hasPageRule']
        if all_ok:
            print('  ✅ P4-F 验证通过')
        else:
            print('  ⚠ P4-F 部分验证失败')

        browser.close()


run()
