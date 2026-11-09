/**
 * AIFabStateService 单元测试
 */

import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { AIFabStateService } from './ai-fab-state.service';

describe('AIFabStateService (P0-5)', () => {
  let service: AIFabStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AIFabStateService);
    service.resetForTest();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('初始状态为 idle', async () => {
    const s = await firstValueFrom(service.state$);
    expect(s).toBe('idle');
  });

  it('setUnread > 0 状态变 message', async () => {
    const states: string[] = [];
    service.state$.subscribe((s) => states.push(s));
    service.setUnread(3);
    expect(states[states.length - 1]).toBe('message');
  });

  it('addReward + setStuckMinutes=15: 优先级 stuck > reward', async () => {
    service.addReward();
    service.setStuckMinutes(15);
    const s = await firstValueFrom(service.state$);
    expect(s).toBe('stuck');
  });

  it('addReward 后无 stuck: 状态 reward', async () => {
    service.addReward();
    const s = await firstValueFrom(service.state$);
    expect(s).toBe('reward');
  });

  it('popOpeningMessage: reward 态返 reward 开场白', () => {
    service.addReward();
    const msg = service.popOpeningMessage();
    expect(msg).toContain('升级');
  });

  it('popOpeningMessage: stuck 态返 stuck 开场白（带分钟数）', () => {
    service.setStuckMinutes(12);
    const msg = service.popOpeningMessage();
    expect(msg).toContain('12');
  });

  it('popOpeningMessage: idle 态返 null', () => {
    expect(service.popOpeningMessage()).toBeNull();
  });

  it('clearStuck 清空后状态回退', async () => {
    service.setStuckMinutes(20);
    service.clearStuck();
    // 同时仍有 reward
    service.addReward();
    const s = await firstValueFrom(service.state$);
    expect(s).toBe('reward');
  });

  it('consumeReward 减 1', () => {
    service.addReward();
    service.addReward();
    service.consumeReward();
    return firstValueFrom(service.pendingRewards$).then((n) => {
      expect(n).toBe(1);
    });
  });

  it('incUnread 加 1', () => {
    service.incUnread();
    service.incUnread();
    return firstValueFrom(service.unreadCount$).then((n) => {
      expect(n).toBe(2);
    });
  });
});
