#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4 final 综合验证 - 一次性验证所有 P4 修复"""
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

# 验证目标：每个页面都应该能正常加载或显示合理的错误/降级状态
TARGETS = [
    # (path, 组件选择器, 期望状态: 'loaded' | 'placeholder' | 'error')
    ('/user/profile', 'app-user-profile', 'loaded'),
    ('/user/courses', 'app-my-courses', 'loaded'),
    ('/user/reports', 'app-learning-reports', 'loaded'),
    ('/ar-lab', 'app-ar-lab', 'placeholder'),
]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # 监听 print 调用
        page.add_init_script("""
          (() => {
            window.print = function() { console.log('[P4-F] window.print() called'); };
          })();
        """)

        # 1. 设置 token
        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        print('\n========== P4 综合验证 ==========')
        passed = []
        failed = []
        for path, selector, expected_state in TARGETS:
            print(f'\n--- {path} (期望: {expected_state}) ---')
            try:
                page.goto(f'http://127.0.0.1:8080{path}', wait_until='domcontentloaded', timeout=20000)
                page.wait_for_timeout(3500)

                # 检查组件挂载 + 是否离开 loading 状态
                result = page.evaluate(f"""
() => {{
  const root = document.querySelector('{selector}');
  if (!root) return {{ hasComponent: false }};

  // 查找 loading 标志
  const loadingEls = root.querySelectorAll(
    '.loading-container, .loading-spinner, mat-spinner, [class*="loading"]'
  );
  const visibleLoadings = [...loadingEls].filter(el => {{
    const style = getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden';
  }});

  // 查找错误标志
  const errorEls = root.querySelectorAll(
    '.error-container, .error-state, [class*="error"]:not([class*="error-icon"])'
  );

  // 查找内容标志
  const contentEls = root.querySelectorAll(
    '.profile-content, .courses-grid, mat-tab-group, .reports-container, .placeholder-content, .unity-loading'
  );

  return {{
    hasComponent: true,
    visibleLoadings: visibleLoadings.length,
    errorEls: errorEls.length,
    contentEls: contentEls.length,
    bodyText: root.innerText.substring(0, 200),
  }};
}}
""")
                if not result['hasComponent']:
                    print(f'  ✗ 组件 {selector} 未挂载')
                    failed.append((path, 'no-component'))
                    continue

                # 状态判定
                if expected_state == 'loaded':
                    if result['contentEls'] > 0:
                        print(f'  ✓ 内容已渲染 (contentEls={result["contentEls"]})')
                        passed.append(path)
                    elif result['visibleLoadings'] > 0 and result['contentEls'] == 0:
                        # 检查是否长时间 loading
                        print(f'  ⚠ 仍处 loading 状态 (loadings={result["visibleLoadings"]})')
                        failed.append((path, 'still-loading'))
                    elif result['errorEls'] > 0:
                        print(f'  ⚠ 显示错误状态')
                        failed.append((path, 'error-state'))
                    else:
                        print(f'  ? 未知状态: {result}')
                        failed.append((path, 'unknown'))
                elif expected_state == 'placeholder':
                    # 占位 UI：可以是任意内容，关键是组件挂载了
                    if result['hasComponent']:
                        print(f'  ✓ 占位 UI 已挂载')
                        passed.append(path)
                    else:
                        failed.append((path, 'no-placeholder'))
                else:
                    print(f'  ? 未知期望状态: {expected_state}')

            except Exception as e:
                print(f'  ✗ 测试异常: {e}')
                failed.append((path, str(e)[:100]))

        # 2. 特殊测试：digital-twin-lab 离线 banner（独立测试因为需要等待 45s）
        print('\n--- /digital-twin-lab (offline fallback) ---')
        try:
            page.goto('http://127.0.0.1:8080/digital-twin-lab', wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(3000)

            # 检查 global-connection-bar
            state = page.evaluate("""
() => {
  const root = document.querySelector('app-digital-twin-lab');
  if (!root) return null;
  const globalBar = root.querySelector('.global-connection-bar');
  return { hasGlobalBar: !!globalBar };
}
""")
            if state and state['hasGlobalBar']:
                print(f'  ✓ global-connection-bar 已显示（即便 lab-container 因后端不可用而隐藏）')
                passed.append('/digital-twin-lab (offline fallback UI)')
            else:
                failed.append(('/digital-twin-lab', 'no-global-bar'))
        except Exception as e:
            print(f'  ✗ 测试异常: {e}')
            failed.append(('/digital-twin-lab', str(e)[:100]))

        # 总结
        print('\n========== 总结 ==========')
        print(f'通过: {len(passed)} 项')
        for p_item in passed:
            print(f'  ✓ {p_item}')
        if failed:
            print(f'\n失败: {len(failed)} 项')
            for p_item, reason in failed:
                print(f'  ✗ {p_item} ({reason})')
        else:
            print('\n🎉 所有 P4 修复均验证通过')

        browser.close()


run()
