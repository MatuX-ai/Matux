#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v14：检查页面是否有多个 user-profile 元素"""
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
""")
        page = ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(5000)

        # 详细检查 DOM 结构
        result = page.evaluate("""
() => {
  const allUserProfiles = document.querySelectorAll('app-user-profile');
  const allLoadingContainers = document.querySelectorAll('.loading-container');
  const allProfileContents = document.querySelectorAll('.profile-content');
  const allErrorContainers = document.querySelectorAll('.error-container');

  return {
    userProfileCount: allUserProfiles.length,
    loadingContainerCount: allLoadingContainers.length,
    profileContentCount: allProfileContents.length,
    errorContainerCount: allErrorContainers.length,
    userProfileInfo: Array.from(allUserProfiles).map((el, i) => ({
      index: i,
      classList: Array.from(el.classList),
      innerHTML: el.innerHTML.substring(0, 300),
      parentTag: el.parentElement?.tagName,
      parentClass: el.parentElement?.className,
      visible: el.offsetParent !== null
    })),
    bodyClasses: document.body.className,
    appRoot: document.querySelector('app-root')?.outerHTML?.substring(0, 500)
  };
}
""")
        print('=== DOM 结构 ===')
        print(result)

        # 详细 console logs
        print('\n=== console logs (最后 30 条) ===')
        for log in logs[-30:]:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:500]}")

        browser.close()


run()