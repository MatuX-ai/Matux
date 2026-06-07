import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';

@Component({
  selector: 'app-minimal-dashboard',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatCardModule],
  templateUrl: './minimal-dashboard.component.html',
  styleUrls: ['./minimal-dashboard.component.scss'],
})
export class MinimalDashboardComponent {
  constructor(private router: Router) {}

  startLearning(): void {
    // 跳转到登录页面，用户可以点击"测试账号一键登录"
    void this.router.navigate(['/auth/login']);
  }
}
