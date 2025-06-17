from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model


from django.forms import inlineformset_factory
from .models import (
    Communication, CommunicationAttachment,
    CommunicationRecipient, CommunicationTargetGroup,
    CustomUser, TeachingPosition, NonTeachingPosition, 
    Branch, StaffProfile,StudentProfile,StudentClass, 
    ClassArm, ParentProfile, CommunicationComment
)
        
from django.forms.widgets import ClearableFileInput

from django.contrib.auth import get_user_model
from django.forms.widgets import CheckboxSelectMultiple
from django.db.models import Q
from django.utils.timezone import localtime
import re
from django.contrib.contenttypes.models import ContentType
from django.http import QueryDict


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'role', 
                'staff_type', 'teaching_positions', 'non_teaching_positions', 'branch', 'password', 'password_confirmation']

    password_confirmation = forms.CharField(widget=forms.PasswordInput(), label='Confirm Password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')

        if password != password_confirmation:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


class TeachingPositionForm(forms.ModelForm):
    class Meta:
        model = TeachingPosition
        fields = ['name', 'is_class_teacher']

    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter position name'})
    )

    is_class_teacher = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("This field is required.")
        return name


class NonTeachingPositionForm(forms.ModelForm):
    class Meta:
        model = NonTeachingPosition
        fields = ['name']

    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter position name'})
    )
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("This field is required.")
        return name


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = '__all__'


class StaffCreationForm(UserCreationForm):
    teaching_positions = forms.ModelMultipleChoiceField(
        queryset=TeachingPosition.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    non_teaching_positions = forms.ModelMultipleChoiceField(
        queryset=NonTeachingPosition.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    profile_picture = forms.ImageField(required=False)
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'),('others', 'Others')],
        required=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'profile_picture', 'username', 'first_name', 'last_name',
            'gender', 'role', 'staff_type', 'teaching_positions', 'non_teaching_positions',
            'branch', 'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].widget.attrs['placeholder'] = 'Enter new password (optional)'
            self.fields['password2'].widget.attrs['placeholder'] = 'Confirm new password'

        if user:
            if user.role == 'superadmin':
                self.fields['role'].choices = [
                    ('superadmin', 'Super Admin'),
                    ('branch_admin', 'Branch Admin'),
                    ('staff', 'Staff'),
                ]
                self.fields['branch'].queryset = Branch.objects.all()

            elif user.role == 'branch_admin':
                self.fields['role'].choices = [
                    ('branch_admin', 'Branch Admin'),
                    ('staff', 'Staff'),
                ]
                self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
                self.fields['branch'].initial = user.branch

            elif user.role == 'staff' and user == self.instance:
                readonly_fields = [
                    'role', 'staff_type', 'branch',
                    'teaching_positions', 'non_teaching_positions', 'gender'
                ]
                for field in readonly_fields:
                    if field in self.fields:
                        self.fields[field].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = CustomUser.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get("password1")

        if password1:
            user.set_password(password1)
        elif self.instance and self.instance.pk:
            existing_user = CustomUser.objects.get(pk=self.instance.pk)
            user.password = existing_user.password

        if 'profile_picture' in self.cleaned_data:
            user.profile_picture = self.cleaned_data['profile_picture']
            print("Profile picture saved:", user.profile_picture)

        if commit:
            user.save()
            self.save_m2m()

        return user

class StaffProfileForm(forms.ModelForm):
    primary_position = forms.ChoiceField(label="Primary Position", required=False)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set initial value for primary_position from model instance
        current_position = self.instance.primary_position  # This uses the GenericForeignKey
        if current_position:
            model_name = 'teaching' if isinstance(current_position, TeachingPosition) else 'non_teaching'
            self.initial['primary_position'] = f"{model_name}:{current_position.id}"

        if not user or user.role not in ['superadmin', 'branch_admin']:
            self.fields['primary_position'].widget = forms.HiddenInput()
            self.fields['primary_position'].disabled = True
        else:
            teaching_positions = TeachingPosition.objects.all()
            non_teaching_positions = NonTeachingPosition.objects.all()

            choices = [('', '---------')]
            choices += [(f"teaching:{p.id}", f"{p.name} (Teaching)") for p in teaching_positions]
            choices += [(f"non_teaching:{p.id}", f"{p.name} (Non-Teaching)") for p in non_teaching_positions]

            self.fields['primary_position'].choices = choices

            self.fields['managing_class'].required = False
            self.fields['managing_class_arm'].required = False

        if user and user.role == 'staff' and user == self.instance.user:
            editable_fields = [
                'phone_number', 'qualification',
                'years_of_experience', 'address', 'primary_position'
            ]
            for field_name in self.fields:
                if field_name not in editable_fields:
                    self.fields[field_name].disabled = True

    class Meta:
        model = StaffProfile
        fields = [
            'phone_number', 'date_of_birth',
            'qualification', 'years_of_experience',
            'address', 'nationality', 'state',
            'staff_number', 'managing_class',
            'managing_class_arm', 
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validate managing_class and managing_class_arm dependency
        managing_class = cleaned_data.get('managing_class')
        managing_class_arm = cleaned_data.get('managing_class_arm')

        if managing_class_arm and not managing_class:
            raise forms.ValidationError(
                "Please select a managing class before selecting a class arm."
            )

        # Handle primary_position field (Generic ForeignKey logic)
        primary_position_value = cleaned_data.get('primary_position')

        if primary_position_value:
            try:
                type_str, obj_id = primary_position_value.split(':')
                obj_id = int(obj_id)
            except (ValueError, AttributeError):
                raise forms.ValidationError("Invalid format for primary position.")

            if type_str == 'teaching':
                model = TeachingPosition
            elif type_str == 'non_teaching':
                model = NonTeachingPosition
            else:
                raise forms.ValidationError("Invalid position type.")

            try:
                model.objects.get(id=obj_id)
            except model.DoesNotExist:
                raise forms.ValidationError("Selected position does not exist.")

            content_type = ContentType.objects.get_for_model(model)
            self.instance.position_content_type = content_type
            self.instance.position_object_id = obj_id
        else:
            self.instance.position_content_type = None
            self.instance.position_object_id = None

        return cleaned_data

class StudentClassForm(forms.ModelForm):
    arms = forms.ModelMultipleChoiceField(
        queryset=ClassArm.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Display checkboxes for selecting multiple arms
        required=True
    )

    class Meta:
        model = StudentClass
        fields = ['name', 'arms']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        arms = cleaned_data.get('arms')

        # Check if the form is for an update
        if self.instance.pk:
            # During an update, exclude the current instance from the check
            if StudentClass.objects.filter(name=name, arms__in=arms).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A class with the same name and arms already exists.")
        else:
            # During creation, ensure the combination doesn't already exist
            if StudentClass.objects.filter(name=name, arms__in=arms).exists():
                raise ValidationError("A class with the same name and arms already exists.")
        
        return cleaned_data

# class ParentCreationForm(forms.ModelForm):
#     password1 = forms.CharField(
#         label='Password',
#         widget=forms.PasswordInput(attrs={'placeholder':'Enter password'}),
#         required=False,
#     )

#     password2 = forms.CharField(
#         label='Confirm Password',
#         widget=forms.PasswordInput(attrs={'placeholder':'Confirm password'}),
#         required=False
#     )
    
#     parent_number = forms.CharField(
#     max_length=50,
#     required=False,
#     help_text="Leave blank to auto-generate. Format: LAGS/PAR/YYYY/XXXX"
#     )
    
#     occupation = forms.CharField(max_length=50)
#     address = forms.CharField(widget=forms.Textarea, required=False)
#     phone_number = forms.CharField(max_length=15, required=False, label="Phone Number", help_text="Optional: Include country code.")
#     nationality = forms.CharField(max_length=30,label="Country")
#     state = forms.CharField(max_length=30,label="State")
#     RELATIONSHIP_CHOICES = [
#         ('father', 'Father'),
#         ('mother', 'Mother'),
#         ('guardian', 'Guardian'),
#         ('other', 'Other'),
#     ]

#     relationship_to_student = forms.ChoiceField(
#         choices=RELATIONSHIP_CHOICES,
#         label="Relationship to Student"
#     )
#     date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
#     gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'),('others', 'Others')],required=False, label="Gender")
#     preferred_contact_method =  forms.ChoiceField(choices=[
#         ('phone', 'Phone'),
#         ('email', 'Email'),
#         ('sms', 'SMS')
#     ])
    
#     class Meta:
#         model = CustomUser
#         fields = [
#             'email', 'username', 'first_name', 'last_name', 'profile_picture',
#             'branch', 'password1', 'password2', 'phone_number', 'gender'
#         ]
#         widgets = {
#             'email': forms.EmailInput(),
#             'username': forms.TextInput(),
#         }

#     def __init__(self, *args, **kwargs):
#         self.request = kwargs.pop('request', None)  # Capture request user
#         user = self.request.user
#         super().__init__(*args, **kwargs)
        
#         for field in self.fields.values():
#             field.widget.attrs['class'] = 'form-control'

#         # Force role to student only and hide it from form
#         self.instance.role = 'parent'

#         # Field filtering based on user role
#         if self.request and not self.request.user.is_superuser and hasattr(self.request.user, 'role') and self.request.user.role == 'branch_admin':
#             self.fields['branch'].queryset = self.fields['branch'].queryset.filter(id=self.request.user.branch.id)

#         # Pre-fill fields for update if the instance is an existing parent
#         if self.instance and self.instance.pk:
#             self.fields['password1'].required = False
#             self.fields['password2'].required = False
#             self.fields['password1'].widget.attrs['placeholder'] = 'Enter new password (optional)'
#             self.fields['password2'].widget.attrs['placeholder'] = 'Confirm new password'

#             try:
#                 profile = self.instance.parentprofile
#                 self.fields['relationship_to_student'].initial = profile.relationship_to_student
#                 self.fields['date_of_birth'].initial = profile.date_of_birth
#                 self.fields['nationality'].initial = profile.nationality
#                 self.fields['state'].initial = profile.state

#             except ParentProfile.DoesNotExist:
#                 pass

#         # Set branch choices based on user role
#         if user:
#             if user.role == 'superadmin':
#                 self.fields['branch'].queryset = Branch.objects.all()

#             elif user.role == 'branch_admin':
#                 self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
#                 self.fields['branch'].initial = user.branch

#             if user.role == 'parent' and user == self.instance:
#                 readonly_fields = [
#                     'role',
#                     'branch',
#                     'gender',
#                     'relationship_to_student',
#                     'date_of_birth',
#                     'parent_number'
#                 ]
#                 for field in readonly_fields:
#                     if field in self.fields:
#                         self.fields[field].disabled = True  # Disable the fields for students
#                         self.fields[field].required = False  # Make them not required

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         qs = CustomUser.objects.filter(email=email)
#         if self.instance.pk:
#             qs = qs.exclude(pk=self.instance.pk)
#         if qs.exists():
#             raise ValidationError("This email is already in use.")
#         return email

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         qs = CustomUser.objects.filter(username=username)
#         if self.instance.pk:
#             qs = qs.exclude(pk=self.instance.pk)
#         if qs.exists():
#             raise ValidationError("This username is already taken.")
#         return username

#     def clean_parent_number(self):
#         parent_number = self.cleaned_data.get('parent_number')
#         if not parent_number:
#             return parent_number

#         pattern = r'^LAGS/PAR/\d{4}/\d{4}$'
#         if not re.match(pattern, parent_number):
#             raise ValidationError("Invalid format. Use: LAGS/PAR/YYYY/XXXX")

#         existing = ParentProfile.objects.filter(parent_number=parent_number)
#         if self.instance.pk:
#             existing = existing.exclude(user_id=self.instance.pk)
#         if existing.exists():
#             raise ValidationError("This parent number is already in use.")
        
#         return parent_number

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.role = 'parent'
#         user.gender = self.cleaned_data.get('gender')
        
#         password1 = self.cleaned_data.get("password1")
#         if password1:
#             user.set_password(password1)
#         elif self.instance and self.instance.pk:
#             existing_user = CustomUser.objects.get(pk=self.instance.pk)
#             user.password = existing_user.password

#         if 'profile_picture' in self.cleaned_data:
#             user.profile_picture = self.cleaned_data['profile_picture']
#             print("Profile picture saved:", user.profile_picture)

#         if commit:
#             user.save()
#             profile, created = ParentProfile.objects.get_or_create(user=user)
#             profile.date_of_birth = self.cleaned_data['date_of_birth']
#             profile.address = self.cleaned_data['address']
#             profile.phone_number = self.cleaned_data['phone_number']
#             profile.occupation = self.cleaned_data['occupation']
#             profile.preferred_contact_method = self.cleaned_data['preferred_contact_method']
#             profile.relationship_to_student = self.cleaned_data['relationship_to_student']
#             profile.nationality = self.cleaned_data['nationality']
#             profile.state = self.cleaned_data['state']
#             profile.save()
            
#         return user

class ParentCreationForm(forms.ModelForm):
    # USER fields - passwords optional on update
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        required=False,
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=False,
    )

    # PARENT PROFILE fields
    parent_number = forms.CharField(
        max_length=50,
        required=False,
        help_text="Leave blank to auto-generate. Format: LAGS/PAR/YYYY/XXXX"
    )
    occupation = forms.CharField(max_length=50, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number", help_text="Optional: Include country code.")
    nationality = forms.CharField(max_length=30, label="Country")
    state = forms.CharField(max_length=30, label="State")
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('other', 'Other'),
    ]
    relationship_to_student = forms.ChoiceField(
        choices=RELATIONSHIP_CHOICES,
        label="Relationship to Student"
    )
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')],
        required=False,
        label="Gender"
    )
    preferred_contact_method = forms.ChoiceField(choices=[
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('sms', 'SMS')
    ])

    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name', 'profile_picture',
            'branch', 'password1', 'password2', 'gender'
        ]
        widgets = {
            'email': forms.EmailInput(),
            'username': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        user = self.request.user if self.request else None

        # Add bootstrap class for all fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.instance.role = 'parent'

        # Limit branch selection if user is branch_admin
        if user and user.role == 'branch_admin':
            self.fields['branch'].queryset = self.fields['branch'].queryset.filter(id=user.branch_id)
            self.fields['branch'].initial = user.branch

        # Populate ParentProfile fields if editing existing user
        if self.instance and self.instance.pk:
            self.fields['password1'].widget.attrs['placeholder'] = 'Enter new password (optional)'
            self.fields['password2'].widget.attrs['placeholder'] = 'Confirm new password'

            try:
                profile = self.instance.parentprofile
                self.fields['relationship_to_student'].initial = profile.relationship_to_student
                self.fields['date_of_birth'].initial = profile.date_of_birth
                self.fields['nationality'].initial = profile.nationality
                self.fields['state'].initial = profile.state
                self.fields['address'].initial = profile.address
                self.fields['occupation'].initial = profile.occupation
                self.fields['preferred_contact_method'].initial = profile.preferred_contact_method
                self.fields['phone_number'].initial = profile.phone_number
                self.fields['parent_number'].initial = profile.parent_number
            except ParentProfile.DoesNotExist:
                pass

            if user and user.role == 'parent' and user == self.instance:
                readonly_fields = [
                    'role', 'branch', 'gender', 'relationship_to_student',
                    'date_of_birth', 'parent_number'
                ]
                for field in readonly_fields:
                    if field in self.fields:
                        self.fields[field].disabled = True
                        self.fields[field].required = False

        # Note: We keep password1 and password2 fields for update but empty by default
        # No need to pop password fields on update - users can update password if they want

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = CustomUser.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_parent_number(self):
        parent_number = self.cleaned_data.get('parent_number')
        if not parent_number:
            return parent_number

        pattern = r'^LAGS/PAR/\d{4}/\d{4}$'
        if not re.match(pattern, parent_number):
            raise ValidationError("Invalid format. Use: LAGS/PAR/YYYY/XXXX")

        existing = ParentProfile.objects.filter(parent_number=parent_number)
        if self.instance.pk:
            existing = existing.exclude(user_id=self.instance.pk)
        if existing.exists():
            raise ValidationError("This parent number is already in use.")

        return parent_number

    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get("password1")
        pwd2 = cleaned_data.get("password2")

        # Only validate if at least one password field is filled
        if pwd1 or pwd2:
            if pwd1 != pwd2:
                self.add_error('password2', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            user = super().save(commit=False)
            user.role = 'parent'
            user.gender = self.cleaned_data.get('gender')

            password1 = self.cleaned_data.get("password1")

            if password1:
                user.set_password(password1)
            elif self.instance and self.instance.pk:
                existing_user = CustomUser.objects.get(pk=self.instance.pk)
                user.password = existing_user.password

            if 'profile_picture' in self.cleaned_data:
                user.profile_picture = self.cleaned_data['profile_picture']

            if commit:
                user.save()

                profile, created = ParentProfile.objects.get_or_create(user=user)
                profile.date_of_birth = self.cleaned_data['date_of_birth']
                profile.address = self.cleaned_data['address']
                profile.phone_number = self.cleaned_data['phone_number']
                profile.occupation = self.cleaned_data['occupation']
                profile.preferred_contact_method = self.cleaned_data['preferred_contact_method']
                profile.relationship_to_student = self.cleaned_data['relationship_to_student']
                profile.nationality = self.cleaned_data['nationality']
                profile.state = self.cleaned_data['state']
                profile.parent_number = self.cleaned_data.get('parent_number') or profile.parent_number
                profile.save()

            return user

class ClassArmForm(forms.ModelForm):
    class Meta:
        model = ClassArm
        fields = ['name']  # Only the 'name' field for the ClassArm

    def clean_name(self):
        name = self.cleaned_data['name'].strip()  # Strip any unnecessary spaces
        if ClassArm.objects.filter(name=name).exists():  # Check if the arm already exists
            raise forms.ValidationError(f"The class arm '{name}' already exists.")
        return name


class StudentCreationForm(UserCreationForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label='Confirm Password'
    )
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    profile_picture = forms.ImageField(required=False)
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')],
        required=True
    )
    class Meta:
        model = CustomUser
        fields = [
            'email', 'profile_picture', 'username', 'first_name', 'last_name',
            'gender', 'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
            
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        # Adjust branch queryset based on the current user role
        if user and hasattr(self.fields, 'branch'):
            if user.role == 'superadmin':
                self.fields['branch'].queryset = Branch.objects.all()
            elif user.role == 'branch_admin':
                self.fields['branch'].queryset = Branch.objects.filter(id=user.branch.id)

        # If editing existing user, make passwords optional with placeholders
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].widget.attrs['placeholder'] = 'Enter new password (optional)'
            self.fields['password2'].widget.attrs['placeholder'] = 'Confirm new password'

        # Disable gender field if the logged-in user is a student (cannot edit gender)
        if user and user.role == 'student':
            self.fields['gender'].disabled = True
            
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = CustomUser.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        # Enforce role to 'student'
        user.role = 'student'

        password1 = self.cleaned_data.get("password1")
        if password1:
            user.set_password(password1)
        elif self.instance and self.instance.pk:
            existing_user = CustomUser.objects.get(pk=self.instance.pk)
            user.password = existing_user.password

        if 'profile_picture' in self.cleaned_data:
            user.profile_picture = self.cleaned_data['profile_picture']

        if commit:
            user.save()
        return user

class StudentProfileForm(forms.ModelForm):
    parent = forms.ModelChoiceField(queryset=ParentProfile.objects.none(), required=True)
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number", help_text="Optional: Include country code.")
    nationality = forms.CharField(max_length=30,label="Country")
    state = forms.CharField(max_length=30,label="State")
    class Meta:
        model = StudentProfile
        fields = [
            'phone_number', 'date_of_birth',
            'admission_number', 'current_class', 'current_class_arm',
            'parent', 'nationality', 'state', 'address', 'guardian_name'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
        
            
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Superadmin or Branch Admin can choose from full/branch-limited queryset
        if user:
            if user.role == 'branch_admin':
                self.fields['parent'].queryset = ParentProfile.objects.filter(user__branch=user.branch)
            elif user.role == 'superadmin':
                self.fields['parent'].queryset = ParentProfile.objects.all()

        # If student, limit parent queryset and disable field
        if user and user.role == 'student' and user == getattr(self.instance, 'user', None):
            # Ensure only the assigned parent is in the queryset
            if hasattr(self.instance, 'parent') and self.instance.parent:
                self.fields['parent'].queryset = ParentProfile.objects.filter(pk=self.instance.parent.pk)
                self.fields['parent'].initial = self.instance.parent
                self.fields['parent'].disabled = True
                self.fields['parent'].widget.attrs['readonly'] = True
            
            else:
                self.fields['parent'].queryset = ParentProfile.objects.none()
                self.fields['parent'].disabled = True
                self.fields['parent'].label = "No Parent Assigned"

        # Optional: mark other fields as read-only for students
        if user and user.role == 'student' and user == getattr(self.instance, 'user', None):
            readonly_fields = [
                'date_of_birth', 'admission_number', 'current_class',
                'current_class_arm', 'guardian_name', 'state', 'nationality'
            ]
            for field in readonly_fields:
                if field in self.fields:
                    self.fields[field].disabled = True
                    
    def clean_admission_number(self):
        admission_number = self.cleaned_data.get('admission_number')

        if not admission_number:
            return admission_number  # Skip if it's empty (may be generated in model)

        # Validate format: LAGS/STU/YYYY/XXXX
        pattern = r'^LAGS/STU/\d{4}/\d{4}$'
        if not re.match(pattern, admission_number):
            raise ValidationError("Admission number must be in the format 'LAGS/STU/YYYY/XXXX'.")

        # Check for uniqueness, excluding current instance
        existing = StudentProfile.objects.filter(admission_number=admission_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError("This admission number has already been assigned to another student.")

        return admission_number
    
class CommunicationForm(forms.ModelForm):
    manual_emails = forms.CharField(
        required=False,
        label="Add manual emails",
        widget=forms.Textarea(attrs={
            "placeholder": "Comma-separated emails",
            "rows": 2,
            "cols": 40
        }),
        help_text="Add emails manually (e.g., external contacts)"
    )
    scheduled_time = forms.DateTimeField(
        input_formats=['%d-%m-%Y %I:%M %p'],
        widget=forms.DateTimeInput(
            attrs={
                'type': 'text',
                'id': 'scheduledTimePicker',
                'class': 'form-control',
                'placeholder': 'You can schedule in this format 01-01-2025 9:10 AM'
            }
        ),
        required=False
    )
    class Meta:
        model = Communication
        fields = [
            'message_type',
            'title',
            'body',
            'is_draft',
            'scheduled_time',
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Format scheduled_time for display
        if self.instance and self.instance.scheduled_time:
            local_dt = localtime(self.instance.scheduled_time)
            self.initial['scheduled_time'] = local_dt.strftime('%Y-%m-%dT%H:%M')
            self.fields['scheduled_time'].label = "Scheduled time (24-hour clock)"

        # Message type filtering based on user role
        if 'message_type' in self.fields:
            all_message_types = [
                ('announcement', 'Announcement'),
                ('post', 'Post'),
                ('notification', 'Notification'),
                ('news', 'News'),
                ('personal', 'Personal'),
                ('group', 'Group'),
            ]

            if self.user and self.user.role in ['student', 'parent']:
                allowed_types = ['post', 'personal', 'group']
                filtered_choices = [(v, l) for v, l in all_message_types if v in allowed_types]
                self.fields.pop('manual_emails', None)  # Hide manual emails for limited roles
            else:
                filtered_choices = all_message_types

            self.fields['message_type'].choices = filtered_choices
            self.fields['message_type'].choices = [('', '--------------')] + filtered_choices
            self.fields['title'].required = True  
            self.fields['body'].required = True  

    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type')
        title = cleaned_data.get('title')
        body = cleaned_data.get('body')
        manual_emails = cleaned_data.get('manual_emails')

        # Validate required fields
        if not message_type:
            self.add_error('message_type', "Message type is required.")
        if not title:
            self.add_error('title', "Title is required.")
        if not body:
            self.add_error('body', "Body is required.")

        # Validate manual emails
        if manual_emails:
            emails = [e.strip() for e in manual_emails.split(',') if e.strip()]
            registered_emails = CustomUser.objects.filter(email__in=emails).values_list('email', flat=True)

            invalid_emails = []
            for email in emails:
                if email in registered_emails:
                    self.add_error(
                        'manual_emails',
                        f"The email '{email}' belongs to a registered user. Please select them from the recipient list instead."
                    )
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    self.add_error('manual_emails', f"The email '{email}' is not a valid format.")
                    invalid_emails.append(email)

        return cleaned_data


class CommunicationTargetGroupForm(forms.ModelForm):
    STUDENT_ROLES = ['student', 'parent']
    STAFF_ROLES = ['staff', 'branch_admin', 'superadmin']

    class Meta:
        model = CommunicationTargetGroup
        fields = [
            'branch', 'role', 'staff_type',
            'teaching_positions', 'non_teaching_positions',
            'student_class', 'class_arm',
        ]
        widgets = {
            'teaching_positions': forms.CheckboxSelectMultiple(),
            'non_teaching_positions': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        data = kwargs.get("data", None)

        # Fix: only proceed if data exists
        if data:
            if not isinstance(data, QueryDict):
                qd = QueryDict("", mutable=True)
                qd.update(data)
                data = qd
            else:
                data = data.copy()

            # Defensive: wrap single string into list
            for name in ["teaching_positions", "non_teaching_positions"]:
                if name in data and isinstance(data.get(name), str):
                    data.setlist(name, [data.get(name)])

            # Replace data in kwargs (DO NOT pass again in *args)
            kwargs["data"] = data

        # Final: pass everything cleanly to parent
        super().__init__(*args, **kwargs)
        
        role = self.initial.get('role') or self.data.get('role')
        if self.user and self.user.role == 'student':
            if role == 'student':
                self.fields['student_class'].required = True
                self.fields['class_arm'].required = True
        
        if self.user and self.user.role == 'parent':
            self.fields['staff_type'].choices = [('teaching', 'Teaching Staff')]

            self.fields['teaching_positions'].queryset = TeachingPosition.objects.filter(is_class_teacher=True)

            self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.none()
            self.fields['student_class'].queryset = StudentClass.objects.all()
            self.fields['class_arm'].queryset = ClassArm.objects.all()

        else:
            self.fields['teaching_positions'].queryset = TeachingPosition.objects.all()
            self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.all()
            self.fields['student_class'].queryset = StudentClass.objects.all()
            self.fields['class_arm'].queryset = ClassArm.objects.all()

        # Make optional fields not required
        for field in ['teaching_positions', 'non_teaching_positions', 'student_class', 'class_arm']:
            self.fields[field].required = False

        # Customize form fields based on user role
        if self.user:
            self._customize_fields_based_on_user_role()

    def _customize_fields_based_on_user_role(self):
        if self.user.role in self.STUDENT_ROLES:
            # Branch is fixed to user's branch
            self.fields['branch'].initial = self.user.branch
            self.fields['branch'].disabled = True
            
            if self.user.role == 'parent':
                self.fields['role'].choices = [
                    ('', '------------'),
                    ('student', 'My Child/Children'),
                    ('staff', 'Class Teacher'),
                    ('branch_admin', 'Branch Admin'),
                ]
            elif self.user.role == 'student':
                self.fields['role'].choices = [
                    ('', '------------'),
                    ('student', 'Students'),
                    ('parent', 'My Parent'),
                    ('staff', 'Staffs'),
                    ('branch_admin', 'Branch Admin'),
                ]
                
            self.fields['role'].required = True
            self.fields['branch'].required = False  # disabled field

        elif self.user.role in self.STAFF_ROLES:
            self.fields['branch'].queryset = Branch.objects.all()
            self.fields['branch'].disabled = False
            self.fields['branch'].required = True
            self.fields['role'].choices = [('', '-----------')] + list(CommunicationTargetGroup.ROLE_CHOICES)
            self.fields['role'].required = False

    def clean(self):
        cleaned_data = super().clean()

        # Normalize empty strings or missing values to None
        for field in ['student_class', 'class_arm', 'staff_type']:
            if not cleaned_data.get(field):
                cleaned_data[field] = None

        role = cleaned_data.get('role')
        staff_type = cleaned_data.get('staff_type')
        branch = cleaned_data.get('branch')
        # teaching_positions = cleaned_data.get('teaching_positions') or self.fields['teaching_positions'].queryset.none()
        teaching_positions = cleaned_data.get('teaching_positions')
        if teaching_positions is None:
            teaching_positions = []
        cleaned_data['teaching_positions'] = teaching_positions
        # non_teaching_positions = cleaned_data.get('non_teaching_positions') or self.fields['non_teaching_positions'].queryset.none()
        non_teaching_positions = cleaned_data.get('non_teaching_positions')
        if non_teaching_positions is None:
            non_teaching_positions = []
        cleaned_data['non_teaching_positions'] = non_teaching_positions

        student_class = cleaned_data.get('student_class')
        class_arm = cleaned_data.get('class_arm')

        # If no role is selected, clear all filters and exit early
        if not role:
            cleaned_data['student_class'] = None
            cleaned_data['class_arm'] = None
            cleaned_data['staff_type'] = None
            cleaned_data['teaching_positions'] = []
            cleaned_data['non_teaching_positions'] = []
            return cleaned_data

        # If the logged-in user is a student and selects "student" recipients
        if self.user.role == 'student' and role == 'student':
            if not student_class:
                self.add_error('student_class', "This field is required for students.")
            if not class_arm:
                self.add_error('class_arm', "This field is required for students.")
            if not student_class or not class_arm:
                raise ValidationError('Please select both class and class arm to view student recipients.')

        # If user is in student roles, override branch and validate role
        if self.user.role in self.STUDENT_ROLES:
            cleaned_data['branch'] = self.user.branch
            if not role:
                raise ValidationError('You must select a role.')

        # If user is in staff roles, validate filters
        elif self.user.role in self.STAFF_ROLES:
            if not branch:
                raise ValidationError('Branch must be selected.')

            require_staff_filter = (
                staff_type or teaching_positions.exists() or non_teaching_positions.exists()
            )

            if role in ['staff', 'branch_admin', 'superadmin'] and require_staff_filter:
                self._validate_staff_positions(
                    staff_type,
                    teaching_positions,
                    non_teaching_positions
                )

        return cleaned_data

    # def _validate_staff_positions(self, staff_type, teaching_positions, non_teaching_positions):
    #     if not staff_type and not teaching_positions.exists() and not non_teaching_positions.exists():
    #         raise ValidationError("Staff type and at least one teaching or non-teaching position must be selected.")

    #     if staff_type == 'teaching':
    #         if non_teaching_positions.exists():
    #             raise ValidationError("Non-teaching positions cannot be selected for teaching staff type.")
    #         if not teaching_positions.exists():
    #             raise ValidationError("At least one teaching position must be selected.")

    #     elif staff_type == 'non_teaching':
    #         if teaching_positions.exists():
    #             raise ValidationError("Teaching positions cannot be selected for non-teaching staff type.")
    #         if not non_teaching_positions.exists():
    #             raise ValidationError("At least one non-teaching position must be selected.")

    #     elif staff_type == 'both':
    #         if not (teaching_positions.exists() or non_teaching_positions.exists()):
    #             raise ValidationError("Select at least one teaching or non-teaching position for 'both' staff type.")
    def _validate_staff_positions(self, staff_type, teaching_positions, non_teaching_positions):
        # Ensure we are not dealing with None values
        teaching_positions = teaching_positions or []
        non_teaching_positions = non_teaching_positions or []

        if not staff_type and not teaching_positions and not non_teaching_positions:
            raise ValidationError("Staff type and at least one teaching or non-teaching position must be selected.")

        if staff_type == 'teaching':
            if non_teaching_positions:
                raise ValidationError("Non-teaching positions cannot be selected for teaching staff type.")
            if not teaching_positions:
                raise ValidationError("At least one teaching position must be selected.")

        elif staff_type == 'non_teaching':
            if teaching_positions:
                raise ValidationError("Teaching positions cannot be selected for non-teaching staff type.")
            if not non_teaching_positions:
                raise ValidationError("At least one non-teaching position must be selected.")

        elif staff_type == 'both':
            if not teaching_positions and not non_teaching_positions:
                raise ValidationError("Select at least one teaching or non-teaching position for 'both' staff type.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sender = self.user

        role = self.cleaned_data.get('role')

        if self.user.role in self.STUDENT_ROLES:
            instance.branch = self.user.branch
            instance.role = role

            if role in ['student', 'parent']:
                instance.student_class = self.cleaned_data.get('student_class')
                instance.class_arm = self.cleaned_data.get('class_arm')

                # Clear staff fields
                instance.staff_type = None
                instance.teaching_positions.clear()
                instance.non_teaching_positions.clear()

            elif role in self.STAFF_ROLES:
                instance.staff_type = self.cleaned_data.get('staff_type')
                if instance.staff_type == 'teaching':
                    # instance.teaching_positions.set(self.cleaned_data.get('teaching_positions'))
                    instance.teaching_positions.set(self.cleaned_data.get('teaching_positions') or [])
                    instance.non_teaching_positions.clear()
                elif instance.staff_type == 'non_teaching':
                    # instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions'))
                    instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions') or [])
                    instance.teaching_positions.clear()
                else:  # both or none
                    instance.teaching_positions.clear()
                    instance.non_teaching_positions.clear()

                instance.student_class = None
                instance.class_arm = None
            else:
                raise ValidationError(f"Invalid role selected: {role}")

        elif self.user.role in self.STAFF_ROLES:
            instance.branch = self.cleaned_data.get('branch')
            instance.role = self.cleaned_data.get('role')
            instance.staff_type = self.cleaned_data.get('staff_type')

            if instance.staff_type == 'teaching':
                instance.teaching_positions.set(self.cleaned_data.get('teaching_positions') or [])
                instance.non_teaching_positions.clear()
            elif instance.staff_type == 'non_teaching':
                instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions') or [])
                instance.teaching_positions.clear()
            else:
                instance.teaching_positions.clear()
                instance.non_teaching_positions.clear()

            instance.student_class = self.cleaned_data.get('student_class')
            instance.class_arm = self.cleaned_data.get('class_arm')

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    def get_filtered_recipients(self, target_group_data):
        # Extract filters
        role = target_group_data.get('role')
        branch = target_group_data.get('branch')
        staff_type = target_group_data.get('staff_type')
        student_class = target_group_data.get('student_class')
        class_arm = target_group_data.get('class_arm')
        teaching_positions = target_group_data.get('teaching_positions') or []
        non_teaching_positions = target_group_data.get('non_teaching_positions') or []
        search = target_group_data.get('search')

        # Base queryset excluding current user
        qs = CustomUser.objects.filter(is_active=True).exclude(id=self.user.id)
    

        def filter_staff(qs, staff_type, teaching_positions, non_teaching_positions):
            if not staff_type:
                return qs.none()

            user_role = self.user.role
            valid_roles = {
                "student": ['staff', 'branch_admin'],
                "parent": ['staff', 'branch_admin'],
                "default": ['staff', 'branch_admin', 'superadmin']
            }


            def has_required_positions(required_positions):
                return bool(required_positions)

            # def apply_filter(roles, s_type, positions_field, positions):
            #     if not has_required_positions(positions):
            #         return CustomUser.objects.none()

            #     # Ensure positions is a list/tuple/set for __in lookup
            #     from django.db.models.query import QuerySet
            #     if not isinstance(positions, (list, tuple, set, QuerySet)):
            #         positions = [positions]

            #     return qs.filter(
            #         role__in=roles,
            #         staff_type=s_type,
            #         **{positions_field: positions}
            #     ).distinct()
            
            def apply_filter(roles, s_type, positions_field, positions):
                from django.db.models.query import QuerySet
                from django.contrib.contenttypes.models import ContentType
                from accounts.models import CustomUser, StaffProfile, TeachingPosition
                from django.db.models import Q

                if not roles or not has_required_positions(positions):
                    return CustomUser.objects.none()

                if not isinstance(positions, (list, tuple, set, QuerySet)):
                    positions = [positions]

                # Basic M2M and generic filtering
                direct_user_ids = qs.filter(
                    role__in=roles,
                    staff_type=s_type,
                    **{positions_field: positions}
                ).values_list('id', flat=True)

                content_type = ContentType.objects.get_for_model(positions[0].__class__)
                position_ids = [p.id for p in positions]

                via_profile_ids = StaffProfile.objects.filter(
                    position_content_type=content_type,
                    position_object_id__in=position_ids,
                    user__role__in=roles,
                    user__staff_type=s_type
                ).values_list('user_id', flat=True)

                all_user_ids = set(direct_user_ids).union(set(via_profile_ids))

                # Handle "class teacher" positions
                if any(getattr(p, 'is_class_teacher', False) for p in positions):
                    teaching_ct = ContentType.objects.get_for_model(TeachingPosition)
                    class_teacher_positions = TeachingPosition.objects.filter(is_class_teacher=True)

                    primary_class_teacher_ids = StaffProfile.objects.filter(
                        position_content_type=teaching_ct,
                        position_object_id__in=class_teacher_positions.values_list('id', flat=True)
                    ).values_list('user_id', flat=True)

                    direct_class_teacher_ids = CustomUser.objects.filter(
                        teaching_positions__in=class_teacher_positions
                    ).values_list('id', flat=True)

                    # Optional: include managing class/arm logic — less targeted without children
                    managed_ids = StaffProfile.objects.filter(
                        managing_class_id__isnull=False,
                        managing_class_arm_id__isnull=False
                    ).values_list('user_id', flat=True)

                    final_class_teacher_ids = set(primary_class_teacher_ids).union(direct_class_teacher_ids)
                    final_user_ids = final_class_teacher_ids.intersection(managed_ids)

                    all_user_ids |= final_user_ids

                return qs.filter(id__in=all_user_ids).distinct()

            if user_role == "student":
                if staff_type == 'teaching':
                    return apply_filter(valid_roles["student"], 'teaching', 'teaching_positions__in', teaching_positions)
                elif staff_type == 'non_teaching':
                    return apply_filter(valid_roles["student"], 'non_teaching', 'non_teaching_positions__in', non_teaching_positions)
                else:
                    return qs.filter(role__in=valid_roles["student"])

            elif user_role == "parent":
                if staff_type == 'teaching':
                    return apply_filter(valid_roles["parent"], 'teaching', 'teaching_positions__in', teaching_positions)
                # for later if he can message non teaching staff
                # elif staff_type == 'non_teaching':
                #     return apply_filter(valid_roles["parent"], 'non_teaching', 'non_teaching_positions__in', non_teaching_positions)
    
            # Default for other roles (e.g. staff, admin)
            if staff_type == 'teaching':
                return apply_filter(valid_roles["default"], 'teaching', 'teaching_positions__in', teaching_positions)
            elif staff_type == 'non_teaching':
                return apply_filter(valid_roles["default"], 'non_teaching', 'non_teaching_positions__in', non_teaching_positions)
            else:
                return qs.filter(role__in=valid_roles["default"])

        if self.user.role in self.STUDENT_ROLES:
            branch = self.user.branch
            qs = qs.filter(branch=branch)

            if self.user.role == 'student':
                if not role:
                    return  qs.none()

                if role == 'student':
                    qs = qs.filter(role='student')
                    if not student_class:
                        qs = qs.none()
                    else:
                        qs = qs.filter(studentprofile__current_class_id=student_class)
                        if class_arm:
                            qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

                elif role == 'parent':
                    try:
                        parent_user_id = self.user.studentprofile.parent.user.id
                        qs = qs.filter(id=parent_user_id, role='parent')
                    except StudentProfile.DoesNotExist:
                        qs = CustomUser.objects.none()

                else:
                    qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)

            elif self.user.role == 'parent':
                from django.contrib.contenttypes.models import ContentType
                from accounts.models import TeachingPosition, StaffProfile
                from django.db.models import Q

                parent = self.user.parentprofile
                children = parent.students.all()

                if not role:
                    return qs.none()

                if role == 'student':
                    qs = qs.filter(role='student', studentprofile__parent=parent)
                    if student_class:
                        qs = qs.filter(studentprofile__current_class_id=student_class)
                    if class_arm:
                        qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

                elif role == 'branch_admin':
                    return qs.filter(role='branch_admin', branch_id=self.user.branch_id)

                elif role == 'staff':
                    if not teaching_positions:
                        return qs.none()

                    child_class_pairs = children.values_list('current_class', 'current_class_arm')

                    class_arm_filters = Q()
                    for class_id, arm_id in child_class_pairs:
                        if class_id and arm_id:
                            class_arm_filters |= Q(managing_class_id=class_id, managing_class_arm_id=arm_id)

                    managing_staff_user_ids = StaffProfile.objects.filter(
                        class_arm_filters
                    ).values_list('user_id', flat=True)

                    teaching_ct = ContentType.objects.get_for_model(TeachingPosition)
                    class_teacher_positions = TeachingPosition.objects.filter(is_class_teacher=True)
                    class_teacher_ids = class_teacher_positions.values_list('id', flat=True)

                    primary_class_teacher_ids = StaffProfile.objects.filter(
                        position_content_type=teaching_ct,
                        position_object_id__in=class_teacher_ids
                    ).values_list('user_id', flat=True)

                    any_class_teacher_ids = CustomUser.objects.filter(
                        teaching_positions__in=class_teacher_positions
                    ).values_list('id', flat=True)

                    class_teacher_user_ids = set(primary_class_teacher_ids).union(any_class_teacher_ids)
                    final_staff_user_ids = set(managing_staff_user_ids).intersection(class_teacher_user_ids)

                    branch_admin_class_teacher_ids = CustomUser.objects.filter(
                        id__in=class_teacher_user_ids,
                        role='branch_admin',
                        branch_id=self.user.branch_id
                    ).values_list('id', flat=True)

                    allowed_user_ids = list(final_staff_user_ids.union(branch_admin_class_teacher_ids))
                    return qs.filter(id__in=allowed_user_ids).distinct()

        elif self.user.role in self.STAFF_ROLES:
            if not branch:
                return CustomUser.objects.none()

            qs = qs.filter(branch=branch)

            if role in ['staff', 'branch_admin', 'superadmin'] and staff_type:
                qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)
            elif role:
                qs = qs.filter(role=role)

        if search:
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))

        return qs


class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class CommunicationAttachmentModelForm(forms.ModelForm):
    class Meta:
        model = CommunicationAttachment
        fields = ['file']


AttachmentFormSet = inlineformset_factory(
    Communication,
    CommunicationAttachment,
    form=CommunicationAttachmentModelForm,
    extra=2,
    can_delete=True
)


class CommunicationRecipientForm(forms.ModelForm):
    class Meta:
        model = CommunicationRecipient
        fields = ['recipient']


class CommunicationCommentForm(forms.ModelForm):
    class Meta:
        model = CommunicationComment
        fields = ['comment']


# # Student inbox - only receive from allowed sources
# if user.role == 'student':
#     inbox = Message.objects.filter(
#         recipient=user,
#         sender__in=User.objects.filter(
#             Q(role='parent', id=user.parent.id) |
#             Q(role='staff', branch=user.branch) |
#             Q(role='branch_admin', branch=user.branch) |
#             Q(role='superadmin')
#         )
#     )




# ////////////////////////////////////////////////////

# class CommunicationTargetGroupForm(forms.ModelForm):
#     STUDENT_ROLES = ['student', 'parent']
#     STAFF_ROLES = ['staff', 'branch_admin', 'superadmin']

#     class Meta:
#         model = CommunicationTargetGroup
#         fields = [
#             'branch', 'role', 'staff_type',
#             'teaching_positions', 'non_teaching_positions',
#             'student_class', 'class_arm',
#         ]
#         widgets = {
#             'teaching_positions': forms.CheckboxSelectMultiple(),
#             'non_teaching_positions': forms.CheckboxSelectMultiple(),
#         }

#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         # self.request = kwargs.pop('request', None)
#         super().__init__(*args, **kwargs)
        
#         role = self.initial.get('role') or self.data.get('role')
#         if self.user and self.user.role == 'student':
#             if role == 'student':
#                 self.fields['student_class'].required = True
#                 self.fields['class_arm'].required = True
        
#         if self.user and self.user.role == 'parent':
#             self.fields['staff_type'].choices = [('teaching', 'Teaching Staff')]

#             self.fields['teaching_positions'].queryset = TeachingPosition.objects.filter(is_class_teacher=True)

#             self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.none()
#             self.fields['student_class'].queryset = StudentClass.objects.all()
#             self.fields['class_arm'].queryset = ClassArm.objects.all()

#         else:
#             self.fields['teaching_positions'].queryset = TeachingPosition.objects.all()
#             self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.all()
#             self.fields['student_class'].queryset = StudentClass.objects.all()
#             self.fields['class_arm'].queryset = ClassArm.objects.all()

#         # Make optional fields not required
#         for field in ['teaching_positions', 'non_teaching_positions', 'student_class', 'class_arm']:
#             self.fields[field].required = False

#         # Customize form fields based on user role
#         if self.user:
#             self._customize_fields_based_on_user_role()

#     def _customize_fields_based_on_user_role(self):
#         if self.user.role in self.STUDENT_ROLES:
#             # Branch is fixed to user's branch
#             self.fields['branch'].initial = self.user.branch
#             self.fields['branch'].disabled = True
            
#             if self.user.role == 'parent':
#                 self.fields['role'].choices = [
#                     ('', '------------'),
#                     ('student', 'My Child/Children'),
#                     ('staff', 'Staff'),
#                     ('branch_admin', 'Branch Admin'),
#                 ]
#             elif self.user.role == 'student':
#                 self.fields['role'].choices = [
#                     ('', '------------'),
#                     ('student', 'Students'),
#                     ('parent', 'My Parent'),
#                     ('staff', 'Staffs'),
#                     ('branch_admin', 'Branch Admin'),
#                 ]
                
#             self.fields['role'].required = True
#             self.fields['branch'].required = False  # disabled field

#         elif self.user.role in self.STAFF_ROLES:
#             self.fields['branch'].queryset = Branch.objects.all()
#             self.fields['branch'].disabled = False
#             self.fields['branch'].required = True
#             self.fields['role'].choices = [('', '-----------')] + list(CommunicationTargetGroup.ROLE_CHOICES)
#             self.fields['role'].required = False

#     def clean(self):
#         cleaned_data = super().clean()

#         role = cleaned_data.get('role')
#         staff_type = cleaned_data.get('staff_type')
#         branch = cleaned_data.get('branch')
#         teaching_positions = cleaned_data.get('teaching_positions') or self.fields['teaching_positions'].queryset.none()
#         non_teaching_positions = cleaned_data.get('non_teaching_positions') or self.fields['non_teaching_positions'].queryset.none()
#         student_class = cleaned_data.get('student_class')
#         class_arm = cleaned_data.get('class_arm')
        
#         if not role:
#             # Automatically clear all recipient-related filters if no role selected
#             cleaned_data['student_class'] = None
#             cleaned_data['class_arm'] = None
#             cleaned_data['staff_type'] = None
#             cleaned_data['teaching_positions'] = []
#             cleaned_data['non_teaching_positions'] = []
#             return cleaned_data

#         if self.user.role == 'student':
#             if role == 'student':
#                 if not student_class:
#                     self.add_error('student_class', "This field is required for students and parents.")
#                 if not class_arm:
#                     self.add_error('class_arm', "This field is required for students and parents.")
                    
#         if self.user.role in self.STUDENT_ROLES:
#             # Force branch to user's branch
#             cleaned_data['branch'] = self.user.branch

#             if not role:
#                 raise ValidationError('You must select a role.')

#             # require_full_filter = student_class or class_arm  # Trigger validation if either is selected

#             # if role in ['student', 'parent'] and require_full_filter:
#             #     if not student_class or not class_arm:
#             #         raise ValidationError('Both class and arm are required to filter.')
            
#             if role == 'student' and self.user.role == 'student':
#                 if student_class is None or class_arm is None:
#                     raise ValidationError('Both class and arm are required for student users.')


#         elif self.user.role in self.STAFF_ROLES:
#             if not branch:
#                 raise ValidationError('Branch must be selected.')

#             require_staff_filter = staff_type or teaching_positions.exists() or non_teaching_positions.exists()

#             if role in ['staff', 'branch_admin', 'superadmin'] and require_staff_filter:
#                 self._validate_staff_positions(
#                     staff_type,
#                     teaching_positions,
#                     non_teaching_positions
#                 )

#         return cleaned_data

#     def _validate_staff_positions(self, staff_type, teaching_positions, non_teaching_positions):
#         if not staff_type and not teaching_positions.exists() and not non_teaching_positions.exists():
#             raise ValidationError("Staff type and at least one teaching or non-teaching position must be selected.")

#         if staff_type == 'teaching':
#             if non_teaching_positions.exists():
#                 raise ValidationError("Non-teaching positions cannot be selected for teaching staff type.")
#             if not teaching_positions.exists():
#                 raise ValidationError("At least one teaching position must be selected.")

#         elif staff_type == 'non_teaching':
#             if teaching_positions.exists():
#                 raise ValidationError("Teaching positions cannot be selected for non-teaching staff type.")
#             if not non_teaching_positions.exists():
#                 raise ValidationError("At least one non-teaching position must be selected.")

#         elif staff_type == 'both':
#             if not (teaching_positions.exists() or non_teaching_positions.exists()):
#                 raise ValidationError("Select at least one teaching or non-teaching position for 'both' staff type.")

#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         instance.sender = self.user

#         role = self.cleaned_data.get('role')

#         if self.user.role in self.STUDENT_ROLES:
#             instance.branch = self.user.branch
#             instance.role = role

#             if role in ['student', 'parent']:
#                 instance.student_class = self.cleaned_data.get('student_class')
#                 instance.class_arm = self.cleaned_data.get('class_arm')

#                 # Clear staff fields
#                 instance.staff_type = None
#                 instance.teaching_positions.clear()
#                 instance.non_teaching_positions.clear()

#             elif role in self.STAFF_ROLES:
#                 instance.staff_type = self.cleaned_data.get('staff_type')
#                 if instance.staff_type == 'teaching':
#                     instance.teaching_positions.set(self.cleaned_data.get('teaching_positions'))
#                     instance.non_teaching_positions.clear()
#                 elif instance.staff_type == 'non_teaching':
#                     instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions'))
#                     instance.teaching_positions.clear()
#                 else:  # both or none
#                     instance.teaching_positions.clear()
#                     instance.non_teaching_positions.clear()

#                 instance.student_class = None
#                 instance.class_arm = None
#             else:
#                 raise ValidationError(f"Invalid role selected: {role}")

#         elif self.user.role in self.STAFF_ROLES:
#             instance.branch = self.cleaned_data.get('branch')
#             instance.role = self.cleaned_data.get('role')
#             instance.staff_type = self.cleaned_data.get('staff_type')

#             if instance.staff_type == 'teaching':
#                 instance.teaching_positions.set(self.cleaned_data.get('teaching_positions') or [])
#                 instance.non_teaching_positions.clear()
#             elif instance.staff_type == 'non_teaching':
#                 instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions') or [])
#                 instance.teaching_positions.clear()
#             else:
#                 instance.teaching_positions.clear()
#                 instance.non_teaching_positions.clear()

#             instance.student_class = self.cleaned_data.get('student_class')
#             instance.class_arm = self.cleaned_data.get('class_arm')

#         if commit:
#             instance.save()
#             self.save_m2m()

#         return instance

#     def get_filtered_recipients(self, target_group_data):
#         # Extract filters
#         role = target_group_data.get('role')
#         branch = target_group_data.get('branch')
#         staff_type = target_group_data.get('staff_type')
#         student_class = target_group_data.get('student_class')
#         class_arm = target_group_data.get('class_arm')
#         teaching_positions = target_group_data.get('teaching_positions') or []
#         non_teaching_positions = target_group_data.get('non_teaching_positions') or []
#         search = target_group_data.get('search')

#         # Base queryset excluding current user
#         qs = CustomUser.objects.filter(is_active=True).exclude(id=self.user.id)
    
#         # def filter_staff(qs, staff_type, teaching_positions, non_teaching_positions):
#         #     if not staff_type:
#         #         return CustomUser.objects.none()

#         #     if self.user.role == "student":
#         #         if staff_type == 'teaching':
#         #             if not teaching_positions:
#         #                 return CustomUser.objects.none()
#         #             return qs.filter(
#         #                 role__in=['staff', 'branch_admin'],
#         #                 staff_type='teaching',
#         #                 teaching_positions__in=teaching_positions
#         #             ).distinct()

#         #         elif staff_type == 'non_teaching':
#         #             if not non_teaching_positions:
#         #                 return CustomUser.objects.none()
#         #             return qs.filter(
#         #                 role__in=['staff', 'branch_admin'],
#         #                 staff_type='non_teaching',
#         #                 non_teaching_positions__in=non_teaching_positions
#         #             ).distinct()

#         #         else:  # both or none
#         #             return qs.filter(role__in=['staff', 'branch_admin'])
                            
#         #     elif self.user.role == "parent":
#         #         if staff_type == 'teaching':
#         #             if not teaching_positions:
#         #                 return CustomUser.objects.none()
#         #             return qs.filter(
#         #                 role='staff',
#         #                 staff_type='teaching',
#         #                 teaching_positions__in=teaching_positions
#         #             ).distinct()
                
#         #     else:
#         #         if staff_type == 'teaching':
#         #             if not teaching_positions:
#         #                 return CustomUser.objects.none()
#         #             return qs.filter(
#         #                 role__in=['staff', 'branch_admin', 'superadmin'],
#         #                 staff_type='teaching',
#         #                 teaching_positions__in=teaching_positions
#         #             ).distinct()

#         #         elif staff_type == 'non_teaching':
#         #             if not non_teaching_positions:
#         #                 return CustomUser.objects.none()
#         #             return qs.filter(
#         #                 role__in=['staff', 'branch_admin', 'superadmin'],
#         #                 staff_type='non_teaching',
#         #                 non_teaching_positions__in=non_teaching_positions
#         #             ).distinct()

#         #         else:  # both or none
#         #             return qs.filter(role__in=['staff', 'branch_admin', 'superadmin'])
                            
#         def filter_staff(qs, staff_type, teaching_positions, non_teaching_positions):
#             if not staff_type:
#                 return CustomUser.objects.none()

#             user_role = self.user.role
#             valid_roles = {
#                 "student": ['staff', 'branch_admin'],
#                 "parent": ['staff'],
#                 "default": ['staff', 'branch_admin', 'superadmin']
#             }

#             def has_required_positions(required_positions):
#                 return bool(required_positions)

#             def apply_filter(roles, s_type, positions_field, positions):
#                 if not has_required_positions(positions):
#                     return CustomUser.objects.none()
#                 return qs.filter(
#                     role__in=roles,
#                     staff_type=s_type,
#                     **{positions_field: positions}
#                 ).distinct()

#             if user_role == "student":
#                 if staff_type == 'teaching':
#                     return apply_filter(valid_roles["student"], 'teaching', 'teaching_positions__in', teaching_positions)
#                 elif staff_type == 'non_teaching':
#                     return apply_filter(valid_roles["student"], 'non_teaching', 'non_teaching_positions__in', non_teaching_positions)
#                 else:
#                     return qs.filter(role__in=valid_roles["student"])

#             elif user_role == "parent":
#                 if staff_type == 'teaching':
#                     return apply_filter(valid_roles["parent"], 'teaching', 'teaching_positions__in', teaching_positions)

#             # Default for other roles (e.g. staff, admin)
#             if staff_type == 'teaching':
#                 return apply_filter(valid_roles["default"], 'teaching', 'teaching_positions__in', teaching_positions)
#             elif staff_type == 'non_teaching':
#                 return apply_filter(valid_roles["default"], 'non_teaching', 'non_teaching_positions__in', non_teaching_positions)
#             else:
#                 return qs.filter(role__in=valid_roles["default"])

#         # if self.user.role in self.STUDENT_ROLES:
#         #     branch = self.user.branch
#         #     qs = qs.filter(branch=branch)

#         #     if self.user.role == 'student':
#         #         if not role:
#         #             return CustomUser.objects.none()

#         #         # Student wants to see other students
#         #         if role == 'student':
#         #             qs = qs.filter(role='student')

#         #             # Initially return none if no class is selected
#         #             if not student_class:
#         #                 qs = qs.none()
#         #             else:
#         #                 qs = qs.filter(studentprofile__current_class_id=student_class)
#         #                 if class_arm:
#         #                     qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

#         #         # Student wants to see their own parent
#         #         elif role == 'parent':
#         #             try:
#         #                 parent_user_id = self.user.studentprofile.parent.user.id
#         #                 qs = qs.filter(id=parent_user_id, role='parent')
#         #             except StudentProfile.DoesNotExist:
#         #                 qs = CustomUser.objects.none()

#         #         # Staff members (e.g., for directory view or info)
#         #         else:
#         #             qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)
            
#         #     elif self.user.role == 'parent':
#         #         from django.contrib.contenttypes.models import ContentType
#         #         from accounts.models import TeachingPosition, StaffProfile
#         #         from django.db.models import Q

#         #         parent = self.user.parentprofile
#         #         children = parent.students.all()

#         #         if not role:
#         #             return qs.none()
                
#         #         if role == 'student':
#         #             # Show all the parent's students
#         #             qs = qs.filter(role='student', studentprofile__parent=parent)

#         #             if student_class:
#         #                 qs = qs.filter(studentprofile__current_class_id=student_class)

#         #             # Optionally filter by class arm
#         #             if class_arm:
#         #                 qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

    
#         #         elif role == 'branch_admin':
#         #             qs = qs.filter(
#         #                 role='branch_admin',
#         #                 branch_id=self.user.branch_id
#         #             )
#         #             return qs

#         #         elif role == 'staff':
#         #             # Return none if no teaching position selected
#         #             if not teaching_positions:
#         #                 return qs.none()

#         #             # Get the (class, arm) combinations for the parent's children
#         #             child_class_pairs = children.values_list('current_class', 'current_class_arm')

#         #             # Build class_arm filter
#         #             class_arm_filters = Q()
#         #             for class_id, arm_id in child_class_pairs:
#         #                 if class_id and arm_id:
#         #                     class_arm_filters |= Q(managing_class_id=class_id, managing_class_arm_id=arm_id)

#         #             # Staff who manage those class + arm pairs
#         #             managing_staff_user_ids = StaffProfile.objects.filter(
#         #                 class_arm_filters
#         #             ).values_list('user_id', flat=True)

#         #             # Get the ContentType for TeachingPosition
#         #             teaching_ct = ContentType.objects.get_for_model(TeachingPosition)

#         #             # All teaching positions where is_class_teacher = True
#         #             class_teacher_positions = TeachingPosition.objects.filter(is_class_teacher=True)
#         #             class_teacher_ids = class_teacher_positions.values_list('id', flat=True)

#         #             # Staff whose primary position is a class teacher
#         #             primary_class_teacher_ids = StaffProfile.objects.filter(
#         #                 position_content_type=teaching_ct,
#         #                 position_object_id__in=class_teacher_ids
#         #             ).values_list('user_id', flat=True)

#         #             # Users who have any class teacher role (many-to-many)
#         #             any_class_teacher_ids = CustomUser.objects.filter(
#         #                 teaching_positions__in=class_teacher_positions
#         #             ).values_list('id', flat=True)

#         #             # Combine both sets of class teacher user IDs
#         #             class_teacher_user_ids = set(primary_class_teacher_ids).union(set(any_class_teacher_ids))

#         #             # Staff who both manage relevant class/arm and are class teachers
#         #             final_staff_user_ids = set(managing_staff_user_ids).intersection(class_teacher_user_ids)

#         #             # Include branch_admins who are also class teachers
#         #             branch_admin_class_teacher_ids = CustomUser.objects.filter(
#         #                 id__in=class_teacher_user_ids,
#         #                 role='branch_admin',
#         #                 branch_id=self.user.branch_id
#         #             ).values_list('id', flat=True)

#         #             # Combine both sets of allowed user IDs
#         #             allowed_user_ids = list(final_staff_user_ids.union(branch_admin_class_teacher_ids))

#         #             # Final filtered queryset
#         #             return qs.filter(id__in=allowed_user_ids).distinct()

#         # elif self.user.role in self.STAFF_ROLES:
#         #     if not branch:
#         #         return CustomUser.objects.none()
#         #     qs = qs.filter(branch=branch)

#         #     if role in ['staff', 'branch_admin', 'superadmin'] and staff_type:
#         #         qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)
#         #     elif role:
#         #         qs = qs.filter(role=role)

#         # # Apply search filter
#         # if search:
#         #     qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))

#         # return qs
        
#         if self.user.role in self.STUDENT_ROLES:
#             branch = self.user.branch
#             qs = qs.filter(branch=branch)

#             if self.user.role == 'student':
#                 if not role:
#                     return CustomUser.objects.none()

#                 if role == 'student':
#                     qs = qs.filter(role='student')
#                     if not student_class:
#                         qs = qs.none()
#                     else:
#                         qs = qs.filter(studentprofile__current_class_id=student_class)
#                         if class_arm:
#                             qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

#                 elif role == 'parent':
#                     try:
#                         parent_user_id = self.user.studentprofile.parent.user.id
#                         qs = qs.filter(id=parent_user_id, role='parent')
#                     except StudentProfile.DoesNotExist:
#                         qs = CustomUser.objects.none()

#                 else:
#                     qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)

#             elif self.user.role == 'parent':
#                 from django.contrib.contenttypes.models import ContentType
#                 from accounts.models import TeachingPosition, StaffProfile
#                 from django.db.models import Q

#                 parent = self.user.parentprofile
#                 children = parent.students.all()

#                 if not role:
#                     return qs.none()

#                 if role == 'student':
#                     qs = qs.filter(role='student', studentprofile__parent=parent)
#                     if student_class:
#                         qs = qs.filter(studentprofile__current_class_id=student_class)
#                     if class_arm:
#                         qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

#                 elif role == 'branch_admin':
#                     return qs.filter(role='branch_admin', branch_id=self.user.branch_id)

#                 elif role == 'staff':
#                     if not teaching_positions:
#                         return qs.none()

#                     child_class_pairs = children.values_list('current_class', 'current_class_arm')

#                     class_arm_filters = Q()
#                     for class_id, arm_id in child_class_pairs:
#                         if class_id and arm_id:
#                             class_arm_filters |= Q(managing_class_id=class_id, managing_class_arm_id=arm_id)

#                     managing_staff_user_ids = StaffProfile.objects.filter(
#                         class_arm_filters
#                     ).values_list('user_id', flat=True)

#                     teaching_ct = ContentType.objects.get_for_model(TeachingPosition)
#                     class_teacher_positions = TeachingPosition.objects.filter(is_class_teacher=True)
#                     class_teacher_ids = class_teacher_positions.values_list('id', flat=True)

#                     primary_class_teacher_ids = StaffProfile.objects.filter(
#                         position_content_type=teaching_ct,
#                         position_object_id__in=class_teacher_ids
#                     ).values_list('user_id', flat=True)

#                     any_class_teacher_ids = CustomUser.objects.filter(
#                         teaching_positions__in=class_teacher_positions
#                     ).values_list('id', flat=True)

#                     class_teacher_user_ids = set(primary_class_teacher_ids).union(any_class_teacher_ids)
#                     final_staff_user_ids = set(managing_staff_user_ids).intersection(class_teacher_user_ids)

#                     branch_admin_class_teacher_ids = CustomUser.objects.filter(
#                         id__in=class_teacher_user_ids,
#                         role='branch_admin',
#                         branch_id=self.user.branch_id
#                     ).values_list('id', flat=True)

#                     allowed_user_ids = list(final_staff_user_ids.union(branch_admin_class_teacher_ids))
#                     return qs.filter(id__in=allowed_user_ids).distinct()

#         elif self.user.role in self.STAFF_ROLES:
#             if not branch:
#                 return CustomUser.objects.none()

#             qs = qs.filter(branch=branch)

#             if role in ['staff', 'branch_admin', 'superadmin'] and staff_type:
#                 qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)
#             elif role:
#                 qs = qs.filter(role=role)

#         if search:
#             qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))

#         return qs
