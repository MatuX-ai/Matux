/**
 * LevelUpModalComponent 单元测试
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { LevelUpModalComponent } from './level-up-modal.component';
import { LevelEventService } from '../../../core/services/level-event.service';
import { LevelTitleService } from '../../../core/services/level-title.service';
import type { UserLevel } from '../../../user/student/services/student-dashboard-data.service';

function lvl(current: number, totalExp = 0): UserLevel {
  return {
    current,
    title: '',
    exp: 0,
    expToNext: 0,
    totalExp,
    expProgressPercent: 0,
  };
}

describe('LevelUpModalComponent (P0-2)', () => {
  let fixture: ComponentFixture<LevelUpModalComponent>;
  let component: LevelUpModalComponent;
  let levelEvent: LevelEventService;
  let levelTitle: LevelTitleService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CommonModule, NoopAnimationsModule, LevelUpModalComponent],
      providers: [LevelEventService, LevelTitleService],
    }).compileComponents();

    fixture = TestBed.createComponent(LevelUpModalComponent);
    component = fixture.componentInstance;
    levelEvent = TestBed.inject(LevelEventService);
    levelTitle = TestBed.inject(LevelTitleService);
    levelEvent.reset();
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('默认不渲染 mask', () => {
    const mask: HTMLElement | null = fixture.nativeElement.querySelector('.level-up-mask');
    expect(mask).toBeNull();
  });

  it('emitLevelUp 后依次进入 4 阶段', fakeAsync(() => {
    // countUp 使用 performance.now()，fakeAsync 只 mock setTimeout/Date.now 不 mock performance.now。
    // 覆写为 Date.now() 后 fakeAsync 可正确驱动 countUp。
    spyOn(performance, 'now').and.callFake(() => Date.now());

    const payload = { old: lvl(2, 0), next: lvl(3, 700), totalExp: 700 };
    levelEvent.emitLevelUp('u1', payload.old, payload.next, payload.totalExp);
    tick(16);
    fixture.detectChanges();
    expect(component.phase).toBe('enter');
    tick(400);
    fixture.detectChanges();
    expect(component.phase).toBe('old-burst');
    tick(400);
    fixture.detectChanges();
    expect(component.phase).toBe('new-reveal');
    tick(800);
    fixture.detectChanges();
    expect(component.phase).toBe('title');
    // countUp 从 phase='title' 后开始，duration=1200ms，需 tick 足
    tick(1300);
    fixture.detectChanges();
    expect(component.displayedExp).toBe(700);
  }));

  it('title 阶段应展示新称号', fakeAsync(() => {
    levelEvent.emitLevelUp('u1', lvl(2), lvl(5, 1500), 1500);
    tick(1600);
    fixture.detectChanges();
    expect(component.newTitleLabel.length).toBeGreaterThan(0);
    expect(component.newTierColor).toBeTruthy();
  }));

  it('close() 切到 exit 然后 idle', fakeAsync(() => {
    levelEvent.emitLevelUp('u1', lvl(2), lvl(3, 700), 700);
    tick(1600);
    fixture.detectChanges();
    component.close();
    expect(component.phase).toBe('exit');
    tick(400);
    fixture.detectChanges();
    expect(component.phase).toBe('idle');
    expect(component.visible).toBeFalse();
  }));

  it('Esc 关闭', fakeAsync(() => {
    levelEvent.emitLevelUp('u1', lvl(2), lvl(3, 700), 700);
    tick(1600);
    fixture.detectChanges();
    component.onEsc();
    tick(400);
    fixture.detectChanges();
    expect(component.visible).toBeFalse();
  }));

  it('新等级为 10 满级使用 star 段位色', fakeAsync(() => {
    levelEvent.emitLevelUp('u1', lvl(9, 14000), lvl(10, 21000), 21000);
    tick(16);
    fixture.detectChanges();
    expect(component.newTierColor).toBe(levelTitle.getTierColor('star'));
  }));
});
