# -*- coding: utf-8 -*-
"""
R-02 ai-edu 模板修复:
- 把 fallback-banner 移到 modules-grid 上方(顶部位置)
- 给有 modules 的 banner 也加 '重新加载' 按钮
- 用 cloud_off icon (有 modules 时, 提示更明显)
"""
import re

path = r'I:\iMato\src\app\components\ai-edu-dashboard\ai-edu-dashboard.component.ts'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换: 移除原 modules-grid 下方的 fallback-banner
old_block = '''        <div class="modules-grid" *ngIf="!loading || modules.length > 0">
          <div
            class="module-card"
            *ngFor="let module of modules"
            (click)="enterModule(module)"
            (keyup.enter)="enterModule(module)"
            tabindex="0"
            role="button"
          >
            <div class="module-icon">
              <mat-icon>{{ iconForCategory(module.category) }}</mat-icon>
            </div>
            <h4 class="module-name">{{ module.name }}</h4>
            <p class="module-desc">{{ module.description }}</p>
            <div class="module-meta">
              <span><mat-icon>menu_book</mat-icon> {{ module.expected_lessons }} 节</span>
              <span><mat-icon>schedule</mat-icon> {{ module.expected_duration_minutes }} 分钟</span>
            </div>
          </div>
        </div>

        <div *ngIf="error && modules.length > 0" class="fallback-banner">
          <mat-icon>info</mat-icon>
          <span>{{ error }}</span>
        </div>
      </section>'''

new_block = '''        <!-- 【P2-2 BUG02 修复】顶部 fallback 提示: 后端不可达时优先显示,
             即使 modules 已有兜底数据也提示用户当前为离线模式 -->
        <div *ngIf="error && modules.length > 0" class="fallback-banner fallback-banner-top">
          <mat-icon>cloud_off</mat-icon>
          <span>{{ error }}</span>
          <button mat-stroked-button color="warn" (click)="loadModules()">
            <mat-icon>refresh</mat-icon>
            重新加载
          </button>
        </div>

        <div class="modules-grid" *ngIf="!loading || modules.length > 0">
          <div
            class="module-card"
            *ngFor="let module of modules"
            (click)="enterModule(module)"
            (keyup.enter)="enterModule(module)"
            tabindex="0"
            role="button"
          >
            <div class="module-icon">
              <mat-icon>{{ iconForCategory(module.category) }}</mat-icon>
            </div>
            <h4 class="module-name">{{ module.name }}</h4>
            <p class="module-desc">{{ module.description }}</p>
            <div class="module-meta">
              <span><mat-icon>menu_book</mat-icon> {{ module.expected_lessons }} 节</span>
              <span><mat-icon>schedule</mat-icon> {{ module.expected_duration_minutes }} 分钟</span>
            </div>
          </div>
        </div>
      </section>'''

assert old_block in content, "old_block not found"
content = content.replace(old_block, new_block)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: ai-edu-dashboard 模板修复完成, fallback banner 已移到顶部")
