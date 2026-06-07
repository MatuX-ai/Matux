/**
 * 首次启动引导组件
 * 
 * 功能:
 * 1. 6 步引导流程
 * 2. 设备能力评估
 * 3. 插件推荐选择
 * 4. 捆绑包选择
 * 5. 批量下载安装
 * 6. 完成标记
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatStepperModule } from '@angular/material/stepper';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface GuideStep {
  id: string;
  title: string;
  description: string;
  icon: string;
  order: number;
  action?: string;
  optional?: boolean;
}

interface Module {
  id: string;
  name: string;
  description: string;
  size: string;
  category: string;
  recommended?: boolean;
}

@Component({
  selector: 'app-first-run-guide',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatStepperModule,
    MatCheckboxModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatDialogModule,
  ],
  templateUrl: './first-run-guide.component.html',
  styleUrls: ['./first-run-guide.component.scss'],
})
export class FirstRunGuideComponent implements OnInit, OnDestroy {
  // 引导步骤
  steps: GuideStep[] = [];
  currentStep = 0;
  loading = false;
  
  // 设备信息
  deviceClass = '';
  deviceScore = 0;
  deviceAssessing = false;
  
  // 模块选择
  availableModules: Module[] = [];
  selectedModules: Set<string> = new Set();
  modulesLoading = false;
  
  // 捆绑包选择
  bundles: any[] = [];
  selectedBundles: Set<string> = new Set();
  bundlesLoading = false;
  
  // 安装进度
  installing = false;
  installProgress = 0;
  installCurrent = '';
  installTotal = 0;
  
  private destroy$ = new Subject<void>();
  
  constructor(
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
  ) {}
  
  ngOnInit(): void {
    this.loadGuideSteps();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * 加载引导步骤
   */
  async loadGuideSteps(): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = (await window.pluginAPI.getFirstRunGuide()) as { success: boolean; data: { steps: GuideStep[] } };
      if (result.success && result.data) {
        this.steps = result.data.steps.sort((a: GuideStep, b: GuideStep) => a.order - b.order);
      }
    } catch (err) {
      console.error('加载引导步骤失败:', err);
      // 使用默认步骤
      this.steps = this.getDefaultSteps();
    }
  }
  
  /**
   * 默认引导步骤
   */
  getDefaultSteps(): GuideStep[] {
    return [
      { id: 'welcome', title: '欢迎使用', description: '让我们为您配置最佳的学习环境', icon: 'waving_hand', order: 1 },
      { id: 'device-assessment', title: '设备评估', description: '检测您的硬件配置', icon: 'memory', order: 2, action: 'assess_device' },
      { id: 'plugin-selection', title: '选择插件', description: '基于设备评级为您推荐插件', icon: 'extension', order: 3, action: 'show_recommendations' },
      { id: 'bundle-selection', title: '选择捆绑包', description: '一键安装常用插件组合', icon: 'inventory_2', order: 4, action: 'show_bundles', optional: true },
      { id: 'download-install', title: '下载安装', description: '开始下载选中的插件', icon: 'download', order: 5, action: 'start_download' },
      { id: 'complete', title: '设置完成', description: '开始您的学习之旅', icon: 'check_circle', order: 6 },
    ];
  }
  
  /**
   * 评估设备
   */
  async assessDevice(): Promise<void> {
    this.deviceAssessing = true;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = (await window.pluginAPI.reassessDevice()) as { success: boolean; data: any };
      if (result.success && result.data) {
        this.deviceClass = result.data.assessment?.deviceClass || 'basic';
        this.deviceScore = result.data.assessment?.score || 0;
        
        this.snackBar.open(`设备评级: ${this.deviceClass} (${this.deviceScore}分)`, '关闭', {
          duration: 3000,
        });
      }
    } catch (err) {
      this.snackBar.open(`设备评估失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    } finally {
      this.deviceAssessing = false;
    }
  }
  
  /**
   * 加载推荐模块
   */
  async loadRecommendedModules(): Promise<void> {
    this.modulesLoading = true;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = (await window.pluginAPI.getRecommendedModules(this.deviceClass)) as { success: boolean; data: any[] };
      if (result.success && result.data) {
        this.availableModules = result.data;
        // 默认选中所有推荐模块
        this.selectedModules = new Set(
          this.availableModules.filter(m => m.recommended).map(m => m.id)
        );
      }
    } catch (err) {
      this.snackBar.open(`加载模块失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    } finally {
      this.modulesLoading = false;
    }
  }
  
  /**
   * 切换模块选择
   */
  toggleModule(moduleId: string): void {
    if (this.selectedModules.has(moduleId)) {
      this.selectedModules.delete(moduleId);
    } else {
      this.selectedModules.add(moduleId);
    }
  }
  
  /**
   * 下一步
   */
  async nextStep(): Promise<void> {
    const currentStep = this.steps[this.currentStep];
    
    // 根据步骤执行相应操作
    if (currentStep.action === 'assess_device') {
      await this.assessDevice();
    } else if (currentStep.action === 'show_recommendations') {
      await this.loadRecommendedModules();
    } else if (currentStep.action === 'show_bundles') {
      await this.loadBundles();
    } else if (currentStep.action === 'start_download') {
      await this.startInstallation();
      return; // 安装完成后自动进入下一步
    }
    
    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++;
    }
  }
  
  /**
   * 上一步
   */
  prevStep(): void {
    if (this.currentStep > 0) {
      this.currentStep--;
    }
  }
  
  /**
   * 加载捆绑包
   */
  async loadBundles(): Promise<void> {
    this.bundlesLoading = true;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = (await window.pluginAPI.getRecommendations({
        maxRecommendations: 0,
        includeBundles: true,
      })) as { success: boolean; data: { bundles: any[] } };
      
      if (result.success && result.data) {
        this.bundles = result.data.bundles || [];
        // 默认选中第一个捆绑包
        if (this.bundles.length > 0) {
          this.selectedBundles.add(this.bundles[0].id);
        }
      }
    } catch (err) {
      this.snackBar.open(`加载捆绑包失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    } finally {
      this.bundlesLoading = false;
    }
  }
  
  /**
   * 切换捆绑包选择
   */
  toggleBundle(bundleId: string): void {
    if (this.selectedBundles.has(bundleId)) {
      this.selectedBundles.delete(bundleId);
    } else {
      this.selectedBundles.add(bundleId);
    }
  }
  
  /**
   * 开始安装
   */
  async startInstallation(): Promise<void> {
    this.installing = true;
    this.installProgress = 0;
    
    try {
      // 合并模块和捆绑包中的插件
      const pluginsToInstall = new Set<string>();
      
      // 添加选中的模块
      for (const moduleId of this.selectedModules) {
        pluginsToInstall.add(moduleId);
      }
      
      // 添加选中捆绑包中的插件
      for (const bundleId of this.selectedBundles) {
        const bundle = this.bundles.find(b => b.id === bundleId);
        if (bundle) {
          for (const pluginId of bundle.plugins) {
            pluginsToInstall.add(pluginId);
          }
        }
      }
      
      const pluginsArray = Array.from(pluginsToInstall);
      this.installTotal = pluginsArray.length;
      
      // 逐个安装
      for (let i = 0; i < pluginsArray.length; i++) {
        const pluginId = pluginsArray[i];
        this.installCurrent = pluginId;
        
        try {
          if (!window.pluginAPI) {
            throw new Error('Plugin API 不可用');
          }
          
          await window.pluginAPI.installPlugin(pluginId);
          await window.pluginAPI.addInstalledModule(pluginId);
          
          this.installProgress = ((i + 1) / this.installTotal) * 100;
        } catch (err) {
          console.warn(`插件 ${pluginId} 安装失败:`, err);
        }
      }
      
      // 标记首次运行完成
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      await window.pluginAPI.markFirstRunCompleted();
      
      this.snackBar.open('安装完成！', '关闭', { duration: 3000 });
      
      // 延迟进入下一步
      setTimeout(() => {
        if (this.currentStep < this.steps.length - 1) {
          this.currentStep++;
        }
      }, 1000);
    } catch (err) {
      this.snackBar.open(`安装失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    } finally {
      this.installing = false;
    }
  }
  
  /**
   * 跳过当前步骤
   */
  skipStep(): void {
    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++;
    }
  }
  
  /**
   * 完成引导
   */
  completeGuide(): void {
    this.snackBar.open('欢迎使用 iMato！', '关闭', { duration: 3000 });
    // 可以在这里触发路由跳转到主页
  }
}
