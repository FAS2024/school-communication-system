from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Branch, TeachingPosition, NonTeachingPosition

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'role', 'branch', 'staff_type', 'is_active', 'is_staff')
    list_filter = ('role', 'branch', 'staff_type', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role/Branch', {'fields': ('role', 'branch', 'staff_type', 'teaching_positions', 'non_teaching_positions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'branch', 'staff_type', 'teaching_positions', 'non_teaching_positions', 'is_staff', 'is_active')}
        ),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Branch)
admin.site.register(TeachingPosition)
admin.site.register(NonTeachingPosition)
