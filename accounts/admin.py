from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Branch, TeachingPosition, NonTeachingPosition, StaffProfile
from django.utils.html import format_html  # Import format_html


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'role', 'branch', 'staff_type', 'is_active', 'is_staff', 'profile_picture_thumb')  # Add profile_picture_thumb
    list_filter = ('role', 'branch', 'staff_type', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    # Add profile_picture to fieldsets to allow viewing and updating the profile picture in the admin form
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'profile_picture')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role/Branch', {'fields': ('role', 'branch', 'staff_type', 'teaching_positions', 'non_teaching_positions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'branch', 'staff_type', 'teaching_positions', 'non_teaching_positions', 'is_staff', 'is_active', 'profile_picture')}
        ),
    )

    # Custom method to display the profile picture thumbnail in list display
    def profile_picture_thumb(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_picture.url)
        return 'No image'

    profile_picture_thumb.short_description = 'Profile Picture'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Branch)
admin.site.register(TeachingPosition)
admin.site.register(NonTeachingPosition)
admin.site.register(StaffProfile)
