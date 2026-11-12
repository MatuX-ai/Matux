/**
 * 【P0-4 合规】用户中心 AI 面板「离线模式」角标 UI 测试
 *
 * 覆盖三态：
 * 1. 后端返回 isMock=true（本地模板回复）→ 显示「离线模式」角标
 * 2. 后端返回 isMock=false（真实 LLM 回复）→ 不显示角标
 * 3. /chat 请求失败 → 显示「离线模式」角标
 *
 * 背景：原先组件用 `res?.model === 'mock'` 判定，而后端实际返回
 * `mock-ai-teacher`，角标从不显示；判定口径已统一为 isMock。
 */

import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { BehaviorSubject, of, throwError } from 'rxjs';

import { AiAssistantToggleService } from '../../../core/services/ai-assistant-toggle.service';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { UserCenterService } from '../../services/user-center.service';
import { UserFooterComponent } from '../user-footer/user-footer.component';
import { UserNavbarComponent } from '../user-navbar/user-navbar.component';
import { UserPageLayoutComponent } from './user-page-layout.component';

/** 顶部导航栏替身（避免拉起真实导航栏的依赖树） */
@Component({ selector: 'app-user-navbar', standalone: true, template: '' })
class StubNavbarComponent {}

/** 底部页脚替身 */
@Component({ selector: 'app-user-footer', standalone: true, template: '' })
class StubFooterComponent {}

describe('UserPageLayoutComponent (P0-4 离线模式角标)', () => {
  let fixture: ComponentFixture<UserPageLayoutComponent>;
  let component: UserPageLayoutComponent;
  let chatSpy: jasmine.Spy;

  const userCenterStub = {
    currentUser$: new BehaviorSubject<unknown>(null),
    getCurrentUser: () => null,
  };

  const aiToggleStub = {
    panelOpen$: new BehaviorSubject<boolean>(false),
    toggle: () => undefined,
  };

  beforeEach(async () => {
    chatSpy = jasmine.createSpy('chat');

    await TestBed.configureTestingModule({
      imports: [UserPageLayoutComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: {} },
        { provide: UserCenterService, useValue: userCenterStub },
        { provide: AiAssistantToggleService, useValue: aiToggleStub },
        { provide: AITeacherService, useValue: { chat: chatSpy } },
      ],
    })
      .overrideComponent(UserPageLayoutComponent, {
        remove: { imports: [UserNavbarComponent, UserFooterComponent] },
        add: { imports: [StubNavbarComponent, StubFooterComponent] },
      })
      .compileComponents();

    fixture = TestBed.createComponent(UserPageLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy();
  });

  /** 发送一条消息并渲染结果 */
  function sendMessage(): void {
    component.aiMessage = '你好';
    component.sendAIMessage();
    fixture.detectChanges();
  }

  /** 读取当前渲染出的角标文本 */
  function offlineBadges(): string[] {
    const nodes = fixture.nativeElement.querySelectorAll('.ai-bubble-note');
    return Array.from(nodes).map((node) => (node as HTMLElement).textContent?.trim() ?? '');
  }

  it('后端返回 isMock=true 时应显示「离线模式」角标', () => {
    chatSpy.and.returnValue(
      of({
        reply: '本地模板回复',
        sessionId: 's1',
        emotionDetected: 'neutral',
        memoriesReferenced: [],
        knowledgeUsed: false,
        suggestions: [],
        model: 'mock-ai-teacher',
        confidence: 0.85,
        inferenceTimeMs: 5,
        isMock: true,
      })
    );

    sendMessage();

    expect(offlineBadges()).toEqual(['离线模式']);
    expect(component.aiMessages[1].fallback).toBeTrue();
  });

  it('真实 LLM 回复（isMock=false）不应显示角标', () => {
    chatSpy.and.returnValue(
      of({
        reply: '真实模型回复',
        sessionId: 's1',
        emotionDetected: 'neutral',
        memoriesReferenced: [],
        knowledgeUsed: false,
        suggestions: [],
        model: 'gpt-4o',
        confidence: 0.9,
        inferenceTimeMs: 120,
        isMock: false,
      })
    );

    sendMessage();

    expect(offlineBadges()).toEqual([]);
    expect(component.aiMessages[1].fallback).toBeFalse();
  });

  it('/chat 请求失败时应显示「离线模式」角标', () => {
    chatSpy.and.returnValue(throwError(() => new Error('network down')));

    sendMessage();

    expect(offlineBadges()).toEqual(['离线模式']);
    expect(component.aiMessages[1].fallback).toBeTrue();
  });
});
