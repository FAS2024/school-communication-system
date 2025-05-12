from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Branch, TeachingPosition, NonTeachingPosition, StaffProfile,StudentClass,ClassArm
from django.utils.html import format_html  # Import format_html


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'role', 'branch', 'staff_type', 'gender', 'is_active', 'is_staff', 'profile_picture_thumb')
    list_filter = ('role', 'branch', 'staff_type', 'gender', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'gender', 'profile_picture')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role/Branch', {'fields': ('role', 'branch', 'staff_type', 'teaching_positions', 'non_teaching_positions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'role', 'branch', 'staff_type', 'teaching_positions', 'non_teaching_positions',
                'is_staff', 'is_active', 'gender', 'profile_picture'
            ),
        }),
    )

    def profile_picture_thumb(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_picture.url)
        return 'No image'

    profile_picture_thumb.short_description = 'Profile Picture'


class StudentClassAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('arms',)  # Allows selecting multiple arms with checkboxes

class ClassArmAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(StudentClass, StudentClassAdmin)
admin.site.register(ClassArm, ClassArmAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Branch)
admin.site.register(TeachingPosition)
admin.site.register(NonTeachingPosition)
admin.site.register(StaffProfile)
