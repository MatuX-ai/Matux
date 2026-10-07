#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v17：直接检查 Zone 是否有能力 patch setTimeout（手动调用）"""
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

        # 测试 setTimeout 在 zone 内是否进入 zone
        result = page.evaluate("""
() => {
  return new Promise(resolve => {
    // 测试 1: 在当前 zone 内执行 setTimeout
    const startZone = Zone.current.name;
    window.setTimeout(() => {
      const callbackZone = Zone.current.name;
      resolve({
        startZone,
        callbackZone,
        sameZone: startZone === callbackZone,
        // 查 __symbol__setTimeout
        patchedSetTimeoutSymbol: typeof Zone?.__symbol__('setTimeout') !== 'undefined',
        setTimeoutOrig: !!window.__zone_symbol__setTimeout || !!window[Zone?.__symbol__('setTimeout')],
        hasSetTimeoutDelegate: window.setTimeout.toString().includes('setTimeout')
      });
    }, 100);
  });
}
""")
        print('=== Zone 测试 ===')
        print(result)

        # Console logs
        print('\n=== console logs ===')
        for log in logs[-30:]:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:500]}")

        browser.close()


run()