#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v21：通过强制 CD 测试 view 能否更新"""
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

        # 1. 找到 Angular 的 ng debug API
        result = page.evaluate("""
() => {
  // 找 mat-spinner 元素，看是否停止动画
  const spinner = document.querySelector('mat-spinner');
  const spinnerHTML = spinner?.outerHTML?.substring(0, 500) ?? null;

  // 找所有的 mat-progress-spinner
  const allSpinners = document.querySelectorAll('mat-spinner');
  const spinnersInfo = Array.from(allSpinners).map((s, i) => ({
    index: i,
    tag: s.tagName,
    classes: s.className.substring(0, 200),
    diameter: s.getAttribute('diameter'),
    isAnimating: !!s.querySelector('.mdc-circular-progress')
  }));

  // 查看 user-profile 内容 (找 form elements 或 buttons)
  const allButtons = document.querySelectorAll('app-user-profile button');
  const allInputs = document.querySelectorAll('app-user-profile input');
  const allMatCards = document.querySelectorAll('app-user-profile mat-card');

  return {
    spinnerHTML,
    spinnersInfo,
    buttonsCount: allButtons.length,
    inputsCount: allInputs.length,
    cardsCount: allMatCards.length,
    bodyText: document.body.innerText.substring(0, 300)
  };
}
""")
        print('=== 详细状态 ===')
        print(result)

        # Console logs
        print('\n=== console logs ===')
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:500]}")

        browser.close()


run()