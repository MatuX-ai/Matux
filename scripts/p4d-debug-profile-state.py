#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D debug：注入 JS 看 user-profile 组件的状态"""
import time
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
        page.wait_for_timeout(2000)

        # 查找 Angular 组件实例
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };

  // 试图通过 ng probe 获取实例
  const ng = window.ng;
  if (!ng || !ng.getComponent) return { hasComponent: true, hasNgProbe: false };

  try {
    const comp = ng.getComponent(root);
    return {
      hasComponent: true,
      hasNgProbe: true,
      loading: comp.loading,
      saving: comp.saving,
      error: comp.error,
      hasUserProfile: !!comp.userProfile,
      userProfileKeys: comp.userProfile ? Object.keys(comp.userProfile) : [],
      destroyFired: comp.destroy$ ? comp.destroy$.isStopped : 'no-destroy$',
      isEditing: comp.isEditing
    };
  } catch (e) {
    return { hasComponent: true, hasNgProbe: true, error: e.message };
  }
}
""")
        print("=== t=2s ===")
        print(result)

        page.wait_for_timeout(10000)
        result2 = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  const ng = window.ng;
  if (!ng || !ng.getComponent) return { hasComponent: true, hasNgProbe: false };
  try {
    const comp = ng.getComponent(root);
    return {
      loading: comp.loading,
      saving: comp.saving,
      error: comp.error,
      hasUserProfile: !!comp.userProfile
    };
  } catch (e) {
    return { error: e.message };
  }
}
""")
        print("\n=== t=12s ===")
        print(result2)

        print("\n=== console logs ===")
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        browser.close()

run()
