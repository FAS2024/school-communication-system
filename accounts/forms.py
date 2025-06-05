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
        fields = ['name']

    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter position name'})
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
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.role == 'staff' and user == self.instance.user:
            # Staff can only edit these fields
            editable_fields = ['phone_number', 'qualification', 'years_of_experience', 'address']
            for field_name in self.fields:
                if field_name not in editable_fields:
                    self.fields[field_name].disabled = True

    class Meta:
        model = StaffProfile
        fields = ['phone_number', 'date_of_birth', 'qualification', 'years_of_experience', 'address']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
        
# class StudentCreationForm(forms.ModelForm):
#     password = forms.CharField(
#         widget=forms.PasswordInput(),
#         required=False,
#         label='Password'
#     )
#     confirm_password = forms.CharField(
#         widget=forms.PasswordInput(),
#         required=False,
#         label='Confirm Password'
#     )

#     # Fields for StudentProfile
#     admission_number = forms.CharField(required=True, label="Admission Number")
#     current_class = forms.ModelChoiceField(
#         queryset=StudentClass.objects.all(),  
#         required=True,
#         label="Current Class"
#     )
#     current_class_arm = forms.ModelChoiceField(
#         queryset=ClassArm.objects.all(),  
#         required=True,
#         label="Current Class Arm"
#     )
#     date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
#     address = forms.CharField(required=True, label="Address", widget=forms.Textarea)
#     phone_number = forms.CharField(required=True, label="Phone Number")
#     parent = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='parent'), required=True, label="Parent")
#     branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True, widget=forms.HiddenInput())  # Hidden and required
#     guardian_name = forms.CharField(required=True, label="Guardian Name")

#     # Fields for CustomUser (user fields)
#     first_name = forms.CharField(required=True, label="First Name")
#     last_name = forms.CharField(required=True, label="Last Name")
#     email = forms.EmailField(required=True, label="Email Address")
#     username = forms.CharField(required=True, label="Username")
#     gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')], required=True)
#     profile_picture = forms.ImageField(required=False, label="Profile Picture", widget=forms.ClearableFileInput())
    
#     class Meta:
#         model = CustomUser
#         fields = [
#             'email', 'username', 'first_name', 'last_name', 'profile_picture',
#             'password', 'confirm_password', 'phone_number', 'gender', 'branch'
#         ]
#         widgets = {
#             'email': forms.EmailInput(),
#             'username': forms.TextInput(),
#         }

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)

#         super().__init__(*args, **kwargs)
        
#         # self.fields['branch'] = forms.CharField(widget=forms.HiddenInput(), required=False)

#         if self.instance and self.instance.pk:
#             self.fields['password'].required = False
#             self.fields['confirm_password'].required = False
#             self.fields['password'].widget.attrs['placeholder'] = 'Enter new password (optional)'
#             self.fields['confirm_password'].widget.attrs['placeholder'] = 'Confirm new password'

#         if user:
#             if user.role == 'superadmin':
#                 self.fields['branch'].queryset = Branch.objects.all()
#                 self.fields['parent'].queryset = ParentProfile.objects.all()

#             elif user.role == 'branch_admin':
#                 self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
#                 self.fields['branch'].initial = user.branch
#                 self.fields['parent'].queryset = ParentProfile.objects.filter(user__branch=user.branch)
#                 self.instance.user.branch = user.branch

#             elif user.role == 'student' and user == self.instance:
#                 readonly_fields = ['user', 'admission_number', 'current_class', 'current_class_arm', 
#                         'date_of_birth', 'parent', 'guardian_name', 'branch'
#                 ]
#                 for field in readonly_fields:
#                     if field in self.fields:
#                         self.fields[field].disabled = True


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
    
#     def clean_phone_number(self):
#         phone_number = self.cleaned_data.get('phone_number')
#         if phone_number:
#             validator = RegexValidator(r'^\d{10,15}$', 'Phone number must contain only digits and be between 10 and 15 characters.')
#             try:
#                 validator(phone_number)
#             except ValidationError as e:
#                 self.add_error('phone_number', e)
#         return phone_number

#     def clean_password(self):
#         password = self.cleaned_data.get("password")
#         confirm_password = self.cleaned_data.get("confirm_password")
        
#         # If password and confirm_password are provided and don't match, add an error
#         if password and confirm_password and password != confirm_password:
#             self.add_error('confirm_password', "Passwords do not match.")
#         return password


#     def save(self, commit=True):
#         with transaction.atomic():
#             # Step 1: Ensure we are working with a CustomUser instance
#             user = super().save(commit=False)  # This should be the CustomUser instance

#             user.role = 'student'

#             # Get selected parent from the form and assign branch
#             parent = self.cleaned_data.get('parent')
#             if parent and parent.branch:
#                 user.branch = parent.branch
#             else:
#                 # Optional: you can handle this case (e.g., set a default branch or raise an error)
#                 raise ValueError("Parent must have a branch assigned.")
            
#             password = self.cleaned_data.get("password")
#             parent = self.cleaned_data["parent"]  # Parent is selected in the form dropdown

#             # If there's a password, set it, otherwise, retain the existing password if updating
#             if password:
#                 user.set_password(password)  # Hash the password before saving it
#             elif self.instance and self.instance.pk:
#                 existing_user = CustomUser.objects.get(pk=self.instance.pk)
#                 user.password = existing_user.password  # Retain the existing password on update

#             # If a profile picture is provided, save it to the user
#             if 'profile_picture' in self.cleaned_data:
#                 profile_picture = self.cleaned_data['profile_picture']
#                 if profile_picture:
#                     user.profile_picture = profile_picture

#             # Step 2: Save the CustomUser instance (save the user)
#             if commit:
#                 user.save()  # Save the CustomUser instance

#             # Step 3: Create or update the StudentProfile instance
#             profile, created = StudentProfile.objects.get_or_create(user=user)  # Create or get the profile

#             # Now populate the profile fields
#             profile.date_of_birth = self.cleaned_data['date_of_birth']
#             profile.address = self.cleaned_data['address']
#             profile.phone_number = self.cleaned_data['phone_number']
#             profile.admission_number = self.cleaned_data['admission_number']
#             profile.current_class = self.cleaned_data['current_class']
#             profile.current_class_arm = self.cleaned_data['current_class_arm']
#             profile.guardian_name = self.cleaned_data['guardian_name']
#             profile.parent = parent  # Assign the parent (this comes from the dropdown in the form)

#             profile.save()  # Save the StudentProfile instance

#             return user  # Return the saved CustomUser instance

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



class ParentCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder':'Enter password'}),
        required=False,
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder':'Confirm password'}),
        required=False
    )
    
    occupation = forms.CharField(max_length=50)
    address = forms.CharField(widget=forms.Textarea, required=False)
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number", help_text="Optional: Include country code.")
    nationality = forms.CharField(max_length=30,label="Country")
    state = forms.CharField(max_length=30,label="State")
    relationship_to_student = forms.CharField(max_length=15,  label="Relationship to Student")
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'),('others', 'Others')],required=False, label="Gender")
    preferred_contact_method =  forms.ChoiceField(choices=[
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('sms', 'SMS')
    ])
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name', 'profile_picture',
            'branch', 'password1', 'password2', 'phone_number', 'gender'
        ]
        widgets = {
            'email': forms.EmailInput(),
            'username': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Capture request user
        user = self.request.user
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        # Force role to student only and hide it from form
        self.instance.role = 'parent'

        # Field filtering based on user role
        if self.request and not self.request.user.is_superuser and hasattr(self.request.user, 'role') and self.request.user.role == 'branch_admin':
            self.fields['branch'].queryset = self.fields['branch'].queryset.filter(id=self.request.user.branch.id)

        # Pre-fill fields for update if the instance is an existing parent
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].widget.attrs['placeholder'] = 'Enter new password (optional)'
            self.fields['password2'].widget.attrs['placeholder'] = 'Confirm new password'

            try:
                profile = self.instance.parentprofile
                self.fields['relationship_to_student'].initial = profile.relationship_to_student
                self.fields['date_of_birth'].initial = profile.date_of_birth
                self.fields['nationality'].initial = profile.nationality
                self.fields['state'].initial = profile.state

            except ParentProfile.DoesNotExist:
                pass

        # Set branch choices based on user role
        if user:
            if user.role == 'superadmin':
                self.fields['branch'].queryset = Branch.objects.all()

            elif user.role == 'branch_admin':
                self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
                self.fields['branch'].initial = user.branch

            if user.role == 'parent' and user == self.instance:
                readonly_fields = [
                    'role',
                    'branch',
                    'gender',
                    'relationship_to_student',
                    'date_of_birth',
                ]
                for field in readonly_fields:
                    if field in self.fields:
                        self.fields[field].disabled = True  # Disable the fields for students
                        self.fields[field].required = False  # Make them not required

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
            print("Profile picture saved:", user.profile_picture)

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


# class CommunicationForm(forms.ModelForm):
#     # send_to_all = forms.BooleanField(required=False, label="Send to all users")
#     manual_emails = forms.CharField(
#         required=False,
#         label="Add manual emails",
#         widget=forms.Textarea(attrs={
#             "placeholder": "Comma-separated emails",
#             "rows": 2,  # reduce height
#             "cols": 40  # optional: adjust width
#         }),
#         help_text="Add emails manually (e.g., external contacts)"
#     )

#     class Meta:
#         model = Communication
#         fields = [
#             'message_type',
#             'title',
#             'body',
#             'is_draft',
#             'scheduled_time',
#             # 'send_to_all',
#         ]
#         widgets = {
#             'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         }

#     def __init__(self, *args, user=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user = user

#         if self.instance and self.instance.scheduled_time:
#             local_dt = localtime(self.instance.scheduled_time)
#             self.initial['scheduled_time'] = local_dt.strftime('%Y-%m-%dT%H:%M')
#             self.fields['scheduled_time'].label = "Scheduled time (24-hour clock)"

#         # Restrict message_type choices depending on sender role
#         if 'message_type' in self.fields:
#             all_message_types = [
#                 ('announcement', 'Announcement'),
#                 ('post', 'Post'),
#                 ('notification', 'Notification'),
#                 ('news', 'News'),
#                 ('personal', 'Personal'),
#                 ('group', 'Group'),
#             ]

#             if self.user.role in ['student', 'parent']:
#                 allowed_types = ['post', 'personal', 'group']
#                 filtered_choices = [
#                     (value, label) for value, label in all_message_types if value in allowed_types
#                 ]
#                 # Remove manual_emails field so students and parents don't see it
#                 self.fields.pop('manual_emails', None)
#             else:
#                 filtered_choices = all_message_types

#             self.fields['message_type'].choices = filtered_choices
#             self.fields['message_type'].choices = [('', 'Select a message type')] + filtered_choices


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

    class Meta:
        model = Communication
        fields = [
            'message_type',
            'title',
            'body',
            'is_draft',
            'scheduled_time',
        ]
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

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

        # Check for required fields manually to improve clarity
        if not message_type:
            self.add_error('message_type', "Message type is required.")
        if not title:
            self.add_error('title', "Title is required.")
        if not body:
            self.add_error('body', "Body is required.")

        # Raise global form error if any of the above is missing
        if self.errors:
            raise ValidationError("Please correct the required fields.")

        return cleaned_data

# class CommunicationTargetGroupForm(forms.ModelForm):
#     class Meta:
#         model = CommunicationTargetGroup
#         fields = [
#             'branch',
#             'role',
#             'staff_type',
#             'teaching_positions',
#             'non_teaching_positions',
#             'student_class',
#             'class_arm',
#         ]
#         widgets = {
#             'teaching_positions': forms.CheckboxSelectMultiple(),
#             'non_teaching_positions': forms.CheckboxSelectMultiple(),
#         }

#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#         if self.user:
#             if self.user.role in ['student', 'parent']:
#                 self.fields.pop('branch', None)
#             else:
#                 self.fields['branch'].queryset = Branch.objects.all()

#             if 'role' in self.fields:
#                 if self.user.role in ['student', 'parent']:
#                     self.fields['role'].choices = [
#                         ('', '------------'),
#                         ('student', 'Student'),
#                         ('staff', 'Staff'),
#                         ('branch_admin', 'Branch Admin'),
#                     ]
#                 else:
#                     self.fields['role'].choices = [
#                         ('', '-----------'),
#                         *CommunicationTargetGroup.ROLE_CHOICES,
#                     ]

#         self.fields['teaching_positions'].queryset = TeachingPosition.objects.all()
#         self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.all()
#         self.fields['student_class'].queryset = StudentClass.objects.all()
#         self.fields['class_arm'].queryset = ClassArm.objects.all()

#     def clean(self):
#         cleaned_data = super().clean()
#         staff_type = cleaned_data.get('staff_type')
#         teaching_positions = cleaned_data.get('teaching_positions')
#         non_teaching_positions = cleaned_data.get('non_teaching_positions')

#         if staff_type == 'teaching':
#             if non_teaching_positions.exists():
#                 raise ValidationError("Non-teaching positions must not be selected for teaching staff type.")
#             if not teaching_positions.exists():
#                 raise ValidationError("Please select at least one teaching position.")
        
#         elif staff_type == 'non_teaching':
#             if teaching_positions.exists():
#                 raise ValidationError("Teaching positions must not be selected for non-teaching staff type.")
#             if not non_teaching_positions.exists():
#                 raise ValidationError("Please select at least one non-teaching position.")
        
#         elif staff_type == 'both':
#             if not (teaching_positions.exists() or non_teaching_positions.exists()):
#                 raise ValidationError("At least one teaching or non-teaching position must be selected for 'both' staff type.")

#         return cleaned_data
    
#     def get_filtered_recipients(self, target_group_data):
#         from .models import CustomUser,StudentProfile
#         from django.db.models import Q
#         qs = CustomUser.objects.filter(is_active=True)


#         user = self.user

#         branch_id = target_group_data.get('branch')
#         role_name = target_group_data.get('role')
#         staff_type = target_group_data.get('staff_type')
#         teaching_positions_ids = target_group_data.get('teaching_positions')
#         non_teaching_positions_ids = target_group_data.get('non_teaching_positions')
#         student_class_id = target_group_data.get('student_class')
#         class_arm_id = target_group_data.get('class_arm')
#         search = target_group_data.get('search')

#         def filter_staff(qs):
#             if staff_type:
#                 qs = qs.filter(staff_type=staff_type)
#             if teaching_positions_ids:
#                 qs = qs.filter(teaching_positions__id__in=teaching_positions_ids)
#             if non_teaching_positions_ids:
#                 qs = qs.filter(non_teaching_positions__id__in=non_teaching_positions_ids)
#             return qs

#         def filter_students(qs):
#             if student_class_id:
#                 qs = qs.filter(studentprofile__current_class_id=student_class_id)
#             if class_arm_id:
#                 qs = qs.filter(studentprofile__current_class_arm_id=class_arm_id)
#             return qs

#         def apply_role_filters(qs):
#             if role_name:
#                 qs = qs.filter(role=role_name)

#             if role_name in ['staff', 'branch_admin'] or role_name is None:
#                 qs = filter_staff(qs)
#             if role_name == 'student' or role_name is None:
#                 qs = filter_students(qs)

#             return qs

#         if user.role == 'student':
#             qs = CustomUser.objects.filter(
#                 branch_id=user.branch_id,
#                 role__in=['student', 'staff', 'branch_admin']
#             ).exclude(id=user.id)
#             if not role_name:
#                 return CustomUser.objects.none()
#             qs = apply_role_filters(qs)

#         elif user.role == 'parent':
#             children = StudentProfile.objects.filter(parent__user=user)
#             child_class_ids = children.values_list('current_class_id', flat=True)

#             children_users = CustomUser.objects.filter(id__in=children.values_list('user_id', flat=True))
#             class_teacher_users = CustomUser.objects.filter(role='staff', class_teacher_of__id__in=child_class_ids)
#             branch_admins = CustomUser.objects.filter(role='branch_admin', branch_id=user.branch_id)

#             qs = (children_users | class_teacher_users | branch_admins).distinct()
#             if not role_name:
#                 return CustomUser.objects.none()
#             qs = apply_role_filters(qs)

#         elif user.role in ['staff', 'branch_admin', 'superadmin']:
#             if not (role_name or branch_id):
#                 return CustomUser.objects.none()
#             qs = CustomUser.objects.all()
#             if branch_id:
#                 qs = qs.filter(branch_id=branch_id)
#             qs = apply_role_filters(qs)

#         else:
#             return CustomUser.objects.none()

#         # Apply search filter if present
#         if search:
#             qs = qs.filter(
#                 Q(first_name__icontains=search) |
#                 Q(last_name__icontains=search) |
#                 Q(email__icontains=search)
#             )

#         return qs.exclude(id=user.id).distinct()


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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Setup queryset for related fields
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
            self.fields['role'].choices = [
                ('', '------------'),
                ('student', 'Student'),
                ('parent', 'Parent'),
                ('staff', 'Staff'),
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

    # def clean(self):
    #     cleaned_data = super().clean()

    #     role = cleaned_data.get('role')
    #     staff_type = cleaned_data.get('staff_type')
    #     branch = cleaned_data.get('branch')
    #     teaching_positions = cleaned_data.get('teaching_positions') or self.fields['teaching_positions'].queryset.none()
    #     non_teaching_positions = cleaned_data.get('non_teaching_positions') or self.fields['non_teaching_positions'].queryset.none()
    #     student_class = cleaned_data.get('student_class')
    #     class_arm = cleaned_data.get('class_arm')

    #     if self.user.role in self.STUDENT_ROLES:
    #         # Force branch to user branch
    #         cleaned_data['branch'] = self.user.branch

    #         if not role:
    #             raise ValidationError('You must select a role.')

    #         require_full_filter = student_class or class_arm  # True if either is selected

    #         if role in ['student', 'parent'] and require_full_filter:
    #             if not student_class or not class_arm:
    #                 raise ValidationError('Both class and arm are required to filter.')
                
    #     elif self.user.role in self.STAFF_ROLES:
    #         if not branch:
    #             raise ValidationError('Branch must be selected.')

    #         require_staff_filter = staff_type or teaching_positions or non_teaching_positions

    #         if role in ['staff', 'branch_admin', 'superadmin'] and require_staff_filter:
    #             self._validate_staff_positions(staff_type, teaching_positions, non_teaching_positions)

    #     return cleaned_data

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

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     instance.sender = self.user

    #     # Enforce branch and role constraints based on user role
    #     if self.user.role in self.STUDENT_ROLES:
    #         instance.branch = self.user.branch
    #         role = self.cleaned_data.get('role')

    #         if role in ['student', 'parent']:
    #             instance.student_class = self.cleaned_data.get('student_class')
    #             instance.class_arm = self.cleaned_data.get('class_arm')
    #             # Clear staff-related fields
    #             instance.staff_type = None
    #             instance.teaching_positions.clear()
    #             instance.non_teaching_positions.clear()

    #         elif role in ['staff', 'branch_admin', 'superadmin']:
    #             instance.staff_type = self.cleaned_data.get('staff_type')

    #             if instance.staff_type == 'teaching':
    #                 instance.teaching_positions.set(self.cleaned_data.get('teaching_positions'))
    #                 instance.non_teaching_positions.clear()
    #             elif instance.staff_type == 'non_teaching':
    #                 instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions'))
    #                 instance.teaching_positions.clear()
    #             else:  # both or none
    #                 # clear or set as needed
    #                 pass

    #             instance.student_class = None
    #             instance.class_arm = None

    #         else:
    #             raise ValidationError("Invalid role selected.")

    #         instance.role = role

    #     elif self.user.role in self.STAFF_ROLES:
    #         # Staff/admin users can set branch, role, staff_type freely
    #         instance.branch = self.cleaned_data.get('branch')
    #         instance.role = self.cleaned_data.get('role')
    #         instance.staff_type = self.cleaned_data.get('staff_type')

    #         if instance.staff_type == 'teaching':
    #             instance.teaching_positions.set(self.cleaned_data.get('teaching_positions') or [])
    #             instance.non_teaching_positions.clear()
    #         elif instance.staff_type == 'non_teaching':
    #             instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions') or [])
    #             instance.teaching_positions.clear()
    #         else:
    #             instance.teaching_positions.clear()
    #             instance.non_teaching_positions.clear()

    #         instance.student_class = self.cleaned_data.get('student_class')
    #         instance.class_arm = self.cleaned_data.get('class_arm')

    #     if commit:
    #         instance.save()
    #         self.save_m2m()

    #     return instance
    
    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get('role')
        staff_type = cleaned_data.get('staff_type')
        branch = cleaned_data.get('branch')
        teaching_positions = cleaned_data.get('teaching_positions') or self.fields['teaching_positions'].queryset.none()
        non_teaching_positions = cleaned_data.get('non_teaching_positions') or self.fields['non_teaching_positions'].queryset.none()
        student_class = cleaned_data.get('student_class')
        class_arm = cleaned_data.get('class_arm')

        if self.user.role in self.STUDENT_ROLES:
            # Force branch to user's branch
            cleaned_data['branch'] = self.user.branch

            if not role:
                raise ValidationError('You must select a role.')

            require_full_filter = student_class or class_arm  # Trigger validation if either is selected

            if role in ['student', 'parent'] and require_full_filter:
                if not student_class or not class_arm:
                    raise ValidationError('Both class and arm are required to filter.')

        elif self.user.role in self.STAFF_ROLES:
            if not branch:
                raise ValidationError('Branch must be selected.')

            require_staff_filter = staff_type or teaching_positions.exists() or non_teaching_positions.exists()

            if role in ['staff', 'branch_admin', 'superadmin'] and require_staff_filter:
                self._validate_staff_positions(
                    staff_type,
                    teaching_positions,
                    non_teaching_positions
                )

        return cleaned_data

    def _validate_staff_positions(self, staff_type, teaching_positions, non_teaching_positions):
        if not staff_type and not teaching_positions.exists() and not non_teaching_positions.exists():
            raise ValidationError("Staff type and at least one teaching or non-teaching position must be selected.")

        if staff_type == 'teaching':
            if non_teaching_positions.exists():
                raise ValidationError("Non-teaching positions cannot be selected for teaching staff type.")
            if not teaching_positions.exists():
                raise ValidationError("At least one teaching position must be selected.")

        elif staff_type == 'non_teaching':
            if teaching_positions.exists():
                raise ValidationError("Teaching positions cannot be selected for non-teaching staff type.")
            if not non_teaching_positions.exists():
                raise ValidationError("At least one non-teaching position must be selected.")

        elif staff_type == 'both':
            if not (teaching_positions.exists() or non_teaching_positions.exists()):
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
                    instance.teaching_positions.set(self.cleaned_data.get('teaching_positions'))
                    instance.non_teaching_positions.clear()
                elif instance.staff_type == 'non_teaching':
                    instance.non_teaching_positions.set(self.cleaned_data.get('non_teaching_positions'))
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
                return CustomUser.objects.none()

            if staff_type == 'teaching':
                if not teaching_positions:
                    return CustomUser.objects.none()
                return qs.filter(
                    role__in=['staff', 'branch_admin', 'superadmin'],
                    staff_type='teaching',
                    teaching_positions__in=teaching_positions
                ).distinct()

            elif staff_type == 'non_teaching':
                if not non_teaching_positions:
                    return CustomUser.objects.none()
                return qs.filter(
                    role__in=['staff', 'branch_admin', 'superadmin'],
                    staff_type='non_teaching',
                    non_teaching_positions__in=non_teaching_positions
                ).distinct()

            else:  # both or none
                return qs.filter(role__in=['staff', 'branch_admin', 'superadmin'])

        if self.user.role in self.STUDENT_ROLES:
            branch = self.user.branch
            qs = qs.filter(branch=branch)

            if self.user.role == 'student':
                if not role:
                    return CustomUser.objects.none()

                # Student wants to see other students
                if role == 'student':
                    qs = qs.filter(role='student')

                    # Optional: Limit to same class/arm only, if that's the intent
                    if student_class:
                        qs = qs.filter(studentprofile__current_class_id=student_class)
                    if class_arm:
                        qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

                # Student wants to see their own parent
                elif role == 'parent':
                    try:
                        parent_user_id = self.user.studentprofile.parent.user.id
                        qs = qs.filter(id=parent_user_id, role='parent')
                    except StudentProfile.DoesNotExist:
                        qs = CustomUser.objects.none()

                # Staff members (e.g., for directory view or info)
                else:
                    qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)

            elif self.user.role == 'parent':
                parent = self.user.parentprofile

                # Get all children linked to this parent
                children = parent.students.all()
                child_class_ids = children.values_list('current_class_id', flat=True)

                # Children (as CustomUser)
                children_user_ids = children.values_list('user_id', flat=True)

                # Class teachers of children's classes
                class_teacher_user_ids = CustomUser.objects.filter(
                    role='staff',
                    class_teacher_of__id__in=child_class_ids
                ).values_list('id', flat=True)

                # Branch admins
                branch_admin_ids = CustomUser.objects.filter(
                    role='branch_admin',
                    branch_id=self.user.branch_id
                ).values_list('id', flat=True)

                # Combine all allowed user IDs
                allowed_user_ids = list(children_user_ids) + list(class_teacher_user_ids) + list(branch_admin_ids)
                qs = qs.filter(id__in=allowed_user_ids).distinct()

                # Now filter by specific role if provided
                if not role:
                    return qs.none()

                if role == 'student':
                    # Just the parent's children, optionally filtered by class and class_arm
                    qs = qs.filter(
                        role='student',
                        studentprofile__parent=parent
                    )
                    if student_class:
                        qs = qs.filter(studentprofile__current_class_id=student_class)
                    if class_arm:
                        qs = qs.filter(studentprofile__current_class_arm_id=class_arm)

                else:
                    # Staff filtering logic
                    qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)

        elif self.user.role in self.STAFF_ROLES:
            if not branch:
                return CustomUser.objects.none()
            qs = qs.filter(branch=branch)

            if role in ['staff', 'branch_admin', 'superadmin'] and staff_type:
                qs = filter_staff(qs, staff_type, teaching_positions, non_teaching_positions)
            elif role:
                qs = qs.filter(role=role)

        # Apply search filter
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


# def get_filtered_recipients(self, target_group_data):
#         user = self.user

#         # Extract filter parameters
#         branch_id = target_group_data.get('branch')
#         role_name = target_group_data.get('role')
#         staff_type = target_group_data.get('staff_type')
#         teaching_positions_ids = target_group_data.get('teaching_positions')
#         non_teaching_positions_ids = target_group_data.get('non_teaching_positions')
#         student_class_id = target_group_data.get('student_class')
#         class_arm_id = target_group_data.get('class_arm')

#         def filter_staff(qs):
#             if staff_type:
#                 qs = qs.filter(staff_type=staff_type)
#             if teaching_positions_ids:
#                 qs = qs.filter(teaching_positions__id__in=teaching_positions_ids)
#             if non_teaching_positions_ids:
#                 qs = qs.filter(non_teaching_positions__id__in=non_teaching_positions_ids)
#             return qs

#         def filter_students(qs):
#             if student_class_id:
#                 qs = qs.filter(studentprofile__current_class_id=student_class_id)
#             if class_arm_id:
#                 qs = qs.filter(studentprofile__current_class_arm_id=class_arm_id)
#             return qs

#         def apply_role_filters(qs):
#             if role_name:
#                 qs = qs.filter(role=role_name)
#             if role_name in ['staff', 'branch_admin'] or role_name is None:
#                 qs = filter_staff(qs)
#             if role_name == 'student' or role_name is None:
#                 qs = filter_students(qs)
#             return qs

#         # Main logic by user role
#         if user.role == 'student':
#             qs = CustomUser.objects.filter(
#                 branch_id=user.branch_id,
#                 role__in=['student', 'staff', 'branch_admin']
#             ).exclude(id=user.id)

#             if role_name:
#                 qs = apply_role_filters(qs)
#             else:
#                 return CustomUser.objects.none()

#         elif user.role == 'parent':
#             children = StudentProfile.objects.filter(parent__user=user)
#             child_class_ids = children.values_list('current_class_id', flat=True)

#             children_users = CustomUser.objects.filter(id__in=children.values_list('user_id', flat=True))
#             class_teacher_users = CustomUser.objects.filter(role='staff', class_teacher_of__id__in=child_class_ids)
#             branch_admins = CustomUser.objects.filter(role='branch_admin', branch_id=user.branch_id)

#             qs = (children_users | class_teacher_users | branch_admins).distinct()

#             if role_name:
#                 qs = apply_role_filters(qs)
#             else:
#                 return CustomUser.objects.none()

#         elif user.role in ['staff', 'branch_admin', 'superadmin']:
#             qs = CustomUser.objects.all()

#             if branch_id:
#                 qs = qs.filter(branch_id=branch_id)
                
#             qs = apply_role_filters(qs) 
    
#         else:
#             return CustomUser.objects.none()

#         return qs.exclude(id=user.id).distinct()