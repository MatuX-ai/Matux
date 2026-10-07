#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v7：手动调用 setTimeout 在 page context 强制改状态"""
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

        # 等 5s 让 page render
        page.wait_for_timeout(5000)

        # 通过 evaluate 找到 user-profile 组件实例
        result = page.evaluate("""
() => {
  // 试着通过 ng.getComponent 获取实例
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };

  // 检查 Angular Debug API
  const ngContext = root.__ngContext__;
  if (ngContext) {
    return { hasNgContext: true, ngContextKeys: Object.keys(ngContext) };
  }
  return { hasComponent: true, hasNgContext: false, html: root.outerHTML.substring(0, 500) };
}
""")
        print("=== Component instance ===")
        print(result)

        # 试一下点击页面触发 CD
        print("\n=== 模拟点击页面 ===")
        page.mouse.click(640, 400)
        page.wait_for_timeout(2000)

        # 再次检查状态
        result2 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  return {
    loadingContainerVisible: !!root.querySelector('.loading-container'),
    errorContainerVisible: !!root.querySelector('.error-container'),
    profileContentVisible: !!root.querySelector('.profile-content'),
    innerText: root.innerText.substring(0, 200)
  };
}
""")
        print("点击后:", result2)

        # 再等 10s 看 safety net 是否触发
        print("\n=== 再等 10s (总共 17s) ===")
        page.wait_for_timeout(10000)
        result3 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  return {
    loadingContainerVisible: !!root.querySelector('.loading-container'),
    errorContainerVisible: !!root.querySelector('.error-container'),
    profileContentVisible: !!root.querySelector('.profile-content'),
    errorMessage: root.querySelector('.error-container .error-message')?.innerText ?? null,
    innerText: root.innerText.substring(0, 200)
  };
}
""")
        print("结果:", result3)

        print("\n=== console logs ===")
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:400]}")

        browser.close()

run()
