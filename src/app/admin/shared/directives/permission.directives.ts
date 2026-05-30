import { Directive, Input, OnInit, TemplateRef, ViewContainerRef } from '@angular/core';

import { Permission, PermissionService } from '../services/permission.service';

/**
 * 权限显示指令
 * 用法: *appHasPermission="'view_users'"
 */
@Directive({
  selector: '[appHasPermission]',
  standalone: false,
})
export class HasPermissionDirective implements OnInit {
  private permission!: Permission;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private permissionService: PermissionService
  ) {}

  @Input() set appHasPermission(permission: string) {
    this.permission = permission as Permission;
    this.updateView();
  }

  ngOnInit(): void {
    this.updateView();
  }

  private updateView(): void {
    if (this.permissionService.hasPermission(this.permission)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    } else {
      this.viewContainer.clear();
    }
  }
}

/**
 * 权限隐藏指令（与显示指令相反）
 * 用法: *appHasNoPermission="'view_users'"
 */
@Directive({
  selector: '[appHasNoPermission]',
  standalone: false,
})
export class HasNoPermissionDirective implements OnInit {
  private permission!: Permission;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private permissionService: PermissionService
  ) {}

  @Input() set appHasNoPermission(permission: string) {
    this.permission = permission as Permission;
    this.updateView();
  }

  ngOnInit(): void {
    this.updateView();
  }

  private updateView(): void {
    if (!this.permissionService.hasPermission(this.permission)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    } else {
      this.viewContainer.clear();
    }
  }
}

/**
 * 多权限显示指令（满足任一权限即可）
 * 用法: *appHasAnyPermission="['view_users', 'edit_users']"
 */
@Directive({
  selector: '[appHasAnyPermission]',
  standalone: false,
})
export class HasAnyPermissionDirective implements OnInit {
  private permissions: Permission[] = [];

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private permissionService: PermissionService
  ) {}

  @Input() set appHasAnyPermission(permissions: string[]) {
    this.permissions = permissions as Permission[];
    this.updateView();
  }

  ngOnInit(): void {
    this.updateView();
  }

  private updateView(): void {
    if (this.permissionService.hasAnyPermission(this.permissions)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    } else {
      this.viewContainer.clear();
    }
  }
}

/**
 * 多权限显示指令（必须满足所有权限）
 * 用法: *appHasAllPermissions="['view_users', 'edit_users']"
 */
@Directive({
  selector: '[appHasAllPermissions]',
  standalone: false,
})
export class HasAllPermissionsDirective implements OnInit {
  private permissions: Permission[] = [];

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private permissionService: PermissionService
  ) {}

  @Input() set appHasAllPermissions(permissions: string[]) {
    this.permissions = permissions as Permission[];
    this.updateView();
  }

  ngOnInit(): void {
    this.updateView();
  }

  private updateView(): void {
    if (this.permissionService.hasAllPermissions(this.permissions)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    } else {
      this.viewContainer.clear();
    }
  }
}

/**
 * 角色显示指令
 * 用法: *appHasRole="'admin'"
 */
@Directive({
  selector: '[appHasRole]',
  standalone: false,
})
export class HasRoleDirective implements OnInit {
  private role!: string;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private permissionService: PermissionService
  ) {}

  @Input() set appHasRole(role: string) {
    this.role = role;
    this.updateView();
  }

  ngOnInit(): void {
    this.updateView();
  }

  private updateView(): void {
    if (this.permissionService.hasRole(this.role as any)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    } else {
      this.viewContainer.clear();
    }
  }
}
