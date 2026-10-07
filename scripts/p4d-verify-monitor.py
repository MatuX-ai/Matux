#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v13：监控 setTimeout 是否生效 - 等待 30s 看 15s 安全网是否 fire"""
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

        ctx.add_init_script("""
window.__setTimeoutCalls = [];
window.__setTimeoutOrig = window.setTimeout;
window.setTimeout = function(fn, delay) {
  window.__setTimeoutCalls.push({ delay: delay, time: Date.now() });
  return window.__setTimeoutOrig.call(this, fn, delay);
};
window.__setTimeoutFireCount = 0;
const origClear = window.clearTimeout;
window.clearTimeout = function(id) {
  window.__setTimeoutFireCount = (window.__setTimeoutFireCount || 0) - 1;
  return origClear.call(this, id);
};
console.log('>>> MONITOR INSTALLED v2 <<<');
""")
        page = ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.wait_for_timeout(500)
        page.evaluate(INIT)

        nav_start = page.evaluate('() => Date.now()')
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)

        # 等 25s
        for sec in [3, 5, 10, 15, 20, 25]:
            page.wait_for_timeout((sec - (sec - 5 if sec > 5 else 0)) * 1000)
            # 累计 wait 实际是 sec*1000,这里让我简化
            pass

        # 重新更简单：累计 wait
        page.wait_for_timeout(25000)

        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    setTimeoutCount: (window.__setTimeoutCalls || []).length,
    lastTen: (window.__setTimeoutCalls || []).slice(-10).map(c => ({ delay: c.delay, at: c.time - window.__navStart })),
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    errorContainerVisible: !!root?.querySelector('.error-container'),
    profileContentVisible: !!root?.querySelector('.profile-content'),
    innerText: root?.innerText?.substring(0, 200) ?? null
  };
}
""")
        print('=== 25s 后 ===')
        print(result)

        print('\n=== console logs ===')
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:500]}")

        browser.close()


run()