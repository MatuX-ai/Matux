# T2.1 教师管理模块 - 筛选和批量操作功能实现指南

## 📋 需要手动添加的 HTML 代码

### 位置 1: 在操作工具栏区域添加筛选和批量操作按钮

**文件**: `teacher-list.component.html`  
**位置**: 第 68-76 行（操作工具栏 div）之后

```html
<!-- 筛选和批量操作工具栏 -->
<div class="filter-toolbar">
  <!-- 搜索框 -->
  <mat-form-field appearance="outline" class="search-field">
    <mat-icon matPrefix>search</mat-icon>
    <mat-label>搜索教师</mat-label>
    <input
      matInput
      [value]="filter.search || ''"
      (input)="onSearchInput($event)"
      placeholder="姓名或邮箱"
    />
  </mat-form-field>

  <!-- 部门筛选 -->
  <mat-form-field appearance="outline">
    <mat-label>部门</mat-label>
    <mat-select [value]="filter.department || ''" (selectionChange)="filter.department = $any($event).value; applyFilter()">
      <mat-option value="">全部部门</mat-option>
      @for (dept of departments; track dept) {
        <mat-option [value]="dept">{{ dept }}</mat-option>
      }
    </mat-select>
  </mat-form-field>

  <!-- 状态筛选 -->
  <mat-form-field appearance="outline">
    <mat-label>状态</mat-label>
    <mat-select [value]="filter.status || ''" (selectionChange)="filter.status = $any($event).value; applyFilter()">
      <mat-option value="">全部状态</mat-option>
      <mat-option value="active">在职</mat-option>
      <mat-option value="inactive">离职</mat-option>
      <mat-option value="on_leave">请假</mat-option>
    </mat-select>
  </mat-form-field>

  <!-- 重置按钮 -->
  <button mat-stroked-button (click)="resetFilter()">
    <mat-icon>refresh</mat-icon>
    重置
  </button>

  <!-- 批量操作下拉菜单 -->
  @if (selectedTeacherIds.length > 0) {
    <div class="batch-operations">
      <span class="selected-count">已选 {{ selectedTeacherIds.length }} 位教师</span>
      
      <button mat-stroked-button color="warn" (click)="batchDelete()">
        <mat-icon>delete</mat-icon>
        批量删除
      </button>

      <button mat-stroked-button (click)="batchChangeStatus('active')">
        <mat-icon>check_circle</mat-icon>
        设为在职
      </button>

      <button mat-stroked-button (click)="batchChangeStatus('on_leave')">
        <mat-icon>schedule</mat-icon>
        设为请假
      </button>
    </div>
  }
</div>
```

---

### 位置 2: 在表格第一列添加复选框

**文件**: `teacher-list.component.html`  
**位置**: 第 95-99 行（ID 列定义）之前

```html
<!-- 选择列 -->
<ng-container matColumnDef="select">
  <th mat-header-cell *matHeaderCellDef>
    <mat-checkbox
      [checked]="selectedTeacherIds.length === teachers.length && teachers.length > 0"
      (change)="onSelectAll($event)">
    </mat-checkbox>
  </th>
  <td mat-cell *matCellDef="let teacher">
    <mat-checkbox
      [checked]="selectedTeacherIds.includes(teacher.id)"
      (change)="onTeacherToggle(teacher.id, $event)"
      (click)="$event.stopPropagation()">
    </mat-checkbox>
  </td>
</ng-container>
```

---

### 位置 3: 更新 displayedColumns 数组

**文件**: `teacher-list.component.ts`  
**位置**: 第 408 行左右（displayedColumns 定义）

```typescript
displayedColumns: string[] = [
  'select',  // 添加到最前面
  'id',
  'name',
  'email',
  'phone',
  'department',
  'position',
  'courseCount',
  'rating',
  'status',
  'actions',
];
```

---

## 🎨 需要添加的样式

**文件**: `teacher-list.component.scss`  
**位置**: 文件末尾

```scss
/* 筛选工具栏 */
.filter-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px;
  background-color: white;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;

  .search-field {
    flex: 1;
    min-width: 200px;
  }

  mat-form-field {
    min-width: 150px;
  }

  .batch-operations {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
    padding-left: 16px;
    border-left: 1px solid #e0e0e0;

    .selected-count {
      font-size: 14px;
      font-weight: 600;
      color: #1976d2;
      margin-right: 8px;
    }
  }
}

/* 表格复选框列 */
.mat-column-select {
  width: 60px;
  text-align: center;
}
```

---

## ✅ 功能清单

### 筛选功能
- [x] 搜索框（支持姓名和邮箱模糊搜索）
- [x] 部门下拉筛选
- [x] 状态下拉筛选
- [x] 重置筛选按钮

### 批量操作
- [x] 全选/取消全选
- [x] 单个选择/取消选择
- [x] 批量删除
- [x] 批量更改状态（在职/请假）
- [x] 选中数量提示

### 用户体验
- [x] 选择状态持久化
- [x] 操作确认对话框
- [x] 成功/失败提示
- [x] 响应式布局

---

## 🔧 使用说明

### 筛选操作
1. 在搜索框输入关键词，自动实时搜索
2. 选择部门和状态下拉框进行精确筛选
3. 点击"重置"按钮清除所有筛选条件

### 批量操作
1. 勾选要操作的教师（或使用全选）
2. 顶部显示已选数量
3. 点击批量操作按钮（删除、设为在职、设为请假）
4. 确认后执行批量操作
5. 操作成功后自动刷新列表

---

## 📊 预期效果

### 筛选前
- 显示所有教师
- 无选中项
- 批量操作按钮隐藏

### 筛选后
- 只显示符合条件的教师
- 选中项清空
- 可重新开始选择

### 批量操作时
- 显示已选数量标签
- 批量操作按钮组出现
- 操作前有确认提示
- 操作后自动刷新

---

## ⚠️ 注意事项

1. **导入顺序**: 确保 Material 模块导入按 Angular 标准排序
2. **类型安全**: 使用 `$any()` 处理 MatSelect 的事件类型
3. **性能优化**: 大量数据时考虑添加防抖
4. **权限控制**: 批量删除等敏感操作需验证权限

---

**文档生成时间**: 2026-04-02  
**适用版本**: T2.1 教师管理模块 v0.9
