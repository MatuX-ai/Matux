#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-E verification：验证 /digital-twin-lab 页面正常显示 + 离线 fallback 生效
测试目标：
1. 页面能正常加载（loading → error/lab）
2. WebSocket 连接失败时 offline banner 在 global-connection-bar 中显示
3. 状态文本正确
4. 重连按钮可见且可点击
"""
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

        console_logs = []
        page.on('console', lambda m: console_logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: console_logs.append({'type': 'pageerror', 'text': str(e)}))

        # 1. 登录页 + 设置 token
        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        # 2. 导航到 /digital-twin-lab
        print('\n=== 测试 /digital-twin-lab ===')
        page.goto('http://127.0.0.1:8080/digital-twin-lab', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)

        # 检查组件是否渲染完成（loading 应消失，显示 error + global-connection-bar）
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-digital-twin-lab');
  if (!root) return { hasComponent: false };
  const loading = root.querySelector('.loading-container');
  const error = root.querySelector('.error-container');
  const labContainer = root.querySelector('.lab-container');
  const globalBar = root.querySelector('.global-connection-bar');
  const connectionStatus = root.querySelector('.connection-status');
  return {
    hasComponent: true,
    loadingVisible: !!loading,
    errorVisible: !!error,
    errorText: error ? error.innerText.substring(0, 100) : null,
    labContainerVisible: !!labContainer,
    globalBarVisible: !!globalBar,
    connectionStatusVisible: !!connectionStatus,
    statusText: connectionStatus ? connectionStatus.innerText.substring(0, 50) : null,
  };
}
""")
        print(f'  3s 时: {result}')

        # 3. 等待 WebSocket 重试耗尽
        print('\n=== 等待 WebSocket 重试耗尽（最多 50s）===')
        for i in range(20):
            page.wait_for_timeout(2500)
            state = page.evaluate("""
() => {
  const root = document.querySelector('app-digital-twin-lab');
  if (!root) return null;
  const banner = root.querySelector('.offline-banner');
  const reconnect = root.querySelector('.reconnect-btn');
  const statusSpan = document.querySelector('.connection-status span');
  return {
    bannerVisible: !!banner,
    bannerText: banner ? banner.innerText.substring(0, 200) : null,
    reconnectVisible: !!reconnect,
    statusText: statusSpan ? statusSpan.innerText : null,
  };
}
""")
            elapsed_s = (i + 1) * 2.5
            print(f'  {elapsed_s:.1f}s: banner={state["bannerVisible"]}, status="{state["statusText"]}", reconnect={state["reconnectVisible"]}')
            if state['bannerVisible']:
                print(f'  ✓ Offline banner 已显示: {state["bannerText"][:120]}')
                break
        else:
            print(f'  ⚠ 50s 内 offline banner 仍未显示')

        # 4. 测试重连按钮可点击
        print('\n=== 测试重连按钮 ===')
        try:
            page.click('.reconnect-btn', timeout=3000)
            print('  ✓ 重连按钮可点击')
            page.wait_for_timeout(1500)
            state2 = page.evaluate("""
() => {
  const statusSpan = document.querySelector('.connection-status span');
  return { statusText: statusSpan ? statusSpan.innerText : null };
}
""")
            print(f'  点击后状态: {state2}')
        except Exception as e:
            print(f'  ✗ 重连按钮点击失败: {e}')

        # 5. 显示错误摘要
        print('\n=== 关键 console logs ===')
        keywords = ['websocket', 'WebSocket', '离线', '连接', 'failed', 'offline']
        seen = set()
        for log in console_logs:
            text = log.get('text', '')
            if any(k.lower() in text.lower() for k in keywords):
                if log['type'] in ('pageerror', 'error'):
                    key = text[:80]
                    if key not in seen:
                        seen.add(key)
                        print(f"  [{log['type']}] {text[:200]}")

        # 总结
        print('\n=== 总结 ===')
        has_global_bar = result['globalBarVisible']
        has_status = result['connectionStatusVisible']
        has_banner = state['bannerVisible']
        has_reconnect = state['reconnectVisible']
        print(f'  global-connection-bar 显示: {has_global_bar}')
        print(f'  connection-status 显示: {has_status}')
        print(f'  offline-banner 显示: {has_banner}')
        print(f'  reconnect 按钮显示: {has_reconnect}')
        if has_banner and has_reconnect:
            print('  ✅ P4-E 验证通过')
        else:
            print('  ⚠ P4-E 部分验证失败')

        browser.close()


run()
