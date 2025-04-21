from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserCreditCard, UserPreferences, UserActivity


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserPreferencesInline(admin.StackedInline):
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'Preferences'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserPreferencesInline)


class UserCreditCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'credit_card', 'card_number_last4', 'status', 'joining_date', 'credit_limit')
    list_filter = ('status', 'annual_fee_waived', 'joining_date')
    search_fields = ('user__username', 'credit_card__card_name', 'card_number_last4')
    date_hierarchy = 'joining_date'
    raw_id_fields = ('user', 'credit_card')


class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'credit_card', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'activity_type', 'credit_card', 'description', 'metadata', 'created_at')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register other models
admin.site.register(UserCreditCard, UserCreditCardAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
