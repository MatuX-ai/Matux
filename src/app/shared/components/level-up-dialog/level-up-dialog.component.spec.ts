/**
 * LevelUpDialogComponent 冒烟测试
 *
 * 验证升级庆祝弹窗基本功能
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { LevelUpDialogComponent, LevelUpData } from './level-up-dialog.component';

describe('LevelUpDialogComponent', () => {
  let component: LevelUpDialogComponent;
  let fixture: ComponentFixture<LevelUpDialogComponent>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<LevelUpDialogComponent>>;

  const mockData: LevelUpData = {
    oldLevel: {
      current: 4,
      title: '学徒',
      exp: 800,
      expToNext: 1000,
      totalExp: 1800,
      expProgressPercent: 80,
    },
    newLevel: {
      current: 5,
      title: '探索者',
      exp: 200,
      expToNext: 1500,
      totalExp: 2000,
      expProgressPercent: 13,
    },
  };

  beforeEach(async () => {
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      imports: [LevelUpDialogComponent, NoopAnimationsModule],
      providers: [
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: mockData },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LevelUpDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display new level number', () => {
    const el: HTMLElement = fixture.nativeElement;
    const lvText = el.querySelector('.lv-text');
    expect(lvText?.textContent).toContain('Lv.5');
  });

  it('should display celebration title', () => {
    const el: HTMLElement = fixture.nativeElement;
    const title = el.querySelector('.title');
    expect(title?.textContent).toContain('升级啦');
  });

  it('should display new level title', () => {
    const el: HTMLElement = fixture.nativeElement;
    const subtitle = el.querySelector('.subtitle');
    expect(subtitle?.textContent).toContain('探索者');
  });

  it('should display old and new level in transition row', () => {
    const el: HTMLElement = fixture.nativeElement;
    const oldLevel = el.querySelector('.old-level');
    const newLevel = el.querySelector('.new-level');
    expect(oldLevel?.textContent).toContain('Lv.4');
    expect(oldLevel?.textContent).toContain('学徒');
    expect(newLevel?.textContent).toContain('Lv.5');
    expect(newLevel?.textContent).toContain('探索者');
  });

  it('should close dialog when onClose is called', () => {
    component.onClose();
    expect(dialogRefSpy.close).toHaveBeenCalledTimes(1);
  });

  it('should have confirm button that calls onClose', () => {
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector('.confirm-btn') as HTMLButtonElement;
    expect(btn).toBeTruthy();
    expect(btn.textContent).toContain('继续学习');
    btn.click();
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });

  it('should have correct data binding', () => {
    expect(component.data.oldLevel.current).toBe(4);
    expect(component.data.newLevel.current).toBe(5);
  });
});
