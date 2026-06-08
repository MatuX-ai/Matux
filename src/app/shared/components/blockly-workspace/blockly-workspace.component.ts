/**
 * Blockly 工作区组件（简化版）
 *
 * 提供可视化的 Blockly 积木编程工作区
 *
 * 基于 PRD F-05: Blockly 可视化编程
 */

import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';

import { BlocklyService, TargetLanguage } from '../../../core/services/blockly.service';

@Component({
  selector: 'app-blockly-workspace',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatSelectModule,
    MatTooltipModule,
    MatFormFieldModule,
  ],
  template: `
    <div class="blockly-workspace">
      <mat-card>
        <mat-card-header>
          <mat-card-title>Blockly 可视化编程</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div #workspaceContainer class="workspace-container">
            <p>Blockly 工作区加载中...</p>
          </div>
          <div class="code-preview">
            <h4>生成的代码：</h4>
            <pre>{{ generatedCode }}</pre>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .blockly-workspace {
      height: 100%;
      padding: 16px;
    }
    .workspace-container {
      height: 400px;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: #fafafa;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .code-preview {
      margin-top: 16px;
    }
    pre {
      background: #f5f5f5;
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
    }
  `],
})
export class BlocklyWorkspaceComponent implements AfterViewInit, OnDestroy {
  @ViewChild('workspaceContainer') workspaceContainer!: ElementRef<HTMLDivElement>;

  @Input() showCodePreview = true;
  @Input() initialXml?: string;

  @Output() codeChanged = new EventEmitter<string>();
  @Output() workspaceChanged = new EventEmitter<unknown>();

  generatedCode = '# 等待生成代码';

  private blocklyService: BlocklyService;

  constructor() {
    this.blocklyService = new BlocklyService();
  }

  ngAfterViewInit(): void {
    console.log('[BlocklyWorkspace] 组件初始化');
    this.generatedCode = this.blocklyService.generateCode();
  }

  ngOnDestroy(): void {
    this.blocklyService.dispose();
  }
}
