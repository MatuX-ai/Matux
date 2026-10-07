# -*- coding: utf-8 -*-
"""
诊断 R-02: 直接探测 /ai-edu 页面运行时 error / modules / banner DOM
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
        page.on('console', lambda m: print(f'  [console-{m.type}] {m.text[:200]}'))

        # 拦截 /api/v1/org/1/ai-edu/modules 网络请求
        ai_edu_calls = []
        async def on_route(route, req):
            if 'ai-edu/modules' in req.url:
                ai_edu_calls.append({'method': req.method, 'url': req.url, 'time': asyncio.get_event_loop().time()})
            await route.continue_()
        await page.route('**/api/v1/**', on_route)

        await page.goto('http://localhost:8080/ai-edu', wait_until='domcontentloaded')
        print(f'[T+0] 页面加载完成')

        # 每秒检查一次
        for t in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            await asyncio.sleep(1)
            # 检查 banner DOM
            banner_top = await page.locator('.fallback-banner-top').count()
            banner_any = await page.locator('.fallback-banner').count()
            modules_grid = await page.locator('.modules-grid .module-card').count()
            skeleton = await page.locator('.module-skeleton').count()
            loading = await page.locator('.loading-badge').count()

            # 取页面所有文本看有没有错误信息
            page_text = await page.inner_text('body')

            print(f'[T+{t}s] banner_top={banner_top} banner_any={banner_any} modules={modules_grid} skeleton={skeleton} loading_badge={loading}')

        await page.screenshot(path=os.path.join(OUT, 'diag-r2-final.png'), full_page=True)

        print(f'\n[ai-edu/modules 网络调用次数]: {len(ai_edu_calls)}')
        for c in ai_edu_calls:
            print(f'  {c}')

        # 完整 DOM body 取样 (找 error 字符串)
        page_html = await page.content()
        for keyword in ['后端不可达', '后端响应超时', '本地推荐', 'fallback-banner-top', 'cloud_off']:
            idx = page_html.find(keyword)
            if idx >= 0:
                print(f'\n[DOM 找到 {keyword}]: 位置 {idx}')
                print(f'  上下文: {page_html[max(0,idx-80):idx+200]}')
            else:
                print(f'\n[DOM 找不到 {keyword}]')

        await browser.close()

asyncio.run(main())
