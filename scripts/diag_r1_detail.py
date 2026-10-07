# -*- coding: utf-8 -*-
"""R-01 增强诊断: 截图 + 检查所有可能的元素"""
import asyncio, os, json
from playwright.async_api import async_playwright

OUT = r'I:\iMato\screenshots\ux-session-20261006-5'
os.makedirs(OUT, exist_ok=True)

USER_DATA = {'id': 1, 'username': 'diag_r1', 'nickname': 'DiagR1', 'email': 'diag@test.com', 'orgId': 1, 'role': 'student'}
INIT = f"""
window.localStorage.setItem('user_data', JSON.stringify({json.dumps(USER_DATA)}));
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=r'C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe')
        ctx = await browser.new_context(viewport={'width': 1366, 'height': 900}, locale='zh-CN')
        await ctx.add_init_script(INIT)
        page = await ctx.new_page()
        page.on('console', lambda m: print(f'  [console-{m.type}] {m.text[:300]}'))
        page.on('pageerror', lambda e: print(f'  [pageerror] {e}'))

        # 拦截所有 /api/v1 请求 → 502
        async def mock_all(route, req):
            await route.fulfill(status=502, content_type='application/json', body='{}')
        await page.route('**/api/v1/**', mock_all)

        await page.goto('http://localhost:8080/user/growth-trajectory', wait_until='domcontentloaded')

        await asyncio.sleep(10)
        # 取完整 URL 和 page title
        url = page.url
        title = await page.title()
        print(f'URL: {url}')
        print(f'Title: {title}')

        # 找页面所有 mat-icon
        icons = await page.locator('mat-icon').all_text_contents()
        print(f'mat-icons ({len(icons)}): {icons}')

        # 检查各种状态
        for sel in ['app-growth-trajectory', '.growth-page', '.page-header', '.loading-state', '.error-state', '.fallback-banner', 'h1', 'p']:
            n = await page.locator(sel).count()
            if n > 0:
                txt = await page.locator(sel).first.inner_text() if await page.locator(sel).first.count() > 0 else ''
                print(f'  [{sel}] count={n} first_text="{txt[:80]}"')

        page_html = await page.content()
        print(f'\nPage HTML length: {len(page_html)}')

        # 检查关键字符串
        for kw in ['成长轨迹', '演示数据', 'cloud_off', 'fallback-banner', 'growth-trajectory']:
            cnt = page_html.count(kw)
            print(f'DOM 中 "{kw}" 出现 {cnt} 次')
            if cnt > 0 and kw in ['演示数据', '成长轨迹']:
                idx = page_html.find(kw)
                print(f'  上下文: {page_html[max(0,idx-50):idx+200]}')

        await page.screenshot(path=os.path.join(OUT, 'diag-r1-detail.png'), full_page=True)
        await browser.close()

asyncio.run(main())
