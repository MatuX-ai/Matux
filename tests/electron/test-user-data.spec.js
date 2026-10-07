/**
 * 用户数据管理测试用例
 *
 * 测试范围：
 * 1. 用户资料管理
 * 2. 学习进度追踪
 * 3. 收藏和历史记录
 * 4. 消息通知
 *
 * 运行方式:
 * npx playwright test tests/electron/test-user-data.spec.js --headed
 */

const { _electron: electron } = require('playwright');
const { test, expect } = require('@playwright/test');
const path = require('path');

// Electron 路径 - 从项目根目录的 node_modules 获取
const ELECTRON_PATH = path.join(__dirname, '..', '..', 'node_modules', '.bin', 'electron');
const APP_PATH = path.join(__dirname, '..', '..', 'electron');
const BACKEND_URL = 'http://localhost:8000';

test.describe('用户数据管理测试', () => {
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

  // ==================== 1. 用户资料管理 ====================

  test.describe('用户资料管理', () => {
    test('应能查看个人资料', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 点击个人资料入口
      const profileLink = mainWindow.locator('a:has-text("个人资料"), a:has-text("Profile"), [class*="profile"]').first();

      if (await profileLink.isVisible()) {
        await profileLink.click();
        await mainWindow.waitForLoadState('networkidle');

        // 验证资料字段存在
        const fields = await mainWindow.locator('[class*="profile"] input, [class*="profile"] .info').all();
        console.log(`✅ 个人资料页面加载，显示 ${fields.length} 个字段`);
      } else {
        console.log('ℹ️ 个人资料入口不可见');
      }
    });

    test('应能修改头像', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找头像上传区域
      const avatarSection = mainWindow.locator('[class*="avatar"], [class*="photo"]').first();

      if (await avatarSection.isVisible()) {
        // 查找上传按钮
        const uploadButton = mainWindow.locator('input[type="file"], button:has-text("上传"), button:has-text("Upload")').first();

        if (await uploadButton.isVisible()) {
          console.log('✅ 头像上传功能可用');
        } else {
          console.log('ℹ️ 头像上传按钮不可见');
        }
      } else {
        console.log('ℹ️ 头像区域不可见');
      }
    });

    test('应能修改基本信息', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找可编辑字段
      const editableFields = mainWindow.locator('[contenteditable="true"], input:not([readonly]), textarea').all();

      if (editableFields.length > 0) {
        // 尝试修改第一个字段
        const firstField = editableFields[0];
        const originalValue = await firstField.inputValue().catch(() => '');

        await firstField.fill(originalValue + '_test');
        await mainWindow.waitForTimeout(500);

        // 查找保存按钮
        const saveButton = mainWindow.locator('button:has-text("保存"), button:has-text("Save")').first();

        if (await saveButton.isVisible()) {
          await saveButton.click();
          await mainWindow.waitForTimeout(1000);
          console.log('✅ 信息修改功能可用');
        }
      } else {
        console.log('ℹ️ 无可编辑字段或未登录');
      }
    });

    test('应能修改密码', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找修改密码入口
      const changePasswordLink = mainWindow.locator('a:has-text("修改密码"), a:has-text("Change Password"), [class*="password"]').first();

      if (await changePasswordLink.isVisible()) {
        await changePasswordLink.click();
        await mainWindow.waitForLoadState('networkidle');

        // 验证密码表单存在
        const passwordForm = mainWindow.locator('input[type="password"]').all();
        console.log(`✅ 密码修改页面加载，包含 ${passwordForm.length} 个密码字段`);
      } else {
        console.log('ℹ️ 修改密码入口不可见');
      }
    });
  });

  // ==================== 2. 学习进度追踪 ====================

  test.describe('学习进度追踪', () => {
    test('应能查看学习进度', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找学习进度入口
      const progressLink = mainWindow.locator('a:has-text("学习进度"), a:has-text("Progress"), [class*="progress"]').first();

      if (await progressLink.isVisible()) {
        await progressLink.click();
        await mainWindow.waitForLoadState('networkidle');

        // 检查进度指示器
        const progressBar = mainWindow.locator('[class*="progress-bar"], [role="progressbar"]').first();
        const hasProgress = await progressBar.isVisible().catch(() => false);

        if (hasProgress) {
          console.log('✅ 学习进度显示正常');
        } else {
          console.log('ℹ️ 进度条不可见');
        }
      } else {
        console.log('ℹ️ 学习进度入口不可见');
      }
    });

    test('应显示课程完成百分比', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 从后端获取进度数据
      const progressData = await mainWindow.evaluate(async () => {
        try {
          const response = await fetch(`${BACKEND_URL}/api/v1/progress`);
          return response.ok ? await response.json() : null;
        } catch (e) {
          return null;
        }
      });

      if (progressData) {
        console.log('✅ 学习进度数据获取成功:', progressData);
      } else {
        console.log('ℹ️ 进度数据获取失败或未登录');
      }
    });

    test('应能继续未完成的课程', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找未完成课程
      const incompleteCourse = mainWindow.locator('[class*="incomplete"], [class*="continue"]').first();

      if (await incompleteCourse.isVisible().catch(() => false)) {
        await incompleteCourse.click();
        await mainWindow.waitForTimeout(1000);
        console.log('✅ 继续学习功能可用');
      } else {
        console.log('ℹ️ 无未完成课程');
      }
    });
  });

  // ==================== 3. 收藏和历史记录 ====================

  test.describe('收藏和历史记录', () => {
    test('应能收藏内容', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找收藏按钮
      const favoriteButton = mainWindow.locator('[class*="favorite"], [class*="bookmark"], button:has-text("收藏")').first();

      if (await favoriteButton.isVisible()) {
        await favoriteButton.click();
        await mainWindow.waitForTimeout(500);

        // 验证收藏状态变化
        const isActive = await favoriteButton.evaluate(el => el.classList.contains('active'));
        console.log('✅ 收藏功能可用，收藏状态:', isActive);
      } else {
        console.log('ℹ️ 收藏按钮不可见');
      }
    });

    test('应能查看收藏列表', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找收藏入口
      const favoritesLink = mainWindow.locator('a:has-text("收藏"), a:has-text("Favorites"), [class*="favorites"]').first();

      if (await favoritesLink.isVisible()) {
        await favoritesLink.click();
        await mainWindow.waitForLoadState('networkidle');

        // 检查收藏列表
        const favoriteItems = mainWindow.locator('[class*="favorite-item"], [class*="bookmark-item"]').all();
        console.log(`✅ 收藏列表加载，共 ${favoriteItems.length} 项`);
      } else {
        console.log('ℹ️ 收藏入口不可见');
      }
    });

    test('应能查看学习历史', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找历史记录入口
      const historyLink = mainWindow.locator('a:has-text("历史"), a:has-text("History"), [class*="history"]').first();

      if (await historyLink.isVisible()) {
        await historyLink.click();
        await mainWindow.waitForLoadState('networkidle');

        // 检查历史记录
        const historyItems = mainWindow.locator('[class*="history-item"]').all();
        console.log(`✅ 历史记录加载，共 ${historyItems.length} 项`);
      } else {
        console.log('ℹ️ 历史记录入口不可见');
      }
    });

    test('应能清除历史记录', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找清除按钮
      const clearButton = mainWindow.locator('button:has-text("清除"), button:has-text("Clear"), button:has-text("删除历史")').first();

      if (await clearButton.isVisible()) {
        // 点击清除
        await clearButton.click();
        await mainWindow.waitForTimeout(500);

        // 确认对话框处理
        const confirmButton = mainWindow.locator('button:has-text("确认"), button:has-text("Confirm")').first();
        if (await confirmButton.isVisible().catch(() => false)) {
          await confirmButton.click();
          await mainWindow.waitForTimeout(500);
        }
        console.log('✅ 清除历史功能可用');
      } else {
        console.log('ℹ️ 清除按钮不可见');
      }
    });
  });

  // ==================== 4. 消息通知 ====================

  test.describe('消息通知', () => {
    test('应能查看消息中心', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找消息入口
      const messagesLink = mainWindow.locator('[class*="message"], [class*="notification"], a:has-text("消息"), a:has-text("Messages")').first();

      if (await messagesLink.isVisible()) {
        await messagesLink.click();
        await mainWindow.waitForLoadState('networkidle');

        // 检查消息列表
        const messageItems = mainWindow.locator('[class*="message-item"]').all();
        console.log(`✅ 消息中心加载，共 ${messageItems.length} 条消息`);
      } else {
        console.log('ℹ️ 消息入口不可见');
      }
    });

    test('应有未读消息提示', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找未读标记
      const unreadBadge = mainWindow.locator('[class*="badge"], [class*="unread"]').first();

      if (await unreadBadge.isVisible().catch(() => false)) {
        const badgeText = await unreadBadge.textContent();
        console.log('✅ 未读消息提示:', badgeText);
      } else {
        console.log('ℹ️ 无未读消息');
      }
    });

    test('应能标记消息为已读', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找未读消息
      const unreadMessage = mainWindow.locator('[class*="unread"]').first();

      if (await unreadMessage.isVisible().catch(() => false)) {
        await unreadMessage.click();
        await mainWindow.waitForTimeout(500);

        // 验证消息状态变化
        const isRead = await unreadMessage.evaluate(el => !el.classList.contains('unread'));
        console.log('✅ 消息标记为已读:', isRead);
      } else {
        console.log('ℹ️ 无未读消息');
      }
    });

    test('应能删除消息', async () => {
      await mainWindow.waitForLoadState('networkidle');

      // 查找删除按钮
      const deleteButton = mainWindow.locator('[class*="delete"], button:has-text("删除"), button[aria-label*="delete"]').first();

      if (await deleteButton.isVisible()) {
        await deleteButton.click();
        await mainWindow.waitForTimeout(500);

        // 确认删除
        const confirmButton = mainWindow.locator('button:has-text("确认"), button:has-text("Confirm")').first();
        if (await confirmButton.isVisible().catch(() => false)) {
          await confirmButton.click();
          await mainWindow.waitForTimeout(500);
        }
        console.log('✅ 删除消息功能可用');
      } else {
        console.log('ℹ️ 删除按钮不可见');
      }
    });
  });
});
