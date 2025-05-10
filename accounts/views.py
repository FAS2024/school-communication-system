from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from .forms import (
        UserRegistrationForm,
        TeachingPositionForm, 
        NonTeachingPositionForm, 
        StaffCreationForm, 
        StaffProfileForm,
        BranchForm
    )
from .models import (
        CustomUser, 
        StudentProfile, 
        ParentProfile, 
        StaffProfile,
        TeachingPosition,
        NonTeachingPosition,
        Branch
    )
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.http import Http404

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db import IntegrityError

User = get_user_model()



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


# Check if user is superadmin or branch admin
def is_superadmin_or_branchadmin(user):
    return user.role in ['superadmin', 'branch_admin']


@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def teaching_position_list(request):
    # If branch_admin, filter by the branch
    if request.user.role == 'branch_admin':
        branch = request.user.branch
        teaching_positions = TeachingPosition.objects.filter(branch=branch)
    else:
        teaching_positions = TeachingPosition.objects.all()

    paginator = Paginator(teaching_positions, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'teaching_position_list.html', {
        'page_obj': page_obj,
        'start_index': page_obj.start_index(),
    })



# View to add a new teaching position (only accessible by superadmin and branchadmin)
@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def teaching_position_create(request):
    if request.user.role == 'branch_admin':
        branch = request.user.branch
    else:
        branch = None

    if request.method == 'POST':
        form = TeachingPositionForm(request.POST)
        if form.is_valid():
            teaching_position = form.save(commit=False)
            teaching_position.branch = branch  # Set branch if it's branch_admin
            teaching_position.save()
            return redirect('teaching_position_list')
    else:
        form = TeachingPositionForm()

    return render(request, 'teaching_position_form.html', {'form': form})

# View to edit a teaching position (only accessible by superadmin and branchadmin)
@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def teaching_position_edit(request, pk):
    teaching_position = get_object_or_404(TeachingPosition, pk=pk)

    # Restrict branch_admin to only edit their own branch teaching positions
    if request.user.role == 'branch_admin' and teaching_position.branch != request.user.branch:
        return HttpResponseForbidden("You are not allowed to edit this teaching position.")

    if request.method == 'POST':
        form = TeachingPositionForm(request.POST, instance=teaching_position)
        if form.is_valid():
            form.save()
            return redirect('teaching_position_list')
    else:
        form = TeachingPositionForm(instance=teaching_position)

    return render(request, 'teaching_position_form.html', {'form': form})

# View to delete a teaching position (only accessible by superadmin and branchadmin)
@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def teaching_position_delete(request, pk):
    teaching_position = get_object_or_404(TeachingPosition, pk=pk)

    # Restrict branch_admin to only delete their own branch teaching positions
    if request.user.role == 'branch_admin' and teaching_position.branch != request.user.branch:
        return HttpResponseForbidden("You are not allowed to delete this teaching position.")

    if request.method == 'POST':
        teaching_position.delete()
        return redirect('teaching_position_list')

    return render(request, 'teaching_position_confirm_delete.html', {'teaching_position': teaching_position})



@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def non_teaching_position_list(request):
    if request.user.role == 'branch_admin':
        branch = request.user.branch
        non_teaching_positions = NonTeachingPosition.objects.filter(branch=branch)
    else:
        non_teaching_positions = NonTeachingPosition.objects.all()

    paginator = Paginator(non_teaching_positions, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'non_teaching_position_list.html', {
        'page_obj': page_obj,
        'start_index': page_obj.start_index(),
    })


# View to add a new non-teaching position (only accessible by superadmin and branchadmin)
@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def non_teaching_position_create(request):
    if request.user.role == 'branch_admin':
        branch = request.user.branch
    else:
        branch = None

    if request.method == 'POST':
        form = NonTeachingPositionForm(request.POST)
        if form.is_valid():
            non_teaching_position = form.save(commit=False)
            non_teaching_position.branch = branch  # Set branch if it's branch_admin
            non_teaching_position.save()
            return redirect('non_teaching_position_list')
    else:
        form = NonTeachingPositionForm()

    return render(request, 'non_teaching_position_form.html', {'form': form})

# View to edit a non-teaching position (only accessible by superadmin and branchadmin)
@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def non_teaching_position_edit(request, pk):
    non_teaching_position = get_object_or_404(NonTeachingPosition, pk=pk)

    # Restrict branch_admin to only edit their own branch non-teaching positions
    if request.user.role == 'branch_admin' and non_teaching_position.branch != request.user.branch:
        return HttpResponseForbidden("You are not allowed to edit this non-teaching position.")

    if request.method == 'POST':
        form = NonTeachingPositionForm(request.POST, instance=non_teaching_position)
        if form.is_valid():
            form.save()
            return redirect('non_teaching_position_list')
    else:
        form = NonTeachingPositionForm(instance=non_teaching_position)

    return render(request, 'non_teaching_position_form.html', {'form': form})

# View to delete a non-teaching position (only accessible by superadmin and branchadmin)
@login_required
@user_passes_test(is_superadmin_or_branchadmin)
def non_teaching_position_delete(request, pk):
    non_teaching_position = get_object_or_404(NonTeachingPosition, pk=pk)

    # Restrict branch_admin to only delete their own branch non-teaching positions
    if request.user.role == 'branch_admin' and non_teaching_position.branch != request.user.branch:
        return HttpResponseForbidden("You are not allowed to delete this non-teaching position.")

    if request.method == 'POST':
        non_teaching_position.delete()
        return redirect('non_teaching_position_list')

    return render(request, 'non_teaching_position_confirm_delete.html', {'non_teaching_position': non_teaching_position})


@login_required
def create_staff(request):
    if request.user.role not in ['superadmin', 'branchadmin']:
        messages.error(request, "You do not have permission to create staff.")
        return redirect('home')

    if request.method == 'POST':
        user_form = StaffCreationForm(request.POST, user=request.user)
        profile_form = StaffProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            selected_role = user_form.cleaned_data['role']

            # Superadmin can assign any branch, branchadmin only their own
            if request.user.role == 'branchadmin':
                user.branch = request.user.branch  # Force branch assignment

            user.role = selected_role
            user.save()

            # Ensure StaffProfile is created for all relevant roles
            if selected_role in ['superadmin', 'branchadmin', 'staff']:
                staff_profile = profile_form.save(commit=False)
                staff_profile.user = user
                staff_profile.branch = user.branch  # assign same branch as the user

                # Get validated data from cleaned_data
                staff_profile.phone_number = profile_form.cleaned_data['phone_number']
                staff_profile.date_of_birth = profile_form.cleaned_data['date_of_birth']
                staff_profile.qualification = profile_form.cleaned_data['qualification']
                staff_profile.years_of_experience = profile_form.cleaned_data['years_of_experience']
                staff_profile.address = profile_form.cleaned_data['address']

                staff_profile.save()

            messages.success(request, f"{selected_role.capitalize()} created successfully.")
            return redirect('staff_list')

        else:
            print("User form errors:", user_form.errors)
            print("Profile form errors:", profile_form.errors)
            messages.error(request, "Please correct the form errors.")

    else:
        user_form = StaffCreationForm(user=request.user)
        profile_form = StaffProfileForm()

    return render(request, 'staff_create.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })




@login_required
def staff_list(request):
    """
    View to list all staff users.
    - Superadmin sees all staff.
    - Branch admin sees staff in their own branch.
    """
    if request.user.role == 'superadmin':
        staff_users = CustomUser.objects.filter(role__in=['staff', 'branch_admin'])
    elif request.user.role == 'branch_admin':
        staff_users = CustomUser.objects.filter(
            role__in=['staff'],
            branch=request.user.branch
        )
    else:
        staff_users = CustomUser.objects.none()  # Regular staff have no access

    # Set up pagination: Show 10 staff per page
    paginator = Paginator(staff_users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff_list.html', {
        'page_obj': page_obj
    })



@login_required
def delete_staff(request, user_id):
    """
    View to delete a staff user and their associated profile.
    Only superadmins can delete staff.
    """
    user_to_delete = get_object_or_404(CustomUser, id=user_id)

    # Only superadmins can delete staff
    if request.user.role != 'superadmin':
        raise Http404("You do not have permission to delete this user.")

    if request.method == 'POST':
        user_to_delete.delete()
        return redirect('staff_list')  # Replace with the actual URL name for your staff list

    return render(request, 'confirm_delete_staff.html', {
        'user_to_delete': user_to_delete,
    })



@login_required
def update_staff_profile(request, staff_id):
    """
    View to update an existing staff user's account and profile.
    Only superadmins and branch_admins are allowed.
    """
    if request.user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You do not have permission to update staff.")
        return redirect('home')

    # Fetch the staff user and profile
    user = get_object_or_404(CustomUser, id=staff_id)
    staff_profile = get_object_or_404(StaffProfile, user=user)

    if request.method == 'POST':
        user_form = StaffCreationForm(request.POST, instance=user, user=request.user)
        profile_form = StaffProfileForm(request.POST, instance=staff_profile)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                # Save the user form (CustomUser)
                user = user_form.save(commit=False)
                if user_form.cleaned_data['password1']:
                    user.set_password(user_form.cleaned_data['password1'])
                user.save()

                # Save the profile form (StaffProfile)
                profile = profile_form.save(commit=False)
                profile.user = user  # Ensure the profile is linked to the user
                profile.save()

                messages.success(request, f"Staff {user.get_full_name()} updated successfully.")
                return redirect('staff_list')

            except IntegrityError:
                messages.error(request, "There was an error while updating the staff.")
                return redirect('staff_list')

        else:
            messages.error(request, "There were errors in the form. Please check the fields.")
            for form in [user_form, profile_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        user_form = StaffCreationForm(instance=user, user=request.user)
        profile_form = StaffProfileForm(instance=staff_profile)

    return render(request, 'staff_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'staff_id': staff_id,
    })




@login_required
def staff_detail(request, user_id):
    """
    View to display a staff member's profile.
    """
    # Retrieve the user (staff member)
    user = get_object_or_404(CustomUser, id=user_id)

    # Access control: Only superadmin, branch admin, or the user themselves can view
    if request.user != user and request.user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You do not have permission to view this staff profile.")
        return redirect('home')

    # Check that the user is a staff member
    if user.role not in ['staff', 'superadmin', 'branch_admin']:
        messages.error(request, "This user is not a staff member.")
        return redirect('home')

    # Retrieve the staff profile associated with the user
    try:
        staff_profile = user.staffprofile
    except StaffProfile.DoesNotExist:
        raise Http404("Staff profile does not exist.")

    return render(request, 'staff_profile_detail.html', {
        'user': user,
        'staff_profile': staff_profile,
    })

# class BranchListView(ListView):
#     model = Branch
#     template_name = 'branch_list.html'
#     context_object_name = 'branches'
#     paginate_by = 10



def branch_list(request):
    branch_list = Branch.objects.all()
    paginator = Paginator(branch_list, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'branch_list.html', {
        'branches': page_obj,  # This is now a Page object
    })

class BranchCreateView(CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'branch_form.html'
    success_url = reverse_lazy('branch_list')

class BranchUpdateView(UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'branch_form.html'
    success_url = reverse_lazy('branch_list')

class BranchDeleteView(DeleteView):
    model = Branch
    template_name = 'branch_confirm_delete.html'
    success_url = reverse_lazy('branch_list')

class BranchDetailView(DetailView):
    model = Branch
    template_name = 'branch_detail.html'
    context_object_name = 'branch'




