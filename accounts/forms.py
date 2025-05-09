from django import forms
from .models import CustomUser, TeachingPosition, NonTeachingPosition, Branch

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
