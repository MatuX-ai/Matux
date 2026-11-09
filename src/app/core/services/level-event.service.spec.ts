/**
 * LevelEventService 单元测试
 */

import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { LevelEventService, LevelUpPayload } from './level-event.service';
import type { UserLevel } from '../../user/student/services/student-dashboard-data.service';

function lvl(current: number, totalExp = 0): UserLevel {
  return {
    current,
    title: '',
    exp: 0,
    expToNext: 0,
    totalExp,
    expProgressPercent: 0,
  };
}

describe('LevelEventService (P0-2)', () => {
  let service: LevelEventService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LevelEventService);
    service.reset();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('emitLevelUp: next > old 时推送事件', async () => {
    const received: LevelUpPayload[] = [];
    service.levelUp$.subscribe((p) => received.push(p));
    service.emitLevelUp('u1', lvl(2), lvl(3), 700);
    expect(received.length).toBe(1);
    expect(received[0].next.current).toBe(3);
  });

  it('emitLevelUp: next <= old 不触发', () => {
    const received: LevelUpPayload[] = [];
    service.levelUp$.subscribe((p) => received.push(p));
    service.emitLevelUp('u1', lvl(3), lvl(2), 100);
    expect(received.length).toBe(0);
  });

  it('emitLevelUp: 同一用户同等级去重', () => {
    const received: LevelUpPayload[] = [];
    service.levelUp$.subscribe((p) => received.push(p));
    service.emitLevelUp('u1', lvl(2), lvl(3), 700);
    service.emitLevelUp('u1', lvl(2), lvl(3), 700);
    expect(received.length).toBe(1);
  });

  it('emitLevelUp: 不同用户互不干扰', () => {
    const a: LevelUpPayload[] = [];
    const b: LevelUpPayload[] = [];
    // 用 totalExp 作为用户隔离的判别：用户 a → 700，用户 b → 1500
    service.levelUp$.subscribe((p) => (p.totalExp === 700 ? a.push(p) : b.push(p)));
    service.emitLevelUp('a', lvl(2), lvl(3), 700);
    service.emitLevelUp('b', lvl(2), lvl(3), 1500);
    expect(a.length).toBe(1);
    expect(b.length).toBe(1);
  });

  it('emitLevelUp: 跨级一次跳到 Lv5 也仅触发一次', () => {
    const received: LevelUpPayload[] = [];
    service.levelUp$.subscribe((p) => received.push(p));
    service.emitLevelUp('u1', lvl(2), lvl(5), 1500);
    expect(received.length).toBe(1);
    expect(received[0].next.current).toBe(5);
  });

  it('reset: 清空去重缓存', () => {
    const received: LevelUpPayload[] = [];
    service.levelUp$.subscribe((p) => received.push(p));
    service.emitLevelUp('u1', lvl(2), lvl(3), 700);
    service.reset();
    service.emitLevelUp('u1', lvl(2), lvl(3), 700);
    expect(received.length).toBe(2);
  });

  it('emitLevelUp: 异步订阅者也能收到', async () => {
    const promise = firstValueFrom(service.levelUp$);
    service.emitLevelUp('u1', lvl(2), lvl(4), 700);
    const payload = await promise;
    expect(payload.next.current).toBe(4);
  });
});
