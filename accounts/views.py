from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from .forms import UserRegistrationForm
from .models import CustomUser, StudentProfile, ParentProfile, StaffProfile
from django import forms


def home(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


# Define the login view
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check the user's role and redirect based on it
            if user.role == 'student':
                return redirect('student_dashboard')  # Redirect to student dashboard
            elif user.role == 'parent':
                return redirect('parent_dashboard')  # Redirect to parent dashboard
            elif user.role == 'staff':
                return redirect('staff_dashboard')  # Redirect to staff dashboard
            elif user.role == 'branch_admin':
                return redirect('branch_admin_dashboard')  # Redirect to branch admin dashboard
            elif user.role == 'superadmin':
                return redirect('superadmin_dashboard')  # Redirect to super admin dashboard
            else:
                messages.error(request, 'Unknown user role')
                return redirect('login')
        
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    
    return render(request, 'registration/login.html')  # Render login form if GET request

# Define the student dashboard
@login_required
def student_dashboard(request):
    return render(request, 'dashboard/student_dashboard.html')

# Define the parent dashboard
@login_required
def parent_dashboard(request):
    return render(request, 'dashboard/parent_dashboard.html')

# Define the staff dashboard
@login_required
def staff_dashboard(request):
    return render(request, 'dashboard/staff_dashboard.html')

# Define the branch admin dashboard
@login_required
def branch_admin_dashboard(request):
    return render(request, 'dashboard/branch_admin_dashboard.html')

# Define the superadmin dashboard
@login_required
def superadmin_dashboard(request):
    return render(request, 'dashboard/superadmin_dashboard.html')


def logout(request):
    auth_logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


@login_required
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            raw_password = form.cleaned_data.get('password')
            user.set_password(raw_password)
            user.save()

            messages.success(request, f"{user.get_full_name()} registered successfully.")

            # Redirect based on role
            if user.role == 'staff':
                return redirect('staff_list')    # Replace with actual staff list URL name
            elif user.role == 'student':
                return redirect('student_list')  # Replace with actual student list URL name
            elif user.role == 'parent':
                return redirect('parent_list')   # Replace with actual parent list URL name
            else:
                return redirect('default_dashboard')  # Optional fallback
        else:
            messages.error(request, 'There was an error in your form.')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register_user.html', {'form': form})
