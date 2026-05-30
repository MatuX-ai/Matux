"""
硬件模块Django管理界面扩展
提供硬件模块和租赁记录的后台管理功能
"""

from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from models.hardware_module import (
    DamageLevel,
    HardwareModule,
    HardwareModuleStatus,
    ModuleRentalRecord,
    ModuleRentalStatus,
)


@admin.register(HardwareModule)
class HardwareModuleAdmin(admin.ModelAdmin):
    """硬件模块管理界面"""

    list_display = [
        "name",
        "module_type",
        "serial_number",
        "price_per_day",
        "total_quantity",
        "quantity_available",
        "status_badge",
        "is_active",
        "created_at",
    ]

    list_filter = ["module_type", "status", "is_active", "created_at"]

    search_fields = ["name", "serial_number", "description"]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("基本信息"),
            {"fields": ("name", "module_type", "serial_number", "description")},
        ),
        (_("价格信息"), {"fields": ("price_per_day", "deposit_amount")}),
        (_("库存信息"), {"fields": ("total_quantity", "quantity_available")}),
        (_("状态管理"), {"fields": ("status", "is_active")}),
        (
            _("时间信息"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = [
        "make_available",
        "make_unavailable",
        "activate_modules",
        "deactivate_modules",
    ]

    def status_badge(self, obj):
        """显示状态徽章"""
        status_colors = {
            HardwareModuleStatus.AVAILABLE: "success",
            HardwareModuleStatus.RENTED: "warning",
            HardwareModuleStatus.MAINTENANCE: "info",
            HardwareModuleStatus.RETIRED: "secondary",
        }

        color = status_colors.get(obj.status, "secondary")
        return format_html(
            '<span class="badge badge-{}">{}</span>', color, obj.get_status_display()
        )

    status_badge.short_description = _("状态")
    status_badge.allow_tags = True

    def make_available(self, request, queryset):
        """批量设为可用"""
        updated = queryset.update(status=HardwareModuleStatus.AVAILABLE)
        self.message_user(
            request, f"已将 {updated} 个模块设为可用状态", messages.SUCCESS
        )

    make_available.short_description = _("设为可用")

    def make_unavailable(self, request, queryset):
        """批量设为不可用"""
        updated = queryset.update(status=HardwareModuleStatus.RETIRED)
        self.message_user(
            request, f"已将 {updated} 个模块设为不可用状态", messages.WARNING
        )

    make_unavailable.short_description = _("设为不可用")

    def activate_modules(self, request, queryset):
        """批量激活模块"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"已激活 {updated} 个模块", messages.SUCCESS)

    activate_modules.short_description = _("激活选中模块")

    def deactivate_modules(self, request, queryset):
        """批量停用模块"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"已停用 {updated} 个模块", messages.WARNING)

    deactivate_modules.short_description = _("停用选中模块")


@admin.register(ModuleRentalRecord)
class ModuleRentalRecordAdmin(admin.ModelAdmin):
    """模块租赁记录管理界面"""

    list_display = [
        "id",
        "module_link",
        "user_license_link",
        "rental_period",
        "daily_rate",
        "total_amount",
        "status_badge",
        "is_damaged",
        "damage_level_display",
        "created_at",
    ]

    list_filter = [
        "status",
        "is_damaged",
        "damage_level",
        "created_at",
        "actual_return_date",
    ]

    search_fields = [
        "module__name",
        "module__serial_number",
        "user_license__license_key",
    ]

    readonly_fields = ["created_at", "updated_at", "compensation_amount"]

    fieldsets = (
        (
            _("基础信息"),
            {
                "fields": (
                    "module",
                    "user_license",
                    "rental_start_date",
                    "rental_end_date",
                    "actual_return_date",
                )
            },
        ),
        (
            _("费用信息"),
            {
                "fields": (
                    "daily_rate",
                    "total_amount",
                    "deposit_paid",
                    "deposit_refunded",
                )
            },
        ),
        (
            _("状态信息"),
            {
                "fields": (
                    "status",
                    "is_damaged",
                    "damage_level",
                    "damage_description",
                    "compensation_amount",
                )
            },
        ),
        (
            _("时间信息"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["mark_as_returned", "process_damage_claims"]

    def module_link(self, obj):
        """显示模块链接"""
        if obj.module:
            url = f"/admin/models/hardwaremodule/{obj.module.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.module.name)
        return "-"

    module_link.short_description = _("硬件模块")
    module_link.allow_tags = True

    def user_license_link(self, obj):
        """显示用户许可证链接"""
        if obj.user_license:
            url = f"/admin/models/userlicense/{obj.user_license.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.user_license.license_key)
        return "-"

    user_license_link.short_description = _("用户许可证")
    user_license_link.allow_tags = True

    def rental_period(self, obj):
        """显示租赁期间"""
        if obj.rental_start_date and obj.rental_end_date:
            return f"{obj.rental_start_date.strftime('%Y-%m-%d')} 至 {obj.rental_end_date.strftime('%Y-%m-%d')}"
        return "-"

    rental_period.short_description = _("租赁期间")

    def status_badge(self, obj):
        """显示状态徽章"""
        status_colors = {
            ModuleRentalStatus.ACTIVE: "primary",
            ModuleRentalStatus.OVERDUE: "danger",
            ModuleRentalStatus.RETURNED: "success",
            ModuleRentalStatus.COMPLETED: "secondary",
        }

        color = status_colors.get(obj.status, "secondary")
        return format_html(
            '<span class="badge badge-{}">{}</span>', color, obj.get_status_display()
        )

    status_badge.short_description = _("状态")
    status_badge.allow_tags = True

    def damage_level_display(self, obj):
        """显示损坏等级"""
        if obj.is_damaged and obj.damage_level:
            level_colors = {
                DamageLevel.LIGHT: "warning",
                DamageLevel.MODERATE: "orange",
                DamageLevel.SEVERE: "danger",
            }
            color = level_colors.get(obj.damage_level, "secondary")
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color,
                obj.get_damage_level_display(),
            )
        elif obj.is_damaged:
            return format_html('<span class="badge badge-secondary">未知</span>')
        return "-"

    damage_level_display.short_description = _("损坏等级")
    damage_level_display.allow_tags = True

    def mark_as_returned(self, request, queryset):
        """标记为已归还"""
        updated = 0
        for record in queryset:
            if record.status == ModuleRentalStatus.ACTIVE:
                record.status = ModuleRentalStatus.RETURNED
                record.actual_return_date = timezone.now()
                record.save()
                updated += 1

        self.message_user(
            request, f"已将 {updated} 个租赁记录标记为已归还", messages.SUCCESS
        )

    mark_as_returned.short_description = _("标记为已归还")

    def process_damage_claims(self, request, queryset):
        """处理损坏索赔"""
        damaged_records = queryset.filter(is_damaged=True, compensation_amount__gt=0)
        processed = 0

        for record in damaged_records:
            if record.status in [
                ModuleRentalStatus.RETURNED,
                ModuleRentalStatus.ACTIVE,
            ]:
                # 这里可以添加实际的损坏处理逻辑
                record.status = ModuleRentalStatus.COMPLETED
                record.save()
                processed += 1

        self.message_user(request, f"已处理 {processed} 个损坏索赔记录", messages.INFO)

    process_damage_claims.short_description = _("处理损坏索赔")


# 自定义管理站点配置
class HardwareRentalAdminSite(admin.AdminSite):
    """硬件租赁专用管理站点"""

    site_header = _("iMato 硬件租赁管理系统")
    site_title = _("硬件租赁管理")
    index_title = _("硬件租赁管理面板")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "inventory-report/",
                self.admin_view(self.inventory_report),
                name="inventory-report",
            ),
            path(
                "rental-statistics/",
                self.admin_view(self.rental_statistics),
                name="rental-statistics",
            ),
        ]
        return custom_urls + urls

    def inventory_report(self, request):
        """库存报告视图"""
        # 获取库存统计信息
        modules = HardwareModule.objects.all()
        total_modules = modules.count()
        available_modules = modules.filter(
            status=HardwareModuleStatus.AVAILABLE
        ).count()
        rented_modules = modules.filter(status=HardwareModuleStatus.RENTED).count()

        context = {
            "title": _("库存报告"),
            "total_modules": total_modules,
            "available_modules": available_modules,
            "rented_modules": rented_modules,
            "maintenance_modules": modules.filter(
                status=HardwareModuleStatus.MAINTENANCE
            ).count(),
            "retired_modules": modules.filter(
                status=HardwareModuleStatus.RETIRED
            ).count(),
        }

        return render(request, "admin/hardware/inventory_report.html", context)

    def rental_statistics(self, request):
        """租赁统计视图"""
        # 获取租赁统计信息
        records = ModuleRentalRecord.objects.all()
        active_rentals = records.filter(status=ModuleRentalStatus.ACTIVE).count()
        overdue_rentals = records.filter(status=ModuleRentalStatus.OVERDUE).count()
        total_revenue = records.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

        context = {
            "title": _("租赁统计"),
            "active_rentals": active_rentals,
            "overdue_rentals": overdue_rentals,
            "completed_rentals": records.filter(
                status=ModuleRentalStatus.COMPLETED
            ).count(),
            "total_revenue": total_revenue,
        }

        return render(request, "admin/hardware/rental_statistics.html", context)


# 注册自定义管理站点
hardware_rental_admin = HardwareRentalAdminSite(name="hardware_rental_admin")
hardware_rental_admin.register(HardwareModule, HardwareModuleAdmin)
hardware_rental_admin.register(ModuleRentalRecord, ModuleRentalRecordAdmin)
