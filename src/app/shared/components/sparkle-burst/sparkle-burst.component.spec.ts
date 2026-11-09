/**
 * SparkleBurstComponent 单元测试
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';

import { SparkleBurstComponent } from './sparkle-burst.component';

describe('SparkleBurstComponent (P0-1/2/4 共享)', () => {
  let fixture: ComponentFixture<SparkleBurstComponent>;
  let component: SparkleBurstComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CommonModule, SparkleBurstComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SparkleBurstComponent);
    component = fixture.componentInstance;
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('默认 active=false 不创建粒子', () => {
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelectorAll('.particle').length).toBe(0);
  });

  it('active=true 触发 burst 后会创建 count 个粒子并清理', async () => {
    component.x = 100;
    component.y = 200;
    component.count = 6;
    component.active = true;
    fixture.detectChanges();
    // 等待 microtask + burst 创建
    await new Promise((r) => setTimeout(r, 30));
    const host: HTMLElement = fixture.nativeElement;
    const particles = host.querySelectorAll('.particle');
    expect(particles.length).toBe(6);
    // 等待动画结束（mock 时长 800ms）
    await new Promise((r) => setTimeout(r, 900));
    expect(host.querySelectorAll('.particle').length).toBe(0);
  });

  it('color 输入传到粒子', async () => {
    component.x = 0;
    component.y = 0;
    component.count = 2;
    component.color = '#06b6d4';
    component.active = true;
    fixture.detectChanges();
    await new Promise((r) => setTimeout(r, 30));
    const p: HTMLElement | null = fixture.nativeElement.querySelector('.particle');
    expect(p?.style.background).toContain('rgb(6, 182, 212)');
  });
});
