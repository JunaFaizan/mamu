from django.contrib import admin

from .models import Booking, Group, Maintenance, Purchase, Room, Salary


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('item', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('item', 'notes')


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('staff_name', 'month', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('staff_name', 'month', 'notes')


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'amount', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('title', 'notes')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'type', 'rate', 'status')
    list_filter = ('status', 'type')
    search_fields = ('number', 'type')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'room', 'check_in', 'check_out', 'guests', 'status', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('guest_name', 'phone')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'members', 'check_in', 'check_out', 'status', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('group_name', 'contact', 'phone')
