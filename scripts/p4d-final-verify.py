#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D final verification：验证 /user/profile 正常加载 + 多个页面是否也都正常"""
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

# 多个 P4 关键页面
PAGES = [
    ('/user/profile', 'app-user-profile', '.profile-content', '.loading-container'),
    ('/user/courses', 'app-my-courses', '.courses-grid, mat-tab-group, app-my-courses mat-card', '.loading-spinner, [class*="loading"]'),
]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        logs = []

        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)}))

        # 1. 登录页 + 设置 token
        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        for url, selector, success_selector, loading_selector in PAGES:
            print(f'\n=== 测试 {url} ===')
            page.goto(f'http://127.0.0.1:8080{url}', wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(3000)

            # 等更久看是否完成
            for _ in range(3):
                result = page.evaluate(f"""
() => {{
  const root = document.querySelector('{selector}');
  if (!root) return {{ hasComponent: false }};
  return {{
    hasComponent: true,
    successVisible: !!root.querySelector('{success_selector}'),
    loadingVisible: !!root.querySelector('{loading_selector}'),
    innerText: root.innerText.substring(0, 150)
  }};
}}
""")
                if result.get('successVisible'):
                    break
                page.wait_for_timeout(2000)

            print(f'  5s+ 后: {result}')

            if result.get('successVisible'):
                print(f'  ✓ {url} 加载成功')
            else:
                print(f'  ✗ {url} 加载失败 (loading仍可见或没找到成功标志)')
                print(f'    innerText: {result.get("innerText", "")}')

        # 显示所有 console errors
        print('\n=== 所有 pageerrors / console errors ===')
        for log in logs:
            if log['type'] in ('pageerror', 'error'):
                text = log.get('text', '')
                if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text or 'ERR_FAILED' in text and 'UserProfileService' not in text:
                    continue
                print(f"  [{log['type']}] {text[:500]}")

        browser.close()


run()