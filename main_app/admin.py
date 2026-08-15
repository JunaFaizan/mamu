from django.contrib import admin

from .models import Booking, Group, Purchase, Room


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('item', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('item', 'notes')


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
