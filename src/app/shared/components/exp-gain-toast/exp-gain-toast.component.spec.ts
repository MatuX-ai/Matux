/**
 * ExpGainToastComponent 冒烟测试
 *
 * 验证积分飞升动画组件基本功能
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { ExpGainToastComponent, ExpGainData } from './exp-gain-toast.component';

describe('ExpGainToastComponent', () => {
  let component: ExpGainToastComponent;
  let fixture: ComponentFixture<ExpGainToastComponent>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<ExpGainToastComponent>>;

  const defaultData: ExpGainData = {
    amount: 50,
    reason: '答对题目',
  };

  beforeEach(async () => {
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      imports: [ExpGainToastComponent, NoopAnimationsModule],
      providers: [
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: defaultData },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ExpGainToastComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display the EXP amount', () => {
    const el: HTMLElement = fixture.nativeElement;
    const amountEl = el.querySelector('.exp-amount');
    expect(amountEl?.textContent).toContain('+50');
  });

  it('should display EXP unit', () => {
    const el: HTMLElement = fixture.nativeElement;
    const unitEl = el.querySelector('.exp-unit');
    expect(unitEl?.textContent).toContain('EXP');
  });

  it('should display reason when provided', () => {
    const el: HTMLElement = fixture.nativeElement;
    const reasonEl = el.querySelector('.exp-reason');
    expect(reasonEl?.textContent).toContain('答对题目');
  });

  // fakeAsync zone 内重新创建组件,确保 setTimeout 在 fakeAsync zone 注册,
  // 否则 beforeEach 中的 setTimeout 跑在外部 zone,tick() 控制不到。
  it('should not display reason when not provided', () => {
    // OnPush 组件下,直接修改注入数据 + detectChanges 不会触发 *ngIf 重算,
    // 最干净的做法是重建 TestBed,提供一个无 reason 的 data。
    TestBed.resetTestingModule();
    void TestBed.configureTestingModule({
      imports: [ExpGainToastComponent, NoopAnimationsModule],
      providers: [
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: { amount: 100 } },
      ],
    });
    const localFixture = TestBed.createComponent(ExpGainToastComponent);
    localFixture.detectChanges();
    const localEl: HTMLElement = localFixture.nativeElement;
    expect(localEl.querySelector('.exp-reason')).toBeNull();
  });

  it('should auto-close after 1300ms', fakeAsync(() => {
    // 在 fakeAsync zone 内重新创建组件,确保构造器的 setTimeout 注册到 fakeAsync zone
    const localDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);
    TestBed.resetTestingModule();
    void TestBed.configureTestingModule({
      imports: [ExpGainToastComponent, NoopAnimationsModule],
      providers: [
        { provide: MatDialogRef, useValue: localDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: { amount: 10 } },
      ],
    });
    const localTestFixture = TestBed.createComponent(ExpGainToastComponent);
    localTestFixture.detectChanges();

    expect(localDialogRef.close).not.toHaveBeenCalled();
    tick(1300);
    expect(localDialogRef.close).toHaveBeenCalledTimes(1);
  }));

  it('should have correct data binding', () => {
    expect(component.data.amount).toBe(50);
    expect(component.data.reason).toBe('答对题目');
  });
});