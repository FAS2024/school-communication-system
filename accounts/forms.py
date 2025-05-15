from django import forms
from .models import CustomUser, TeachingPosition, NonTeachingPosition, Branch, StaffProfile,StudentProfile,StudentClass, ClassArm, ParentProfile
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model


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




# class StudentCreationForm(UserCreationForm):
#     password1 = forms.CharField(
#         widget=forms.PasswordInput(),
#         required=False,
#         label='Password'
#     )
#     password2 = forms.CharField(
#         widget=forms.PasswordInput(),
#         required=False,
#         label='Confirm Password'
#     )
#     email = forms.EmailField(required=True)
#     username = forms.CharField(required=True)
#     profile_picture = forms.ImageField(required=False)
#     gender = forms.ChoiceField(
#         choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')],
#         required=True
#     )

#     class Meta:
#         model = CustomUser
#         fields = [
#             'email', 'profile_picture', 'username', 'first_name', 'last_name',
#             'gender', 'password1', 'password2',
#         ]

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#         for field in self.fields.values():
#             field.widget.attrs['class'] = 'form-control'

#         self.instance.role = 'student'  # Force role to student

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
#         user = super().save(commit=False)
#         password1 = self.cleaned_data.get("password1")

#         if password1:
#             user.set_password(password1)
#         elif self.instance and self.instance.pk:
#             existing_user = CustomUser.objects.get(pk=self.instance.pk)
#             user.password = existing_user.password

#         if 'profile_picture' in self.cleaned_data:
#             user.profile_picture = self.cleaned_data['profile_picture']

#         if commit:
#             user.save()
#         return user


# class StudentProfileForm(forms.ModelForm):
#     class Meta:
#         model = StudentProfile
#         fields = [
#             'phone_number', 'date_of_birth',
#             'admission_number', 'current_class', 'current_class_arm',
#             'parent', 'address', 'guardian_name'
#         ]
#         widgets = {
#             'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
#             'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
#             'address': forms.Textarea(attrs={'rows': 2}),
#         }

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#         if user:
#             if user.role == 'branch_admin':
#                 self.fields['parent'].queryset = ParentProfile.objects.filter(user__branch=user.branch)
#             elif user.role == 'superadmin':
#                 self.fields['parent'].queryset = ParentProfile.objects.all()

#             if user.role == 'student' and user == getattr(self.instance, 'user', None):
#                 readonly_fields = [
#                     'date_of_birth', 'admission_number', 'current_class',
#                     'current_class_arm', 'parent', 'guardian_name'
#                 ]
#                 for field in readonly_fields:
#                     if field in self.fields:
#                         self.fields[field].disabled = True


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, StudentProfile, ParentProfile, Branch

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
    class Meta:
        model = StudentProfile
        fields = [
            'phone_number', 'date_of_birth',
            'admission_number', 'current_class', 'current_class_arm',
            'parent', 'address', 'guardian_name'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            if user.role == 'branch_admin':
                # Show only parents from this branch
                self.fields['parent'].queryset = ParentProfile.objects.filter(user__branch=user.branch)
            elif user.role == 'superadmin':
                # Show all parents
                self.fields['parent'].queryset = ParentProfile.objects.all()

        if user and user.role == 'student' and user == getattr(self.instance, 'user', None):
            readonly_fields = [
                'date_of_birth', 'admission_number', 'current_class',
                'current_class_arm', 'parent', 'guardian_name'
            ]
            for field in readonly_fields:
                if field in self.fields:
                    self.fields[field].disabled = True
