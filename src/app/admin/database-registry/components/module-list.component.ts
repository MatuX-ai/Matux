import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatPaginator } from '@angular/material/paginator';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { debounceTime, distinctUntilChanged, Subscription } from 'rxjs';

import { DatabaseRegistryService, ModuleInfo } from '../services/database-registry.service';

import { ModuleActivationDialogComponent } from './module-activation-dialog.component';

@Component({
  selector: 'app-module-list',
  standalone: false,
  templateUrl: './module-list.component.html',
  styleUrls: ['./module-list.component.scss'],
})
export class ModuleListComponent implements OnInit, OnDestroy {
  dataSource = new MatTableDataSource<ModuleInfo>([]);
  displayedColumns: string[] = ['name', 'table_name', 'category', 'version', 'status', 'actions'];
  loading = true;
  error: string | null = null;

  filterForm: FormGroup;
  categories: string[] = [];

  private subscriptions = new Subscription();

  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatPaginator) paginator!: MatPaginator;

  constructor(
    private registryService: DatabaseRegistryService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
    private fb: FormBuilder
  ) {
    this.filterForm = this.fb.group({
      search: [''],
      category: ['all'],
      status: ['all'],
    });
  }

  ngOnInit(): void {
    this.loadModules();
    this.setupFilters();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  ngAfterViewInit(): void {
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
  }

  private loadModules(): void {
    this.loading = true;
    this.error = null;

    const sub = this.registryService.getRegistryModules().subscribe({
      next: (modules) => {
        this.dataSource.data = modules;
        this.extractCategories(modules);
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load modules:', error);
        this.error = '加载模块列表失败';
        this.loading = false;
      },
    });
    this.subscriptions.add(sub);
  }

  private setupFilters(): void {
    const searchSub = this.filterForm
      .get('search')!
      .valueChanges.pipe(debounceTime(300), distinctUntilChanged())
      .subscribe(() => this.applyFilter());

    const categorySub = this.filterForm
      .get('category')!
      .valueChanges.subscribe(() => this.applyFilter());

    const statusSub = this.filterForm
      .get('status')!
      .valueChanges.subscribe(() => this.applyFilter());

    this.subscriptions.add(searchSub);
    this.subscriptions.add(categorySub);
    this.subscriptions.add(statusSub);
  }

  private applyFilter(): void {
    const searchTerm = this.filterForm.get('search')!.value?.toLowerCase() || '';
    const category = this.filterForm.get('category')!.value;
    const status = this.filterForm.get('status')!.value;

    this.dataSource.filterPredicate = (data: ModuleInfo, filter: string): boolean => {
      const matchesSearch =
        !searchTerm ||
        data.name.toLowerCase().includes(searchTerm) ||
        data.table_name.toLowerCase().includes(searchTerm) ||
        (data.description ? data.description.toLowerCase().includes(searchTerm) : false);

      const matchesCategory = category === 'all' || data.category === category;
      const matchesStatus =
        status === 'all' ||
        (status === 'active' && data.is_active) ||
        (status === 'inactive' && !data.is_active);

      return Boolean(matchesSearch && matchesCategory && matchesStatus);
    };

    this.dataSource.filter = 'trigger'; // 触发过滤
  }

  private extractCategories(modules: ModuleInfo[]): void {
    const cats = [...new Set(modules.map((m) => m.category))];
    this.categories = cats.sort();
  }

  refreshModules(): void {
    this.loadModules();
  }

  toggleModuleStatus(module: ModuleInfo): void {
    const dialogRef = this.dialog.open(ModuleActivationDialogComponent, {
      width: '400px',
      data: {
        module,
        action: module.is_active ? 'deactivate' : 'activate',
      },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.updateModuleStatus(module.name, !module.is_active);
      }
    });
  }

  private updateModuleStatus(moduleName: string, isActive: boolean): void {
    const sub = this.registryService.toggleModuleStatus(moduleName, isActive).subscribe({
      next: () => {
        const module = this.dataSource.data.find((m) => m.name === moduleName);
        if (module) {
          module.is_active = isActive;
          this.dataSource.data = [...this.dataSource.data]; // 触发变更检测
        }

        this.snackBar.open(`模块 ${moduleName} 已${isActive ? '激活' : '停用'}`, '关闭', {
          duration: 3000,
        });
      },
      error: (error) => {
        console.error('Failed to update module status:', error);
        this.snackBar.open(`操作失败: ${error.message || '未知错误'}`, '关闭', { duration: 5000 });
      },
    });
    this.subscriptions.add(sub);
  }

  viewModuleDetails(module: ModuleInfo): void {
    // 导航到模块详情页
    // this.router.navigate(['../modules', module.name], { relativeTo: this.route });
    console.log('View details for module:', module.name);
  }

  getStatusColor(isActive: boolean): string {
    return isActive ? 'primary' : 'warn';
  }

  getStatusText(isActive: boolean): string {
    return isActive ? '活跃' : '停用';
  }

  getCategoryColor(category: string): string {
    const colors: { [key: string]: string } = {
      user: 'blue',
      course: 'green',
      education: 'orange',
      payment: 'purple',
      permission: 'red',
      hardware: 'brown',
      default: 'grey',
    };
    return colors[category as keyof typeof colors] || colors['default'] || 'grey';
  }

  clearFilters(): void {
    this.filterForm.reset({
      search: '',
      category: 'all',
      status: 'all',
    });
  }
}
