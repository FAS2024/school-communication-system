from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Communication,
    CommunicationAttachment,
    CommunicationTargetGroup,
    CommunicationRecipient,
    CommunicationComment,
    CustomUser, 
    Branch, 
    TeachingPosition, 
    NonTeachingPosition, 
    StaffProfile,
    StudentClass,
    ClassArm, 
    StudentProfile, 
    ParentProfile

)
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



# --- Inline classes for nested admin views ---

class CommunicationAttachmentInline(admin.TabularInline):
    model = CommunicationAttachment
    extra = 1


class CommunicationTargetGroupInline(admin.TabularInline):
    model = CommunicationTargetGroup
    extra = 1


class CommunicationRecipientInline(admin.TabularInline):
    model = CommunicationRecipient
    extra = 1


class CommunicationCommentInline(admin.TabularInline):
    model = CommunicationComment
    extra = 1
    readonly_fields = ['created_at']


# --- Main admin class ---

@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('message_type', 'title', 'sender', 'is_draft', 'scheduled_time', 'created_at')
    search_fields = ('title', 'body', 'sender__username')
    list_filter = ('message_type', 'is_draft', 'created_at')

    inlines = [
        CommunicationAttachmentInline,
        CommunicationTargetGroupInline,
        CommunicationRecipientInline,
        CommunicationCommentInline,
    ]


# Registering the remaining models separately (optional)
@admin.register(CommunicationAttachment)
class CommunicationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('communication', 'file', 'uploaded_at')


@admin.register(CommunicationRecipient)
class CommunicationRecipientAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'communication', 'read', 'read_at')


@admin.register(CommunicationComment)
class CommunicationCommentAdmin(admin.ModelAdmin):
    list_display = ('commenter', 'communication', 'created_at')
    search_fields = ('comment',)


@admin.register(CommunicationTargetGroup)
class CommunicationTargetGroupAdmin(admin.ModelAdmin):
    list_display = ('communication', 'role', 'branch', 'get_student_class', 'get_class_arm')

    def get_student_class(self, obj):
        return obj.student_class.name if obj.student_class else '-'
    get_student_class.short_description = 'Class'

    def get_class_arm(self, obj):
        return obj.class_arm.name if obj.class_arm else '-'
    get_class_arm.short_description = 'Arm'



admin.site.register(StudentClass, StudentClassAdmin)
admin.site.register(ClassArm, ClassArmAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Branch)
admin.site.register(TeachingPosition)
admin.site.register(NonTeachingPosition)
admin.site.register(StaffProfile)
admin.site.register(StudentProfile)
admin.site.register(ParentProfile)
