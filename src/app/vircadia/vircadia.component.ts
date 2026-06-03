import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';

@Component({
  selector: 'app-vircadia',
  standalone: true,
  imports: [RouterModule, MatTabsModule, MatIconModule, MatToolbarModule],
  template: `
    <div class="vircadia-container">
      <mat-toolbar class="vircadia-toolbar">
        <span class="toolbar-title">
          <mat-icon>view_in_ar</mat-icon>
          Vircadia 元宇宙
        </span>
        <nav class="toolbar-nav">
          <a mat-tab-link routerLink="classroom" routerLinkActive="active-link">
            <mat-icon>school</mat-icon> 虚拟教室
          </a>
          <a mat-tab-link routerLink="lab" routerLinkActive="active-link">
            <mat-icon>science</mat-icon> 虚拟实验室
          </a>
          <a mat-tab-link routerLink="avatar" routerLinkActive="active-link">
            <mat-icon>face</mat-icon> Avatar 换装
          </a>
        </nav>
      </mat-toolbar>

      <div class="vircadia-content">
        <router-outlet></router-outlet>
      </div>
    </div>
  `,
  styles: [
    `
      .vircadia-container { height: 100%; display: flex; flex-direction: column; }
      .vircadia-toolbar { display: flex; gap: 16px; background: #1a1a2e; color: white; }
      .toolbar-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 500; margin-right: 32px; }
      .toolbar-nav { display: flex; align-items: center; gap: 4px; }
      .toolbar-nav a { color: rgba(255,255,255,0.7); text-decoration: none; padding: 8px 16px; display: flex; align-items: center; gap: 6px; border-radius: 8px; transition: all 0.2s; font-size: 14px; }
      .toolbar-nav a:hover { color: white; background: rgba(255,255,255,0.1); }
      .toolbar-nav a.active-link { color: white; background: rgba(255,255,255,0.15); }
      .vircadia-content { flex: 1; overflow: hidden; background: #0f0f1a; }
    `,
  ],
})
export class VircadiaComponent {}
