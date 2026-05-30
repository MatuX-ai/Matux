import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterModule } from '@angular/router';

// 指令
import {
  HasAllPermissionsDirective,
  HasAnyPermissionDirective,
  HasNoPermissionDirective,
  HasPermissionDirective,
  HasRoleDirective,
} from './directives/permission.directives';
// 服务
import { DataExportService } from './services/data-export.service';
import { PermissionService } from './services/permission.service';

@NgModule({
  declarations: [
    HasPermissionDirective,
    HasNoPermissionDirective,
    HasAnyPermissionDirective,
    HasAllPermissionsDirective,
    HasRoleDirective,
  ],
  imports: [CommonModule, MatIconModule, MatButtonModule, MatListModule, RouterModule],
  exports: [
    HasPermissionDirective,
    HasNoPermissionDirective,
    HasAnyPermissionDirective,
    HasAllPermissionsDirective,
    HasRoleDirective,
  ],
  providers: [DataExportService, PermissionService],
})
export class AdminSharedModule {}
