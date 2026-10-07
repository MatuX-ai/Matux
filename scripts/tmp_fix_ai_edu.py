# -*- coding: utf-8 -*-
import re

path = r'I:\iMato\src\app\components\ai-edu-dashboard\ai-edu-dashboard.component.ts'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 替换 imports 块
old_imports = """import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { catchError, of, timeout } from 'rxjs';"""

new_imports = """import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  NgZone,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { Subject, catchError, of, timeout } from 'rxjs';
import { takeUntil } from 'rxjs/operators';"""

assert old_imports in content, "old imports block not found"
content = content.replace(old_imports, new_imports)

# 2. 给 @Component 加 changeDetection
old_component = """@Component({
  selector: 'app-ai-edu-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatButtonModule, HttpClientModule],"""

new_component = """@Component({
  selector: 'app-ai-edu-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatButtonModule, HttpClientModule],
  changeDetection: ChangeDetectionStrategy.Default,"""

assert old_component in content, "old @Component block not found"
content = content.replace(old_component, new_component)

# 3. 替换 class 定义 + constructor + ngOnInit + 加 destroy$/fallbackTimer + ngOnDestroy
old_class = """export class AIEduDashboardComponent implements OnInit {
  modules: AIEduModule[] = [];
  statistics: AIEduStatistics | null = null;
  loading = true;
  error: string | null = null;

  /**
   * 【P2-2 修复】默认从 localStorage 或注入的用户信息推断 orgId，
   * 缺少时退回 1 以匹配后端临时测试路由。
   */
  private readonly orgId = this.resolveOrgId();

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadModules();
    this.loadStatistics();
  }"""

new_class = """export class AIEduDashboardComponent implements OnInit, OnDestroy {
  modules: AIEduModule[] = [];
  statistics: AIEduStatistics | null = null;
  loading = true;
  error: string | null = null;

  /**
   * 【P2-2 修复】默认从 localStorage 或注入的用户信息推断 orgId，
   * 缺少时退回 1 以匹配后端临时测试路由。
   */
  private readonly orgId = this.resolveOrgId();

  /** 【P2-2 BUG02 修复】内部销毁信号,避免 setTimeout 兑底回调对已销毁组件调用 */
  private destroy$ = new Subject<void>();

  /** 【P2-2 BUG02 修复】兑底定时器句柄,用于 ngOnDestroy 时清理 */
  private fallbackTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.loadModules();
    this.loadStatistics();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.fallbackTimer !== null) {
      clearTimeout(this.fallbackTimer);
      this.fallbackTimer = null;
    }
  }"""

assert old_class in content, "old class block not found"
content = content.replace(old_class, new_class)

# 4. 替换 loadModules + 新增 applyModulesFallback
old_load_modules = """  /**
   * 【P2-2 修复】加载后端模块列表；失败时降级到静态示例
   * 增加 6s 限时，避免后端 hang 住导致 stuck loading
   */
  loadModules(): void {
    this.loading = true;
    this.http
      .get<{ success: boolean; data: AIEduModule[] }>(
        `/api/v1/org/${this.orgId}/ai-edu/modules`
      )
      .pipe(
        // 【P2-2 修复】6s 超时兑底 — 后端无响应时自动降级到示例数据
        timeout({ each: 6000 }),
        catchError(() => {
          this.error = '后端不可达，已切换到本地推荐目录';
          return of({ success: true, data: FALLBACK_MODULES });
        })
      )
      .subscribe((resp) => {
        this.modules = resp?.data ?? [];
        this.loading = false;
      });
  }"""

new_load_modules = """  /**
   * 【P2-2 BUG02 修复】加载后端模块列表,失败时降级到静态示例。
   * 三层防护：
   * 1) RxJS timeout({ each: 6000 }) — pipe 级超时
   * 2) HttpTimeoutInterceptor (5s) — 全局超时(可能在 pipe 之前触发)
   * 3) setTimeout(6000) runOutsideAngular — 兑底,确保任何边界条件下 6s 后
   *    一定切换到 fallback,避免 stuck loading
   */
  loadModules(): void {
    this.loading = true;
    if (this.fallbackTimer !== null) {
      clearTimeout(this.fallbackTimer);
      this.fallbackTimer = null;
    }
    this.http
      .get<{ success: boolean; data: AIEduModule[] }>(
        `/api/v1/org/${this.orgId}/ai-edu/modules`
      )
      .pipe(
        timeout({ each: 6000 }),
        catchError(() => {
          this.applyModulesFallback('后端不可达，已切换到本地推荐目录');
          return of({ success: true, data: FALLBACK_MODULES });
        })
      )
      .pipe(takeUntil(this.destroy$))
      .subscribe((resp) => {
        if (resp?.data) {
          this.modules = resp.data;
        } else if (this.modules.length === 0) {
          this.modules = FALLBACK_MODULES;
        }
        this.loading = false;
        if (this.fallbackTimer !== null) {
          clearTimeout(this.fallbackTimer);
          this.fallbackTimer = null;
        }
        this.cdr.markForCheck();
      });

    // 兑底定时器：6s 后若仍在 loading,强制切到 fallback。
    this.zone.runOutsideAngular(() => {
      this.fallbackTimer = setTimeout(() => {
        if (!this.loading) return;
        this.zone.run(() => {
          this.applyModulesFallback('后端响应超时，已切换到本地推荐目录');
        });
      }, 6000);
    });
  }

  /**
   * 【P2-2 BUG02 修复】统一的 modules fallback 应用入口。
   * setTimeout 兑底和 catchError 走同一逻辑,避免状态不一致。
   */
  private applyModulesFallback(reason: string): void {
    if (this.modules.length === 0) {
      this.modules = FALLBACK_MODULES;
    }
    this.error = reason;
    this.loading = false;
    if (this.fallbackTimer !== null) {
      clearTimeout(this.fallbackTimer);
      this.fallbackTimer = null;
    }
    this.cdr.markForCheck();
  }"""

assert old_load_modules in content, "old loadModules block not found"
content = content.replace(old_load_modules, new_load_modules)

# 5. 给 loadStatistics 加 takeUntil + cdr.markForCheck
old_load_stats = """    this.http
      .get<{ success: boolean; data: AIEduStatistics }>(
        `/api/v1/org/${this.orgId}/ai-edu/progress/statistics`
      )
      .pipe(
        // 【P2-2 修复】6s 超时兑底
        timeout({ each: 6000 }),
        catchError(() => of(fallback))
      )
      .subscribe((resp) => {
        this.statistics = resp?.data ?? null;
      });
  }"""

new_load_stats = """    this.http
      .get<{ success: boolean; data: AIEduStatistics }>(
        `/api/v1/org/${this.orgId}/ai-edu/progress/statistics`
      )
      .pipe(
        // 【P2-2 修复】6s 超时兑底
        timeout({ each: 6000 }),
        catchError(() => of(fallback))
      )
      .pipe(takeUntil(this.destroy$))
      .subscribe((resp) => {
        this.statistics = resp?.data ?? null;
        this.cdr.markForCheck();
      });
  }"""

assert old_load_stats in content, "old loadStatistics block not found"
content = content.replace(old_load_stats, new_load_stats)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: ai-edu-dashboard.component.ts patched successfully")
