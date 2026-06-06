/**
 * 我的插件 - 前端组件
 * 
 * 这是一个示例 Angular 组件，展示如何创建插件的前端 UI。
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface PluginResponse {
  success: boolean;
  message: string;
  data?: any;
}

@Component({
  selector: 'app-my-plugin',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatInputModule,
    MatFormFieldModule,
    MatSnackBarModule,
  ],
  templateUrl: './my-plugin.component.html',
  styleUrls: ['./my-plugin.component.scss'],
})
export class MyPluginComponent implements OnInit, OnDestroy {
  // 数据
  message = '';
  responseData: any = null;
  loading = false;
  error: string | null = null;
  
  // 表单
  inputName = '';
  inputValue = '';
  
  private destroy$ = new Subject<void>();
  
  constructor(
    private http: HttpClient,
    private snackBar: MatSnackBar,
  ) {}
  
  ngOnInit(): void {
    this.loadHello();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * 加载 Hello World 消息
   */
  async loadHello(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      const response = await this.http.get<PluginResponse>('/api/v1/my-plugin/hello')
        .pipe(takeUntil(this.destroy$))
        .toPromise();
      
      if (response?.success) {
        this.message = response.message;
        this.responseData = response.data;
      } else {
        this.error = '加载失败';
      }
    } catch (err) {
      this.error = `请求失败: ${(err as Error).message}`;
      this.snackBar.open(this.error, '关闭', { duration: 5000 });
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * 处理数据
   */
  async processData(): Promise<void> {
    if (!this.inputName.trim()) {
      this.snackBar.open('请输入名称', '关闭', { duration: 2000 });
      return;
    }
    
    this.loading = true;
    this.error = null;
    
    try {
      const response = await this.http.post<PluginResponse>('/api/v1/my-plugin/process', {
        name: this.inputName,
        value: this.inputValue || null,
      })
        .pipe(takeUntil(this.destroy$))
        .toPromise();
      
      if (response?.success) {
        this.message = response.message;
        this.responseData = response.data;
        this.snackBar.open('处理成功', '关闭', { duration: 2000 });
      } else {
        this.error = '处理失败';
        this.snackBar.open(this.error, '关闭', { duration: 3000 });
      }
    } catch (err) {
      this.error = `请求失败: ${(err as Error).message}`;
      this.snackBar.open(this.error, '关闭', { duration: 5000 });
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * 清除表单
   */
  clearForm(): void {
    this.inputName = '';
    this.inputValue = '';
    this.responseData = null;
  }
}
