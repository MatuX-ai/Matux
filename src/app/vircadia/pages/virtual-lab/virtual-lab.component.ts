import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTabsModule } from '@angular/material/tabs';

import { VircadiaSceneViewerComponent } from '../../../components/vircadia-scene-viewer/vircadia-scene-viewer.component';

@Component({
  selector: 'app-virtual-lab',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatTabsModule,
    VircadiaSceneViewerComponent,
  ],
  template: `
    <div class="virtual-lab">
      <div class="scene-panel">
        <app-vircadia-scene-viewer
          serverUrl="http://localhost:9000"
          [autoConnect]="true"
          [debugMode]="false"
        ></app-vircadia-scene-viewer>
      </div>

      <div class="lab-panel">
        <mat-tabs>
          <mat-tab label="🔬 物理实验">
            <div class="tab-content">
              <p>在虚拟环境中进行物理实验模拟</p>
              <div class="lab-actions">
                <button mat-raised-button color="primary" (click)="loadLabScene('physics')">力学实验</button>
                <button mat-raised-button color="accent" (click)="loadLabScene('optics')">光学实验</button>
                <button mat-raised-button (click)="loadLabScene('circuit')">电路实验</button>
              </div>
            </div>
          </mat-tab>
          <mat-tab label="🧪 化学实验">
            <div class="tab-content">
              <p>3D 分子结构与化学反应可视化</p>
              <button mat-raised-button color="primary" (click)="loadLabScene('chemistry')">进入化学实验室</button>
            </div>
          </mat-tab>
          <mat-tab label="🔧 工程实践">
            <div class="tab-content">
              <p>工程设计、3D 打印预览</p>
              <button mat-raised-button color="primary" (click)="loadLabScene('engineering')">进入工程实验室</button>
            </div>
          </mat-tab>
        </mat-tabs>
      </div>
    </div>
  `,
  styles: [
    `
      .virtual-lab { height: 100%; display: flex; }
      .scene-panel { flex: 1; position: relative; }
      .lab-panel { width: 320px; padding: 16px; overflow-y: auto; background: rgba(255,255,255,0.05); }
      .tab-content { padding: 16px; }
      .tab-content p { color: rgba(255,255,255,0.7); margin-bottom: 16px; }
      .lab-actions { display: flex; flex-direction: column; gap: 8px; }
      .lab-actions button { width: 100%; }
    `,
  ],
})
export class VirtualLabComponent {
  loadLabScene(type: string): void {
    console.log('[VirtualLab] Loading scene:', type);
  }
}
