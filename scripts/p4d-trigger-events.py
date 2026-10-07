#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v20：检查 component 实际状态 - 通过触发事件强制 CD"""
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

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)

        # 强制触发 Angular CD
        # 通过模拟一个真实的 DOM 事件触发 zone
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { error: 'no root' };

  // 触发事件 (mouseenter 会进入 Angular NgZone)
  root.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));

  return { dispatched: true };
}
""")
        print('event result:', result)
        page.wait_for_timeout(500)

        # 状态
        result2 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 200)
  };
}
""")
        print('mouseenter 后:', result2)

        # 通过 click 试试
        page.mouse.click(400, 300)
        page.wait_for_timeout(500)
        result3 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 200)
  };
}
""")
        print('click 后:', result3)

        # 用 keyboard input 试试
        page.keyboard.press('Tab')
        page.wait_for_timeout(500)
        result4 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 200)
  };
}
""")
        print('Tab 后:', result4)

        print('\n=== console logs ===')
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        browser.close()


run()