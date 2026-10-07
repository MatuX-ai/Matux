#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v16：检查 zone.js 是否真的 patch 了 setTimeout"""
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

        # 检查 zone
        result = page.evaluate("""
() => {
  const checks = {
    hasZone: typeof Zone !== 'undefined',
    hasWindowZone: typeof window.Zone !== 'undefined',
    hasZoneSymbol: typeof Zone?.__symbol__ !== 'undefined' || typeof Zone?.symbol !== 'undefined',
    setTimeoutPatched: window.setTimeout.toString().includes('[native code]') === false,
    setTimeoutString: window.setTimeout.toString().substring(0, 200),
    setTimeoutLength: window.setTimeout.length,
    hasNgZone: typeof window.ng !== 'undefined' && typeof window.ng.getContext !== 'undefined',
    ngZoneAvailable: typeof window.ng?.getInjector !== 'undefined'
  };

  // 找 Zone current
  if (typeof Zone !== 'undefined') {
    try {
      checks.zoneCurrent = Zone.current?.name;
    } catch (e) {
      checks.zoneError = e.message;
    }
  }

  return checks;
}
""")
        print('=== Zone 检查 ===')
        print(result)

        print('\n=== console logs ===')
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        browser.close()


run()