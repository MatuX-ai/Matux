/**
 * 【P0-4 合规】AITeacherService 单元测试
 *
 * 覆盖：
 * - isMockModel() 集合判定（mock / mock-ai-teacher / rule-based-fallback + 前缀变体）
 * - normalizeChatResponse 的 isMock 推导（后端显式标记优先 + degraded 强制 + 集合回退）
 * - /chat 请求失败时的本地降级必须标记 isMock=true
 * - /chat 鉴权失败（401/403）不得降级，必须原样抛给调用方
 *
 * 背景：原先前端用 `model === 'mock'` 单值比较判定离线模式，
 * 而后端实际返回的模型名是 `mock-ai-teacher`，导致离线角标从不显示。
 */

import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AITeacherChatResponse } from '../models/ai-teacher.models';
import { AiTeacherLiveService } from './ai-teacher-live.service';
import { AITeacherService } from './ai-teacher.service';
import { EmotionalCompanionService } from './emotional-companion.service';
import { VectorKnowledgeService } from './vector-knowledge.service';

describe('AITeacherService (P0-4 离线模式角标)', () => {
  let service: AITeacherService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: VectorKnowledgeService, useValue: { ragRetrieve: () => of(null) } },
        { provide: EmotionalCompanionService, useValue: { logEmotion: () => undefined } },
        { provide: AiTeacherLiveService, useValue: {} },
      ],
    });
    service = TestBed.inject(AITeacherService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  /** 发一次 /chat 并把后端响应冲回去，返回归一化后的响应 */
  function flushChat(payload: Record<string, unknown>): AITeacherChatResponse {
    let received: AITeacherChatResponse | undefined;
    service.chat({ userId: '', message: '你好', sessionId: 's1' }).subscribe((res) => {
      received = res;
    });
    httpMock.expectOne('/api/v1/ai-teacher/chat').flush(payload);
    return received as AITeacherChatResponse;
  }

  describe('isMockModel 集合判定', () => {
    it('应命中 mock 模型名集合', () => {
      expect(AITeacherService.isMockModel('mock')).toBeTrue();
      expect(AITeacherService.isMockModel('mock-ai-teacher')).toBeTrue();
      expect(AITeacherService.isMockModel('rule-based-fallback')).toBeTrue();
    });

    it('应兼容 mock / rule-based 前缀变体', () => {
      expect(AITeacherService.isMockModel('mock-v2')).toBeTrue();
      expect(AITeacherService.isMockModel('rule-based-fallback-v2')).toBeTrue();
    });

    it('真实 LLM 模型名不应命中', () => {
      expect(AITeacherService.isMockModel('gpt-4o')).toBeFalse();
      expect(AITeacherService.isMockModel('qwen-plus')).toBeFalse();
      expect(AITeacherService.isMockModel('deepseek-chat')).toBeFalse();
    });

    it('空值不应命中', () => {
      expect(AITeacherService.isMockModel('')).toBeFalse();
      expect(AITeacherService.isMockModel(null)).toBeFalse();
      expect(AITeacherService.isMockModel(undefined)).toBeFalse();
    });
  });

  describe('isMock 推导', () => {
    it('后端显式 is_mock=true 时应标记为离线模式', () => {
      const res = flushChat({
        reply: '你好',
        session_id: 's1',
        model: 'mock-ai-teacher',
        is_mock: true,
      });
      expect(res.isMock).toBeTrue();
    });

    it('后端显式 is_mock=false 且为真实模型时不应标记离线', () => {
      const res = flushChat({
        reply: '你好',
        session_id: 's1',
        model: 'gpt-4o',
        is_mock: false,
      });
      expect(res.isMock).toBeFalse();
    });

    it('后端缺少 is_mock 时应回退到 model 集合判定', () => {
      const res = flushChat({
        reply: '你好',
        session_id: 's1',
        model: 'mock-ai-teacher',
      });
      expect(res.isMock).toBeTrue();
    });

    it('后端标记 degraded 时应强制标记为离线模式', () => {
      const res = flushChat({
        reply: '你好',
        session_id: 's1',
        model: 'gpt-4o',
        degraded: true,
      });
      expect(res.isMock).toBeTrue();
    });

    it('后端显式标记优先于 model 集合判定', () => {
      const res = flushChat({
        reply: '你好',
        session_id: 's1',
        model: 'mock-ai-teacher',
        is_mock: false,
      });
      expect(res.isMock).toBeFalse();
    });
  });

  describe('/chat 降级与鉴权失败', () => {
    it('请求失败时应降级为本地回复并标记 isMock=true', () => {
      let received: AITeacherChatResponse | undefined;
      service.chat({ userId: '', message: '你好', sessionId: 's1' }).subscribe((res) => {
        received = res;
      });
      httpMock
        .expectOne('/api/v1/ai-teacher/chat')
        .flush('boom', { status: 500, statusText: 'Server Error' });

      expect(received).toBeDefined();
      expect(received?.isMock).toBeTrue();
      expect(received?.model).toBe('mock');
    });

    it('401 鉴权失败不得降级，必须原样抛错', () => {
      let received: AITeacherChatResponse | undefined;
      let error: unknown;
      service.chat({ userId: '', message: '你好', sessionId: 's1' }).subscribe({
        next: (res) => {
          received = res;
        },
        error: (err) => {
          error = err;
        },
      });
      httpMock
        .expectOne('/api/v1/ai-teacher/chat')
        .flush('unauthorized', { status: 401, statusText: 'Unauthorized' });

      expect(received).toBeUndefined();
      expect(error).toBeTruthy();
      expect((error as { status?: number })?.status).toBe(401);
    });

    it('403 越权不得降级，必须原样抛错', () => {
      let received: AITeacherChatResponse | undefined;
      let error: unknown;
      service.chat({ userId: '', message: '你好', sessionId: 's1' }).subscribe({
        next: (res) => {
          received = res;
        },
        error: (err) => {
          error = err;
        },
      });
      httpMock
        .expectOne('/api/v1/ai-teacher/chat')
        .flush('forbidden', { status: 403, statusText: 'Forbidden' });

      expect(received).toBeUndefined();
      expect(error).toBeTruthy();
      expect((error as { status?: number })?.status).toBe(403);
    });
  });
});
