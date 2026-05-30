import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  inject,
  Input,
  Output,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';

// 实验配置类型 - 使用 any 作为临时类型
type ExperimentConfig = any;
type ExperimentStep = any;
type ExperimentParameter = any;
type ExperimentEquipment = any;

@Component({
  selector: 'app-experiment-editor',
  standalone: true,
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatChipsModule,
    FormsModule,
  ],
  template: `
    <div class="experiment-editor">
      <mat-tab-group [(selectedIndex)]="selectedTab">
        <!-- 基础配置 -->
        <mat-tab label="基础配置">
          <div class="config-section">
            <mat-form-field appearance="outline">
              <mat-label>实验名称</mat-label>
              <input matInput [(ngModel)]="config.name" />
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>实验类型</mat-label>
              <mat-select [(ngModel)]="config.type">
                <mat-option value="robotics">机器人实验</mat-option>
                <mat-option value="physics">物理实验</mat-option>
                <mat-option value="chemistry">化学实验</mat-option>
                <mat-option value="electronics">电子实验</mat-option>
                <mat-option value="programming">编程实验</mat-option>
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>实验时长 (分钟)</mat-label>
              <input matInput type="number" [(ngModel)]="config.duration" />
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>难度等级</mat-label>
              <mat-select [(ngModel)]="config.difficulty">
                <mat-option value="beginner">初级</mat-option>
                <mat-option value="intermediate">中级</mat-option>
                <mat-option value="advanced">高级</mat-option>
                <mat-option value="expert">专家</mat-option>
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>实验目标</mat-label>
              <textarea matInput [(ngModel)]="config.objectives" rows="4"></textarea>
            </mat-form-field>
          </div>
        </mat-tab>

        <!-- 实验器材 -->
        <mat-tab label="实验器材">
          <div class="config-section">
            <div class="equipment-list">
              @for (equipment of equipments(); track equipment.id) {
                <div class="equipment-item">
                  <div class="equipment-info">
                    <input
                      matInput
                      [(ngModel)]="equipment.name"
                      placeholder="器材名称"
                      class="equipment-name"
                    />
                    <input
                      matInput
                      [(ngModel)]="equipment.model"
                      placeholder="型号"
                      class="equipment-model"
                    />
                    <input
                      matInput
                      type="number"
                      [(ngModel)]="equipment.quantity"
                      placeholder="数量"
                      class="equipment-quantity"
                    />
                  </div>
                  <button mat-icon-button color="warn" (click)="removeEquipment(equipment.id)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              }
            </div>
            <button mat-button (click)="addEquipment()">
              <mat-icon>add</mat-icon>
              添加器材
            </button>
          </div>
        </mat-tab>

        <!-- 实验步骤 -->
        <mat-tab label="实验步骤">
          <div class="config-section">
            <div class="steps-list">
              @for (step of steps(); track step.id) {
                <div class="step-item" [class.draggable]="true">
                  <div class="step-header">
                    <mat-icon class="drag-handle">drag_indicator</mat-icon>
                    <span class="step-number">步骤 {{ step.order }}</span>
                    <button mat-icon-button color="warn" (click)="removeStep(step.id)">
                      <mat-icon>delete</mat-icon>
                    </button>
                  </div>
                  <mat-form-field appearance="outline" class="step-title">
                    <mat-label>步骤标题</mat-label>
                    <input matInput [(ngModel)]="step.title" />
                  </mat-form-field>
                  <mat-form-field appearance="outline" class="step-description">
                    <mat-label>步骤描述</mat-label>
                    <textarea matInput [(ngModel)]="step.description" rows="3"></textarea>
                  </mat-form-field>
                  <div class="step-actions">
                    <mat-slide-toggle [(ngModel)]="step.hasImage">包含图片</mat-slide-toggle>
                    <mat-slide-toggle [(ngModel)]="step.hasVideo">包含视频</mat-slide-toggle>
                    <mat-slide-toggle [(ngModel)]="step.critical">关键步骤</mat-slide-toggle>
                  </div>
                </div>
              }
            </div>
            <button mat-button (click)="addStep()">
              <mat-icon>add</mat-icon>
              添加步骤
            </button>
          </div>
        </mat-tab>

        <!-- 实验参数 -->
        <mat-tab label="实验参数">
          <div class="config-section">
            <div class="parameters-list">
              @for (param of parameters(); track param.id) {
                <div class="parameter-item">
                  <input
                    matInput
                    [(ngModel)]="param.name"
                    placeholder="参数名称"
                    class="param-name"
                  />
                  <mat-select [(ngModel)]="param.type" class="param-type">
                    <mat-option value="number">数值</mat-option>
                    <mat-option value="string">文本</mat-option>
                    <mat-option value="boolean">布尔</mat-option>
                    <mat-option value="range">范围</mat-option>
                  </mat-select>
                  @if (param.type === 'number' || param.type === 'range') {
                    <input
                      matInput
                      type="number"
                      [(ngModel)]="param.defaultValue"
                      placeholder="默认值"
                      class="param-default"
                    />
                  }
                  @if (param.type === 'range') {
                    <input
                      matInput
                      type="number"
                      [(ngModel)]="param.min"
                      placeholder="最小值"
                      class="param-min"
                    />
                    <input
                      matInput
                      type="number"
                      [(ngModel)]="param.max"
                      placeholder="最大值"
                      class="param-max"
                    />
                  }
                  <button mat-icon-button color="warn" (click)="removeParameter(param.id)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              }
            </div>
            <button mat-button (click)="addParameter()">
              <mat-icon>add</mat-icon>
              添加参数
            </button>
          </div>
        </mat-tab>

        <!-- 安全须知 -->
        <mat-tab label="安全须知">
          <div class="config-section">
            <mat-slide-toggle [(ngModel)]="config.safetyWarnings.required">
              需要安全培训
            </mat-slide-toggle>

            <mat-form-field appearance="outline">
              <mat-label>安全警告</mat-label>
              <textarea matInput [(ngModel)]="config.safetyWarnings.warnings" rows="6"></textarea>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>防护措施</mat-label>
              <textarea
                matInput
                [(ngModel)]="config.safetyWarnings.precautions"
                rows="4"
              ></textarea>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>应急措施</mat-label>
              <textarea matInput [(ngModel)]="config.safetyWarnings.emergency" rows="4"></textarea>
            </mat-form-field>
          </div>
        </mat-tab>
      </mat-tab-group>

      <!-- 底部操作栏 -->
      <div class="editor-actions">
        <button mat-button (click)="preview.emit(config)">
          <mat-icon>visibility</mat-icon>
          预览
        </button>
        <div class="action-spacer"></div>
        <button mat-button (click)="saveAsTemplate.emit(config)">
          <mat-icon>save</mat-icon>
          保存为模板
        </button>
        <button mat-raised-button color="primary" (click)="save.emit(config)">
          <mat-icon>check</mat-icon>
          保存
        </button>
      </div>
    </div>
  `,
  styles: `
    :host {
      display: block;
      height: 100%;
    }

    .experiment-editor {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--mat-sys-surface);
    }

    .config-section {
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .mat-mdc-form-field {
      width: 100%;
    }

    /* 器材列表 */
    .equipment-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 16px;
    }

    .equipment-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      background: var(--mat-sys-surface-container);
      border-radius: var(--mat-sys-shape-corner-small);
    }

    .equipment-info {
      display: flex;
      gap: 12px;
      flex: 1;
    }

    .equipment-name {
      flex: 2;
    }

    .equipment-model {
      flex: 1;
    }

    .equipment-quantity {
      width: 80px;
    }

    /* 步骤列表 */
    .steps-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 16px;
    }

    .step-item {
      padding: 20px;
      background: var(--mat-sys-surface-container);
      border-radius: var(--mat-sys-shape-corner-medium);
      border: 2px solid transparent;
      transition: all 0.2s ease;
    }

    .step-item.draggable:hover {
      border-color: var(--mat-sys-primary);
    }

    .step-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }

    .drag-handle {
      cursor: move;
      color: var(--mat-sys-on-surface-variant);
    }

    .step-number {
      font-weight: 600;
      color: var(--mat-sys-primary);
      font-size: 16px;
    }

    .step-title,
    .step-description {
      margin-bottom: 12px;
    }

    .step-actions {
      display: flex;
      gap: 24px;
    }

    /* 参数列表 */
    .parameters-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 16px;
    }

    .parameter-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      background: var(--mat-sys-surface-container);
      border-radius: var(--mat-sys-shape-corner-small);
    }

    .param-name {
      flex: 2;
    }

    .param-type {
      flex: 1;
    }

    .param-default,
    .param-min,
    .param-max {
      width: 100px;
    }

    /* 操作栏 */
    .editor-actions {
      display: flex;
      align-items: center;
      padding: 16px 24px;
      background: var(--mat-sys-surface-container);
      border-top: 1px solid var(--mat-sys-outline-variant);
    }

    .action-spacer {
      flex: 1;
    }

    .editor-actions button {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* 响应式 */
    @media (max-width: 768px) {
      .equipment-info {
        flex-direction: column;
      }

      .parameter-item {
        flex-wrap: wrap;
      }

      .param-name,
      .param-type {
        width: 100%;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExperimentEditorComponent {
  @Input() config: ExperimentConfig = {
    name: '',
    type: 'robotics',
    duration: 60,
    difficulty: 'intermediate',
    objectives: '',
    safetyWarnings: {
      required: false,
      warnings: '',
      precautions: '',
      emergency: '',
    },
  };

  @Output() save = new EventEmitter<ExperimentConfig>();
  @Output() saveAsTemplate = new EventEmitter<ExperimentConfig>();
  @Output() preview = new EventEmitter<ExperimentConfig>();

  selectedTab = signal<number>(0);
  equipments = signal<ExperimentEquipment[]>([]);
  steps = signal<ExperimentStep[]>([]);
  parameters = signal<ExperimentParameter[]>([]);

  private snackBar = inject(MatSnackBar);

  private equipmentIdCounter = 0;
  private stepIdCounter = 0;
  private parameterIdCounter = 0;

  addEquipment(): void {
    this.equipments.update((eqs) => [
      ...eqs,
      {
        id: ++this.equipmentIdCounter,
        name: '',
        model: '',
        quantity: 1,
      },
    ]);
  }

  removeEquipment(id: number): void {
    this.equipments.update((eqs) => eqs.filter((e) => e.id !== id));
  }

  addStep(): void {
    this.steps.update((sts) => [
      ...sts,
      {
        id: ++this.stepIdCounter,
        order: sts.length + 1,
        title: '',
        description: '',
        hasImage: false,
        hasVideo: false,
        critical: false,
      },
    ]);
  }

  removeStep(id: number): void {
    this.steps.update((sts) => {
      const filtered = sts.filter((s) => s.id !== id);
      return filtered.map((s, i) => ({ ...s, order: i + 1 }));
    });
  }

  addParameter(): void {
    this.parameters.update((params) => [
      ...params,
      {
        id: ++this.parameterIdCounter,
        name: '',
        type: 'number',
        defaultValue: undefined,
        min: undefined,
        max: undefined,
      },
    ]);
  }

  removeParameter(id: number): void {
    this.parameters.update((params) => params.filter((p) => p.id !== id));
  }

  onSave(): void {
    if (!this.config.name) {
      this.snackBar.open('请输入实验名称', '关闭', { duration: 3000 });
      return;
    }

    const completeConfig: ExperimentConfig = {
      ...this.config,
      equipments: this.equipments(),
      steps: this.steps(),
      parameters: this.parameters(),
    };

    this.save.emit(completeConfig);
    this.snackBar.open('实验配置已保存', '关闭', { duration: 3000 });
  }
}
