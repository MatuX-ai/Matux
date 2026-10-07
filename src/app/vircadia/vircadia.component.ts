import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-vircadia',
  standalone: true,
  imports: [RouterModule, MatButtonModule, MatIconModule, MatToolbarModule],
  template: `
    <div class="vircadia-container">
      <mat-toolbar class="vircadia-toolbar">
        <span class="toolbar-title">
          <mat-icon>view_in_ar</mat-icon>
          Vircadia 元宇宙
        </span>
        <nav class="toolbar-nav">
          <a mat-button routerLink="classroom" routerLinkActive="active-link">
            <mat-icon>school</mat-icon>
            <span class="nav-label">虚拟教室</span>
          </a>
          <a mat-button routerLink="lab" routerLinkActive="active-link">
            <mat-icon>science</mat-icon>
            <span class="nav-label">虚拟实验室</span>
          </a>
          <a mat-button routerLink="avatar" routerLinkActive="active-link">
            <mat-icon>face</mat-icon>
            <span class="nav-label">Avatar 换装</span>
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
      .vircadia-container {
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .vircadia-toolbar {
        display: flex;
        gap: 16px;
        background: #1a1a2e;
        color: white;
        min-height: 56px;
      }
      .toolbar-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 500;
        margin-right: 32px;
      }
      .toolbar-nav {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .toolbar-nav a {
        color: rgba(255, 255, 255, 0.7);
        text-decoration: none;
      }
      .toolbar-nav a.active-link {
        color: white;
        background: rgba(255, 255, 255, 0.15);
      }
      .nav-label {
        margin-left: 4px;
      }
      .vircadia-content {
        flex: 1;
        overflow: hidden;
        background: #0f0f1a;
      }
    `,
  ],
})
export class VircadiaComponent {}
