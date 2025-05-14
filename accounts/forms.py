from django import forms
from .models import CustomUser, TeachingPosition, NonTeachingPosition, Branch, StaffProfile,StudentProfile,StudentClass, ClassArm, ParentProfile
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.contrib.auth import password_validation


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
    
#     admission_number = forms.CharField(max_length=50)
#     current_class = forms.ModelChoiceField(
#         queryset=StudentClass.objects.all(),
#         required=False,
#         empty_label="Select a class"
#     )
#     current_class_arm = forms.ModelChoiceField(
#         queryset=ClassArm.objects.all(),
#         required=False,
#         empty_label="Select a class arm"
#     )
#     parent = forms.ModelChoiceField(
#         queryset=ParentProfile.objects.all(),
#         required=True,
#         empty_label="Select a Parent"
#     )
#     date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
#     guardian_name = forms.CharField(max_length=100,required=False, label="Guardian/Child Handler")
#     address = forms.CharField(widget=forms.Textarea, required=False)
#     phone_number = forms.CharField(max_length=15, required=False, label="Phone Number", help_text="Optional: Include country code.")
#     gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'),('others', 'Others')],required=False, label="Gender")

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
#         self.instance.role = 'student'

#         # Field filtering based on user role
#         if self.request and not self.request.user.is_superuser and hasattr(self.request.user, 'role') and self.request.user.role == 'branch_admin':
#             self.fields['branch'].queryset = self.fields['branch'].queryset.filter(id=self.request.user.branch.id)

#         # Pre-fill fields for update if the instance is an existing student
#         if self.instance and self.instance.pk:
#             self.fields['password1'].required = False
#             self.fields['password2'].required = False
#             self.fields['password1'].widget.attrs['placeholder'] = 'Enter new password (optional)'
#             self.fields['password2'].widget.attrs['placeholder'] = 'Confirm new password'

#             try:
#                 profile = self.instance.studentprofile
#                 self.fields['current_class_arm'].initial = profile.current_class_arm
#                 self.fields['admission_number'].initial = profile.admission_number
#                 self.fields['current_class'].initial = profile.current_class
#                 self.fields['date_of_birth'].initial = profile.date_of_birth
#                 self.fields['parent'].initial = profile.parent
#                 self.fields['guardian_name'].initial = profile.guardian_name
#             except StudentProfile.DoesNotExist:
#                 pass

#         # Set branch choices based on user role
#         if user:
#             if user.role == 'superadmin':
#                 self.fields['branch'].queryset = Branch.objects.all()

#             elif user.role == 'branch_admin':
#                 self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
#                 self.fields['branch'].initial = user.branch

#             if user.role == 'student' and user == self.instance:
#                 readonly_fields = [
#                     'role',
#                     'branch',
#                     'gender',
#                     'admission_number',
#                     'current_class',
#                     'current_class_arm',
#                     'date_of_birth',
#                     'parent',
#                     'guardian_name'
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

#     def save(self, commit=True):
#         with transaction.atomic():
#             # Save the user without committing to DB yet
#             user = super().save(commit=False)
#             user.role = 'student'
#             user.gender = self.cleaned_data.get('gender')

#             # Handle password
#             password1 = self.cleaned_data.get("password1")
#             if password1:
#                 user.set_password(password1)
#             elif self.instance and self.instance.pk:
#                 existing_user = CustomUser.objects.get(pk=self.instance.pk)
#                 user.password = existing_user.password

#             # Handle profile picture
#             if 'profile_picture' in self.cleaned_data:
#                 user.profile_picture = self.cleaned_data['profile_picture']

#             if not commit:
#                 return user

#             # Save the user
#             user.save()

#             # Define the required student profile fields
#             required_fields = [
#                 'admission_number', 'current_class', 'current_class_arm',
#                 'date_of_birth', 'guardian_name', 'parent',
#                 'phone_number', 'address'
#             ]

#             # Check for any missing required fields
#             missing_fields = [f for f in required_fields if not self.cleaned_data.get(f)]
#             if missing_fields:
#                 raise ValidationError(f"Please fill out all required student profile fields: {', '.join(missing_fields)}")

#             # Ensure 'parent' field is provided
#             parent = self.cleaned_data.get('parent')
#             if not parent:
#                 raise ValidationError("Parent is a required field and cannot be null.")

#             # Get or create the StudentProfile and assign required fields
#             profile, created = StudentProfile.objects.get_or_create(user=user)
#             profile.admission_number = self.cleaned_data['admission_number']
#             profile.current_class = self.cleaned_data['current_class']
#             profile.current_class_arm = self.cleaned_data['current_class_arm']
#             profile.date_of_birth = self.cleaned_data['date_of_birth']
#             profile.guardian_name = self.cleaned_data['guardian_name']
#             profile.address = self.cleaned_data['address']
#             profile.phone_number = self.cleaned_data['phone_number']
#             profile.parent = parent  # Make sure parent is assigned properly
#             profile.save()

#             return user



class StudentCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label='Confirm Password'
    )

    # Fields for StudentProfile
    admission_number = forms.CharField(required=True, label="Admission Number")
    current_class = forms.CharField(required=True, label="Current Class")
    current_class_arm = forms.CharField(required=True, label="Current Class Arm")
    date_of_birth = forms.DateField(required=True, label="Date of Birth")
    address = forms.CharField(required=True, label="Address", widget=forms.Textarea)
    phone_number = forms.CharField(required=True, label="Phone Number")
    parent = forms.ModelChoiceField(queryset=ParentProfile.objects.all(), required=True, label="Parent")
    guardian_name = forms.CharField(required=True, label="Guardian Name")

    # Fields for CustomUser (user fields)
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    username = forms.CharField(required=True, label="Username")
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')], required=True)
    profile_picture = forms.ImageField(required=False, label="Profile Picture", widget=forms.ClearableFileInput())

    class Meta:
        model = StudentProfile
        fields = ['admission_number', 'current_class', 'current_class_arm', 'date_of_birth', 'address', 'phone_number', 'parent', 'guardian_name', 'first_name', 'last_name', 'email', 'username', 'gender', 'profile_picture']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user is None:
            raise ValueError("User must be provided.")

        super().__init__(*args, **kwargs)

        self.fields['branch'] = forms.CharField(widget=forms.HiddenInput(), required=False)

        # Filter parent queryset based on the role of the user
        if user.role == 'branchadmin':
            self.fields['parent'].queryset = ParentProfile.objects.filter(user__branch=user.branch)
            self.instance.branch = user.branch

        elif user.role == 'superadmin':
            self.fields['parent'].queryset = ParentProfile.objects.all()

        # If user is a student, disable the fields they shouldn't edit
        if user.role == 'student':
            for field in ['user', 'admission_number', 'current_class', 'current_class_arm', 'date_of_birth', 'parent', 'guardian_name', 'branch']:
                self.fields[field].disabled = True

        self.current_user = user  # Store for later use in validation

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Validate matching passwords
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        # Validate email and username uniqueness
        user_instance = cleaned_data.get('user')
        if user_instance:
            email = cleaned_data.get('email')
            username = cleaned_data.get('username')

            if email:
                try:
                    EmailValidator()(email)
                except ValidationError:
                    self.add_error('email', "Please enter a valid email address.")
                # Check uniqueness excluding the current user if editing
                if CustomUser.objects.filter(email=email).exclude(pk=user_instance.pk).exists():
                    self.add_error('email', "This email is already taken.")

            if username and CustomUser.objects.filter(username=username).exclude(pk=user_instance.pk).exists():
                self.add_error('username', "This username is already taken.")

        # Validate phone number
        phone_number = cleaned_data.get('phone_number')
        if phone_number:
            validator = RegexValidator(r'^\d{10,15}$', 'Phone number must contain only digits and be between 10 and 15 characters.')
            try:
                validator(phone_number)
            except ValidationError as e:
                self.add_error('phone_number', e)

        # Ensure 'branch' is always included in cleaned_data
        if self.current_user.role == 'branchadmin':
            cleaned_data['branch'] = self.current_user.branch
        elif self.instance.parent:
            cleaned_data['branch'] = self.instance.parent.user.branch

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set branch from parent or user if missing
        if instance.parent:
            instance.branch = instance.parent.user.branch
        elif self.current_user.role == 'branchadmin' and not instance.branch:
            instance.branch = self.current_user.branch

        # Handle password
        new_password = self.cleaned_data.get('password')
        if new_password:
            try:
                password_validation.validate_password(new_password, instance.user)
                instance.user.set_password(new_password)
            except ValidationError as e:
                self.add_error('password', e)
                raise ValidationError("Password did not meet complexity requirements.")

        # Handle CustomUser fields (first_name, last_name, email, username, gender, profile_picture)
        user_instance = instance.user
        if user_instance:
            user_instance.first_name = self.cleaned_data.get('first_name')
            user_instance.last_name = self.cleaned_data.get('last_name')
            user_instance.email = self.cleaned_data.get('email')
            user_instance.username = self.cleaned_data.get('username')
            user_instance.gender = self.cleaned_data.get('gender')

            # If profile picture is provided, save it
            profile_picture = self.cleaned_data.get('profile_picture')
            if profile_picture:
                user_instance.profile_picture = profile_picture

            if commit:
                user_instance.save()

        if commit:
            instance.save()
            if new_password:
                instance.user.save()

        return instance

    
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



class ClassArmForm(forms.ModelForm):
    class Meta:
        model = ClassArm
        fields = ['name']  # Only the 'name' field for the ClassArm

    def clean_name(self):
        name = self.cleaned_data['name'].strip()  # Strip any unnecessary spaces
        if ClassArm.objects.filter(name=name).exists():  # Check if the arm already exists
            raise forms.ValidationError(f"The class arm '{name}' already exists.")
        return name



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
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
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
