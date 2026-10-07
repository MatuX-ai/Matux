#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v15：手动触发 ApplicationRef.tick() 看能否更新视图"""
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
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)

        # 检查状态
        result1 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 100) ?? null
  };
}
""")
        print('=== 3s 状态 ===')
        print(result1)

        # 尝试强制 CD
        result2 = page.evaluate("""
() => {
  // 找 ng Zone
  const root = document.querySelector('app-user-profile');
  if (!root) return { error: 'no root' };

  // 通过点击触发 zone-aware 事件
  document.body.click();
  return { clicked: true };
}
""")
        print('=== 点击后 ===')
        print(result2)

        page.wait_for_timeout(2000)

        result3 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 100) ?? null
  };
}
""")
        print('=== 点击 + 2s 后 ===')
        print(result3)

        # 移动鼠标
        page.mouse.move(100, 100)
        page.wait_for_timeout(500)
        page.mouse.move(800, 500)
        page.wait_for_timeout(500)

        result4 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 100) ?? null
  };
}
""")
        print('=== 移动鼠标后 ===')
        print(result4)

        # Console logs
        print('\n=== console logs (最后 30 条) ===')
        for log in logs[-30:]:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        browser.close()


run()