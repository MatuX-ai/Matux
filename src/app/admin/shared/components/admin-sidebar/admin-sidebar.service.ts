import { Injectable } from '@angular/core';

import { ADMIN_MENU_ITEMS, MENU_GROUPS, MenuItem } from './admin-sidebar.config';

/**
 * Admin 侧边栏菜单服务
 *
 * 负责管理菜单配置和权限过滤
 */
@Injectable({
  providedIn: 'root',
})
export class AdminSidebarService {
  private menuItems = ADMIN_MENU_ITEMS;
  private menuGroups = MENU_GROUPS;

  constructor() {}

  /**
   * 获取所有菜单项（不过滤）
   */
  getAllMenuItems(): MenuItem[] {
    return this.menuItems;
  }

  /**
   * 根据 ID 列表获取菜单项
   * @param ids 菜单项 ID 数组
   */
  getMenuItemsByIds(ids: string[]): MenuItem[] {
    return this.menuItems.filter((item) => ids.includes(item.id));
  }

  /**
   * 根据分组获取菜单项
   * @param groupId 分组索引
   */
  getMenuGroup(groupId: number): { title: string; items: MenuItem[] } | null {
    if (groupId < 0 || groupId >= this.menuGroups.length) {
      return null;
    }

    const group = this.menuGroups[groupId];
    const items = this.getMenuItemsByIds(group.items);

    return {
      title: group.title,
      items,
    };
  }

  /**
   * 获取所有分组菜单（已过滤）
   * @param accessibleIds 可访问的菜单项 ID 列表
   */
  getFilteredMenuGroups(accessibleIds: string[]): { title: string; items: MenuItem[] }[] {
    return this.menuGroups
      .map((group) => ({
        title: group.title,
        items: this.getMenuItemsByIds(group.items).filter((item) =>
          accessibleIds.includes(item.id)
        ),
      }))
      .filter((group) => group.items.length > 0);
  }

  /**
   * 根据权限过滤菜单项
   * @param accessibleIds 当前用户可访问的菜单项 ID 列表
   */
  getFilteredMenuItems(accessibleIds: string[]): MenuItem[] {
    return this.menuItems.filter((item) => accessibleIds.includes(item.id));
  }

  /**
   * 检查菜单项是否有子菜单
   */
  hasChildren(menuItem: MenuItem): boolean {
    return !!menuItem.children && menuItem.children.length > 0;
  }

  /**
   * 根据路由获取当前激活的菜单项 ID
   * @param currentRoute 当前路由路径
   */
  getActiveMenuItemId(currentRoute: string): string | null {
    for (const item of this.menuItems) {
      if (currentRoute.startsWith(item.route)) {
        return item.id;
      }

      // 检查子菜单
      if (item.children) {
        for (const child of item.children) {
          if (currentRoute.startsWith(child.route)) {
            return item.id;
          }
        }
      }
    }
    return null;
  }

  /**
   * 搜索菜单项
   * @param keyword 搜索关键词
   */
  searchMenuItems(keyword: string): MenuItem[] {
    const lowerKeyword = keyword.toLowerCase();

    const searchInItems = (items: MenuItem[]): MenuItem[] => {
      return items.filter((item) => {
        const titleMatch = item.title.toLowerCase().includes(lowerKeyword);
        const idMatch = item.id.toLowerCase().includes(lowerKeyword);

        if (titleMatch || idMatch) {
          return true;
        }

        // 在子菜单中搜索
        if (item.children) {
          return searchInItems(item.children).length > 0;
        }

        return false;
      });
    };

    return searchInItems(this.menuItems);
  }
}
