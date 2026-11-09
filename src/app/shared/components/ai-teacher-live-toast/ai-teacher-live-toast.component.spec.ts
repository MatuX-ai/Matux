/**
 * 【P3-B】AiTeacherLiveToastComponent 单元测试
 *
 * 覆盖：
 * - 3 种 variant 渲染（celebration / suggestion / nudge）
 * - 订阅 liveService.pending$ 并展示 toast
 * - 关闭按钮调用 onDismiss → liveService.dismiss
 * - CTA 按钮调用 onCtaClick → router.navigateByUrl + liveService.click
 * - position 输入
 * - trackBy 函数
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';

import {
  AiTeacherLiveEvent,
  AiTeacherLiveSettings,
  DEFAULT_LIVE_SETTINGS,
} from '../../../core/models/ai-teacher.models';
import { AiTeacherLiveService } from '../../../core/services/ai-teacher-live.service';
import {
  GamificationEventBusService,
  GamificationEventType,
} from '../../../core/services/gamification-event-bus.service';
import { AiTeacherLiveToastComponent } from './ai-teacher-live-toast.component';

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

function defaultSettings(): AiTeacherLiveSettings {
  return {
    userId: 'user-1',
    updatedAt: new Date().toISOString(),
    ...DEFAULT_LIVE_SETTINGS,
  };
}

describe('AiTeacherLiveToastComponent (P3-B)', () => {
  let component: AiTeacherLiveToastComponent;
  let fixture: ComponentFixture<AiTeacherLiveToastComponent>;
  let liveService: AiTeacherLiveService;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    if (typeof window !== 'undefined') {
      delete (window as unknown as { __aiTeacherLiveService?: unknown })
        .__aiTeacherLiveService;
    }
    routerSpy = jasmine.createSpyObj('Router', ['navigateByUrl']);

    await TestBed.configureTestingModule({
      imports: [AiTeacherLiveToastComponent, NoopAnimationsModule],
      providers: [
        { provide: Router, useValue: routerSpy },
        GamificationEventBusService,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AiTeacherLiveToastComponent);
    component = fixture.componentInstance;
    liveService = TestBed.inject(AiTeacherLiveService);
    liveService.applySettings(defaultSettings());
    fixture.detectChanges();
  });

  afterEach(() => {
    component.ngOnDestroy();
    liveService.ngOnDestroy();
  });

  it('应能创建', () => {
    expect(component).toBeTruthy();
  });

  it('默认 position 应为 bottom-right', () => {
    expect(component.position).toBe('bottom-right');
  });

  it('应能通过 @Input 设置 position', () => {
    component.position = 'top-right';
    expect(component.position).toBe('top-right');
  });

  describe('toast 渲染', () => {
    it('应将 celebration 事件渲染为 variant-celebration', () => {
      liveService.ingest(
        makeEvent({
          id: 'c-1',
          type: GamificationEventType.AI_TEACHER_CELEBRATION,
          payload: {
            title: '恭喜通关',
            message: '你刚刚完成了一个关卡！',
            emoji: '🎉',
          },
        })
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const toast = el.querySelector('.ai-toast.variant-celebration');
      expect(toast).toBeTruthy();
      expect(toast?.textContent).toContain('恭喜通关');
      expect(toast?.textContent).toContain('你刚刚完成了一个关卡！');
    });

    it('应将 suggestion 事件渲染为 variant-suggestion', () => {
      liveService.ingest(
        makeEvent({
          id: 's-1',
          type: GamificationEventType.AI_TEACHER_SUGGESTION,
          payload: {
            diagnosisType: 'learning_plateau',
            severity: 'warning',
            title: '学习高原期提醒',
            message: '循环的掌握度已经 3 天没有变化了',
          },
        })
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const toast = el.querySelector('.ai-toast.variant-suggestion');
      expect(toast).toBeTruthy();
      expect(toast?.textContent).toContain('学习高原期');
    });

    it('应将 nudge 事件渲染为 variant-nudge', () => {
      liveService.ingest(
        makeEvent({
          id: 'n-1',
          type: GamificationEventType.AI_TEACHER_NUDGE,
          payload: {
            nudgeType: 'comeback',
            title: '欢迎回来',
            message: '已经 1 天没来了，要不要继续学习？',
          },
        })
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const toast = el.querySelector('.ai-toast.variant-nudge');
      expect(toast).toBeTruthy();
      expect(toast?.textContent).toContain('欢迎回来');
    });

    it('应在 toast 内显示 emoji icon', () => {
      liveService.ingest(
        makeEvent({
          id: 'c-emoji',
          type: GamificationEventType.AI_TEACHER_CELEBRATION,
          payload: {
            title: 'T',
            message: 'M',
            emoji: '🌟',
          },
        })
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const icon = el.querySelector('.toast-icon');
      expect(icon?.textContent).toContain('🌟');
    });

    it('应在没有 ctaRoute 时不渲染 CTA 按钮', () => {
      liveService.ingest(
        makeEvent({
          id: 'no-cta',
          type: GamificationEventType.AI_TEACHER_CELEBRATION,
          payload: {
            title: 'T',
            message: 'M',
            emoji: '🎉',
          },
        })
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const ctaBtn = el.querySelector('.cta-btn');
      expect(ctaBtn).toBeFalsy();
    });

    it('应在有 ctaRoute 时渲染 CTA 按钮', () => {
      liveService.ingest(
        makeEvent({
          id: 'with-cta',
          type: GamificationEventType.AI_TEACHER_SUGGESTION,
          payload: {
            diagnosisType: 'prerequisite_missing',
            severity: 'warning',
            title: 'T',
            message: 'M',
            ctaRoute: '/learn/loops',
            ctaLabel: '去学习',
          },
        })
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const ctaBtn = el.querySelector('.cta-btn') as HTMLButtonElement;
      expect(ctaBtn).toBeTruthy();
      expect(ctaBtn?.textContent).toContain('去学习');
    });
  });

  describe('交互', () => {
    it('点击关闭按钮应调用 liveService.dismiss', () => {
      const event = makeEvent({
        id: 'd-1',
        type: GamificationEventType.AI_TEACHER_NUDGE,
        payload: {
          nudgeType: 'try_new',
          title: 'T',
          message: 'M',
        },
      });
      liveService.ingest(event);
      fixture.detectChanges();
      spyOn(liveService, 'dismiss');

      const el: HTMLElement = fixture.nativeElement;
      const dismissBtn = el.querySelector(
        '.dismiss-btn'
      ) as HTMLButtonElement;
      dismissBtn.click();

      expect(liveService.dismiss).toHaveBeenCalledWith('d-1');
    });

    it('点击 CTA 按钮应调用 router.navigateByUrl + liveService.click', () => {
      const event = makeEvent({
        id: 'clk-1',
        type: GamificationEventType.AI_TEACHER_SUGGESTION,
        payload: {
          diagnosisType: 'concept_confusion',
          severity: 'warning',
          title: 'T',
          message: 'M',
          ctaRoute: '/learn/loops',
          ctaLabel: '去学习',
        },
      });
      liveService.ingest(event);
      fixture.detectChanges();
      spyOn(liveService, 'click').and.callThrough();

      const el: HTMLElement = fixture.nativeElement;
      const ctaBtn = el.querySelector('.cta-btn') as HTMLButtonElement;
      ctaBtn.click();

      expect(routerSpy.navigateByUrl).toHaveBeenCalledWith('/learn/loops');
      expect(liveService.click).toHaveBeenCalled();
    });
  });

  describe('trackById', () => {
    it('应返回 toast.id', () => {
      const event = makeEvent({ id: 'tb-1' });
      expect(component.trackById(0, event as never)).toBe('tb-1');
    });
  });

  describe('自动消失', () => {
    it('celebration 事件应在 12s 后自动消失', fakeAsync(() => {
      liveService.ingest(
        makeEvent({
          id: 'auto-c',
          type: GamificationEventType.AI_TEACHER_CELEBRATION,
        })
      );
      fixture.detectChanges();
      expect(component.toasts.length).toBe(1);

      tick(12_000);
      fixture.detectChanges();
      expect(component.toasts.length).toBe(0);
    }));

    it('suggestion 事件应在 8s 后自动消失', fakeAsync(() => {
      liveService.ingest(
        makeEvent({
          id: 'auto-s',
          type: GamificationEventType.AI_TEACHER_SUGGESTION,
        })
      );
      fixture.detectChanges();
      expect(component.toasts.length).toBe(1);

      tick(8_000);
      fixture.detectChanges();
      expect(component.toasts.length).toBe(0);
    }));

    it('nudge 事件应在 6s 后自动消失', fakeAsync(() => {
      liveService.ingest(
        makeEvent({
          id: 'auto-n',
          type: GamificationEventType.AI_TEACHER_NUDGE,
        })
      );
      fixture.detectChanges();
      expect(component.toasts.length).toBe(1);

      tick(6_000);
      fixture.detectChanges();
      expect(component.toasts.length).toBe(0);
    }));
  });
});
