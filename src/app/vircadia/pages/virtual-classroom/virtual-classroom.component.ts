import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject } from 'rxjs';

import { VircadiaSceneViewerComponent } from '../../../components/vircadia-scene-viewer/vircadia-scene-viewer.component';
import { createVircadiaSdk, VircadiaSdkService } from '../../../core/services/vircadia-sdk.service';
import { SceneInfo, UserInfo, VircadiaSDKConfig } from '../../../models/vircadia.models';

@Component({
  selector: 'app-virtual-classroom',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    VircadiaSceneViewerComponent,
  ],
  template: `
    <div class="virtual-classroom">
      <div class="scene-panel">
        <app-vircadia-scene-viewer
          [serverUrl]="serverUrl"
          [accessToken]="accessToken"
          [autoConnect]="true"
          [debugMode]="false"
          (connected)="onConnected($event)"
          (sceneLoaded)="onSceneLoaded($event)"
          (error)="onError($event)"
        ></app-vircadia-scene-viewer>
      </div>

      <div class="info-panel" *ngIf="currentScene">
        <mat-card>
          <mat-card-header>
            <mat-icon mat-card-avatar>school</mat-icon>
            <mat-card-title>{{ currentScene.name || '铏氭嫙鏁欏' }}</mat-card-title>
            <mat-card-subtitle>鍦ㄧ嚎浜烘暟: {{ onlineUsers }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <p>{{ currentScene.description || '娌夋蹈寮忚櫄鎷熷涔犵┖闂? }}</p>
            <div class="scene-actions">
              <button mat-raised-button color="primary" (click)="loadClassroomScene()">
                <mat-icon>class</mat-icon> 鏍囧噯鏁欏
              </button>
              <button mat-raised-button color="accent" (click)="loadLectureScene()">
                <mat-icon>present_to_all</mat-icon> 婕旇鍘?
              </button>
              <button mat-raised-button (click)="loadGroupScene()">
                <mat-icon>groups</mat-icon> 璁ㄨ瀹?
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [
    `
      .virtual-classroom {
        height: 100%;
        display: flex;
      }
      .scene-panel {
        flex: 1;
        position: relative;
      }
      .info-panel {
        width: 320px;
        padding: 16px;
        overflow-y: auto;
        background: rgba(255, 255, 255, 0.05);
      }
      .scene-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 16px;
      }
      .scene-actions button {
        width: 100%;
      }
    `,
  ],
})
export class VirtualClassroomComponent implements OnInit, OnDestroy {
  serverUrl = 'http://localhost:9000';
  accessToken = '';
  currentScene: SceneInfo | null = null;
  onlineUsers = 0;
  private sdk: VircadiaSdkService | null = null;
  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.accessToken = localStorage.getItem('vircadia_token') ?? '';
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onConnected(_user: UserInfo): void {
    const config: VircadiaSDKConfig = { serverUrl: this.serverUrl };
    this.sdk = createVircadiaSdk(config);
    this.loadClassroomScene();
  }

  onSceneLoaded(scene: SceneInfo): void {
    this.currentScene = scene;
  }

  onError(error: Error | string): void {
    console.error('[VirtualClassroom] Error:', error);
  }

  loadClassroomScene(): void {
    if (this.sdk) {
      void this.sdk.switchScene('classroom_default');
    }
  }

  loadLectureScene(): void {
    if (this.sdk) {
      void this.sdk.switchScene('lecture_hall');
    }
  }

  loadGroupScene(): void {
    if (this.sdk) {
      void this.sdk.switchScene('discussion_room');
    }
  }
}
