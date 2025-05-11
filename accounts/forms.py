from django import forms
from .models import CustomUser, TeachingPosition, NonTeachingPosition, Branch, StaffProfile
from django.contrib.auth.forms import UserCreationForm


from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator



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


# class StaffCreationForm(UserCreationForm):
#     teaching_positions = forms.ModelMultipleChoiceField(
#         queryset=TeachingPosition.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         label="Select Teaching Positions",
#         required=False
#     )
#     non_teaching_positions = forms.ModelMultipleChoiceField(
#         queryset=NonTeachingPosition.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         label="Select Non-Teaching Positions",
#         required=False
#     )

#     email = forms.EmailField(
#         required=True,
#         validators=[EmailValidator(message="Enter a valid email address.")],
#         widget=forms.EmailInput(attrs={'placeholder': 'Email'})
#     )
#     username = forms.CharField(
#         max_length=150,
#         required=True,
#         widget=forms.TextInput(attrs={'placeholder': 'Username'})
#     )

#     class Meta:
#         model = CustomUser
#         fields = [
#             'email', 'username', 'first_name', 'last_name',
#             'role', 'staff_type', 'teaching_positions', 'non_teaching_positions',
#             'branch', 'password1', 'password2'
#         ]

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#         # Conditional logic for role and staff_type
#         if user:
#             if user.role == 'superadmin':
#                 self.fields['role'].choices = [
#                     ('superadmin', 'Super Admin'),
#                     ('branch_admin', 'Branch Admin'),
#                     ('staff', 'Staff'),
#                 ]
#             elif user.role == 'branch_admin':
#                 self.fields['role'].choices = [
#                     ('branch_admin', 'Branch Admin'),
#                     ('staff', 'Staff'),
#                 ]
#                 self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
#                 self.fields['branch'].initial = user.branch
#             else:
#                 self.fields['role'].widget = forms.HiddenInput()
#         else:
#             self.fields['role'].widget = forms.HiddenInput()

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if CustomUser.objects.filter(email=email).exists():
#             raise ValidationError('This email is already in use.')
#         return email

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if CustomUser.objects.filter(username=username).exists():
#             raise ValidationError('This username is already taken.')
#         return username

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         if commit:
#             user.save()
#             self.save_m2m()
#         return user


# class StaffProfileForm(forms.ModelForm):
#     class Meta:
#         model = StaffProfile
#         fields = ['phone_number', 'date_of_birth', 'qualification', 'years_of_experience', 'address']
#         widgets = {
#             'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
#             'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
#         }


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = '__all__'


# class StaffCreationForm(UserCreationForm):
#     teaching_positions = forms.ModelMultipleChoiceField(
#         queryset=TeachingPosition.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=False
#     )
#     non_teaching_positions = forms.ModelMultipleChoiceField(
#         queryset=NonTeachingPosition.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=False
#     )
#     email = forms.EmailField(required=True)
#     username = forms.CharField(required=True)

#     class Meta:
#         model = CustomUser
#         fields = [
#             'email', 'username', 'first_name', 'last_name',
#             'role', 'staff_type', 'teaching_positions', 'non_teaching_positions',
#             'branch', 'password1', 'password2'
#         ]

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#         if user:
#             if user.role == 'superadmin':
#                 self.fields['role'].choices = [
#                     ('superadmin', 'Super Admin'),
#                     ('branch_admin', 'Branch Admin'),
#                     ('staff', 'Staff'),
#                 ]
#                 self.fields['branch'].queryset = Branch.objects.all()

#             elif user.role == 'branch_admin':
#                 self.fields['role'].choices = [
#                     ('branch_admin', 'Branch Admin'),
#                     ('staff', 'Staff'),
#                 ]
#                 self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
#                 self.fields['branch'].initial = user.branch

#         else:
#             self.fields['role'].choices = [('staff', 'Staff')]
#             self.fields['branch'].widget = forms.HiddenInput()

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if CustomUser.objects.filter(email=email).exists():
#             raise ValidationError("This email is already in use.")
#         return email

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if CustomUser.objects.filter(username=username).exists():
#             raise ValidationError("This username is already taken.")
#         return username

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         if commit:
#             user.save()
#             self.save_m2m()
#         return user
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

    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'role', 'staff_type', 'teaching_positions', 'non_teaching_positions',
            'branch', 'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Make password optional if editing an existing user
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False

        # Customize field access based on current user's role
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
        else:
            self.fields['role'].choices = [('staff', 'Staff')]
            self.fields['branch'].widget = forms.HiddenInput()

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
            # Retrieve password from the database to retain it
            existing_user = CustomUser.objects.get(pk=self.instance.pk)
            user.password = existing_user.password

        if commit:
            user.save()
            self.save_m2m()
        return user


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['phone_number', 'date_of_birth', 'qualification', 'years_of_experience', 'address']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
