/**
 * 【P3-B】AiTeacherLiveService 单元测试
 *
 * 覆盖：
 * - 构造时自动订阅 gamification bus
 * - ingest() 去重（按 id）
 * - ingest() TTL 过期过滤
 * - ingest() 勿扰时段过滤
 * - ingest() 类型开关过滤
 * - markRead / dismiss / click 状态机
 * - applySettings() 切换 live settings
 * - setUserId() 注入当前用户
 * - replayFromServer() 批量回放
 * - window 桥接
 */

import { TestBed } from '@angular/core/testing';

import {
  AiTeacherLiveEvent,
  AiTeacherLiveSettings,
  DEFAULT_LIVE_SETTINGS,
} from '../models/ai-teacher.models';
import {
  GamificationEventBusService,
  GamificationEventType,
} from './gamification-event-bus.service';
import { AiTeacherLiveService } from './ai-teacher-live.service';

function makeEvent(
  overrides: Partial<AiTeacherLiveEvent> = {}
): AiTeacherLiveEvent {
  return {
    id: overrides.id ?? `evt_${Math.random().toString(36).slice(2)}`,
    type: overrides.type ?? GamificationEventType.AI_TEACHER_CELEBRATION,
    userId: overrides.userId ?? 'user-1',
    payload: overrides.payload ?? {
      title: '默认标题',
      message: '默认内容',
      emoji: '🎉',
    },
    ttlMs: overrides.ttlMs ?? 10 * 60 * 1000,
    cooldownKey: overrides.cooldownKey ?? 'cooldown-default',
    createdAt: overrides.createdAt ?? new Date().toISOString(),
  };
}

function settings(
  overrides: Partial<AiTeacherLiveSettings> = {}
): AiTeacherLiveSettings {
  return {
    userId: 'user-1',
    updatedAt: new Date().toISOString(),
    ...DEFAULT_LIVE_SETTINGS,
    ...overrides,
  };
}

describe('AiTeacherLiveService (P3-B)', () => {
  let service: AiTeacherLiveService;
  let bus: GamificationEventBusService;

  beforeEach(() => {
    // 清理 window 桥接
    if (typeof window !== 'undefined') {
      delete (window as unknown as { __aiTeacherLiveService?: unknown })
        .__aiTeacherLiveService;
    }
    TestBed.configureTestingModule({});
    bus = TestBed.inject(GamificationEventBusService);
    service = TestBed.inject(AiTeacherLiveService);
    // 默认设置：开启全部
    service.applySettings(settings());
  });

  afterEach(() => {
    service.ngOnDestroy();
  });

  it('应能创建（构造时自动订阅 gamification bus）', () => {
    expect(service).toBeTruthy();
    expect(service.pending$).toBeDefined();
    expect(service.history$).toBeDefined();
    expect(service.settings$).toBeDefined();
  });

  it('构造时应将自己注册到 window.__aiTeacherLiveService', () => {
    if (typeof window === 'undefined') return;
    expect(
      (window as unknown as { __aiTeacherLiveService?: AiTeacherLiveService })
        .__aiTeacherLiveService
    ).toBe(service);
  });

  describe('ingest()', () => {
    it('应将事件加入 pending$ 和 history$', () => {
      const event = makeEvent();
      service.ingest(event);
      expect(service.pending$.subscribe).toBeDefined();
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      let history: AiTeacherLiveEvent[] = [];
      service.history$.subscribe((h) => (history = h));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe(event.id);
      expect(history.length).toBe(1);
      expect(history[0].id).toBe(event.id);
    });

    it('应按 id 去重（同一事件只入队一次）', () => {
      const event = makeEvent({ id: 'dup-1' });
      service.ingest(event);
      service.ingest(event);
      service.ingest(event);
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      let history: AiTeacherLiveEvent[] = [];
      service.history$.subscribe((h) => (history = h));
      expect(pending.length).toBe(1);
      expect(history.length).toBe(1);
    });

    it('应过滤已过期的（createdAt + ttlMs 早于当前）', () => {
      const past = new Date(Date.now() - 10 * 60 * 1000).toISOString();
      const event = makeEvent({
        id: 'expired-1',
        createdAt: past,
        ttlMs: 60_000,
      });
      service.ingest(event);
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      let history: AiTeacherLiveEvent[] = [];
      service.history$.subscribe((h) => (history = h));
      expect(pending.length).toBe(0);
      expect(history.length).toBe(0);
    });

    it('应过滤勿扰时段内的事件', () => {
      const currentHour = new Date().getHours();
      service.applySettings(
        settings({
          dndStartHour: currentHour,
          dndEndHour: currentHour, // start == end：实际上不进入勿扰（边界）
        })
      );
      // 构造一个覆盖当前小时的勿扰
      service.applySettings(
        settings({
          dndStartHour: 0,
          dndEndHour: 24,
        })
      );
      const event = makeEvent({ id: 'dnd-1' });
      service.ingest(event);
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(0);
    });

    it('总开关 enabled=false 时应丢弃所有事件', () => {
      service.applySettings(settings({ enabled: false }));
      service.ingest(makeEvent({ id: 'a' }));
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(0);
    });

    it('celebrationEnabled=false 时应只过滤 celebration 事件', () => {
      service.applySettings(settings({ celebrationEnabled: false }));
      service.ingest(
        makeEvent({
          id: 'c-1',
          type: GamificationEventType.AI_TEACHER_CELEBRATION,
        })
      );
      service.ingest(
        makeEvent({
          id: 's-1',
          type: GamificationEventType.AI_TEACHER_SUGGESTION,
        })
      );
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('s-1');
    });

    it('suggestionEnabled=false 时应只过滤 suggestion 事件', () => {
      service.applySettings(settings({ suggestionEnabled: false }));
      service.ingest(
        makeEvent({
          id: 'c-1',
          type: GamificationEventType.AI_TEACHER_CELEBRATION,
        })
      );
      service.ingest(
        makeEvent({
          id: 's-1',
          type: GamificationEventType.AI_TEACHER_SUGGESTION,
        })
      );
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('c-1');
    });

    it('nudgeEnabled=false 时应只过滤 nudge 事件', () => {
      service.applySettings(settings({ nudgeEnabled: false }));
      service.ingest(
        makeEvent({
          id: 's-1',
          type: GamificationEventType.AI_TEACHER_SUGGESTION,
        })
      );
      service.ingest(
        makeEvent({
          id: 'n-1',
          type: GamificationEventType.AI_TEACHER_NUDGE,
        })
      );
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('s-1');
    });

    it('pending 上限为 3 条（超出从尾部丢弃）', () => {
      for (let i = 0; i < 5; i++) {
        service.ingest(makeEvent({ id: `e${i}` }));
      }
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(3);
      // 保留最新 3 条
      expect(pending.map((e) => e.id)).toEqual(['e2', 'e3', 'e4']);
    });

    it('history 上限为 50 条（超出从尾部丢弃）', () => {
      for (let i = 0; i < 60; i++) {
        service.ingest(makeEvent({ id: `h${i}` }));
      }
      let history: AiTeacherLiveEvent[] = [];
      service.history$.subscribe((h) => (history = h));
      expect(history.length).toBe(50);
      // 最新 50 条
      expect(history[0].id).toBe('h59');
      expect(history[49].id).toBe('h10');
    });
  });

  describe('markRead() / dismiss() / click()', () => {
    it('markRead 应从 pending 中移除事件', () => {
      const event = makeEvent({ id: 'read-1' });
      service.ingest(event);
      service.markRead('read-1');
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(0);
    });

    it('dismiss 应触发 dismiss 埋点', () => {
      const event = makeEvent({
        id: 'd-1',
        payload: {
          title: 'T',
          message: 'M',
          emoji: '🎉',
        },
      });
      service.ingest(event);
      const clicks: unknown[] = [];
      service.clicks$.subscribe((c) => clicks.push(c));
      service.dismiss('d-1');
      expect(clicks.length).toBe(1);
      expect((clicks[0] as { action: string }).action).toBe('dismiss');
    });

    it('click(action=cta) 应同时触发埋点和 markRead', () => {
      const event = makeEvent({
        id: 'clk-1',
        payload: {
          title: 'T',
          message: 'M',
          emoji: '🎉',
          ctaRoute: '/learn',
          ctaLabel: '去看看',
        },
      });
      service.ingest(event);
      const clicks: unknown[] = [];
      service.clicks$.subscribe((c) => clicks.push(c));
      service.click(event, 'cta');
      expect(clicks.length).toBe(1);
      const c = clicks[0] as {
        action: string;
        ctaRoute?: string;
        ctaLabel?: string;
      };
      expect(c.action).toBe('cta');
      expect(c.ctaRoute).toBe('/learn');
      expect(c.ctaLabel).toBe('去看看');
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(0);
    });

    it('dismissAll 应清空 pending 并为每条产生 dismiss 埋点', () => {
      service.ingest(makeEvent({ id: 'd1' }));
      service.ingest(makeEvent({ id: 'd2' }));
      const clicks: unknown[] = [];
      service.clicks$.subscribe((c) => clicks.push(c));
      service.dismissAll();
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(0);
      expect(clicks.length).toBe(2);
    });
  });

  describe('applySettings() / setUserId()', () => {
    it('applySettings 应更新 settings$', () => {
      const next = settings({ enabled: false });
      service.applySettings(next);
      let s!: AiTeacherLiveSettings;
      service.settings$.subscribe((v) => (s = v));
      expect(s).toEqual(next);
    });

    it('getSettingsSnapshot 应返回当前 settings', () => {
      const next = settings({ maxPerHour: 7 });
      service.applySettings(next);
      expect(service.getSettingsSnapshot().maxPerHour).toBe(7);
    });

    it('setUserId 应注入 userId 并应用默认设置', () => {
      service.setUserId('user-42');
      const snap = service.getSettingsSnapshot();
      expect(snap.userId).toBe('user-42');
    });
  });

  describe('replayFromServer()', () => {
    it('应批量调用 ingest（带去重）', () => {
      const events = [
        makeEvent({ id: 'r-1' }),
        makeEvent({ id: 'r-2' }),
        makeEvent({ id: 'r-1' }), // 重复
      ];
      service.replayFromServer(events);
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      let history: AiTeacherLiveEvent[] = [];
      service.history$.subscribe((h) => (history = h));
      expect(pending.length).toBe(2);
      expect(history.length).toBe(2);
    });

    it('空数组应不抛错', () => {
      expect(() => service.replayFromServer([])).not.toThrow();
    });
  });

  describe('集成：gamification bus → live service', () => {
    it('应从 gamification bus 接收 ai_teacher_celebration 事件', () => {
      const event: AiTeacherLiveEvent = makeEvent({
        id: 'bus-1',
        type: GamificationEventType.AI_TEACHER_CELEBRATION,
      });
      bus.publish({
        type: GamificationEventType.AI_TEACHER_CELEBRATION,
        data: event,
      });
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('bus-1');
    });

    it('应从 gamification bus 接收 ai_teacher_suggestion 事件', () => {
      const event: AiTeacherLiveEvent = makeEvent({
        id: 'bus-s',
        type: GamificationEventType.AI_TEACHER_SUGGESTION,
      });
      bus.publish({
        type: GamificationEventType.AI_TEACHER_SUGGESTION,
        data: event,
      });
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('bus-s');
    });

    it('应从 gamification bus 接收 ai_teacher_nudge 事件', () => {
      const event: AiTeacherLiveEvent = makeEvent({
        id: 'bus-n',
        type: GamificationEventType.AI_TEACHER_NUDGE,
      });
      bus.publish({
        type: GamificationEventType.AI_TEACHER_NUDGE,
        data: event,
      });
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('bus-n');
    });

    it('应忽略非 ai_teacher_* 事件（gamification 原生事件透传给其他订阅者）', () => {
      bus.publish({
        type: GamificationEventType.ACHIEVEMENT_UNLOCKED,
        data: {
          achievement_id: 'a1',
          name: 'A1',
          rarity: 'common',
        },
      });
      let pending: AiTeacherLiveEvent[] = [];
      service.pending$.subscribe((p) => (pending = p));
      expect(pending.length).toBe(0);
    });
  });
});
