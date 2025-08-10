import os
# Django Core
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.static import static
from django.utils import timezone

# Third-Party
from phonenumber_field.modelfields import PhoneNumberField

# Local App Imports
from accounts.utils import generate_profile_number, get_prefix_for_user
from django.utils.html import strip_tags


class StudentClass(models.Model):
    name = models.CharField(max_length=100, unique=True)
    arms = models.ManyToManyField('ClassArm', related_name='student_classes')
    class_teacher = models.ForeignKey(
        'CustomUser', 
        limit_choices_to={'role': 'staff'}, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='class_teacher_of'
    )

    def __str__(self):
        return self.name


class ClassArm(models.Model):
    name = models.CharField(max_length=50)  # e.g., Alpha, Gold, Apex

    def __str__(self):
        return self.name

class TeachingPosition(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_class_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class NonTeachingPosition(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('branch_admin', 'Branch Admin'),
        ('staff', 'Staff'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]

    STAFF_TYPE_CHOICES = [
        ('teaching', 'Teaching Staff'),
        ('non_teaching', 'Non-Teaching Staff'),
        ('both', 'Teaching and Non-Teaching Staff'),
    ]

    email = models.EmailField(unique=True, max_length=150)  # Updated to 191
    username = models.CharField(max_length=150, unique=True)  # Optional: reduced max_length if needed
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'),('others', 'Others')])
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        default='profile_pictures/default.png',
        help_text="Upload a profile picture."
    )
    
    staff_type = models.CharField(
        max_length=20,
        choices=STAFF_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Specify whether this staff is teaching, non-teaching, or both."
    )

    teaching_positions = models.ManyToManyField(
        TeachingPosition,
        blank=True,
        help_text="Select one or more teaching roles (e.g., class teacher, subject teacher)."
    )

    non_teaching_positions = models.ManyToManyField(
        NonTeachingPosition,
        blank=True,
        help_text="Select one or more non-teaching roles (e.g., driver, cook)."
    )

    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        # return static('assets/img/profile-pic.png')
        return static('profile_pictures/default.png')

class Branch(models.Model):
    name = models.CharField(max_length=150, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class ParentProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'parent'},
        related_name='parentprofile'
    )
    phone_number = PhoneNumberField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    relationship_to_student = models.CharField(
        max_length=20,
        choices=[
            ('father', 'Father'),
            ('mother', 'Mother'),
            ('guardian', 'Guardian'),
            ('other', 'Other'),
        ],
        default='father',
        verbose_name="Relationship to Student",
    )

    date_of_birth = models.DateField(null=True, blank=True)
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('sms', 'SMS')
        ],
        default='phone' 
    )
    nationality = models.CharField(max_length=50, default="Nigeria")
    state = models.CharField(max_length=50, default="Lagos")
    parent_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__last_name']
        verbose_name = "Parent Profile"
        verbose_name_plural = "Parent Profiles"

    def __str__(self):
        return self.user.get_full_name()
    
    def save(self, *args, **kwargs):
        if self.user.role != 'parent':
            raise ValidationError("User must have a 'parent' role.")

        if not self.parent_number:
            prefix = get_prefix_for_user(self.user)
            self.parent_number = generate_profile_number(prefix, ParentProfile)

        super().save(*args, **kwargs)


class StudentProfile(models.Model):
    user = models.OneToOneField(
        'CustomUser', 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'student'},
        related_name='studentprofile'
    )
    admission_number = models.CharField(max_length=50, unique=True, blank=False, null=False)
    current_class = models.ForeignKey('StudentClass', related_name='student_profiles', on_delete=models.SET_NULL, null=True)
    current_class_arm = models.ForeignKey('ClassArm', related_name='student_profiles', on_delete=models.SET_NULL, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    parent = models.ForeignKey('ParentProfile', on_delete=models.CASCADE, related_name='students')
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=50, default='Nigeria')  # temporary default
    state = models.CharField(max_length=50, default='Lagos') 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__last_name']
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return self.admission_number

    def save(self, *args, **kwargs):
        if self.user.role != 'student':
            raise ValidationError("User must have a 'student' role.")
        if not self.admission_number:
            prefix = get_prefix_for_user(self.user)  # This will return 'STU' for students
            self.admission_number = generate_profile_number(prefix, StudentProfile)
        super().save(*args, **kwargs)

    
class StaffProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['staff', 'superadmin', 'branch_admin']},
        related_name='staffprofile'
    )
    phone_number = PhoneNumberField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    address = models.TextField(blank=True, null=True)
    nationality = models.CharField(max_length=50, default="Nigeria")
    state = models.CharField(max_length=50, default="Lagos")
    staff_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    managing_class = models.ForeignKey('StudentClass', related_name='staff_profiles', on_delete=models.SET_NULL, null=True)
    managing_class_arm = models.ForeignKey('ClassArm', related_name='staff_profiles', on_delete=models.SET_NULL, null=True, blank=True)
    # position = models.ForeignKey(TeachingPosition, on_delete=models.SET_NULL, null=True, blank=True)
    # Generic foreign key fields
    position_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=models.Q(app_label='accounts', model__in=['teachingposition', 'nonteachingposition']),
    )
    position_object_id = models.PositiveIntegerField(null=True)
    primary_position = GenericForeignKey('position_content_type', 'position_object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['user__last_name']
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"

    def __str__(self):
        return self.user.get_full_name()
    
    def save(self, *args, **kwargs):
        if self.user.role not in ['staff', 'superadmin', 'branch_admin']:
            raise ValidationError("Invalid user role for StaffProfile")

        if not self.staff_number:
            prefix = get_prefix_for_user(self.user)
            self.staff_number = generate_profile_number(prefix, StaffProfile)

        super().save(*args, **kwargs)


class Communication(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('announcement', 'Announcement'),
        ('post', 'Post'),
        ('notification', 'Notification'),
        ('news', 'News'),
        ('personal', 'Personal'),
        ('group', 'Group'),
    ]

    sender = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='sent_communications')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    is_draft = models.BooleanField(default=False)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    selected_recipient_ids = models.JSONField(blank=True, default=list)
    manual_emails = models.JSONField(blank=True, default=list)
    requires_response = models.BooleanField(default=False)
    saved_filter_data = models.JSONField(blank=True, null=True)

    
    class Meta:
        indexes = [
            models.Index(fields=["sender", "is_draft"]),
            models.Index(fields=["sent", "scheduled_time"]),
        ]

    def short_body(self):
        clean_text = strip_tags(self.body)
        return clean_text[:75] + "..." if len(clean_text) > 75 else clean_text

    def is_due(self):
        return self.scheduled_time is None or self.scheduled_time <= timezone.now()

    def __str__(self):
        return f"{self.message_type.title()} from {self.sender.username}"


class CommunicationAttachment(models.Model):
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='communication_attachments/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    
    @property
    def basename(self):
        return os.path.basename(self.file.name)

class CommunicationTargetGroup(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('branch_admin', 'Branch Admin'),
        ('staff', 'Staff'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]

    STAFF_TYPE_CHOICES = [
        ('teaching', 'Teaching Staff'),
        ('non_teaching', 'Non-Teaching Staff'),
        ('both', 'Teaching and Non-Teaching Staff'),
    ]

    communication = models.ForeignKey(
        Communication, on_delete=models.CASCADE, related_name='target_groups'
    )
    branch = models.ForeignKey('Branch', null=False, blank=False, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True, db_index=True)
    # Staff-specific
    staff_type = models.CharField(
        max_length=20, choices=STAFF_TYPE_CHOICES, null=True, blank=True
    )
    teaching_positions = models.ManyToManyField(
        'TeachingPosition', blank=True
    )
    non_teaching_positions = models.ManyToManyField(
        'NonTeachingPosition', blank=True
    )

    # Student-specific
    student_class = models.ForeignKey(
        'StudentClass', null=True, blank=True, on_delete=models.SET_NULL
    )
    class_arm = models.ForeignKey(
        'ClassArm', null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        parts = []
        if self.branch:
            parts.append(f"Branch: {self.branch}")
        if self.role:
            parts.append(f"Role: {self.role}")
        if self.staff_type:
            parts.append(f"Staff Type: {self.staff_type}")
        for pos in self.teaching_positions.all():
            parts.append(f"Teaching: {pos.name}")
        for pos in self.non_teaching_positions.all():
            parts.append(f"Non-Teaching: {pos.name}")
        if self.student_class:
            parts.append(f"Class: {self.student_class.name}")
        if self.class_arm:
            parts.append(f"Arm: {self.class_arm.name}")
        return ' | '.join(parts) or "General"

    
class CommunicationRecipient(models.Model):
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name='recipients')
    # recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_communications')
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True,  
        blank=True,
        on_delete=models.SET_NULL,
        related_name='received_communications',
    )
    email = models.EmailField(null=True, blank=True)  # required for non-user recipients
    # Soft delete for recipient
    deleted = models.BooleanField(default=False)
    # Read status
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    requires_response = models.BooleanField(default=False)
    has_responded = models.BooleanField(default=False)

    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save()

    def clean(self):
        if not self.recipient and not self.email:
            raise ValidationError("Either a registered user (recipient) or an email must be provided.")
        if self.recipient and self.email:
            raise ValidationError("Provide only a recipient OR an email, not both.")
        
    def __str__(self):
        if self.recipient:
            return f"{self.recipient.username} -> {self.communication.title or 'Untitled Message'}"
        else:
            return f"{self.email} -> {self.communication.title or 'Untitled Message'}"


class CommunicationComment(models.Model):
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter.username} on {self.communication.title or 'Untitled'}"

# Soft delete for sender's sent messages
class SentMessageDelete(models.Model):
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name='sent_deletes')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Sent message {self.communication.id} deleted by {self.sender.username}"

class MessageReply(models.Model):
    recipient_entry = models.ForeignKey(CommunicationRecipient, on_delete=models.CASCADE, related_name='replies')
    responder = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reply_text = models.TextField()
    replied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.responder.username} on {self.recipient_entry.communication.title or 'Untitled'}"


class ReplyAttachment(models.Model):
    reply = models.ForeignKey(MessageReply, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='reply_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    @property
    def basename(self):
        return os.path.basename(self.file.name)
