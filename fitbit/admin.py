from django.contrib import admin
from .models import FitbitUser, DailySummary


@admin.register(FitbitUser)
class FitbitUserAdmin(admin.ModelAdmin):
    list_display = ('fitbit_user_id', 'user', 'get_username', 'get_is_staff', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('fitbit_user_id', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

    def get_username(self, obj):
        return obj.user.username if obj.user else 'N/A'
    get_username.short_description = 'Django Username'

    def get_is_staff(self, obj):
        return obj.user.is_staff if obj.user else False
    get_is_staff.short_description = 'Is Staff'
    get_is_staff.boolean = True


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ('fitbit_user_id', 'date', 'steps', 'distance', 'resting_heart_rate', 'calories', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('fitbit_user_id',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date',)
