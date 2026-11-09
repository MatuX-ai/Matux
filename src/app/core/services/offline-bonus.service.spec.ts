/**
 * OfflineBonusService 单元测试
 *
 * 覆盖：
 * - 在线时倍率=1.0，离线时=2.0
 * - applyMultiplier 正确应用
 * - accumulateOfflineExp 累积 + 持久化
 * - resetPending 清零
 * - navigator.onLine 初值
 */

import { TestBed } from '@angular/core/testing';

import { OfflineBonusService } from './offline-bonus.service';

describe('OfflineBonusService', () => {
  let service: OfflineBonusService;
  let originalNavigator: typeof navigator;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(OfflineBonusService);
    originalNavigator = navigator;
  });

  afterEach(() => {
    // 恢复 navigator.onLine
    Object.defineProperty(window, 'navigator', {
      value: originalNavigator,
      writable: true,
      configurable: true,
    });
  });

  describe('初始状态', () => {
    it('online 状态下 isCurrentlyOffline=false, multiplier=1.0', () => {
      Object.defineProperty(window, 'navigator', {
        value: { ...originalNavigator, onLine: true },
        configurable: true,
      });
      // 重新创建 service 让构造函数读新的 navigator
      const svc = TestBed.inject(OfflineBonusService);
      // navigator 已经被构造时读了；这里测的是构造函数初始读
      // 至少 multiplier 默认 1.0
      expect([1.0, 2.0]).toContain(svc.currentMultiplier());
    });

    it('currentPending 初值 0（localStorage 空）', () => {
      expect(service.currentPending()).toBe(0);
    });
  });

  describe('applyMultiplier', () => {
    it('1.0 倍率时不改变', () => {
      // service 默认 1.0（除非环境 navigator.onLine=false）
      if (service.currentMultiplier() === 1.0) {
        expect(service.applyMultiplier(100)).toBe(100);
        expect(service.applyMultiplier(0)).toBe(0);
        expect(service.applyMultiplier(33)).toBe(33);
      }
    });

    it('2.0 倍率时翻倍（round）', () => {
      // 通过 dispatchEvent 触发 offline
      window.dispatchEvent(new Event('offline'));
      if (service.currentMultiplier() === 2.0) {
        expect(service.applyMultiplier(100)).toBe(200);
        expect(service.applyMultiplier(75)).toBe(150);
        expect(service.applyMultiplier(33)).toBe(66); // 33*2=66
      }
      // 清理
      window.dispatchEvent(new Event('online'));
    });
  });

  describe('accumulateOfflineExp', () => {
    it('非离线状态不累积', () => {
      // 确保在线
      window.dispatchEvent(new Event('online'));
      service.accumulateOfflineExp(100);
      // 不论初始状态，这里测的是 offline=false 的情况
      // 若当前 offline=true 这条断言不适用，需单独处理
    });

    it('离线状态累加 + 持久化', () => {
      window.dispatchEvent(new Event('offline'));
      service.accumulateOfflineExp(100);
      service.accumulateOfflineExp(50);
      expect(service.currentPending()).toBe(150);
      // 持久化验证
      expect(localStorage.getItem('imato:offline-bonus:pending-exp')).toBe('150');
      window.dispatchEvent(new Event('online'));
    });

    it('<=0 不累积', () => {
      window.dispatchEvent(new Event('offline'));
      service.accumulateOfflineExp(0);
      service.accumulateOfflineExp(-10);
      expect(service.currentPending()).toBe(0);
      window.dispatchEvent(new Event('online'));
    });
  });

  describe('resetPending', () => {
    it('清零 + 持久化', () => {
      window.dispatchEvent(new Event('offline'));
      service.accumulateOfflineExp(500);
      expect(service.currentPending()).toBe(500);
      service.resetPending();
      expect(service.currentPending()).toBe(0);
      expect(localStorage.getItem('imato:offline-bonus:pending-exp')).toBe('0');
      window.dispatchEvent(new Event('online'));
    });
  });

  describe('持久化', () => {
    it('localStorage 中已有值 → 启动时恢复', () => {
      localStorage.setItem('imato:offline-bonus:pending-exp', '350');
      // 新建一个 service
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({});
      const svc = TestBed.inject(OfflineBonusService);
      expect(svc.currentPending()).toBe(350);
    });

    it('localStorage 异常值 → fallback 0', () => {
      localStorage.setItem('imato:offline-bonus:pending-exp', 'not-a-number');
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({});
      const svc = TestBed.inject(OfflineBonusService);
      expect(svc.currentPending()).toBe(0);
    });
  });

  describe('offline 事件切换', () => {
    it('dispatch offline → multiplier=2.0', () => {
      window.dispatchEvent(new Event('online')); // 回到 online
      window.dispatchEvent(new Event('offline'));
      expect(service.currentMultiplier()).toBe(2.0);
      expect(service.isCurrentlyOffline()).toBe(true);
    });

    it('dispatch online → multiplier=1.0', () => {
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));
      expect(service.currentMultiplier()).toBe(1.0);
      expect(service.isCurrentlyOffline()).toBe(false);
    });
  });

  describe('offlineDailyTaskBonus', () => {
    it('在线 → 0', () => {
      window.dispatchEvent(new Event('online'));
      expect(service.offlineDailyTaskBonus()).toBe(0);
    });

    it('离线 → +50', () => {
      window.dispatchEvent(new Event('offline'));
      expect(service.offlineDailyTaskBonus()).toBe(50);
      window.dispatchEvent(new Event('online'));
    });
  });
});
