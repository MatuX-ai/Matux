import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

@Component({
  selector: 'mac-icon',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (name && iconPath) {
      <img
        [src]="iconPath"
        [alt]="name"
        class="mac-icon"
        [class.sm]="size === 'sm'"
        [class.md]="size === 'md'"
        [class.lg]="size === 'lg'"
        [class.xl]="size === 'xl'"
        (error)="onImageError($event)"
      />
    }
    @if (!iconPath) {
      <span class="mac-icon-fallback">[{{ name }}]</span>
    }
  `,
  styles: [
    `
      .mac-icon {
        display: inline-block;
        vertical-align: middle;
        object-fit: contain;
      }
      .mac-icon.sm {
        width: 14px;
        height: 14px;
      }
      .mac-icon.md {
        width: 20px;
        height: 20px;
      }
      .mac-icon.lg {
        width: 28px;
        height: 28px;
      }
      .mac-icon.xl {
        width: 40px;
        height: 40px;
      }
      .mac-icon-fallback {
        display: inline-block;
        font-size: 12px;
        color: #ff3b30;
        background: #fee2e2;
        padding: 2px 6px;
        border-radius: 4px;
      }
    `,
  ],
})
export class MacIconComponent {
  @Input() name: string = '';
  @Input() size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
  @Input() color: string = '';

  // 自定义图标列表 - 这些图标位于 /assets/icons/ 根目录
  private customIcons = [
    'phone',
    'desktop',
    'ar',
    'robot',
    'gift',
    'link',
    'code',
    'ai',
    'cloud',
    'blockchain',
    'network',
    'user',
    'users',
    'school',
    'building',
    'home',
    'arrow-right',
    'arrow-down',
    'download',
    'upload',
    'play',
    'search',
    'settings',
    'menu',
    'close',
    'star',
    'check',
    'warning',
    'error',
    'info',
    'favorite',
    'file',
    'folder',
    'image',
    'video',
    'email',
    'notification',
    'mic',
    'cart',
    'card',
    'add',
    'edit',
    'delete',
    'save',
    'refresh',
    'share',
    'check_circle',
    'location_on',
    'rocket',
    'gamepad',
    'cube',
    'brain',
    'wifi',
    'cpu',
    'database',
    'globe',
    'lock',
    'key',
    'calendar',
    'clock',
    'bell',
    'heart',
    'book',
    'lightbulb',
    'target',
    'award',
    'trending_up',
    'activity',
    'lock_open',
    'logo',
  ];

  get iconPath(): string {
    // 优先使用相对路径,回退到绝对路径
    if (this.name === 'logo') {
      return 'assets/branding/logo.png';
    }
    if (this.customIcons.includes(this.name)) {
      return `assets/icons/${this.name}.svg`;
    }
    return '';
  }

  onImageError(event: any): void {
    console.error(`MacIcon: Failed to load icon "${this.name}" from path: ${this.iconPath}`);
    // 尝试使用绝对路径作为fallback
    if (!this.iconPath.startsWith('/')) {
      event.target.src = `/${this.iconPath}`;
    }
  }
}
