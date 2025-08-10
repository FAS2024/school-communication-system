# Standard Library
import json
import os
import logging
from datetime import datetime

# Django Core
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Coalesce
from django.http import (
    JsonResponse, HttpResponseRedirect, 
    HttpResponseForbidden, HttpResponseServerError, FileResponse, Http404
)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    ListView, CreateView, UpdateView, 
    DeleteView, DetailView
)

# Project-Specific Imports
from .utils import send_communication_to_recipients
from .forms import (
    TeachingPositionForm, NonTeachingPositionForm, StaffCreationForm, StaffProfileForm,
    BranchForm, StudentCreationForm, StudentClassForm, ClassArmForm,
    ParentCreationForm, StudentProfileForm, CommunicationForm,
    CommunicationTargetGroupForm, AttachmentFormSet,
    ReplyAttachmentFormSet  
    
)
from .models import (
    CustomUser, StudentProfile, StaffProfile,
    TeachingPosition, NonTeachingPosition, Branch, StudentClass, ClassArm,
    Communication, CommunicationAttachment,
    CommunicationRecipient, SentMessageDelete,MessageReply, ReplyAttachment
)
from django.http import QueryDict
from django.views.decorators.http import require_http_methods

from django.views.decorators.csrf import csrf_protect

logger = logging.getLogger(__name__)



MAX_FILE_COUNT = 5
MAX_TOTAL_SIZE_MB = 20

# Logger
logger = logging.getLogger(__name__)

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



@login_required
def create_staff(request):
    current_user = request.user

    if current_user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You are not authorized to create users.")
        return redirect('home')

    if request.method == 'POST':
        user_form = StaffCreationForm(request.POST, request.FILES, user=current_user)
        profile_form = StaffProfileForm(request.POST, user=current_user)

        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            selected_role = user_form.cleaned_data['role']

            # Branch admin can only assign their own branch
            if current_user.role == 'branch_admin':
                new_user.branch = current_user.branch

            new_user.save()
            user_form.save_m2m()

            try:
                staff_profile = StaffProfile.objects.get(user=new_user)
                
                # Update fields (form.clean() already handles primary_position logic)
                staff_profile.phone_number = profile_form.cleaned_data['phone_number']
                staff_profile.date_of_birth = profile_form.cleaned_data['date_of_birth']
                staff_profile.qualification = profile_form.cleaned_data['qualification']
                staff_profile.years_of_experience = profile_form.cleaned_data['years_of_experience']
                staff_profile.address = profile_form.cleaned_data['address']
                staff_profile.nationality = profile_form.cleaned_data['nationality']
                staff_profile.state = profile_form.cleaned_data['state']
                staff_profile.managing_class = profile_form.cleaned_data['managing_class']
                staff_profile.managing_class_arm = profile_form.cleaned_data['managing_class_arm']

                # Save after all fields (including GenericForeignKey) were populated by form.clean()
                staff_profile.save()

            except StaffProfile.DoesNotExist:
                messages.error(request, "Staff profile was not created properly.")
                return redirect('create_staff')

            messages.success(
                request,
                f"{new_user.get_full_name()} ({selected_role.replace('_', ' ').title()}) created successfully."
            )
            return redirect('staff_list')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        user_form = StaffCreationForm(user=current_user)
        profile_form = StaffProfileForm(user=current_user)

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

    if current_user.id == staff_id:
        user_to_edit = current_user
    else:
        if current_user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You are not authorized to edit other users.")
            return redirect('home')

        user_to_edit = get_object_or_404(CustomUser, id=staff_id)

        if current_user.role == 'branch_admin' and user_to_edit.branch != current_user.branch:
            messages.error(request, "You are not authorized to edit this user.")
            return redirect('staff_list')

    profile, created = StaffProfile.objects.get_or_create(user=user_to_edit)

    if request.method == 'POST':
        user_form = StaffCreationForm(
            request.POST, request.FILES,
            instance=user_to_edit,
            user=current_user
        )
        profile_form = StaffProfileForm(
            request.POST,
            instance=profile,
            user=current_user
        )

        if user_form.is_valid() and profile_form.is_valid():
            edited_user = user_form.save(commit=False)

            if current_user.role == 'branch_admin' and current_user != user_to_edit:
                edited_user.branch = current_user.branch

            edited_user.save()
            user_form.save_m2m()

            # Cleaned_data has already set position_content_type and position_object_id
            # We now safely save the profile
            profile_form.save()

            messages.success(request, f"Staff {edited_user.get_full_name()} updated successfully.")
            return redirect('staff_detail', user_id=edited_user.id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        user_form = StaffCreationForm(instance=user_to_edit, user=current_user)
        profile_form = StaffProfileForm(instance=profile, user=current_user)

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
    branches = Branch.objects.all()
    return render(request, 'branch_list.html', {'branches': branches})


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



def is_branch_or_superadmin(user):
    return user.is_authenticated and (user.role == 'superadmin' or user.role == 'branch_admin')



@login_required
def create_student(request):
    if request.user.role not in ['superadmin', 'branch_admin']:
        raise PermissionDenied("You do not have permission to create students.")

    if request.method == 'POST':
        user_form = StudentCreationForm(request.POST, request.FILES, user=request.user)
        profile_form = StudentProfileForm(request.POST, user=request.user)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    parent = profile_form.cleaned_data['parent']
                    user.branch = parent.user.branch  # link branch from parent
                    user.save()

                    profile = profile_form.save(commit=False)
                    profile.user = user
                    profile.save()

                messages.success(request, f"{user.first_name} {user.last_name} successfully created.")
                return redirect('student_list')

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        user_form = StudentCreationForm(user=request.user)
        profile_form = StudentProfileForm(user=request.user)

    return render(request, 'student_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def update_student(request, pk):
    user_instance = get_object_or_404(CustomUser, pk=pk, role='student')
    profile_instance = get_object_or_404(StudentProfile, user=user_instance)

    # Permissions:
    if request.user.role in ['superadmin', 'branch_admin']:
        # Optional: restrict branch_admin to only their branch
        if request.user.role == 'branch_admin' and user_instance.branch != request.user.branch:
            raise PermissionDenied("You cannot edit students outside your branch.")
    elif request.user.role == 'student':
        # Students can only update their own profile
        if request.user != user_instance:
            raise PermissionDenied("You cannot edit other students.")
    else:
        raise PermissionDenied("You do not have permission to update students.")

    if request.method == 'POST':
        user_form = StudentCreationForm(
            request.POST, request.FILES,
            instance=user_instance,
            user=request.user
        )
        profile_form = StudentProfileForm(
            request.POST,
            instance=profile_instance,
            user=request.user
        )

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    parent = profile_form.cleaned_data['parent']
                    user.branch = parent.user.branch  # Always update branch from parent
                    user.save()

                    profile = profile_form.save(commit=False)
                    profile.user = user
                    profile.save()

                messages.success(request, f"{user.first_name} {user.last_name} successfully updated.")
                return redirect('student_detail', pk=user.pk)

            except Exception as e:
                messages.error(request, f"An error occurred while saving: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = StudentCreationForm(instance=user_instance, user=request.user)
        profile_form = StudentProfileForm(instance=profile_instance, user=request.user)

    return render(request, 'student_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@method_decorator(login_required, name='dispatch')
class StudentListView(ListView):
    model = CustomUser
    template_name = 'student_list.html'  # Adjust if your template is in a subfolder
    context_object_name = 'students'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user

        base_qs = CustomUser.objects.filter(
            role='student',
            studentprofile__isnull=False  # Ensure StudentProfile exists
        ).select_related(
            'studentprofile',
            'branch',
            'studentprofile__current_class',
            'studentprofile__current_class_arm'
        ).order_by('last_name', 'first_name')

        if user.role == 'superadmin':
            return base_qs
        elif user.role == 'branch_admin':
            return base_qs.filter(branch=user.branch)
        else:
            # No permission to see students
            return CustomUser.objects.none()

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


@login_required
def student_detail(request, pk):
    user = request.user

    student = get_object_or_404(
        CustomUser.objects.select_related(
            'studentprofile',
            'branch',
            'studentprofile__current_class',
            'studentprofile__current_class_arm'
        ),
        pk=pk,
        role='student'
    )

    if not hasattr(student, 'studentprofile'):
        messages.error(request, "Student profile data is missing.")
        return redirect('student_list')

    # Access control
    if user.role == 'superadmin':
        pass  # can view any student
    elif user.role == 'branch_admin':
        if student.branch != user.branch:
            return HttpResponseForbidden("You do not have permission to view this student.")
    elif user.role == 'student':
        if user != student:
            return HttpResponseForbidden("You can only view your own profile.")
    else:
        return HttpResponseForbidden("You do not have permission to view this student.")

    return render(request, 'student_detail.html', {'student': student})



@login_required
@user_passes_test(is_branch_or_superadmin)
def student_delete(request, pk):
    user = request.user
    student = get_object_or_404(CustomUser, pk=pk, role='student')

    # branch_admin can only delete students in their branch
    if user.role == 'branch_admin' and student.branch != user.branch:
        messages.error(request, "You don't have permission to delete this student.")
        return redirect('student_list')

    if request.method == 'POST':
        student.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect('student_list')

    return render(request, 'student_confirm_delete.html', {'student': student})



@login_required
def student_class_create(request):
    if request.user.role not in ['superadmin', 'branch_admin']:
        return HttpResponseForbidden("You do not have permission to view this page.")

    if request.user.role == 'branch_admin':
        # Restrict branch admins to only create classes for their branch
        branch = request.user.branch
    else:
        branch = None  # Superadmins can create classes for any branch

    if request.method == 'POST':
        form = StudentClassForm(request.POST)
        if form.is_valid():
            student_class = form.save(commit=False)
            if branch:
                student_class.branch = branch  # Assign the branch if it's a branch_admin
            student_class.save()
            form.save_m2m()  # Save the ManyToManyField (arms)

            messages.success(request, "Student Class created successfully!")
            return redirect('student_class_list')

    else:
        form = StudentClassForm()

    return render(request, 'student-class/student_class_form.html', {'form': form})



@login_required
def student_class_list(request):
    if request.user.role not in ['superadmin', 'branch_admin']:
        return HttpResponseForbidden("You do not have permission to view this page.")

    if request.user.role == 'branch_admin':
        # Filter the classes by branch for branch admins
        student_classes = StudentClass.objects.filter(branch=request.user.branch)
    else:
        student_classes = StudentClass.objects.all()

    return render(request, 'student-class/student_class_list.html', {'student_classes': student_classes})



def student_class_update(request, pk):
    student_class = get_object_or_404(StudentClass, pk=pk)
    
    if request.method == 'POST':
        form = StudentClassForm(request.POST, instance=student_class)
        if form.is_valid():
            # Save the StudentClass instance (but don't save the ManyToMany field yet)
            student_class = form.save(commit=False)
            student_class.save()

            # Save the many-to-many field separately
            form.save_m2m()

            # Adding a success message after successful update
            messages.success(request, f"Student Class '{student_class.name}' was updated successfully!")

            # Redirect to the class list after saving
            return redirect('student_class_list')

        # Adding an error message if the form is not valid
        else:
            messages.error(request, "There was an error updating the Student Class. Please try again.")

    else:
        form = StudentClassForm(instance=student_class)

    return render(request, 'student-class/student_class_form.html', {'form': form})



@login_required
def student_class_delete(request, pk):
    student_class = get_object_or_404(StudentClass, pk=pk)

    # Restrict delete based on roles
    if request.user.role not in ['superadmin', 'branch_admin']:
        return HttpResponseForbidden("You do not have permission to view this page.")

    if request.user.role == 'branch_admin' and student_class.branch != request.user.branch:
        messages.error(request, "You cannot delete classes from another branch.")
        return redirect('student_class_list')

    if request.method == 'POST':
        student_class.delete()
        messages.success(request, "Student Class deleted successfully!")
        return redirect('student_class_list')

    return render(request, 'student-class/student_class_confirm_delete.html', {'student_class': student_class})


# @method_decorator([login_required, user_passes_test(is_superadmin_or_branchadmin)], name='dispatch')
# class ParentCreateView(View):
#     def get(self, request):
#         form = ParentCreationForm(request=request)
#         return render(request, 'parents/parent_form.html', {'form': form})

#     def post(self, request):
#         form = ParentCreationForm(request.POST, request.FILES, request=request)
#         if form.is_valid():
#             parent = form.save()
#             full_name = f"{parent.first_name} {parent.last_name}"
#             messages.success(request, f"Parent '{full_name}' profile updated successfully.")
#             return redirect('parent_list')
#         messages.error(request, "Please correct the errors below.")
#         return render(request, 'parents/parent_form.html', {'form': form})


# @method_decorator(login_required, name='dispatch')
# class ParentUpdateView(View):
#     def get(self, request, pk):
#         user = get_object_or_404(CustomUser, pk=pk, role='parent')

#         # Access control for branch_admin: ensure they only edit parents from their branch
#         if request.user.role == 'branch_admin' and user.branch != request.user.branch:
#             messages.error(request, "You do not have permission to edit this parent.")
#             return redirect('parent_list')

#         # Access control for regular parents: they can only edit their own profile
#         if request.user.role == 'parent' and request.user.pk != user.pk:
#             messages.error(request, "You can only edit your own profile.")
#             return redirect('parent_dashboard')

#         # Populate the form with existing data for editing
#         form = ParentCreationForm(instance=user, request=request, initial={
#             'date_of_birth': getattr(user.parentprofile, 'date_of_birth', ''),
#             'gender': getattr(user.parentprofile, 'gender', ''), 
#             'address': getattr(user.parentprofile, 'address', ''),
#             'phone_number': getattr(user.parentprofile, 'phone_number', ''),
#             'occupation': getattr(user.parentprofile, 'occupation', ''),
#             'relationship_to_student ': getattr(user.parentprofile, 'relationship_to_student ', ''),
#             'preferred_contact_method': getattr(user.parentprofile, 'preferred_contact_method', ''),
#             'nationality ': getattr(user.parentprofile, 'nationality ', ''),
#             'state': getattr(user.parentprofile, 'state', '')
#         })
#         return render(request, 'parents/parent_form.html', {'form': form, 'is_update': True})

#     def post(self, request, pk):
#         user = get_object_or_404(CustomUser, pk=pk, role='parent')

#         # Access control for branch_admin: ensure they only edit parent from their branch
#         if request.user.role == 'branch_admin' and user.branch != request.user.branch:
#             messages.error(request, "You do not have permission to edit this parent.")
#             return redirect('parent_list')

#         # Access control for regular parents: they can only edit their own profile
#         if request.user.role == 'parents' and request.user.pk != user.pk:
#             messages.error(request, "You can only edit your own profile.")
#             return redirect('parent_dashboard')

#         form = ParentCreationForm(request.POST, request.FILES, instance=user, request=request)
#         if form.is_valid():
#             parent = form.save()
#             full_name = f"{parent.first_name} {parent.last_name}"
#             messages.success(request, f"Parent '{full_name}' profile updated successfully.")
#             return redirect('parent_detail', pk=user.pk)
#         messages.error(request, "Please correct the errors below.")
#         return render(request, 'parents/parent_form.html', {'form': form, 'is_update': True})


# @method_decorator(login_required, name='dispatch') 
# class ParentListView(ListView):
#     model = CustomUser
#     template_name = 'parents/parent_list.html'  
#     context_object_name = 'parents'
#     paginate_by = 10 

#     def get_queryset(self):
#         # Ensure that only 'parent' role users are shown in the list
#         return CustomUser.objects.filter(role='parent')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         return context

#     def dispatch(self, request, *args, **kwargs):
#         # Ensure the user has the correct role (either 'superadmin' or 'branch_admin')
#         if request.user.role not in ['superadmin', 'branch_admin']:
#             messages.error(request, "You do not have permission to view this page.")
#             return redirect('parent_dashboard')

#         return super().dispatch(request, *args, **kwargs)


# class ParentDetailView(DetailView):
#     model = CustomUser
#     template_name = 'parents/parent_detail.html' 
#     context_object_name = 'parent'

#     def get_object(self, queryset=None):
#         # Retrieve the parent object by primary key (pk)
#         parent = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='parent')

#         # Access control logic:
#         if self.request.user.role == 'branch_admin' and parent.branch != self.request.user.branch:
#             messages.error(self.request, "You do not have permission to view this parent's details.")
#             return None  # Or you can redirect to a different page
#         elif self.request.user.role == 'parent' and self.request.user.pk != parent.pk:
#             messages.error(self.request, "You can only view your own profile.")
#             return None  # Or you can redirect to a different page

#         return parent

#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             messages.error(request, "You need to be logged in to view parent details.")
#             return redirect('login')  # Redirect to login if not authenticated
#         elif request.user.role not in ['superadmin', 'branch_admin', 'parent']:
#             messages.error(request, "You do not have permission to view this page.")
#             # return redirect('dashboard')  # Redirect to the dashboard if not authorized
#             return None

#         return super().dispatch(request, *args, **kwargs)


# @method_decorator(login_required, name='dispatch')
# class ParentDeleteView(DeleteView):
#     model = CustomUser
#     template_name = 'parents/parent_confirm_delete.html'
#     context_object_name = 'parent'
#     success_url = reverse_lazy('parent_list')

#     def dispatch(self, request, *args, **kwargs):
#         user = request.user

#         # Only superadmin and branch_admin can delete students
#         if user.role not in ['superadmin', 'branch_admin']:
#             messages.error(request, "Access denied. Only superadmins and branch admins can delete students.")
#             return redirect('student_list')

#         return super().dispatch(request, *args, **kwargs)

#     def get_object(self, queryset=None):
#         parent = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='parent')

#         # Branch admin can only delete parents in their branch
#         if self.request.user.role == 'branch_admin' and parent.branch != self.request.user.branch:
#             messages.error(self.request, "You are not authorized to delete this parent.")
#             return None

#         return parent

#     def delete(self, request, *args, **kwargs):
#         parent = self.get_object()

#         if not parent:
#             return redirect('parent_list')

#         messages.success(request, f"Parent '{parent.get_full_name()}' was successfully deleted.")
#         return super().delete(request, *args, **kwargs)


# Helper to check roles
def is_superadmin_or_branchadmin(user):
    return user.role in ['superadmin', 'branch_admin']

@method_decorator([login_required, user_passes_test(is_superadmin_or_branchadmin)], name='dispatch')
class ParentCreateView(View):
    def get(self, request):
        form = ParentCreationForm(request=request)
        return render(request, 'parents/parent_form.html', {'form': form})

    def post(self, request):
        form = ParentCreationForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            parent = form.save()
            full_name = f"{parent.first_name} {parent.last_name}"
            messages.success(request, f"Parent '{full_name}' profile created successfully.")
            return redirect('parent_list')
        messages.error(request, "Please correct the errors below.")
        return render(request, 'parents/parent_form.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ParentUpdateView(View):
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, role='parent')

        # Branch admin access control
        if request.user.role == 'branch_admin' and user.branch != request.user.branch:
            messages.error(request, "You do not have permission to edit this parent.")
            return redirect('parent_list')

        # Parent can only edit own profile
        if request.user.role == 'parent' and request.user.pk != user.pk:
            messages.error(request, "You can only edit your own profile.")
            return redirect('parent_dashboard')

        form = ParentCreationForm(instance=user, request=request, initial={
            'date_of_birth': getattr(user.parentprofile, 'date_of_birth', ''),
            'gender': getattr(user.parentprofile, 'gender', ''),
            'address': getattr(user.parentprofile, 'address', ''),
            'phone_number': getattr(user.parentprofile, 'phone_number', ''),
            'occupation': getattr(user.parentprofile, 'occupation', ''),
            'relationship_to_student': getattr(user.parentprofile, 'relationship_to_student', ''),
            'preferred_contact_method': getattr(user.parentprofile, 'preferred_contact_method', ''),
            'nationality': getattr(user.parentprofile, 'nationality', ''),
            'state': getattr(user.parentprofile, 'state', '')
        })
        return render(request, 'parents/parent_form.html', {'form': form, 'is_update': True})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, role='parent')

        if request.user.role == 'branch_admin' and user.branch != request.user.branch:
            messages.error(request, "You do not have permission to edit this parent.")
            return redirect('parent_list')

        if request.user.role == 'parent' and request.user.pk != user.pk:
            messages.error(request, "You can only edit your own profile.")
            return redirect('parent_dashboard')

        form = ParentCreationForm(request.POST, request.FILES, instance=user, request=request)
        if form.is_valid():
            parent = form.save()
            full_name = f"{parent.first_name} {parent.last_name}"
            messages.success(request, f"Parent '{full_name}' profile updated successfully.")
            return redirect('parent_detail', pk=user.pk)
        messages.error(request, "Please correct the errors below.")
        return render(request, 'parents/parent_form.html', {'form': form, 'is_update': True})


@method_decorator(login_required, name='dispatch')
class ParentListView(ListView):
    model = CustomUser
    template_name = 'parents/parent_list.html'
    context_object_name = 'parents'
    paginate_by = 10

    def get_queryset(self):
        return CustomUser.objects.filter(role='parent')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('parent_dashboard')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ParentDetailView(DetailView):
    model = CustomUser
    template_name = 'parents/parent_detail.html'
    context_object_name = 'parent'

    def get_object(self, queryset=None):
        parent = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='parent')

        if self.request.user.role == 'branch_admin' and parent.branch != self.request.user.branch:
            raise PermissionDenied("You do not have permission to view this parent's details.")
        if self.request.user.role == 'parent' and self.request.user.pk != parent.pk:
            raise PermissionDenied("You can only view your own profile.")

        return parent

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to view parent details.")
            return redirect('login')
        if request.user.role not in ['superadmin', 'branch_admin', 'parent']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ParentDeleteView(DeleteView):
    model = CustomUser
    template_name = 'parents/parent_confirm_delete.html'
    context_object_name = 'parent'
    success_url = reverse_lazy('parent_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "Access denied. Only superadmins and branch admins can delete parents.")
            return redirect('parent_list')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        parent = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='parent')
        if self.request.user.role == 'branch_admin' and parent.branch != self.request.user.branch:
            messages.error(self.request, "You are not authorized to delete this parent.")
            raise PermissionDenied
        return parent

    def delete(self, request, *args, **kwargs):
        parent = self.get_object()
        messages.success(request, f"Parent '{parent.get_full_name()}' was successfully deleted.")
        return super().delete(request, *args, **kwargs)


@login_required
def create_class_arm(request):
    if request.user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You do not have permission to create a class arm.")
        # return redirect('dashboard')  # Redirect to the dashboard or any other view
        return None
    
    if request.method == 'POST':
        form = ClassArmForm(request.POST)
        if form.is_valid():
            class_arm = form.save()
            messages.success(request, f"Class arm '{class_arm.name}' created successfully!")
            return redirect('class_arm_list')  # Redirect to a list view of class arms
    else:
        form = ClassArmForm()

    return render(request, 'class-arms/create_class_arm.html', {'form': form})


# views.py
@login_required
def class_arm_list(request):
    if request.user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You do not have permission to view class arms.")
        # return redirect('dashboard')  
        return None
    
    arms = ClassArm.objects.all()
    return render(request, 'class-arms/class_arm_list.html', {'arms': arms})


# views.py
@login_required
def update_class_arm(request, pk):
    try:
        class_arm = ClassArm.objects.get(pk=pk)
    except ClassArm.DoesNotExist:
        messages.error(request, "Class arm not found.")
        return redirect('class_arm_list')

    if request.user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You do not have permission to update this class arm.")
        # return redirect('dashboard')
        return None
    
    if request.method == 'POST':
        form = ClassArmForm(request.POST, instance=class_arm)
        if form.is_valid():
            class_arm = form.save()
            messages.success(request, f"Class arm '{class_arm.name}' updated successfully!")
            return redirect('class_arm_list')  # Redirect to the class arms list page
    else:
        form = ClassArmForm(instance=class_arm)

    return render(request, 'class-arms/update_class_arm.html', {'form': form})



@login_required
def delete_class_arm(request, pk):
    class_arm = get_object_or_404(ClassArm, pk=pk)

    if request.user.role not in ['superadmin', 'branch_admin']:
        messages.error(request, "You do not have permission to delete this class arm.")
        return None
        # return redirect('dashboard')

    if class_arm.student_classes.exists():
        messages.error(request, f"The class arm '{class_arm.name}' is in use and cannot be deleted.")
        return redirect('class_arm_list')

    if request.method == 'POST':
        class_arm.delete()
        messages.success(request, f"Class arm '{class_arm.name}' deleted successfully.")
        return redirect('class_arm_list')

    return render(request, 'class-arms/confirm_delete_class_arm.html', {'class_arm': class_arm})


@login_required
@require_GET
def ajax_get_filtered_users(request):
    # Define filter fields from the form
    filter_fields = CommunicationTargetGroupForm.Meta.fields

    # Extract raw GET parameters
    raw_filter_values = {
        field: request.GET.get(field, None)
        for field in filter_fields
    }

    # Convert empty strings to None
    cleaned_data = {
        field: (value if value not in [None, ''] else None)
        for field, value in raw_filter_values.items()
    }

    # Instantiate form with cleaned data and user
    form = CommunicationTargetGroupForm(user=request.user, data=cleaned_data)

    if not form.is_valid():
        if settings.DEBUG:
            return JsonResponse({'errors': form.errors}, status=400)
        return JsonResponse({'error': 'Invalid filter data'}, status=400)

    try:
        # Get filtered recipients
        users_qs = form.get_filtered_recipients(form.cleaned_data)
        users_qs = users_qs.select_related('branch')  # optimize query

        # Build user list
        users_list = []
        for user in users_qs:
            profile_picture_url = getattr(getattr(user, 'profile_picture', None), 'url', None)

            users_list.append({
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'branch__name': getattr(user.branch, 'name', 'N/A') if hasattr(user, 'branch') else 'N/A',
                'profile_picture': {'url': profile_picture_url}
            })

        return JsonResponse(users_list, safe=False)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)


# @login_required
# def get_filtered_users(request):
#     form = CommunicationTargetGroupForm(request.GET, user=request.user)

#     if form.is_valid():
#         recipients = form.get_filtered_recipients(form.cleaned_data)
#         users = recipients.values(
#             'id', 'first_name', 'last_name', 'email',
#             'branch__name', 'profile_picture'
#         )
#         return JsonResponse(list(users), safe=False)
    
#     if settings.DEBUG:
#         return JsonResponse({
#             'errors': form.errors,
#             'non_field_errors': form.non_field_errors(),
#         }, status=400)

#     return JsonResponse({'error': 'Invalid filter data'}, status=400)
@login_required
def get_filtered_users(request):
    form = CommunicationTargetGroupForm(request.GET, user=request.user)

    if form.is_valid():
        recipients = form.get_filtered_recipients(form.cleaned_data)
        recipients = recipients.select_related('branch')  # optimize DB hits

        users_list = []
        for user in recipients:
            profile_picture_url = (
                user.profile_picture.url if user.profile_picture else "/static/assets/img/profile-pic.png"
            )
            users_list.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "branch__name": user.branch.name if user.branch else "N/A",
                "profile_picture": {"url": profile_picture_url}
            })

        return JsonResponse(users_list, safe=False)

    if settings.DEBUG:
        return JsonResponse({
            "errors": form.errors,
            "non_field_errors": form.non_field_errors(),
        }, status=400)

    return JsonResponse({"error": "Invalid filter data"}, status=400)


@login_required
def get_user_by_id(request):
    user_id = request.GET.get("id")
    try:
        user = CustomUser.objects.get(pk=user_id)
        return JsonResponse({
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "branch__name": user.branch.name if user.branch else "",
            "profile_picture": {
                "url": getattr(user.profile_picture, "url", "")
            }

        })
    except CustomUser.DoesNotExist:
        return JsonResponse({}, status=404)


@login_required
def communication_index(request):
    communication_data = request.session.pop('communication_form_data', None)
    target_group_data = request.session.pop('target_group_form_data', None)
    attachment_data = request.session.pop('attachment_formset_data', None)
    non_field_errors = request.session.pop('non_field_errors', None)
    form_error = request.session.pop('form_error', False)

    communication_form = CommunicationForm(data=communication_data, user=request.user) if communication_data else CommunicationForm(user=request.user)

    # 🛠 Clean teaching_positions & non_teaching_positions if data exists
    if target_group_data:
        if not isinstance(target_group_data, QueryDict):
            target_group_data = QueryDict('', mutable=True).copy()
        else:
            target_group_data = target_group_data.copy()

        for name in ["teaching_positions", "non_teaching_positions"]:
            if name in target_group_data:
                raw_values = target_group_data.getlist(name)
                clean_ids = []
                for val in raw_values:
                    try:
                        clean_ids.append(str(int(val)))
                    except (ValueError, TypeError):
                        continue
                target_group_data.setlist(name, clean_ids)

    target_group_form = CommunicationTargetGroupForm(
        data=target_group_data or communication_data or None,
        user=request.user
    )

    if attachment_data:
        qd = QueryDict('', mutable=True)
        for k, v in attachment_data.items():
            qd.setlist(k, v if isinstance(v, list) else [v])
        attachment_formset = AttachmentFormSet(data=qd)
    else:
        attachment_formset = AttachmentFormSet()

    if non_field_errors:
        for msg in non_field_errors:
            communication_form.add_error(None, msg)

    return render(request, 'communications/communication_form.html', {
        'communication_form': communication_form,
        'target_group_form': target_group_form,
        'attachment_formset': attachment_formset,
        'form_error': form_error,
        'user_role': request.user.role,
        'user_branch_id': request.user.branch.id if request.user.branch else '',
    })
    
def validate_attachment_formset(formset):
    total_size = 0
    count = 0

    for form in formset:
        file = form.cleaned_data.get('file')
        if file:
            count += 1
            size_mb = file.size / (1024 * 1024)

            if size_mb > settings.MAX_SINGLE_ATTACHMENT_MB:
                raise ValidationError(
                    f"Each file must not exceed {settings.MAX_SINGLE_ATTACHMENT_MB}MB. "
                    f"File '{file.name}' is {size_mb:.2f}MB."
                )

            total_size += size_mb

    if count > settings.MAX_ATTACHMENT_COUNT:
        raise ValidationError(
            f"You can upload up to {settings.MAX_ATTACHMENT_COUNT} attachments only."
        )

    if total_size > settings.MAX_TOTAL_ATTACHMENT_MB:
        raise ValidationError(
            f"Total attachment size exceeds {settings.MAX_TOTAL_ATTACHMENT_MB}MB. "
            f"Currently: {total_size:.2f}MB"
        )


@method_decorator([login_required, require_POST], name='dispatch')
class SendCommunicationView(View):

    def flatten_querydict(self, qd: QueryDict):
        return {k: v[0] if len(v) == 1 else v for k, v in qd.lists()}

    def _get_allowed_recipients(self, target_group_form, user):
        recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data)
        return recipients.exclude(id=user.id)

    def _get_selected_recipients(self, request, allowed_recipients):
        selected_ids = request.POST.getlist('selected_recipients')
        return allowed_recipients.filter(id__in=selected_ids)

    def _parse_manual_emails(self, email_string):
        emails = [email.strip() for email in email_string.split(',') if email.strip()]
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email.lower())
            except ValidationError:
                messages.warning(self.request, f"Invalid manual email skipped: {email}")
        return valid_emails

    def _check_for_duplicate_emails(self, selected_recipients, manual_emails, form):
        if selected_recipients.exists():
            selected_emails = set(email.lower() for email in selected_recipients.values_list('email', flat=True))
            duplicates = selected_emails.intersection(set(manual_emails))
            if duplicates:
                form.add_error(None, f"Duplicate manual email(s): {', '.join(duplicates)}")
                return False
        return True

    def _render_with_errors(self, communication_form, target_group_form, attachment_formset):
        def flatten_querydict(qd):
            return {k: qd.getlist(k) if len(qd.getlist(k)) > 1 else qd.get(k) for k in qd}

        post_data = flatten_querydict(self.request.POST)

        self.request.session['communication_form_data'] = {
            k: v for k, v in post_data.items() if k in communication_form.fields
        }
        self.request.session['target_group_form_data'] = {
            k: v for k, v in post_data.items() if k in target_group_form.fields
        }
        self.request.session['attachment_formset_data'] = post_data
        self.request.session['non_field_errors'] = list(communication_form.non_field_errors())
        self.request.session['form_error'] = True

        messages.error(self.request, "There was an error with your submission. Please correct the highlighted fields.")
        return redirect('communication_index')

    def post(self, request):
        self.request = request

        communication_form = CommunicationForm(request.POST, user=request.user)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES)

        # Sanitize and ensure only valid numeric IDs are passed
        def clean_id_list(raw_list):
            clean = []
            for item in raw_list:
                try:
                    clean.append(str(int(item.strip())))
                except (ValueError, TypeError):
                    continue
            return clean

        saved_filter_data = {
            'branch': request.user.branch.id if request.user.role in ['student', 'parent'] else request.POST.get('saved_branch', ''),
            'role': request.POST.get('saved_role', ''),
            'staff_type': request.POST.get('saved_staff_type', ''),
            'student_class': request.POST.get('saved_student_class', ''),
            'class_arm': request.POST.get('saved_class_arm', ''),
            'teaching_positions': clean_id_list(request.POST.get('saved_teaching_positions', '').split(',')),
            'non_teaching_positions': clean_id_list(request.POST.get('saved_non_teaching_positions', '').split(',')),
        }

        from django.http import QueryDict
        form_data = QueryDict('', mutable=True)
        for key in ['branch', 'role', 'staff_type', 'student_class', 'class_arm']:
            form_data[key] = saved_filter_data[key]
        form_data.setlist('teaching_positions', saved_filter_data['teaching_positions'])
        form_data.setlist('non_teaching_positions', saved_filter_data['non_teaching_positions'])

        target_group_form = CommunicationTargetGroupForm(data=form_data, user=request.user)
        if not target_group_form.is_valid():
            communication_form.add_error(None, "Invalid target group filters.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not communication_form.is_valid() or not attachment_formset.is_valid():
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        try:
            validate_attachment_formset(attachment_formset)
        except ValidationError as e:
            messages.error(request, str(e))
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        allowed_recipients = self._get_allowed_recipients(target_group_form, request.user)
        selected_recipients = self._get_selected_recipients(request, allowed_recipients)

        manual_emails_raw = communication_form.cleaned_data.get('manual_emails', '')
        valid_manual_emails = self._parse_manual_emails(manual_emails_raw)

        if not selected_recipients.exists() and not valid_manual_emails:
            error_msg = "Please select at least one recipient."
            if request.user.role not in ['student', 'parent']:
                error_msg += " Or provide a valid manual email."
            communication_form.add_error(None, error_msg)
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not self._check_for_duplicate_emails(selected_recipients, valid_manual_emails, communication_form):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        communication = communication_form.save(commit=False)
        communication.sender = request.user
        communication.requires_response = communication_form.cleaned_data.get('requires_response', False)
        communication.sent = False
        communication.is_draft = communication_form.cleaned_data.get('is_draft', False)
        communication.selected_recipient_ids = list(selected_recipients.values_list('id', flat=True))
        communication.manual_emails = valid_manual_emails
        communication.saved_filter_data = {
            f"id_{k}": v for k, v in saved_filter_data.items()
        }
        communication.save()

        for form in attachment_formset:
            if form.cleaned_data.get('file'):
                form.instance.communication = communication
                form.save()

        if not communication.is_draft and communication.is_due():
            send_communication_to_recipients(
                communication=communication,
                selected_recipients=selected_recipients,
                manual_emails=valid_manual_emails
            )
            communication.sent = True
            communication.sent_at = timezone.now()
            communication.save()
            messages.success(request, "Communication sent successfully.")
            return redirect('communication_success')

        elif communication.is_draft:
            messages.success(request, "Communication saved as draft.")
            return redirect('draft_messages')

        else:
            url = reverse('communication_scheduled')
            query_string = urlencode({
                'scheduled_time': communication.scheduled_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                'sent': 'false'
            })
            messages.success(request, f"Scheduled for {communication.scheduled_time.strftime('%b %d, %Y at %I:%M %p')}.")
            return redirect(f"{url}?{query_string}")


@method_decorator([login_required, require_http_methods(["GET", "POST"])], name='dispatch')
class EditDraftMessageView(View):

    def _clean_id_list(self, raw_list):
        cleaned = []
        for item in raw_list:
            try:
                cleaned.append(str(int(item.strip())))
            except (ValueError, TypeError):
                continue
        return cleaned

    def _render_with_errors(self, communication_form, target_group_form, attachment_formset):
        messages.error(self.request, "There was an error with your submission. Please correct the highlighted fields.")
        return render(self.request, 'communications/edit_draft.html', {
            'communication_form': communication_form,
            'target_group_form': target_group_form,
            'attachment_formset': attachment_formset,
            'editing_draft': True,
            'communication': self.draft,
            'user_role': self.request.user.role,
            'user_branch_id': self.request.user.branch.id if hasattr(self.request.user, 'branch') else '',
        })

    def get(self, request, pk):
        draft = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
        self.draft = draft

        saved_filter_data = draft.saved_filter_data or {}
        selected_recipient_ids = draft.selected_recipient_ids or []

        initial_data = {
            'branch': Branch.objects.filter(id=saved_filter_data.get('id_branch')).first() if saved_filter_data.get('id_branch') else None,
            'role': saved_filter_data.get('id_role', ''),
            'staff_type': saved_filter_data.get('id_staff_type', ''),
            'student_class': StudentClass.objects.filter(id=saved_filter_data.get('id_student_class')).first() if saved_filter_data.get('id_student_class') else None,
            'class_arm': ClassArm.objects.filter(id=saved_filter_data.get('id_class_arm')).first() if saved_filter_data.get('id_class_arm') else None,
            'teaching_positions': TeachingPosition.objects.filter(
                id__in=self._clean_id_list(saved_filter_data.get('id_teaching_positions', []))
            ),
            'non_teaching_positions': NonTeachingPosition.objects.filter(
                id__in=self._clean_id_list(saved_filter_data.get('id_non_teaching_positions', []))
            ),
        }

        target_group_form = CommunicationTargetGroupForm(initial=initial_data, user=request.user)

        dummy_data = QueryDict('', mutable=True)
        for key in ['id_branch', 'id_role', 'id_staff_type', 'id_student_class', 'id_class_arm']:
            dummy_data[key] = saved_filter_data.get(key, '')
        dummy_data.setlist('id_teaching_positions', self._clean_id_list(saved_filter_data.get('id_teaching_positions', [])))
        dummy_data.setlist('id_non_teaching_positions', self._clean_id_list(saved_filter_data.get('id_non_teaching_positions', [])))

        dummy_form = CommunicationTargetGroupForm(data=dummy_data, user=request.user)
        if dummy_form.is_valid():
            allowed_recipients = dummy_form.get_filtered_recipients(dummy_form.cleaned_data).exclude(id=request.user.id)
        else:
            allowed_recipients = CustomUser.objects.filter(id__in=selected_recipient_ids)

        selected_recipients = allowed_recipients.filter(id__in=selected_recipient_ids)

        communication_form = CommunicationForm(instance=draft, user=request.user)
        attachment_formset = AttachmentFormSet(instance=draft, prefix="attachments")

        context = {
            'communication_form': communication_form,
            'target_group_form': target_group_form,
            'attachment_formset': attachment_formset,
            'communication': draft,
            'saved_filter_data': json.dumps(saved_filter_data),
            'selected_recipient_ids': json.dumps(selected_recipient_ids),
            'recipients': allowed_recipients,
            'selected_recipients': selected_recipients,
            'editing_draft': True,
            'user_branch_id': request.user.branch.id if getattr(request.user, 'branch', None) else '',
            'user_role': request.user.role,
        }

        return render(request, 'communications/edit_draft.html', context)

    def post(self, request, pk):
        self.request = request
        draft = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
        self.draft = draft

        communication_form = CommunicationForm(request.POST, request.FILES, instance=draft, user=request.user)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES, instance=draft)

        saved_filter_data = {
            'branch': request.user.branch.id if request.user.role in ['student', 'parent'] else request.POST.get('saved_branch', ''),
            'role': request.POST.get('saved_role', ''),
            'staff_type': request.POST.get('saved_staff_type', ''),
            'student_class': request.POST.get('saved_student_class', ''),
            'class_arm': request.POST.get('saved_class_arm', ''),
            'teaching_positions': self._clean_id_list(request.POST.get('saved_teaching_positions', '').split(',')),
            'non_teaching_positions': self._clean_id_list(request.POST.get('saved_non_teaching_positions', '').split(',')),
        }

        form_data = QueryDict('', mutable=True)
        for key in ['branch', 'role', 'staff_type', 'student_class', 'class_arm']:
            form_data[key] = saved_filter_data[key]
        form_data.setlist('teaching_positions', saved_filter_data['teaching_positions'])
        form_data.setlist('non_teaching_positions', saved_filter_data['non_teaching_positions'])

        target_group_form = CommunicationTargetGroupForm(data=form_data, user=request.user)

        if not (communication_form.is_valid() and target_group_form.is_valid() and attachment_formset.is_valid()):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        try:
            validate_attachment_formset(attachment_formset)
        except ValidationError as e:
            messages.error(request, str(e))
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        branch = request.user.branch if request.user.role in ['student', 'parent'] else target_group_form.cleaned_data.get('branch')
        if not branch:
            target_group_form.add_error('branch', "Please select a Branch.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        allowed_recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data).exclude(id=request.user.id)
        selected_recipients = allowed_recipients.filter(id__in=request.POST.getlist('selected_recipients'))

        manual_emails_raw = communication_form.cleaned_data.get('manual_emails', '')
        valid_manual_emails = self._parse_manual_emails(manual_emails_raw)

        if not selected_recipients.exists() and not valid_manual_emails:
            communication_form.add_error(None, "Please select at least one recipient or enter a valid manual email.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not self._check_for_duplicate_emails(selected_recipients, valid_manual_emails, communication_form):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        communication = communication_form.save(commit=False)
        communication.requires_response = communication_form.cleaned_data.get('requires_response', False)
        communication.sent = False
        communication.is_draft = communication_form.cleaned_data.get('is_draft', False)
        communication.selected_recipient_ids = list(selected_recipients.values_list('id', flat=True))
        communication.manual_emails = valid_manual_emails
        communication.saved_filter_data = {
            'id_branch': str(branch.id) if branch else '',
            'id_role': target_group_form.cleaned_data.get('role', ''),
            'id_staff_type': target_group_form.cleaned_data.get('staff_type', ''),
            'id_student_class': str(target_group_form.cleaned_data['student_class'].id) if target_group_form.cleaned_data.get('student_class') else '',
            'id_class_arm': str(target_group_form.cleaned_data['class_arm'].id) if target_group_form.cleaned_data.get('class_arm') else '',
            'id_teaching_positions': [str(pos.id) for pos in target_group_form.cleaned_data.get('teaching_positions', [])],
            'id_non_teaching_positions': [str(pos.id) for pos in target_group_form.cleaned_data.get('non_teaching_positions', [])],
        }
        communication.save()

        for form in attachment_formset:
            if form.cleaned_data.get('file'):
                form.instance.communication = communication
                form.save()

        if not communication.is_draft and communication.is_due():
            send_communication_to_recipients(
                communication=communication,
                selected_recipients=selected_recipients,
                manual_emails=valid_manual_emails
            )
            communication.sent = True
            communication.sent_at = timezone.now()
            communication.save()
            messages.success(request, "Communication sent successfully.")
            return redirect('communication_success')

        elif communication.is_draft:
            messages.success(request, "Draft updated successfully.")
            return redirect('draft_messages')

        else:
            url = reverse('communication_scheduled')
            query_string = urlencode({
                'scheduled_time': communication.scheduled_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                'sent': 'false'
            })
            messages.success(request, f"Scheduled for {communication.scheduled_time.strftime('%b %d, %Y at %I:%M %p')}.")
            return redirect(f"{url}?{query_string}")



@method_decorator([login_required, require_http_methods(["GET", "POST"]), csrf_protect], name='dispatch')
class CommunicationCreateEditView(View):
    """
    Handles both creating new Communications and editing existing draft Communications.
    """

    def flatten_querydict(self, qd: QueryDict):
        return {k: v[0] if len(v) == 1 else v for k, v in qd.lists()}

    def _clean_id_list(self, raw_list):
        cleaned = []
        for item in raw_list:
            try:
                cleaned.append(str(int(item.strip())))
            except (ValueError, TypeError):
                continue
        return cleaned

    def _get_allowed_recipients(self, target_group_form, user):
        recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data)
        return recipients.exclude(id=user.id)

    def _get_selected_recipients(self, request, allowed_recipients):
        selected_ids = request.POST.getlist('selected_recipients')
        return allowed_recipients.filter(id__in=selected_ids)

    def _parse_manual_emails(self, email_string):
        emails = [email.strip() for email in email_string.split(',') if email.strip()]
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email.lower())
            except ValidationError:
                messages.warning(self.request, f"Invalid manual email skipped: {email}")
        return valid_emails

    def _check_for_duplicate_emails(self, selected_recipients, manual_emails, form):
        if selected_recipients.exists():
            selected_emails = set(email.lower() for email in selected_recipients.values_list('email', flat=True))
            duplicates = selected_emails.intersection(set(manual_emails))
            if duplicates:
                form.add_error(None, f"Duplicate manual email(s): {', '.join(duplicates)}")
                return False
        return True

    def _render_with_errors(self, communication_form, target_group_form, attachment_formset, template='communications/communication_and_edit_form.html', extra_context=None):
        messages.error(self.request, "There was an error with your submission. Please correct the highlighted fields.")
        context = {
            'communication_form': communication_form,
            'target_group_form': target_group_form,
            'attachment_formset': attachment_formset,
            'user_role': self.request.user.role,
            'user_branch_id': getattr(self.request.user, 'branch', None) and self.request.user.branch.id or '',
        }
        if extra_context:
            context.update(extra_context)
        return render(self.request, template, context)


    def get(self, request, pk=None):
        exclude_fields = ['is_draft', 'requires_response']

        self.request = request
        if pk:
            # Edit existing draft
            draft = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
            self.draft = draft
            saved_filter_data = draft.saved_filter_data or {}
            selected_recipient_ids = draft.selected_recipient_ids or []

            initial_data = {
                'branch': Branch.objects.filter(id=saved_filter_data.get('id_branch')).first() if saved_filter_data.get('id_branch') else None,
                'role': saved_filter_data.get('id_role', ''),
                'staff_type': saved_filter_data.get('id_staff_type', ''),
                'student_class': StudentClass.objects.filter(id=saved_filter_data.get('id_student_class')).first() if saved_filter_data.get('id_student_class') else None,
                'class_arm': ClassArm.objects.filter(id=saved_filter_data.get('id_class_arm')).first() if saved_filter_data.get('id_class_arm') else None,
                'teaching_positions': TeachingPosition.objects.filter(
                    id__in=self._clean_id_list(saved_filter_data.get('id_teaching_positions', []))
                ),
                'non_teaching_positions': NonTeachingPosition.objects.filter(
                    id__in=self._clean_id_list(saved_filter_data.get('id_non_teaching_positions', []))
                ),
            }

            target_group_form = CommunicationTargetGroupForm(initial=initial_data, user=request.user)

            dummy_data = QueryDict('', mutable=True)
            for key in ['id_branch', 'id_role', 'id_staff_type', 'id_student_class', 'id_class_arm']:
                dummy_data[key] = saved_filter_data.get(key, '')
            dummy_data.setlist('id_teaching_positions', self._clean_id_list(saved_filter_data.get('id_teaching_positions', [])))
            dummy_data.setlist('id_non_teaching_positions', self._clean_id_list(saved_filter_data.get('id_non_teaching_positions', [])))

            dummy_form = CommunicationTargetGroupForm(data=dummy_data, user=request.user)
            if dummy_form.is_valid():
                allowed_recipients = dummy_form.get_filtered_recipients(dummy_form.cleaned_data).exclude(id=request.user.id)
            else:
                allowed_recipients = CustomUser.objects.filter(id__in=selected_recipient_ids)

            selected_recipients = allowed_recipients.filter(id__in=selected_recipient_ids)

            communication_form = CommunicationForm(instance=draft, user=request.user)
            attachment_formset = AttachmentFormSet(instance=draft, prefix="attachments")

            context = {
                'communication_form': communication_form,
                'target_group_form': target_group_form,
                'attachment_formset': attachment_formset,
                'communication': draft,
                'saved_filter_data': json.dumps(saved_filter_data),
                'selected_recipient_ids': json.dumps(selected_recipient_ids),
                'recipients': allowed_recipients,
                'selected_recipients': selected_recipients,
                'editing_draft': True,
                'user_branch_id': getattr(request.user, 'branch', None) and request.user.branch.id or '',
                'user_role': request.user.role,
                'exclude_fields': exclude_fields,  # added here
            }

            return render(request, 'communications/communication_and_edit_form.html', context)

        else:
            # Create new communication: render empty forms
            communication_form = CommunicationForm(user=request.user)
            target_group_form = CommunicationTargetGroupForm(user=request.user)
            attachment_formset = AttachmentFormSet(prefix="attachments")

            context = {
                'communication_form': communication_form,
                'target_group_form': target_group_form,
                'attachment_formset': attachment_formset,
                'editing_draft': False,
                'user_role': request.user.role,
                'user_branch_id': getattr(request.user, 'branch', None) and request.user.branch.id or '',
                'exclude_fields': exclude_fields,  # added here as well
            }

            return render(request, 'communications/communication_and_edit_form.html', context)


    def post(self, request, pk=None):
        """
        Handle form submission for both creating new communication and editing existing draft.
        """
        self.request = request
        if pk:
            # Editing existing draft
            communication_instance = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
            editing_draft = True
        else:
            communication_instance = None
            editing_draft = False

        communication_form = CommunicationForm(request.POST, request.FILES, instance=communication_instance, user=request.user)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES, instance=communication_instance, prefix="attachments")

        saved_filter_data = {
            'branch': request.user.branch.id if request.user.role in ['student', 'parent'] else request.POST.get('saved_branch', ''),
            'role': request.POST.get('saved_role', ''),
            'staff_type': request.POST.get('saved_staff_type', ''),
            'student_class': request.POST.get('saved_student_class', ''),
            'class_arm': request.POST.get('saved_class_arm', ''),
            'teaching_positions': self._clean_id_list(request.POST.get('saved_teaching_positions', '').split(',')),
            'non_teaching_positions': self._clean_id_list(request.POST.get('saved_non_teaching_positions', '').split(',')),
        }

        form_data = QueryDict('', mutable=True)
        for key in ['branch', 'role', 'staff_type', 'student_class', 'class_arm']:
            form_data[key] = saved_filter_data[key]
        form_data.setlist('teaching_positions', saved_filter_data['teaching_positions'])
        form_data.setlist('non_teaching_positions', saved_filter_data['non_teaching_positions'])

        target_group_form = CommunicationTargetGroupForm(data=form_data, user=request.user)

        # Validate forms
        if not (communication_form.is_valid() and target_group_form.is_valid() and attachment_formset.is_valid()):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset, 
                                            template='communications/communication_and_edit_form.html' if editing_draft else 'communications/communication_and_edit_form.html',
                                            extra_context={'editing_draft': editing_draft, 'communication': communication_instance})

        try:
            validate_attachment_formset(attachment_formset)
        except ValidationError as e:
            messages.error(request, str(e))
            return self._render_with_errors(communication_form, target_group_form, attachment_formset,
                                            template='communications/communication_and_edit_form.html' if editing_draft else 'communications/communication_and_edit_form.html',
                                            extra_context={'editing_draft': editing_draft, 'communication': communication_instance})

        branch = request.user.branch if request.user.role in ['student', 'parent'] else target_group_form.cleaned_data.get('branch')
        if not branch:
            target_group_form.add_error('branch', "Please select a Branch.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset,
                                            template='communications/communication_and_edit_form.html' if editing_draft else 'communications/communication_and_edit_form.html',
                                            extra_context={'editing_draft': editing_draft, 'communication': communication_instance})

        allowed_recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data).exclude(id=request.user.id)
        selected_recipients = allowed_recipients.filter(id__in=request.POST.getlist('selected_recipients'))

        manual_emails_raw = communication_form.cleaned_data.get('manual_emails', '')
        valid_manual_emails = self._parse_manual_emails(manual_emails_raw)

        if not selected_recipients.exists() and not valid_manual_emails:
            communication_form.add_error(None, "Please select at least one recipient or enter a valid manual email.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset,
                                            template='communications/communication_and_edit_form.html' if editing_draft else 'communications/communication_and_edit_form.html',
                                            extra_context={'editing_draft': editing_draft, 'communication': communication_instance})

        if not self._check_for_duplicate_emails(selected_recipients, valid_manual_emails, communication_form):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset,
                                            template='communications/communication_and_edit_form.html' if editing_draft else 'communications/communication_and_edit_form.html',
                                            extra_context={'editing_draft': editing_draft, 'communication': communication_instance})

        # Save communication
        communication = communication_form.save(commit=False)
        if not editing_draft:
            communication.sender = request.user

        communication.requires_response = communication_form.cleaned_data.get('requires_response', False)
        communication.sent = False
        communication.is_draft = communication_form.cleaned_data.get('is_draft', False)
        communication.selected_recipient_ids = list(selected_recipients.values_list('id', flat=True))
        communication.manual_emails = valid_manual_emails
        communication.saved_filter_data = {
            'id_branch': str(branch.id) if branch else '',
            'id_role': target_group_form.cleaned_data.get('role', ''),
            'id_staff_type': target_group_form.cleaned_data.get('staff_type', ''),
            'id_student_class': str(target_group_form.cleaned_data['student_class'].id) if target_group_form.cleaned_data.get('student_class') else '',
            'id_class_arm': str(target_group_form.cleaned_data['class_arm'].id) if target_group_form.cleaned_data.get('class_arm') else '',
            'id_teaching_positions': [str(pos.id) for pos in target_group_form.cleaned_data.get('teaching_positions', [])],
            'id_non_teaching_positions': [str(pos.id) for pos in target_group_form.cleaned_data.get('non_teaching_positions', [])],
        }
        communication.save()

        # Save attachments
        for form in attachment_formset:
            if form.cleaned_data.get('file'):
                form.instance.communication = communication
                form.save()

        # Send or schedule communication if not draft
        try:
            if not communication.is_draft and communication.is_due():
                send_communication_to_recipients(
                    communication=communication,
                    selected_recipients=selected_recipients,
                    manual_emails=valid_manual_emails
                )
                communication.sent = True
                communication.sent_at = timezone.now()
                communication.save()
                messages.success(request, "Communication sent successfully.")
                return redirect('communication_success')

            elif communication.is_draft:
                msg = "Draft updated successfully." if editing_draft else "Communication saved as draft."
                messages.success(request, msg)
                return redirect('draft_messages')

            else:
                url = reverse('communication_scheduled')
                query_string = urlencode({
                    'scheduled_time': communication.scheduled_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                    'sent': 'false'
                })
                messages.success(request, f"Scheduled for {communication.scheduled_time.strftime('%b %d, %Y at %I:%M %p')}.")
                return redirect(f"{url}?{query_string}")

        except Exception as e:
            logger.error("Error sending communication: %s", e, exc_info=True)
            messages.error(request, "An error occurred while sending communication. Please try again later.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset,
                                            template='communications/communication_and_edit_form.html' if editing_draft else 'communications/communication_and_edit_form.html',
                                            extra_context={'editing_draft': editing_draft, 'communication': communication_instance})



def communication_success(request):
    # This view just renders the success message template.
    return render(request, 'communications/communication_success.html')


def communication_scheduled(request):
    scheduled_time_str = request.GET.get('scheduled_time', None)
    scheduled_time = None
    is_sent = False

    if scheduled_time_str:
        try:
            # Try parsing 12-hour format (with AM/PM)
            scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%d %I:%M:%S %p')
            scheduled_time = timezone.make_aware(scheduled_time, timezone.get_current_timezone())
        except ValueError:
            try:
                # Fallback to 24-hour format
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%d %H:%M:%S')
                scheduled_time = timezone.make_aware(scheduled_time, timezone.get_current_timezone())
            except ValueError:
                scheduled_time = None

    if scheduled_time:
        is_sent = timezone.now() >= scheduled_time

    context = {
        'scheduled_time': scheduled_time,
        'is_sent': is_sent,
    }
    return render(request, 'communications/scheduled_success.html', context)


@login_required(login_url='login')
@require_GET
def inbox_view(request):
    try:
        # Ensure user has an allowed role
        allowed_roles = ['superadmin', 'branch_admin', 'staff', 'student', 'parent']
        user_role = getattr(request.user, 'role', '').lower()

        if user_role not in allowed_roles:
            logger.warning(f"Access denied: user {request.user.pk} with role '{user_role}' tried to access inbox.")
            return HttpResponseForbidden("You do not have permission to view this inbox.")

        # Fetch and sort received messages by sent or created date
        received_messages = CommunicationRecipient.objects.filter(
            recipient=request.user,
            deleted=False,
            communication__sent=True
        ).select_related(
            'communication', 'communication__sender'
        ).annotate(
            display_time=Coalesce('communication__sent_at', 'communication__created_at')
        ).order_by(
            F('display_time').desc()
        )

        return render(request, 'communications/inbox.html', {
            'received_messages': received_messages
        })

    except Exception as e:
        logger.error(f"Unexpected error loading inbox for user {request.user.pk}: {e}", exc_info=True)
        return HttpResponseServerError("Sorry, there was an error loading your inbox. Please try again later.")


@login_required
def read_message(request, pk):
    recipient_entry = get_object_or_404(
        CommunicationRecipient,
        pk=pk,
        recipient=request.user,
        deleted=False
    )
    recipient_entry.mark_as_read()

    reply_instance = MessageReply()  
    attachment_formset = ReplyAttachmentFormSet(
        instance=reply_instance,
        queryset=ReplyAttachment.objects.none(),
        prefix='attachments'
    )

    return render(request, 'communications/message_detail.html', {
        'message': recipient_entry.communication,
        'recipient_entry': recipient_entry,
        'attachment_formset': attachment_formset,
        'MAX_ATTACHMENT_COUNT': settings.MAX_ATTACHMENT_COUNT,
        'MAX_SINGLE_ATTACHMENT_MB': settings.MAX_SINGLE_ATTACHMENT_MB,
    })



@login_required
@require_POST  # Only allow POST for delete operation
def delete_message(request, pk):
    recipient_message = get_object_or_404(
        CommunicationRecipient,
        pk=pk,
        recipient=request.user,
        deleted=False
    )

    recipient_message.deleted = True
    recipient_message.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Message deleted.'})

    messages.success(request, "Message deleted successfully.")
    return redirect('inbox')


@login_required
def download_attachment(request, pk):
    attachment = get_object_or_404(CommunicationAttachment, pk=pk)

    # Optional: Check if user has permission to access the attachment here,
    # for example by verifying ownership or related communication permissions.

    try:
        # Ensure file exists and can be opened
        file_handle = attachment.file.open('rb')
    except FileNotFoundError:
        raise Http404("Attachment file not found on the server.")
    except Exception as e:
        # Log the error if you have logging set up
        # logger.error(f"Error opening attachment {pk}: {e}")
        raise Http404("Unable to access the attachment.")

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=os.path.basename(attachment.basename)
    )
    return response


@login_required(login_url='login')
@require_GET
def outbox_view(request):
    try:
        # Optional: restrict roles that can send messages
        allowed_roles = ['superadmin', 'branch_admin', 'staff', 'student', 'parent']
        user_role = getattr(request.user, 'role', '').lower()

        if user_role not in allowed_roles:
            logger.warning(f"Access denied: user {request.user.pk} with role '{user_role}' tried to access outbox.")
            return HttpResponseForbidden("You do not have permission to view this outbox.")

        # Fetch sent messages excluding soft-deleted ones
        sent_messages = Communication.objects.filter(
            sender=request.user,
            sent=True,
            is_draft=False
        ).exclude(
            sent_deletes__sender=request.user,
            sent_deletes__deleted=True
        ).select_related(
            'sender'
        ).prefetch_related(
            'attachments',
            'recipients__recipient'
        ).annotate(
            display_time=Coalesce('sent_at', 'created_at')
        ).order_by(
            F('display_time').desc()
        )

        logger.info(f"[OUTBOX] User {request.user.pk} has {sent_messages.count()} sent messages (excluding deleted).")

        return render(request, 'communications/outbox.html', {
            'sent_messages': sent_messages
        })

    except Exception as e:
        logger.error(f"Error loading outbox for user {request.user.pk}: {e}", exc_info=True)
        return HttpResponseServerError("Sorry, there was an error loading your outbox. Please try again later.")


@login_required
def read_sent_message(request, pk):
    # Get the sent communication by the logged-in user that is not deleted
    communication = get_object_or_404(
        Communication,
        pk=pk,
        sender=request.user
    )

    # Check if the sender has marked this message as deleted
    sent_delete_entry = SentMessageDelete.objects.filter(
        communication=communication,
        sender=request.user,
        deleted=True
    ).first()

    if sent_delete_entry:
        # Optionally, you can raise 404 if the message is deleted by sender
        raise Http404("This message was deleted.")

    return render(request, 'communications/sent_message_detail.html', {
        'sent_message': communication,
    })


@login_required
def delete_sent_message(request, pk):
    if request.method == 'POST':
        communication = get_object_or_404(Communication, pk=pk, sender=request.user)

        sent_delete_entry, created = SentMessageDelete.objects.get_or_create(
            communication=communication,
            sender=request.user,
            defaults={'deleted': True}
        )

        if not created:
            sent_delete_entry.deleted = True
            sent_delete_entry.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Message deleted.'})

        messages.success(request, "Sent message deleted successfully.")
        return redirect('outbox')  # Replace 'outbox' with your actual outbox URL name

    # If GET or other method, redirect back or show error
    return redirect('outbox')


@login_required
def delete_all_inbox_messages(request):
    if request.method == "POST":
        user = request.user
        CommunicationRecipient.objects.filter(recipient=user, deleted=False).update(deleted=True)
        messages.success(request, "All your inbox messages have been deleted.")
    return redirect('inbox') 


@login_required
def delete_all_sent_messages(request):
    if request.method == "POST":
        user = request.user
        sent_messages = Communication.objects.filter(sender=user, sent=True)

        for msg in sent_messages:
            SentMessageDelete.objects.update_or_create(
                communication=msg,
                sender=user,
                defaults={'deleted': True}
            )
    return redirect('outbox')


@login_required
def submit_reply(request, recipient_id):
    recipient_entry = get_object_or_404(
        CommunicationRecipient,
        pk=recipient_id,
        recipient=request.user,
        deleted=False,
        requires_response=True
    )

    from .forms import ReplyAttachmentFormSet

    if request.method == 'POST':
        reply_text = request.POST.get('reply', '').strip()

        if not reply_text and not request.FILES:
            messages.error(request, "Reply cannot be empty.")
            return redirect('inbox')

        try:
            with transaction.atomic():
                reply = MessageReply.objects.create(
                    recipient_entry=recipient_entry,
                    responder=request.user,
                    reply_text=reply_text
                )

                formset = ReplyAttachmentFormSet(
                    request.POST, request.FILES,
                    instance=reply,
                    prefix='attachments'
                )

                if formset.is_valid():
                    formset.save()
                else:
                    messages.error(request, "There was an error with the attachments.")
                    return redirect('inbox')

                recipient_entry.has_responded = True
                recipient_entry.save()

                messages.success(request, "Your reply has been submitted.")

        except Exception as e:
            messages.error(request, f"An error occurred while saving your reply: {e}")
            return redirect('inbox')

    return redirect('inbox')


@login_required(login_url='login')
@require_GET
def scheduled_messages_view(request):
    try:
        # Allow only specific roles to access scheduled messages
        allowed_roles = ['superadmin', 'branch_admin', 'staff']
        user_role = getattr(request.user, 'role', '').lower()

        if user_role not in allowed_roles:
            logger.warning(f"Access denied: user {request.user.pk} with role '{user_role}' tried to access scheduled messages.")
            return HttpResponseForbidden("You do not have permission to view scheduled messages.")

        # Fetch scheduled messages not sent yet and not drafts
        scheduled_messages = Communication.objects.filter(
            sender=request.user,
            sent=False,
            is_draft=False,
        ).annotate(
            display_time=Coalesce('scheduled_time', 'created_at')
        ).order_by(F('display_time').asc())

        return render(request, 'communications/scheduled.html', {
            'scheduled_messages': scheduled_messages
        })

    except Exception as e:
        logger.error(f"Error loading scheduled messages for user {request.user.pk}: {e}", exc_info=True)
        return HttpResponseServerError("An error occurred while loading scheduled messages.")


@login_required(login_url='login')
@require_GET
def draft_messages_view(request):
    try:
        draft_messages = Communication.objects.filter(
            sender=request.user,
            is_draft=True,
            sent=False
        ).order_by('-created_at')

        return render(request, 'communications/drafts.html', {
            'draft_messages': draft_messages
        })

    except Exception as e:
        logger.error(f"[Draft Messages] Error loading drafts for user {request.user.pk}: {e}", exc_info=True)
        return HttpResponseServerError("An error occurred while loading your draft messages.")


@require_POST
@login_required
def delete_draft_message(request, pk):
    draft = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
    draft.delete()
    messages.success(request, "Draft message deleted successfully.")
    return redirect('draft_messages')  # Make sure this name matches your drafts page URL


@method_decorator(login_required, name='dispatch')
class DeleteAllDraftMessagesView(View):
    def post(self, request):
        Communication.objects.filter(sender=request.user, is_draft=True, sent=False).delete()
        return redirect('draft_messages')  # or wherever you want to go after deletion
