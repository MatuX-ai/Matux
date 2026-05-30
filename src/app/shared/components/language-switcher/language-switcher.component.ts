import { CommonModule } from '@angular/common';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { I18nService } from '@core/services/i18n.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-language-switcher',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatMenuModule],
  template: `
    <button mat-button [matMenuTriggerFor]="menu" class="lang-switcher">
      <mat-icon>language</mat-icon>
      {{ currentLangLabel }}
      <mat-icon>expand_more</mat-icon>
    </button>

    <mat-menu #menu="matMenu">
      <button mat-menu-item (click)="setLanguage('zh-CN')">
        <mat-icon>check_circle</mat-icon>
        <span>简体中文</span>
      </button>
      <button mat-menu-item (click)="setLanguage('en-US')">
        <mat-icon>check_circle</mat-icon>
        <span>English</span>
      </button>
    </mat-menu>
  `,
  styles: [
    `
      .lang-switcher {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 14px;
      }

      button[mat-menu-item] {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }
    `,
  ],
})
export class LanguageSwitcherComponent implements OnDestroy {
  currentLangLabel = '简体中文';
  private subscription: Subscription | null = null;

  constructor(@Inject(I18nService) private i18nService: I18nService) {
    this.subscription = this.i18nService.currentLang$.subscribe((lang: 'zh-CN' | 'en-US') => {
      this.currentLangLabel = lang === 'zh-CN' ? '简体中文' : 'English';
    });
  }

  setLanguage(lang: 'zh-CN' | 'en-US'): void {
    this.i18nService.setLanguage(lang);
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
