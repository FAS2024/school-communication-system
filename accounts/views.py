from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from .forms import (
        TeachingPositionForm, 
        NonTeachingPositionForm, 
        StaffCreationForm, 
        StaffProfileForm,
        BranchForm,
        StudentCreationForm,
        StudentClassForm,
        ClassArmForm,
        ParentCreationForm,
        StudentProfileForm,
        CommunicationForm,
        CommunicationRecipientForm,
        CommunicationTargetGroupForm,
        AttachmentFormSet
    )
from .models import (
        CustomUser, 
        StudentProfile, 
        ParentProfile, 
        StaffProfile,
        TeachingPosition,
        NonTeachingPosition,
        Branch,
        StudentClass,
        ClassArm,
        Communication,
        CommunicationAttachment,
        CommunicationComment,
        CommunicationRecipient,
        CommunicationTargetGroup,
        SentMessageDelete
    )

# views.py
import json
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.views.generic import TemplateView


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
from django.contrib.auth.mixins import LoginRequiredMixin
from . import utility
from django.db import transaction
from django.core.exceptions import PermissionDenied

CustomUser = get_user_model()

from django.db.models import Q
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail


from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


from .utils import send_communication_to_recipients
from django.conf import settings  # Make sure this is imported at the top
from django.urls import reverse
from django.utils.http import urlencode


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


# @login_required
# @require_GET
# def ajax_get_filtered_users(request):
#     # Define filter fields from the form
#     filter_fields = CommunicationTargetGroupForm.Meta.fields

#     # Extract raw GET parameters for filter fields
#     raw_filter_values = {
#         field: request.GET.get(field, None)
#         for field in filter_fields
#     }

#     # If any filter field is present and has an empty string '', return empty result immediately
#     if any(value == '' for value in raw_filter_values.values() if value is not None):
#         return JsonResponse([], safe=False)

#     # Clean and prepare data from GET parameters (convert empty strings to None)
#     cleaned_data = {
#         field: (value if value else None)
#         for field, value in raw_filter_values.items()
#         if value is not None
#     }

#     # Instantiate the form with user context
#     form = CommunicationTargetGroupForm(user=request.user, data=cleaned_data)

#     if not form.is_valid():
#         return JsonResponse({'errors': form.errors}, status=400)

#     try:
#         # Get filtered recipients
#         users_qs = form.get_filtered_recipients(form.cleaned_data)

#         # Optimize DB queries (ensure related fields are prefetched)
#         users_qs = users_qs.select_related('branch')  # if applicable

#         users_list = []
#         for user in users_qs:
#             profile_picture_url = None
#             if hasattr(user, 'profile_picture'):
#                 profile_picture = user.profile_picture
#                 if profile_picture and hasattr(profile_picture, 'url'):
#                     profile_picture_url = profile_picture.url

#             users_list.append({
#                 'id': user.id,
#                 'first_name': user.first_name,
#                 'last_name': user.last_name,
#                 'email': user.email,
#                 'branch__name': getattr(user.branch, 'name', 'N/A') if hasattr(user, 'branch') else 'N/A',
#                 'profile_picture': {
#                     'url': profile_picture_url
#                 }
#             })

#         return JsonResponse(users_list, safe=False)

#     except ValidationError as e:
#         return JsonResponse({'error': str(e)}, status=400)

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


@login_required
def get_filtered_users(request):
    form = CommunicationTargetGroupForm(request.GET, user=request.user)

    if form.is_valid():
        recipients = form.get_filtered_recipients(form.cleaned_data)
        users = recipients.values(
            'id', 'first_name', 'last_name', 'email',
            'branch__name', 'profile_picture'
        )
        return JsonResponse(list(users), safe=False)
    
    # Always show all form errors (including non-field errors) in DEBUG
    if settings.DEBUG:
        error_response = {
            'field_errors': form.errors,
            'non_field_errors': form.non_field_errors(),
        }
        return JsonResponse({'errors': error_response}, status=400)

    return JsonResponse({'error': 'Invalid filter data'}, status=400)


# @login_required
# def communication_index(request):
    
#     context = {
#         'communication_form': CommunicationForm(user=request.user),
#         'target_group_form': CommunicationTargetGroupForm(user=request.user),
#         'attachment_formset': AttachmentFormSet(),
#         'user_role': request.user.role,
#         'user_branch_id': request.user.branch.id if request.user.branch else '',
#     }
#     return render(request, 'communications/communication_form.html', context)

@login_required
def communication_index(request):
    communication_data = request.session.pop('communication_form_data', None)
    target_group_data = request.session.pop('target_group_form_data', None)
    attachment_data = request.session.pop('attachment_formset_data', None)
    non_field_errors = request.session.pop('non_field_errors', None)

    communication_form = CommunicationForm(data=communication_data, user=request.user) if communication_data else CommunicationForm(user=request.user)
    target_group_form = CommunicationTargetGroupForm(data=target_group_data, user=request.user) if target_group_data else CommunicationTargetGroupForm(user=request.user)
    attachment_formset = AttachmentFormSet(data=attachment_data) if attachment_data else AttachmentFormSet()

    # Re-inject non-field errors if available
    if non_field_errors:
        for err_msg in non_field_errors:
            communication_form.add_error(None, err_msg)

    context = {
        'communication_form': communication_form,
        'target_group_form': target_group_form,
        'attachment_formset': attachment_formset,
        'user_role': request.user.role,
        'user_branch_id': request.user.branch.id if request.user.branch else '',
    }
    return render(request, 'communications/communication_form.html', context)


@method_decorator([login_required, require_POST], name='dispatch')
class SendCommunicationView(View):
    def _get_allowed_recipients(self, target_group_form, user):
        # Exclude the sender themselves from recipient list
        recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data)
        return recipients.exclude(id=user.id)

    def _get_selected_recipients(self, request, allowed_recipients):
        # 'selected_recipients' must be the exact name attribute of your checkboxes in the form
        selected_ids = request.POST.getlist('selected_recipients')
        
        print("POST data:", request.POST)
        # Filter to only allowed recipients by their ids
        return allowed_recipients.filter(id__in=selected_ids)

    def _parse_manual_emails(self, email_string):
        emails = [email.strip() for email in email_string.split(',') if email.strip()]
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email.lower())  # normalize to lowercase for comparison
            except ValidationError:
                messages.warning(self.request, f"Invalid manual email skipped: {email}")
        return valid_emails

    def _check_for_duplicate_emails(self, selected_recipients, manual_emails, form):
        if selected_recipients.exists():
            selected_emails = set(email.lower() for email in selected_recipients.values_list('email', flat=True))
            duplicates = selected_emails.intersection(set(manual_emails))
            if duplicates:
                form.add_error(
                    None,
                    f"The following manual email(s) are already among selected recipients: {', '.join(duplicates)}"
                )
                return False
        return True

    def _render_with_errors(self, communication_form, target_group_form, attachment_formset):
        self.request.session['communication_form_data'] = self.request.POST.dict()
        self.request.session['target_group_form_data'] = self.request.POST.dict()
        self.request.session['attachment_formset_data'] = self.request.POST.dict()
        
        # Convert non-field errors to plain list of strings
        non_field_errors = communication_form.non_field_errors()
        self.request.session['non_field_errors'] = [str(error) for error in non_field_errors]

        self.request.session['form_error'] = True
        messages.error(self.request, "There was an error with your submission. Please correct the highlighted fields.")
        return redirect('communication_index')

    def post(self, request):
        self.request = request

        communication_form = CommunicationForm(request.POST, user=request.user)
        target_group_form = CommunicationTargetGroupForm(request.POST, user=request.user)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES)

        if not (communication_form.is_valid() and target_group_form.is_valid() and attachment_formset.is_valid()):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if request.user.role in ['student', 'parent']:
            branch = request.user.branch
            target_group_form.cleaned_data['branch'] = branch
            if hasattr(target_group_form, 'instance'):
                target_group_form.instance.branch = branch

        allowed_recipients = self._get_allowed_recipients(target_group_form, request.user)
        selected_recipients = self._get_selected_recipients(request, allowed_recipients)

        manual_emails_raw = communication_form.cleaned_data.get('manual_emails', '')
        valid_manual_emails = self._parse_manual_emails(manual_emails_raw)

        if not selected_recipients.exists() and not valid_manual_emails:
            if request.user.role in ['student', 'parent']:
                communication_form.add_error(None, "Please select at least one recipient.")
            else:
                communication_form.add_error(None, "Please select at least one recipient or provide a valid manual email.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not self._check_for_duplicate_emails(selected_recipients, valid_manual_emails, communication_form):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        communication = communication_form.save(commit=False)
        communication.sender = request.user
        communication.sent = False
        communication.save()

        for form in attachment_formset:
            if form.cleaned_data.get('file'):
                form.instance.communication = communication
                form.save()

        with transaction.atomic():
            for recipient in selected_recipients:
                CommunicationRecipient.objects.create(communication=communication, recipient=recipient)
            for email in valid_manual_emails:
                CommunicationRecipient.objects.create(communication=communication, email=email)

        if communication.is_due():
            send_communication_to_recipients(communication)
            communication.sent = True
            communication.save()
            messages.success(request, "Communication sent successfully.")
            return redirect('communication_success')
        else:
            url = reverse('communication_scheduled')
            query_string = urlencode({
                'scheduled_time': communication.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
                'sent': 'false'  # explicitly mark as not yet sent
            })
            url_with_params = f"{url}?{query_string}"
            messages.success(request, f"Communication scheduled for {communication.scheduled_time}.")
            return redirect(url_with_params)



def communication_success(request):
    # This view just renders the success message template.
    return render(request, 'communications/communication_success.html')


# def communication_scheduled(request):
#     scheduled_time_str = request.GET.get('scheduled_time', None)
#     scheduled_time = None
#     is_sent = False

#     if scheduled_time_str:
#         # Parse scheduled_time string to datetime object
#         try:
#             scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%d %H:%M:%S')
#             scheduled_time = timezone.make_aware(scheduled_time, timezone.get_current_timezone())
#         except ValueError:
#             scheduled_time = None

#     if scheduled_time:
#         # If scheduled_time has passed, consider it sent
#         is_sent = timezone.now() >= scheduled_time

#     context = {
#         'scheduled_time': scheduled_time,  # This is now a datetime object
#         'is_sent': is_sent,
#     }
#     return render(request, 'communications/scheduled_success.html', context)

def communication_scheduled(request):
    scheduled_time_str = request.GET.get('scheduled_time', None)
    scheduled_time = None
    is_sent = False

    if scheduled_time_str:
        try:
            # Parse as local time (since that's how it was saved and sent via GET param)
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



# def send_notification_email(recipient, communication):
#     subject = f"New Message: {communication.title or 'Untitled'}"
#     message = communication.body
#     from_email = 'no-reply@example.com'
#     recipient_list = [recipient.email]
#     send_mail(subject, message, from_email, recipient_list, fail_silently=True)
