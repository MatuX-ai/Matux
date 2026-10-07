# -*- coding: utf-8 -*-
"""
深度诊断 R-02:
1) 强制 mock /api/v1/org/1/ai-edu/modules 返回 502
2) 监听 console 错误
3) 检查组件 state
"""
import asyncio, os, json
from playwright.async_api import async_playwright

OUT = r'I:\iMato\screenshots\ux-session-20261006-5'
os.makedirs(OUT, exist_ok=True)

USER_DATA = {'id': 1, 'username': 'diag_r2', 'nickname': 'DiagR2', 'email': 'diag@test.com', 'orgId': 1, 'role': 'student'}
INIT = f"""
window.localStorage.setItem('user_data', JSON.stringify({json.dumps(USER_DATA)}));
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=r'C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe')
        ctx = await browser.new_context(viewport={'width': 1366, 'height': 900}, locale='zh-CN')
        await ctx.add_init_script(INIT)
        page = await ctx.new_page()

        # 监听所有 console
        page.on('console', lambda m: print(f'  [console-{m.type}] {m.text[:300]}'))
        page.on('pageerror', lambda e: print(f'  [pageerror] {e}'))

        # 拦截 ai-edu/modules 强制返回 502
        async def mock_ai_edu(route, req):
            if 'ai-edu/modules' in req.url:
                await route.fulfill(
                    status=502,
                    content_type='application/json',
                    body=json.dumps({'error': 'backend proxy error'})
                )
            else:
                await route.continue_()
        await page.route('**/api/v1/org/*/ai-edu/modules', mock_ai_edu)

        await page.goto('http://localhost:8080/ai-edu', wait_until='domcontentloaded')

        # 等待 8 秒让 fallback 触发
        for t in [1, 3, 5, 7]:
            await asyncio.sleep(t - (t-1 if t==1 else 2))
            banner_top = await page.locator('.fallback-banner-top').count()
            banner_any = await page.locator('.fallback-banner').count()
            modules = await page.locator('.modules-grid .module-card').count()
            print(f'[T+{t}s] banner_top={banner_top} banner_any={banner_any} modules={modules}')

        # 完整 DOM 检查
        page_html = await page.content()
        for kw in ['fallback-banner-top', 'cloud_off', '后端不可达', '后端响应超时']:
            cnt = page_html.count(kw)
            print(f'\nDOM 中 "{kw}" 出现 {cnt} 次')

        await page.screenshot(path=os.path.join(OUT, 'diag-r2-forced-502.png'), full_page=True)
        await browser.close()

asyncio.run(main())
