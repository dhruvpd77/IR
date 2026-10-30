from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Asset, Category, InventoryItem, StockMovement, SubCategory, Ticket, TicketMedia, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Plant role', {'fields': ('role', 'employee_code', 'department', 'phone', 'created_by')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Plant role', {'fields': ('first_name', 'last_name', 'role', 'employee_code', 'department', 'phone')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'role', 'employee_code', 'department', 'is_active')
    list_filter = ('role', 'is_active', 'department')
    search_fields = ('username', 'first_name', 'last_name', 'employee_code')
    ordering = ('username',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sort_order', 'is_active')
    search_fields = ('name', 'code')


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'is_active')
    list_filter = ('category',)
    search_fields = ('name', 'code')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'location', 'subcategory', 'is_active')
    search_fields = ('code', 'name', 'location')
    list_filter = ('subcategory__category',)


class MediaInline(admin.TabularInline):
    model = TicketMedia
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_no', 'asset', 'status', 'priority', 'raised_by', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('ticket_no', 'asset__code', 'remarks')
    inlines = [MediaInline]


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'quantity', 'min_quantity', 'unit', 'location')
    search_fields = ('sku', 'name')


@admin.register(StockMovement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity_change', 'balance_after', 'reason', 'ticket', 'created_at')
    list_filter = ('reason',)
