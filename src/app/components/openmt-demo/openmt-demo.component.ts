import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OpenMtSciEdService, Tutorial, HardwareProject } from '../../services/openmt-scied.service';

@Component({
  selector: 'app-openmt-demo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="openmt-demo">
      <h1>OpenMTSciEd API 集成测试</h1>

      <!-- 教程列表 -->
      <section>
        <h2>教程列表</h2>
        <button (click)="loadTutorials()">加载教程</button>
        <div *ngIf="loading" class="loading">加载中...</div>
        <div *ngIf="error" class="error">{{ error }}</div>
        <ul *ngIf="tutorials.length > 0">
          <li *ngFor="let tutorial of tutorials">
            <strong>{{ tutorial.title }}</strong> [{{ tutorial.subject }}]
            <p>{{ tutorial.description }}</p>
          </li>
        </ul>
      </section>

      <!-- 硬件项目 -->
      <section>
        <h2>硬件项目</h2>
        <button (click)="loadHardwareProjects()">加载硬件项目</button>
        <ul *ngIf="hardwareProjects.length > 0">
          <li *ngFor="let project of hardwareProjects">
            <strong>{{ project.title }}</strong> [{{ project.difficulty_level }}]
          </li>
        </ul>
      </section>
    </div>
  `,
  styles: [`
    .openmt-demo { padding: 20px; max-width: 1200px; margin: 0 auto; }
    section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
    button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #0056b3; }
    .loading { color: #666; font-style: italic; }
    .error { color: red; padding: 10px; background: #ffe6e6; border-radius: 4px; }
    ul { list-style: none; padding: 0; }
    li { padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 4px; }
  `]
})
export class OpenMtDemoComponent implements OnInit {
  tutorials: Tutorial[] = [];
  hardwareProjects: HardwareProject[] = [];
  loading = false;
  error: string | null = null;

  constructor(private openMtService: OpenMtSciEdService) {}

  ngOnInit() {
    // 自动加载教程
    this.loadTutorials();
  }

  loadTutorials() {
    this.loading = true;
    this.error = null;

    this.openMtService.getTutorials(1, 5).subscribe({
      next: (data) => {
        this.tutorials = data.items;
        this.loading = false;
        console.log('教程列表:', data);
      },
      error: (err) => {
        this.error = `加载失败: ${err.message}`;
        this.loading = false;
        console.error('错误:', err);
      }
    });
  }

  loadHardwareProjects() {
    this.loading = true;
    this.error = null;

    this.openMtService.getHardwareProjects(1, 5).subscribe({
      next: (data) => {
        this.hardwareProjects = data.items;
        this.loading = false;
        console.log('硬件项目:', data);
      },
      error: (err) => {
        this.error = `加载失败: ${err.message}`;
        this.loading = false;
        console.error('错误:', err);
      }
    });
  }
}
