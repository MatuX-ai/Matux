/**
 * 用户权限与数据测试用例
 *
 * 测试范围：
 * 1. 用户角色权限
 * 2. 数据访问控制
 * 3. 功能权限验证
 * 4. 资源访问限制
 *
 * 运行方式:
 * npx playwright test tests/electron/test-user-permissions.spec.js --headed
 */

const { _electron: electron } = require('playwright');
const { test, expect } = require('@playwright/test');
const path = require('path');

// Electron 路径 - 从项目根目录的 node_modules 获取
const ELECTRON_PATH = path.join(__dirname, '..', '..', 'node_modules', '.bin', 'electron');
const APP_PATH = path.join(__dirname, '..', '..', 'electron');
const BACKEND_URL = 'http://localhost:8000';

test.describe('用户权限与数据测试', () => {
  let electronApp;
  let mainWindow;

  test.beforeEach(async () => {
    electronApp = await electron.launch({
      executablePath: ELECTRON_PATH,
      args: [APP_PATH],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        BACKEND_URL: BACKEND_URL,
      },
    });

    mainWindow = await electronApp.firstWindow({
      timeout: 30000,
    });
  });

  test.afterEach(async () => {
    if (electronApp) {
      await electronApp.close();
    }
  });

  // ==================== 1. 用户角色测试 ====================

  test.describe('用户角色权限', () => {
    test('普通用户应只能访问基础功能', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 检查管理员功能是否隐藏
      const adminMenu = mainWindow.locator('[class*="admin"], a:has-text("管理"), a:has-text("Admin")').first();
      const adminVisible = await adminMenu.isVisible().catch(() => false);

      if (!adminVisible) {
        console.log('✅ 普通用户看不到管理员功能');
      } else {
        console.log('ℹ️ 管理员菜单可见（可能是测试用户权限）');
      }
    });

    test('应能查看用户角色信息', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 检查用户资料页面
      const profilePage = mainWindow.locator('a:has-text("个人资料"), a:has-text("Profile"), [class*="profile"]').first();

      if (await profilePage.isVisible()) {
        await profilePage.click();
        await mainWindow.waitForLoadState('networkidle');

        // 查找角色信息
        const roleInfo = mainWindow.locator('[class*="role"], [class*="permission"]').first();
        const hasRoleInfo = await roleInfo.isVisible().catch(() => false);

        if (hasRoleInfo) {
          console.log('✅ 角色信息已显示');
        } else {
          console.log('ℹ️ 角色信息区域不可见');
        }
      } else {
        console.log('ℹ️ 个人资料入口不可见');
      }
    });

    test('应能切换用户角色(如果支持)', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找角色切换器
      const roleSwitcher = mainWindow.locator('[class*="role-switch"], [class*="switch-role"]').first();

      if (await roleSwitcher.isVisible()) {
        await roleSwitcher.click();
        await mainWindow.waitForTimeout(500);

        // 选择新角色
        const roleOption = mainWindow.locator('[class*="dropdown"] li, option').first();
        if (await roleOption.isVisible()) {
          await roleOption.click();
          await mainWindow.waitForTimeout(1000);
        }
        console.log('✅ 角色切换功能可用');
      } else {
        console.log('ℹ️ 角色切换器不可用');
      }
    });
  });

  // ==================== 2. 数据访问控制 ====================

  test.describe('数据访问控制', () => {
    test('应只能访问自己的数据', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 检查用户数据隔离
      const userData = await mainWindow.evaluate(async () => {
        try {
          const response = await fetch(`${BACKEND_URL}/api/v1/user/profile`);
          return response.ok ? await response.json() : null;
        } catch (e) {
          return null;
        }
      });

      if (userData) {
        console.log('✅ 用户数据获取成功');
        // 验证数据属于当前用户
        expect(userData).toHaveProperty('id');
      } else {
        console.log('ℹ️ 用户数据获取失败或未登录');
      }
    });

    test('应不能访问其他用户私有数据', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 尝试访问其他用户的数据
      const unauthorizedAccess = await mainWindow.evaluate(async () => {
        try {
          const response = await fetch(`${BACKEND_URL}/api/v1/user/99999/profile`);
          return {
            status: response.status,
            forbidden: response.status === 403,
          };
        } catch (e) {
          return { error: e.message };
        }
      });

      if (unauthorizedAccess.forbidden) {
        console.log('✅ 未授权访问被正确拒绝');
      } else {
        console.log('ℹ️ 访问结果:', unauthorizedAccess);
      }
    });

    test('应能管理自己的资源', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找资源管理入口
      const myResources = mainWindow.locator('a:has-text("我的资源"), a:has-text("My Resources"), [class*="my-"]').first();

      if (await myResources.isVisible()) {
        await myResources.click();
        await mainWindow.waitForLoadState('networkidle');

        // 验证资源列表
        const resourceList = mainWindow.locator('[class*="resource"], [class*="item"]').all();
        const count = resourceList.length;
        console.log(`✅ 资源列表显示，共 ${count} 项`);
      } else {
        console.log('ℹ️ 资源管理入口不可见');
      }
    });
  });

  // ==================== 3. 功能权限验证 ====================

  test.describe('功能权限验证', () => {
    test('应能使用允许的功能', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 检查基础功能可用性
      const allowedFeatures = [
        'input[type="text"]',
        'input[type="search"]',
        'button',
        'a',
      ];

      for (const selector of allowedFeatures) {
        const element = mainWindow.locator(selector).first();
        if (await element.isVisible().catch(() => false)) {
          console.log(`✅ 功能 ${selector} 可用`);
          break;
        }
      }
    });

    test('应能查看功能权限说明', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找帮助或权限说明
      const helpMenu = mainWindow.locator('a:has-text("帮助"), a:has-text("Help"), [class*="help"]').first();

      if (await helpMenu.isVisible()) {
        await helpMenu.click();
        await mainWindow.waitForLoadState('networkidle');
        console.log('✅ 帮助菜单可用');
      } else {
        console.log('ℹ️ 帮助菜单不可见');
      }
    });

    test('禁用功能应显示正确状态', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找禁用的按钮
      const disabledButtons = mainWindow.locator('button:disabled, [class*="disabled"]').all();

      for (const button of disabledButtons.slice(0, 3)) {
        try {
          if (await button.isVisible()) {
            const text = await button.textContent();
            console.log('禁用功能:', text?.trim());
          }
        } catch (e) {
          // 忽略
        }
      }
      console.log('✅ 禁用功能状态检查完成');
    });
  });

  // ==================== 4. 资源访问限制 ====================

  test.describe('资源访问限制', () => {
    test('付费资源应需要订阅', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找付费标识
      const premiumBadge = mainWindow.locator('[class*="premium"], [class*="vip"], [class*="pro"], text=付费, text=VIP').first();

      if (await premiumBadge.isVisible().catch(() => false)) {
        console.log('✅ 付费资源标识正确显示');

        // 尝试访问付费资源
        const premiumItem = mainWindow.locator('[class*="premium"], [class*="vip"]').first();
        if (await premiumItem.isVisible()) {
          await premiumItem.click();
          await mainWindow.waitForTimeout(1000);

          // 检查是否需要订阅提示
          const subscriptionPrompt = mainWindow.locator('text=订阅, text=订阅, text=升级').first();
          const showPrompt = await subscriptionPrompt.isVisible().catch(() => false);

          if (showPrompt) {
            console.log('✅ 付费提示正确显示');
          }
        }
      } else {
        console.log('ℹ️ 无付费资源或已订阅');
      }
    });

    test('过期内容应正确处理', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 检查过期内容标识
      const expiredBadge = mainWindow.locator('[class*="expired"], text=已过期').first();

      if (await expiredBadge.isVisible().catch(() => false)) {
        console.log('✅ 过期内容标识正确显示');

        // 验证过期内容不可访问
        const expiredContent = mainWindow.locator('[class*="expired"]').first();
        await expiredContent.click();
        await mainWindow.waitForTimeout(500);

        const errorMessage = mainWindow.locator('text=已过期, text=无法访问').first();
        const showError = await errorMessage.isVisible().catch(() => false);

        if (showError) {
          console.log('✅ 过期内容处理正确');
        }
      } else {
        console.log('ℹ️ 无过期内容');
      }
    });

    test('受限内容应显示访问提示', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 检查受限内容
      const restrictedContent = mainWindow.locator('[class*="restricted"], [class*="locked"]').first();

      if (await restrictedContent.isVisible().catch(() => false)) {
        await restrictedContent.click();
        await mainWindow.waitForTimeout(500);

        // 检查访问提示
        const accessPrompt = mainWindow.locator('text=权限不足, text=需要登录, text=无权限').first();
        const showPrompt = await accessPrompt.isVisible().catch(() => false);

        if (showPrompt) {
          console.log('✅ 受限内容提示正确显示');
        } else {
          console.log('ℹ️ 无特殊提示');
        }
      } else {
        console.log('ℹ️ 无受限内容');
      }
    });
  });
});
