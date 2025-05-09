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


# class StaffCreationForm(UserCreationForm):
#     class Meta:
#         model = CustomUser
#         fields = [
#             'email', 'username', 'first_name', 'last_name',
#             'role', 'staff_type',
#             'teaching_positions', 'non_teaching_positions', 'branch',
#             'password1', 'password2',  # Explicitly include password fields
#         ]

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)  # The logged-in user
#         super().__init__(*args, **kwargs)

#         # If the user is not a superadmin, restrict available roles
#         if user and user.role != 'superadmin':
#             # Non-superadmins should only see "Branch Admin" and "Staff"
#             self.fields['role'].choices = [
#                 ('branch_admin', 'Branch Admin'),
#                 ('staff', 'Staff'),
#             ]
#         else:
#             # Superadmins can see all roles
#             self.fields['role'].choices = [
#                 ('superadmin', 'Super Admin'),
#                 ('branch_admin', 'Branch Admin'),
#                 ('staff', 'Staff'),
#             ]

#         # Branch admin can only select their own branch
#         if user and user.role == 'branch_admin':
#             self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
#             self.fields['branch'].initial = user.branch
#         else:
#             self.fields['branch'].queryset = Branch.objects.all()

#         # Set the queryset for teaching and non-teaching positions
#         self.fields['teaching_positions'].queryset = TeachingPosition.objects.all()
#         self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.all()

#         # Use checkboxes to select multiple positions
#         self.fields['teaching_positions'].widget = forms.CheckboxSelectMultiple()
#         self.fields['non_teaching_positions'].widget = forms.CheckboxSelectMultiple()

#         # Add helpful labels for teaching and non-teaching positions
#         self.fields['teaching_positions'].label = "Select Teaching Positions"
#         self.fields['non_teaching_positions'].label = "Select Non-Teaching Positions"

class StaffCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'role', 'staff_type', 'teaching_positions', 'non_teaching_positions', 'branch',
            'password1', 'password2',  # Explicitly include password fields
        ]
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # The logged-in user
        super().__init__(*args, **kwargs)

        # Restrict available roles based on the current user's role
        if user and user.role != 'superadmin':
            # Non-superadmins should only see "Branch Admin" and "Staff"
            self.fields['role'].choices = [
                ('branch_admin', 'Branch Admin'),
                ('staff', 'Staff'),
            ]
        else:
            # Superadmins can see all roles
            self.fields['role'].choices = [
                ('superadmin', 'Super Admin'),
                ('branch_admin', 'Branch Admin'),
                ('staff', 'Staff'),
            ]
        
        # Branch admin can only select their own branch
        if user and user.role == 'branch_admin':
            self.fields['branch'].queryset = Branch.objects.filter(id=user.branch_id)
            self.fields['branch'].initial = user.branch
        else:
            self.fields['branch'].queryset = Branch.objects.all()

        # Set the queryset for teaching and non-teaching positions
        self.fields['teaching_positions'].queryset = TeachingPosition.objects.all()
        self.fields['non_teaching_positions'].queryset = NonTeachingPosition.objects.all()

        # Use checkboxes to select multiple positions
        self.fields['teaching_positions'].widget = forms.CheckboxSelectMultiple()
        self.fields['non_teaching_positions'].widget = forms.CheckboxSelectMultiple()

        # Add helpful labels for teaching and non-teaching positions
        self.fields['teaching_positions'].label = "Select Teaching Positions"
        self.fields['non_teaching_positions'].label = "Select Non-Teaching Positions"

        # Optional: Customize the staff type field, assuming you have a specific implementation
        # Ensure 'staff_type' field shows options only if the user is a staff member
        if user and user.role == 'staff':
            self.fields['staff_type'].widget = forms.Select(choices=[
                ('full_time', 'Full Time'),
                ('part_time', 'Part Time'),
            ])
        else:
            # Admin users might not need the staff type field
            self.fields['staff_type'].widget = forms.HiddenInput()

        # Optional: Customize the labels and add placeholders for more clarity
        self.fields['role'].label = "Role"
        self.fields['role'].help_text = "Select the appropriate role for the staff member."
        self.fields['branch'].label = "Branch"
        self.fields['branch'].help_text = "Select the branch the staff member belongs to."


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
