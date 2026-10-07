#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v9：在每次新上下文执行前注入监控（addInitScript）"""
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

# 监控 setTimeout：每 100ms 检查页面状态并打印
MONITOR = """
() => {
  if (window.__monitorInstalled) return;
  window.__monitorInstalled = true;
  window.__setTimeoutCalls = [];
  const origSetTimeout = window.setTimeout;
  window.setTimeout = function(fn, delay) {
    window.__setTimeoutCalls.push({ delay, time: Date.now() });
    return origSetTimeout.call(this, fn, delay);
  };
  console.log('=== monitor installed ===');
}
"""


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        # addInitScript 会在每个 page navigation 前执行
        ctx.add_init_script(MONITOR)
        page = ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)}))

        # 1. 访问 login 页面（监控会自动安装）
        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        # 2. 导航到 /user/profile
        nav_start = page.evaluate('() => Date.now()')
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        nav_end = page.evaluate('() => Date.now()')
        print(f'导航耗时: {nav_end - nav_start}ms')

        # 3. 等待组件
        page.wait_for_timeout(2000)
        has_component = page.evaluate("() => !!document.querySelector('app-user-profile')")
        print(f'2s 后组件存在: {has_component}')

        # 4. 列出 setTimeout 调用
        st_2s = page.evaluate('() => window.__setTimeoutCalls')
        print(f'\n=== 2s 时 setTimeout 调用数: {len(st_2s) if st_2s else 0} ===')
        for i, c in enumerate((st_2s or [])[-10:]):
            print(f'  [{i}] delay={c["delay"]}ms at+{c["time"] - nav_start}ms')

        # 5. 等 18s
        page.wait_for_timeout(18000)

        st_20s = page.evaluate('() => window.__setTimeoutCalls')
        print(f'\n=== 20s 时 setTimeout 调用数: {len(st_20s) if st_20s else 0} ===')
        for i, c in enumerate((st_20s or [])[-10:]):
            print(f'  [{i}] delay={c["delay"]}ms at+{c["time"] - nav_start}ms')

        # 6. 最终状态
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  return {
    hasComponent: true,
    loadingContainerVisible: !!root.querySelector('.loading-container'),
    errorContainerVisible: !!root.querySelector('.error-container'),
    profileContentVisible: !!root.querySelector('.profile-content'),
    innerText: root.innerText.substring(0, 200)
  };
}
""")
        print(f'\n=== 20s 后状态 ===')
        print(result)

        print('\n=== console logs ===')
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:500]}")

        browser.close()


run()