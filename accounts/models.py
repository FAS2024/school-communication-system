from django.db import models
from django.contrib.auth.models import BaseUserManager,AbstractBaseUser, PermissionsMixin
from django.conf import settings
from django.templatetags.static import static


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
    

class TeachingPosition(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class NonTeachingPosition(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


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


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


# models.py
class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    admission_number = models.CharField(max_length=50, unique=True)
    current_class = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    guardian_name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.admission_number}"


class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'parent'})
    phone_number = models.CharField(max_length=20)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    children = models.ManyToManyField(CustomUser, related_name='student_parents', limit_choices_to={'role': 'student'})

    def __str__(self):
        return self.user.get_full_name()
    
    def get_children_from_same_branch(self):
        return self.children.filter(branch=self.user.branch)



class StaffProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['staff', 'superadmin', 'branch_admin']}
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()
