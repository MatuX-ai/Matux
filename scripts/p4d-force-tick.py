#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v22：尝试使用 NgZone 的 _inner 机制强制 CD"""
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

        # 通过 mat-spinner 的 svg 触发 click 事件 - Angular Material 会处理
        result = page.evaluate("""
() => {
  // 尝试通过 ApplicationRef 触发 CD
  // 我们知道 Angular 的 ApplicationRef 有 tick() 方法
  // 通过 DOM 事件触发 zone-aware 事件
  const spinner = document.querySelector('mat-spinner');
  if (!spinner) return { error: 'no spinner' };

  // 触发 mousedown 事件（这个会被 addEventListener patched）
  spinner.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
  spinner.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
  spinner.dispatchEvent(new MouseEvent('click', { bubbles: true }));

  return { dispatched: true };
}
""")
        print('事件触发:', result)
        page.wait_for_timeout(1000)

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
        print('mat-spinner click 后:', result2)

        # 找到 Angular 的 element injector 并 ApplicationRef
        result3 = page.evaluate("""
() => {
  // 尝试通过 ɵcmp 静态属性找 component
  const root = document.querySelector('app-user-profile');
  if (!root) return { error: 'no root' };

  // 查 ngContext (production strips it though)
  const ctx = root.__ngContext__;
  if (!ctx) return { error: 'no ngContext' };

  return { hasNgContext: true, ctxKeys: Object.keys(ctx || {}) };
}
""")
        print('ngContext:', result3)

        # Try changing the loading state manually using store mutation
        # This won't work directly since we can't access the component instance
        # But we can verify by checking what's in the template
        result4 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  const loadingDiv = root?.querySelector('.loading-container');
  const profileDiv = root?.querySelector('.profile-content');
  return {
    rootHTML: root?.outerHTML?.substring(0, 2000),
    loadingDivExists: !!loadingDiv,
    profileDivExists: !!profileDiv
  };
}
""")
        print('outerHTML[0:2000]:')
        print(result4.get('rootHTML'))

        browser.close()


run()