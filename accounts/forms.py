from django import forms
from .models import CustomUser, TeachingPosition, NonTeachingPosition, Branch, StaffProfile,StudentProfile,StudentClass, ClassArm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password



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

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("This field is required.")
        return name

class NonTeachingPositionForm(forms.ModelForm):
    class Meta:
        model = NonTeachingPosition
        fields = ['name']

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
        choices=[('male', 'Male'), ('female', 'Female')],
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
        
class StudentCreationForm(forms.ModelForm):
    # For password entry
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep existing password."
    )

    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput,
        required=False
    )

    admission_number = forms.CharField(max_length=50)
    current_class = forms.CharField(max_length=100)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    guardian_name = forms.CharField(max_length=100)
    address = forms.CharField(widget=forms.Textarea, required=False)
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number", help_text="Optional: Include country code.")
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=False, label="Gender")

    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name', 'profile_picture',
            'branch', 'password', 'phone_number', 'gender'
        ]
        widgets = {
            'email': forms.EmailInput(),
            'username': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Capture request user
        super().__init__(*args, **kwargs)

        # Force role to student only and hide it from form
        self.instance.role = 'student'

        # Field filtering based on user role
        if self.request and not self.request.user.is_superuser and hasattr(self.request.user, 'role') and self.request.user.role == 'branch_admin':
            self.fields['branch'].queryset = self.fields['branch'].queryset.filter(id=self.request.user.branch.id)

        if self.instance and self.instance.pk:  # Editing
            self.fields['password'].help_text = "Leave blank to keep the current password."
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("This email is already taken.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            validate_password(password)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'

        # Save the phone number and gender directly on CustomUser
        user.phone_number = self.cleaned_data.get('phone_number')
        user.gender = self.cleaned_data.get('gender')

        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        elif self.instance.pk:
            user.password = self.instance.password

        if commit:
            user.save()

            # Save or update StudentProfile (if required for additional fields)
            profile, created = StudentProfile.objects.get_or_create(user=user)
            profile.admission_number = self.cleaned_data['admission_number']
            profile.current_class = self.cleaned_data['current_class']
            profile.date_of_birth = self.cleaned_data['date_of_birth']
            profile.guardian_name = self.cleaned_data['guardian_name']
            profile.address = self.cleaned_data['address']
            profile.save()

        return user


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

        # Check if a StudentClass with the same name and arms already exists
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
