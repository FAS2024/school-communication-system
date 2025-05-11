from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from .forms import (
        UserRegistrationForm,
        TeachingPositionForm, 
        NonTeachingPositionForm, 
        StaffCreationForm, 
        StaffProfileForm,
        BranchForm,
        StudentCreationForm
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
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views import View


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


# # Check if user is superadmin or branch admin
# def is_superadmin_or_branchadmin(user):
#     return user.role in ['superadmin', 'branch_admin']

def is_superadmin_or_branchadmin(user):
    return user.is_authenticated and user.role in ['superadmin', 'branch_admin']


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


# @login_required
# def create_staff(request):
#     current_user = request.user

#     if current_user.role not in ['superadmin', 'branch_admin']:
#         messages.error(request, "You are not authorized to create users.")
#         return redirect('home')

#     if request.method == 'POST':
#         user_form = StaffCreationForm(request.POST, user=current_user)
#         profile_form = StaffProfileForm(request.POST)


#         if user_form.is_valid() and profile_form.is_valid():
#             new_user = user_form.save(commit=False)
#             selected_role = user_form.cleaned_data['role']

#             # Branch admin can only assign their own branch
#             if current_user.role == 'branch_admin':
#                 new_user.branch = current_user.branch

#             new_user.save()
#             user_form.save_m2m()

#             # Now update the existing StaffProfile
#             try:
#                 staff_profile = StaffProfile.objects.get(user=new_user)
#                 staff_profile.phone_number = profile_form.cleaned_data['phone_number']
#                 staff_profile.date_of_birth = profile_form.cleaned_data['date_of_birth']
#                 staff_profile.qualification = profile_form.cleaned_data['qualification']
#                 staff_profile.years_of_experience = profile_form.cleaned_data['years_of_experience']
#                 staff_profile.address = profile_form.cleaned_data['address']
#                 staff_profile.save()
#             except StaffProfile.DoesNotExist:
#                 messages.error(request, "Staff profile was not created properly.")
#                 return redirect('create_staff')

#             messages.success(request, f"{selected_role.replace('_', ' ').title()} created successfully.")
#             return redirect('staff_list')
#         else:
#             messages.error(request, "Please correct the errors in the form.")
#     else:
#         user_form = StaffCreationForm(user=current_user)
#         profile_form = StaffProfileForm()

#     return render(request, 'staff_create.html', {
#         'user_form': user_form,
#         'profile_form': profile_form
#     })


@login_required
def create_staff(request):
    current_user = request.user

    if current_user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You are not authorized to create users.")
        return redirect('home')

    if request.method == 'POST':
        user_form = StaffCreationForm(request.POST, request.FILES, user=current_user)
        profile_form = StaffProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            selected_role = user_form.cleaned_data['role']

            # Branch admin can only assign their own branch
            if current_user.role == 'branch_admin':
                new_user.branch = current_user.branch

            new_user.save()
            user_form.save_m2m()

            # Now update the existing StaffProfile
            try:
                staff_profile = StaffProfile.objects.get(user=new_user)
                staff_profile.phone_number = profile_form.cleaned_data['phone_number']
                staff_profile.date_of_birth = profile_form.cleaned_data['date_of_birth']
                staff_profile.qualification = profile_form.cleaned_data['qualification']
                staff_profile.years_of_experience = profile_form.cleaned_data['years_of_experience']
                staff_profile.address = profile_form.cleaned_data['address']
                staff_profile.save()
            except StaffProfile.DoesNotExist:
                messages.error(request, "Staff profile was not created properly.")
                return redirect('create_staff')

            messages.success(request, f"{selected_role.replace('_', ' ').title()} created successfully.")
            return redirect('staff_list')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        user_form = StaffCreationForm(user=current_user)
        profile_form = StaffProfileForm()

    return render(request, 'staff_create.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })



@login_required
def staff_list(request):
    """
    View to list all staff users.
    - Superadmin sees all staff.
    - Branch admin sees staff in their own branch.
    - Other users (including staff) are not authorized to view the list.
    """
    current_user = request.user

    # Check if the current user is a superadmin or branch admin
    if current_user.role == 'superadmin':
        # Superadmin sees all staff and branch admins
        staff_users = CustomUser.objects.filter(role__in=['staff', 'branch_admin', 'superadmin'])
    elif current_user.role == 'branch_admin':
        # Branch admin sees only staff in their branch
        staff_users = CustomUser.objects.filter(
            role__in=['staff', 'branch_admin'],  # Branch admins should be able to see staff and other branch admins in their branch
            branch=current_user.branch
        )
    else:
        # Redirect other users (including staff) with no access to the staff list
        messages.error(request, "You do not have permission to view the staff list.")
        return redirect('home')  # Or redirect to any other page (e.g., 'home')

    # Set up pagination: Show 10 staff per page
    paginator = Paginator(staff_users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff_list.html', {
        'page_obj': page_obj
    })
    
    
    
    


@login_required
def update_staff_profile(request, staff_id):
    current_user = request.user

    # Check if the user is editing their own profile
    if current_user.id == staff_id:
        user_to_edit = current_user
    else:
        # Only superadmin or branch_admin can edit other users
        if current_user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You are not authorized to edit other users.")
            return redirect('home')

        user_to_edit = get_object_or_404(CustomUser, id=staff_id)

        # Branch admin can only edit users within their own branch
        if current_user.role == 'branch_admin' and user_to_edit.branch != current_user.branch:
            messages.error(request, "You are not authorized to edit this user.")
            return redirect('staff_list')

    # Get or create StaffProfile
    profile, created = StaffProfile.objects.get_or_create(user=user_to_edit)

    if request.method == 'POST':
        user_form = StaffCreationForm(
            request.POST, request.FILES,
            instance=user_to_edit,
            user=current_user  # Pass the logged-in user for permission logic
        )
        profile_form = StaffProfileForm(
            request.POST,
            instance=profile,
            user=current_user  # Pass current user here as well
        )

        if user_form.is_valid() and profile_form.is_valid():
            edited_user = user_form.save(commit=False)

            # Ensure branch consistency if edited by branch_admin
            if current_user.role == 'branch_admin' and current_user != user_to_edit:
                edited_user.branch = current_user.branch

            edited_user.save()
            user_form.save_m2m()  # Save many-to-many fields like positions
            profile_form.save()

            messages.success(request, f"{edited_user.get_full_name()} updated successfully.")
            return redirect('staff_detail', user_id=edited_user.id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        user_form = StaffCreationForm(
            instance=user_to_edit,
            user=current_user  # still pass for GET
        )
        profile_form = StaffProfileForm(
            instance=profile,
            user=current_user
        )

    return render(request, 'staff_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_to_edit': user_to_edit,
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
    staff_profile = None
    try:
        staff_profile = user.staffprofile
    except StaffProfile.DoesNotExist:
        # If no staff profile exists, allow to show user details
        staff_profile = None  # Set it to None for fallback view

    return render(request, 'staff_profile_detail.html', {
        'user': user,
        'staff_profile': staff_profile,
        'profile_exists': staff_profile is not None,  # Add this flag for view handling
    })



def branch_list(request):
    branch_list = Branch.objects.all()
    paginator = Paginator(branch_list, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'branch_list.html', {
        'branches': page_obj,  # This is now a Page object
    })


class BranchDetailView(DetailView):
    model = Branch
    template_name = 'branch_detail.html'
    context_object_name = 'branch'

class BranchCreateView(CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'branch_form.html'
    success_url = reverse_lazy('branch_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Branch '{self.object.name}' was created successfully.")
        return response


class BranchUpdateView(UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'branch_form.html'
    success_url = reverse_lazy('branch_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Branch '{self.object.name}' was updated successfully.")
        return response



class BranchDeleteView(DeleteView):
    model = Branch
    template_name = 'branch_confirm_delete.html'
    success_url = reverse_lazy('branch_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        branch_name = self.object.name
        self.object.delete()
        messages.warning(request, f"Branch '{branch_name}' was deleted.")
        return HttpResponseRedirect(self.success_url)


def is_student(user):
    return user.is_authenticated and user.role == 'student'


# Create Student View
@method_decorator([login_required, user_passes_test(is_superadmin_or_branchadmin)], name='dispatch')
class StudentCreateView(View):
    def get(self, request):
        form = StudentCreationForm(request=request)
        return render(request, 'student_form.html', {'form': form})

    def post(self, request):
        form = StudentCreationForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, "Student created successfully.")
            return redirect('student_list')  # Change to your desired success URL
        messages.error(request, "Please correct the errors below.")
        return render(request, 'student_form.html', {'form': form})


# Update Student View
@method_decorator(login_required, name='dispatch')
class StudentUpdateView(View):
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, role='student')

        # Access control for branch_admin: ensure they only edit students from their branch
        if request.user.role == 'branch_admin' and user.branch != request.user.branch:
            messages.error(request, "You do not have permission to edit this student.")
            return redirect('student_list')

        # Access control for regular students: they can only edit their own profile
        if request.user.role == 'student' and request.user.pk != user.pk:
            messages.error(request, "You can only edit your own profile.")
            return redirect('dashboard')

        # Populate the form with existing data for editing
        form = StudentCreationForm(instance=user, request=request, initial={
            'admission_number': getattr(user.studentprofile, 'admission_number', ''),
            'current_class': getattr(user.studentprofile, 'current_class', ''),
            'date_of_birth': getattr(user.studentprofile, 'date_of_birth', ''),
            'gender': getattr(user.studentprofile, 'gender', ''),  # Gender already in CustomUser
            'guardian_name': getattr(user.studentprofile, 'guardian_name', ''),
            'address': getattr(user.studentprofile, 'address', ''),
            'phone_number': getattr(user.studentprofile, 'phone_number', ''),  # Ensure phone number is populated
        })
        return render(request, 'student_form.html', {'form': form, 'is_update': True})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, role='student')

        # Access control for branch_admin: ensure they only edit students from their branch
        if request.user.role == 'branch_admin' and user.branch != request.user.branch:
            messages.error(request, "You do not have permission to edit this student.")
            return redirect('student_list')

        # Access control for regular students: they can only edit their own profile
        if request.user.role == 'student' and request.user.pk != user.pk:
            messages.error(request, "You can only edit your own profile.")
            return redirect('dashboard')

        form = StudentCreationForm(request.POST, request.FILES, instance=user, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, "Student profile updated successfully.")
            return redirect('student_detail', pk=user.pk)  # Adjust this URL to match your detail view
        messages.error(request, "Please correct the errors below.")
        return render(request, 'student_form.html', {'form': form, 'is_update': True})
    


class StudentListView(ListView):
    model = CustomUser
    template_name = 'student_list.html'  # Customize the template as needed
    context_object_name = 'students'

    def get_queryset(self):
        # Ensure that only 'student' role users are shown in the list
        return CustomUser.objects.filter(role='student')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to view the student list.")
            return redirect('login')  # Redirect to login if not authenticated
        elif request.user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('dashboard')  # Redirect to the dashboard if not authorized

        return super().dispatch(request, *args, **kwargs)



class StudentDetailView(DetailView):
    model = CustomUser
    template_name = 'student_detail.html'  # Customize the template as needed
    context_object_name = 'student'

    def get_object(self, queryset=None):
        # Retrieve the student object by primary key (pk)
        student = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='student')

        # Access control logic:
        if self.request.user.role == 'branch_admin' and student.branch != self.request.user.branch:
            messages.error(self.request, "You do not have permission to view this student's details.")
            return None  # Or you can redirect to a different page
        elif self.request.user.role == 'student' and self.request.user.pk != student.pk:
            messages.error(self.request, "You can only view your own profile.")
            return None  # Or you can redirect to a different page

        return student

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to view student details.")
            return redirect('login')  # Redirect to login if not authenticated
        elif request.user.role not in ['superadmin', 'branch_admin', 'student']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('dashboard')  # Redirect to the dashboard if not authorized

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class StudentDeleteView(DeleteView):
    model = CustomUser
    template_name = 'student_confirm_delete.html'
    context_object_name = 'student'
    success_url = reverse_lazy('student_list')

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Only superadmin and branch_admin can delete students
        if user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "Access denied. Only superadmins and branch admins can delete students.")
            return redirect('student_list')

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        student = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='student')

        # Branch admin can only delete students in their branch
        if self.request.user.role == 'branch_admin' and student.branch != self.request.user.branch:
            messages.error(self.request, "You are not authorized to delete this student.")
            return None

        return student

    def delete(self, request, *args, **kwargs):
        student = self.get_object()

        if not student:
            return redirect('student_list')

        messages.success(request, f"Student '{student.get_full_name()}' was successfully deleted.")
        return super().delete(request, *args, **kwargs)
