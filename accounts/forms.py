from django import forms
from .models import CustomUser, TeachingPosition, NonTeachingPosition, Branch, StaffProfile
from django.contrib.auth.forms import UserCreationForm


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

class StaffCreationForm(UserCreationForm):
    # Define the fields directly as class attributes
    teaching_positions = forms.ModelMultipleChoiceField(
        queryset=TeachingPosition.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Teaching Positions"
    )
    non_teaching_positions = forms.ModelMultipleChoiceField(
        queryset=NonTeachingPosition.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Non-Teaching Positions"
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'role', 'staff_type', 'teaching_positions', 'non_teaching_positions', 'branch',
            'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # current logged-in user
        super(StaffCreationForm, self).__init__(*args, **kwargs)

        # Control visibility of staff_type field
        if user and user.role in ['superadmin', 'branch_admin']:
            self.fields['staff_type'].widget = forms.Select(choices=CustomUser.STAFF_TYPE_CHOICES)
        else:
            self.fields['staff_type'].widget = forms.HiddenInput()

        # Role field visibility and choices
        if user:
            if user.role == 'superadmin':
                self.fields['role'].choices = [
                    ('superadmin', 'Super Admin'),
                    ('branch_admin', 'Branch Admin'),
                    ('staff', 'Staff'),
                ]
            elif user.role == 'branch_admin':
                self.fields['role'].choices = [
                    ('branch_admin', 'Branch Admin'),
                    ('staff', 'Staff'),
                ]
            else:
                self.fields['role'].widget = forms.HiddenInput()
        else:
            self.fields['role'].widget = forms.HiddenInput()

        # Branch selection restriction
        if user and user.role == 'branch_admin':
            self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
            self.fields['branch'].initial = user.branch
        else:
            self.fields['branch'].queryset = Branch.objects.all()

    def save(self, commit=True):
        # Save the user instance
        user = super(StaffCreationForm, self).save(commit=False)

        # Save the ManyToMany relationships (Teaching and Non-Teaching Positions)
        if commit:
            user.save()  # Save the user instance to the database
            self.save_m2m()  # Save the ManyToMany relationships

        return user




class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = [
            'phone_number',
            'date_of_birth',
            'qualification',
            'years_of_experience',
            'address',
        ]
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Logged-in user (branch_admin or superadmin)
        super().__init__(*args, **kwargs)

        # Adjust form behavior depending on logged-in user's role
        if user and user.role == 'branch_admin':
            # Branch admin should only see staff related to their branch
            self.fields['branch'].queryset = Branch.objects.filter(id=user.branch.id)
        elif user and user.role == 'superadmin':
            # Superadmin can view all branches
            self.fields['branch'].queryset = Branch.objects.all()

        # Additional initialization logic can go here


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = '__all__'
