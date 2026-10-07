#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v19：在 navigation 前安装 setTimeout zone 监控"""
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

MONITOR = """
() => {
  window.__zoneLog = [];
  // Wait for Zone to load, then install monitor
  function installMonitor() {
    if (typeof Zone === 'undefined') {
      setTimeout(installMonitor, 10);
      return;
    }
    const origSetTimeout = window.setTimeout;
    window.setTimeout = function(fn, delay, ...args) {
      const callingZone = Zone.current?.name || 'unknown';
      const id = origSetTimeout.call(this, function() {
        const executionZone = Zone.current?.name || 'unknown';
        window.__zoneLog.push({ delay: delay, calledIn: callingZone, ranIn: executionZone });
        try {
          fn.apply(this, args);
        } catch (e) {
          console.error('[ST] error:', e);
        }
      }, delay, ...args);
      return id;
    };
    console.log('=== ZONE MONITOR installed ===');
  }
  installMonitor();
}
"""


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        ctx.add_init_script(MONITOR)
        page = ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(5000)

        # 读取 zone log
        zone_log = page.evaluate('() => window.__zoneLog || []')
        print(f'=== setTimeout zone log ({len(zone_log)} entries) ===')
        for entry in zone_log:
            print(f'  delay={entry["delay"]}ms calledIn={entry["calledIn"]} ranIn={entry["ranIn"]}')

        # 页面状态
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  return {
    loadingContainerVisible: !!root?.querySelector('.loading-container'),
    profileContentVisible: !!root?.querySelector('.profile-content')
  };
}
""")
        print(f'\n=== 5s 后页面状态 ===\n{result}')

        print('\n=== console logs ===')
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        browser.close()


run()