/**
 * 通知系统模块
 * @module ui/notification
 *
 * 提供原生和内置通知功能
 */

const { Notification, nativeImage } = require('electron');

// 通知配置
const NOTIFICATION_CONFIG = {
  defaultDuration: 5000,  // 默认显示时长（毫秒）
  maxQueueSize: 5,        // 最大队列大小
};

// 通知队列
let notificationQueue = [];
let notificationCounter = 0;

/**
 * 显示通知
 * @param {string} title 通知标题
 * @param {string} body 通知内容
 * @param {string} category 通知类别：'info' | 'success' | 'warning' | 'error' | 'update'
 * @param {BrowserWindow} parentWindow 父窗口（可选）
 */
function showNotification(title, body, category = 'info', parentWindow = null) {
  if (!Notification.isSupported()) {
    console.warn('[WARN] 系统不支持通知');
    return null;
  }

  // 限制队列大小
  if (notificationQueue.length >= NOTIFICATION_CONFIG.maxQueueSize) {
    const oldNotification = notificationQueue.shift();
    if (oldNotification && !oldNotification.isDestroyed()) {
      oldNotification.close();
    }
  }

  const notificationId = ++notificationCounter;

  // 根据类别设置图标和声音
  const config = getNotificationConfig(category);

  const notification = new Notification({
    title,
    body,
    silent: config.silent,
    urgency: config.urgency,
    timeoutType: 'default',
  });

  notification.on('click', () => {
    console.log(`[NOTIFICATION] 点击通知 #${notificationId}: ${title}`);
    // 如果有父窗口，获取焦点
    if (parentWindow && !parentWindow.isDestroyed()) {
      parentWindow.show();
      parentWindow.focus();
    }
  });

  notification.on('close', () => {
    const index = notificationQueue.indexOf(notification);
    if (index > -1) {
      notificationQueue.splice(index, 1);
    }
  });

  notificationQueue.push(notification);
  notification.show();

  return notification;
}

/**
 * 获取通知配置
 * @param {string} category 通知类别
 * @returns {object} 通知配置
 */
function getNotificationConfig(category) {
  const configs = {
    info: {
      silent: false,
      urgency: 'normal',
    },
    success: {
      silent: false,
      urgency: 'low',
    },
    warning: {
      silent: false,
      urgency: 'normal',
    },
    error: {
      silent: false,
      urgency: 'critical',
    },
    update: {
      silent: false,
      urgency: 'normal',
    },
  };

  return configs[category] || configs.info;
}

/**
 * 清除所有通知
 */
function clearAllNotifications() {
  for (const notification of notificationQueue) {
    if (!notification.isDestroyed()) {
      notification.close();
    }
  }
  notificationQueue = [];
}

/**
 * 获取当前通知队列大小
 * @returns {number} 队列大小
 */
function getQueueSize() {
  return notificationQueue.length;
}

/**
 * 创建进度通知（用于长时间操作）
 * @param {string} title 标题
 * @param {string} body 初始内容
 * @param {number} total 总进度
 * @returns {object} 进度通知控制器
 */
function createProgressNotification(title, body, total = 100) {
  let currentProgress = 0;

  const notification = new Notification({
    title,
    body,
    silent: true,
  });

  const controller = {
    update(progress, message = '') {
      currentProgress = Math.min(Math.max(progress, 0), total);
      const percent = Math.round((currentProgress / total) * 100);
      notification.body = message || `进度: ${percent}%`;

      if (percent >= 100) {
        controller.complete('完成');
      }
    },

    complete(message = '完成') {
      notification.body = message;
      notification.show();
      setTimeout(() => notification.close(), 3000);
    },

    error(message = '发生错误') {
      notification.body = message;
      notification.urgency = 'critical';
      notification.show();
    },

    close() {
      if (!notification.isDestroyed()) {
        notification.close();
      }
    },
  };

  notification.show();
  return controller;
}

module.exports = {
  showNotification,
  clearAllNotifications,
  getQueueSize,
  createProgressNotification,
  Notification,
};
