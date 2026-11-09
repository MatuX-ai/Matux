/**
 * 【P3-A-2】GamificationEventBusService 单元测试
 *
 * 覆盖：
 * - publish() 分派到对应 Subject
 * - onAchievementUnlocked / onNodeStatusUpdated / onSetCompleted 订阅
 * - onAnyEvent 通用订阅
 * - onEvent(type) 按类型过滤
 * - 待重放队列（getPendingEvents / clearPending）
 * - 多订阅者独立接收
 * - 未知事件类型不抛错
 */

import {
  GamificationEventBusService,
  GamificationEventType,
} from './gamification-event-bus.service';

describe('GamificationEventBusService', () => {
  let service: GamificationEventBusService;

  beforeEach(() => {
    TestBedResetIfNeeded();
    service = new GamificationEventBusService();
  });

  afterEach(() => {
    service.ngOnDestroy();
  });

  // ================ publish() 分派 ================

  describe('publish', () => {
    it('应将 achievement_unlocked 事件推送到 achievementUnlocked$', (done) => {
      service.onAchievementUnlocked().subscribe((event) => {
        expect(event.achievement_id).toBe('ach-1');
        expect(event.name).toBe('测试徽章');
        expect(event.rarity).toBe('rare');
        done();
      });

      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: {
          achievement_id: 'ach-1',
          name: '测试徽章',
          rarity: 'rare',
          points: 50,
        },
        timestamp: '2026-10-09T10:00:00Z',
      });
    });

    it('应将 node_status_updated 事件推送到 nodeStatusUpdated$', (done) => {
      service.onNodeStatusUpdated().subscribe((event) => {
        expect(event.skill_id).toBe('py-loop');
        expect(event.new_status).toBe('mastered');
        done();
      });

      service.publish({
        type: GamificationEventType.NODE_STATUS_UPDATED,
        data: {
          skill_id: 'py-loop',
          old_status: 'in_progress',
          new_status: 'mastered',
          progress: 1,
        },
      });
    });

    it('应将 set_completed 事件推送到 setCompleted$', (done) => {
      service.onSetCompleted().subscribe((event) => {
        expect(event.set_id).toBe('set-python-master');
        expect(event.set_name).toBe('Python 大师');
        done();
      });

      service.publish({
        type: GamificationEventType.SET_COMPLETED,
        data: {
          set_id: 'set-python-master',
          set_name: 'Python 大师',
        },
      });
    });

    it('未知类型事件不应抛错（仅推送到 allEvents$）', () => {
      service.onAnyEvent().subscribe((event) => {
        expect(event.type).toBe('unknown_type');
      });

      expect(() =>
        service.publish({
          type: 'unknown_type' as GamificationEventType,
          data: { foo: 'bar' },
        }),
      ).not.toThrow();
    });
  });

  // ================ onAnyEvent ================

  describe('onAnyEvent', () => {
    it('应接收所有事件类型（通用流）', () => {
      const events: unknown[] = [];
      service.onAnyEvent().subscribe((e) => events.push(e));

      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });
      service.publish({
        type: GamificationEventType.NODE_STATUS_UPDATED,
        data: { skill_id: 's1', new_status: 'in_progress' },
      });
      service.publish({
        type: GamificationEventType.SET_COMPLETED,
        data: { set_id: 's', name: 'p' },
      });

      expect(events.length).toBe(3);
    });
  });

  // ================ onEvent(type) 过滤 ================

  describe('onEvent(type)', () => {
    it('应只推送指定类型的事件', () => {
      const received: unknown[] = [];
      service
        .onEvent(GamificationEventType.ACHIEVEMENT_UNLOCKED)
        .subscribe((e) => received.push(e.data));

      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });
      service.publish({
        type: GamificationEventType.NODE_STATUS_UPDATED,
        data: { skill_id: 's1', new_status: 'in_progress' },
      });

      expect(received.length).toBe(1);
    });
  });

  // ================ 多订阅者 ================

  describe('多订阅者', () => {
    it('多个订阅者应独立接收事件', () => {
      const r1: unknown[] = [];
      const r2: unknown[] = [];

      service.onAchievementUnlocked().subscribe((e) => r1.push(e));
      service.onAchievementUnlocked().subscribe((e) => r2.push(e));

      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });

      expect(r1.length).toBe(1);
      expect(r2.length).toBe(1);
    });
  });

  // ================ 待重放队列 ================

  describe('待重放队列', () => {
    it('getPendingEvents 应返回所有已发布的事件', () => {
      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });
      service.publish({
        type: GamificationEventType.NODE_STATUS_UPDATED,
        data: { skill_id: 's1', new_status: 'in_progress' },
      });

      const pending = service.getPendingEvents();
      expect(pending.length).toBe(2);
    });

    it('getPendingEvents(type) 应按类型过滤', () => {
      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });
      service.publish({
        type: GamificationEventType.NODE_STATUS_UPDATED,
        data: { skill_id: 's1', new_status: 'in_progress' },
      });

      const achEvents = service.getPendingEvents(
        GamificationEventType.ACHIEVEMENT_UNLOCKED,
      );
      expect(achEvents.length).toBe(1);
      expect(achEvents[0].type).toBe(GamificationEventType.ACHIEVEMENT_UNLOCKED);
    });

    it('clearPending 应清空队列', () => {
      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });
      service.clearPending();
      expect(service.getPendingEvents().length).toBe(0);
    });

    it('超出 MAX_PENDING 时应仅保留最后 N 个', () => {
      // MAX_PENDING = 50
      for (let i = 0; i < 60; i++) {
        service.publish({
          type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
          data: { achievement_id: `a${i}`, name: `A${i}`, rarity: 'common' },
        });
      }
      expect(service.getPendingEvents().length).toBe(50);
    });
  });

  // ================ ngOnDestroy ================

  describe('ngOnDestroy', () => {
    it('应完成所有 Subject（不再有值推送）', () => {
      const r1: unknown[] = [];
      const r2: unknown[] = [];

      service.onAchievementUnlocked().subscribe((e) => r1.push(e));
      service.onAnyEvent().subscribe((e) => r2.push(e));

      service.ngOnDestroy();

      service.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: { achievement_id: 'a1', name: 'A1', rarity: 'common' },
      });

      expect(r1.length).toBe(0);
      expect(r2.length).toBe(0);
    });
  });
});

// 辅助：Angular TestBed 未使用，但保留导入模式的一致性
function TestBedResetIfNeeded(): void {
  // no-op; 保留位置以便未来扩展为 TestBed.inject
}