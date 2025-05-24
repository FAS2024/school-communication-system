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
        CommunicationAttachmentForm,
        CommunicationRecipientForm,
        CommunicationTargetGroupForm,
        CommentForm,
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

            messages.success(request, f"Staff {edited_user.get_full_name()} updated successfully.")
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
    branches = Branch.objects.all().order_by('id')
    paginator = Paginator(branches, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'branch_list.html', {'page_obj': page_obj})


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
@transaction.atomic
def create_student(request):
    # Only superadmin and branch_admin can create students
    if request.user.role not in ['superadmin', 'branch_admin']:
        raise PermissionDenied("You do not have permission to create students.")

    if request.method == 'POST':
        user_form = StudentCreationForm(request.POST, request.FILES, user=request.user)
        profile_form = StudentProfileForm(request.POST, user=request.user)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            parent = profile_form.cleaned_data['parent']
            user.branch = parent.user.branch  # Set branch from parent's branch
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, f"{user.first_name} {user.last_name} successfully created.")
            return redirect('student_list')
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
@transaction.atomic
def update_student(request, pk):
    user_instance = get_object_or_404(CustomUser, pk=pk, role='student')
    profile_instance = get_object_or_404(StudentProfile, user=user_instance)

    # Permissions:
    if request.user.role in ['superadmin', 'branch_admin']:
        # Admins can update any student (with branch filtering if needed)
        pass
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
            user = user_form.save(commit=False)
            parent = profile_form.cleaned_data['parent']
            user.branch = parent.user.branch  # Always update branch from parent
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, f"{user.first_name} {user.last_name} successfully updated.")
            return redirect('student_detail', pk=user.pk)
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
        if user.role == 'superadmin':
            return CustomUser.objects.filter(role='student').order_by('last_name', 'first_name')
        else:
            return CustomUser.objects.filter(role='student', branch=user.branch).order_by('last_name', 'first_name')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('dashboard')  # or wherever you want to redirect unauthorized users
        return super().dispatch(request, *args, **kwargs)



@login_required
def student_detail(request, pk):
    user = request.user
    student = get_object_or_404(CustomUser, pk=pk, role='student')

    # Access control
    if user.role == 'superadmin':
        pass  # can view all
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
            messages.success(request, f"Parent '{full_name}' profile updated successfully.")
            return redirect('parent_list')
        messages.error(request, "Please correct the errors below.")
        return render(request, 'parents/parent_form.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ParentUpdateView(View):
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, role='parent')

        # Access control for branch_admin: ensure they only edit parents from their branch
        if request.user.role == 'branch_admin' and user.branch != request.user.branch:
            messages.error(request, "You do not have permission to edit this parent.")
            return redirect('parent_list')

        # Access control for regular parents: they can only edit their own profile
        if request.user.role == 'parent' and request.user.pk != user.pk:
            messages.error(request, "You can only edit your own profile.")
            return redirect('parent_dashboard')

        # Populate the form with existing data for editing
        form = ParentCreationForm(instance=user, request=request, initial={
            'date_of_birth': getattr(user.parentprofile, 'date_of_birth', ''),
            'gender': getattr(user.parentprofile, 'gender', ''), 
            'address': getattr(user.parentprofile, 'address', ''),
            'phone_number': getattr(user.parentprofile, 'phone_number', ''),
            'occupation': getattr(user.parentprofile, 'occupation', ''),
            'relationship_to_student ': getattr(user.parentprofile, 'relationship_to_student ', ''),
            'preferred_contact_method': getattr(user.parentprofile, 'preferred_contact_method', ''),
            'nationality ': getattr(user.parentprofile, 'nationality ', ''),
            'state': getattr(user.parentprofile, 'state', '')
        })
        return render(request, 'parents/parent_form.html', {'form': form, 'is_update': True})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, role='parent')

        # Access control for branch_admin: ensure they only edit parent from their branch
        if request.user.role == 'branch_admin' and user.branch != request.user.branch:
            messages.error(request, "You do not have permission to edit this parent.")
            return redirect('parent_list')

        # Access control for regular parents: they can only edit their own profile
        if request.user.role == 'parents' and request.user.pk != user.pk:
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
        # Ensure that only 'parent' role users are shown in the list
        return CustomUser.objects.filter(role='parent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def dispatch(self, request, *args, **kwargs):
        # Ensure the user has the correct role (either 'superadmin' or 'branch_admin')
        if request.user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('parent_dashboard')

        return super().dispatch(request, *args, **kwargs)


class ParentDetailView(DetailView):
    model = CustomUser
    template_name = 'parents/parent_detail.html' 
    context_object_name = 'parent'

    def get_object(self, queryset=None):
        # Retrieve the parent object by primary key (pk)
        parent = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='parent')

        # Access control logic:
        if self.request.user.role == 'branch_admin' and parent.branch != self.request.user.branch:
            messages.error(self.request, "You do not have permission to view this parent's details.")
            return None  # Or you can redirect to a different page
        elif self.request.user.role == 'parent' and self.request.user.pk != parent.pk:
            messages.error(self.request, "You can only view your own profile.")
            return None  # Or you can redirect to a different page

        return parent

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to view parent details.")
            return redirect('login')  # Redirect to login if not authenticated
        elif request.user.role not in ['superadmin', 'branch_admin', 'parent']:
            messages.error(request, "You do not have permission to view this page.")
            # return redirect('dashboard')  # Redirect to the dashboard if not authorized
            return None

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ParentDeleteView(DeleteView):
    model = CustomUser
    template_name = 'parents/parent_confirm_delete.html'
    context_object_name = 'parent'
    success_url = reverse_lazy('parent_list')

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Only superadmin and branch_admin can delete students
        if user.role not in ['superadmin', 'branch_admin']:
            messages.error(request, "Access denied. Only superadmins and branch admins can delete students.")
            return redirect('student_list')

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        parent = get_object_or_404(CustomUser, pk=self.kwargs['pk'], role='parent')

        # Branch admin can only delete parents in their branch
        if self.request.user.role == 'branch_admin' and parent.branch != self.request.user.branch:
            messages.error(self.request, "You are not authorized to delete this parent.")
            return None

        return parent

    def delete(self, request, *args, **kwargs):
        parent = self.get_object()

        if not parent:
            return redirect('parent_list')

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



# class CommunicationCreateView(LoginRequiredMixin, TemplateView):
#     template_name = 'communication/communication_create.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         # Helper queries
#         CustomUserModel = CustomUser

#         if user.role == 'student':
#             # Get this student's class and arm from StudentProfile
#             try:
#                 student_profile = user.studentprofile
#                 current_class = student_profile.current_class
#                 current_class_arm = student_profile.current_class_arm
#             except StudentProfile.DoesNotExist:
#                 current_class = None
#                 current_class_arm = None

#             if current_class and current_class_arm:
#                 # Classmates: students in the same class and same arm, exclude self
#                 classmates = CustomUserModel.objects.filter(
#                     role='student',
#                     studentprofile__current_class=current_class,
#                     studentprofile__current_class_arm=current_class_arm
#                 ).exclude(pk=user.pk)

#                 # Class teacher from StudentClass model (class_teacher FK)
#                 class_teacher = CustomUserModel.objects.filter(
#                     pk=current_class.class_teacher_id
#                 )

#                 # Combine classmates and class teacher queryset
#                 context['users'] = classmates | class_teacher
#             else:
#                 context['users'] = CustomUserModel.objects.none()

#         elif user.role == 'staff':
#             # Staff see other staff in same branch + branch admins in same branch
#             staff_users = CustomUserModel.objects.filter(
#                 role='staff',
#                 branch=user.branch
#             ).exclude(pk=user.pk)

#             branch_admins = CustomUserModel.objects.filter(
#                 role='branch_admin',
#                 branch=user.branch
#             )

#             context['users'] = staff_users | branch_admins

#         elif user.role == 'parent':
#             # Parent sees child's class teachers + branch admins

#             # Get all children of this parent (via ParentProfile -> StudentProfile)
#             try:
#                 parent_profile = user.parentprofile
#                 children = parent_profile.students.all()
#             except ParentProfile.DoesNotExist:
#                 children = CustomUserModel.objects.none()

#             # Get all classes of the children
#             children_classes = children.values_list('current_class', flat=True).distinct()

#             # Class teachers for these classes
#             class_teachers = CustomUserModel.objects.filter(
#                 pk__in=StudentClass.objects.filter(id__in=children_classes).values_list('class_teacher', flat=True)
#             )

#             branch_admins = CustomUserModel.objects.filter(
#                 role='branch_admin',
#                 branch=user.branch
#             )

#             context['users'] = class_teachers | branch_admins

#         elif user.role == 'branch_admin':
#             # Branch admin can message anyone in their branch
#             context['users'] = CustomUserModel.objects.filter(branch=user.branch)

#         elif user.role == 'superadmin':
#             # Superadmin can message anyone
#             context['users'] = CustomUserModel.objects.all()

#         else:
#             context['users'] = CustomUserModel.objects.none()

#         # Add all branches for UI filtering if needed
#         context['branches'] = Branch.objects.all()

#         return context

# class CommunicationCreateAjaxView(LoginRequiredMixin, View):
    
#     def get(self, request, *args, **kwargs):
#         """
#         AJAX endpoint to get roles and users filtered by branch and other filters
#         Query params:
#             branch_id: int
#             role: str (e.g. 'staff', 'student', 'parent')
#             staff_type: str (optional, 'teaching' or 'non_teaching')
#         """
#         branch_id = request.GET.get('branch_id')
#         role = request.GET.get('role')
#         staff_type = request.GET.get('staff_type')

#         if not branch_id or not role:
#             return JsonResponse({'success': False, 'error': 'branch_id and role are required'}, status=400)
        
#         try:
#             branch = Branch.objects.get(pk=branch_id)
#         except Branch.DoesNotExist:
#             return JsonResponse({'success': False, 'error': 'Branch not found'}, status=404)

#         users = CustomUser.objects.none()

#         # Example logic - adjust field names and models accordingly
#         if role == 'staff':
#             users = CustomUser.objects.filter(branch=branch, role='staff')
#             if staff_type == 'teaching':
#                 users = users.filter(is_teaching=True)
#             elif staff_type == 'non_teaching':
#                 users = users.filter(is_teaching=False)
#         elif role == 'student':
#             users = CustomUser.objects.filter(branch=branch, role='student')
#         elif role == 'parent':
#             users = CustomUser.objects.filter(branch=branch, role='parent')

#         # Serialize users to send minimal info (id and name)
#         users_data = [{'id': user.id, 'name': user.get_full_name()} for user in users]

#         # Return role info + users list
#         return JsonResponse({
#             'success': True,
#             'role': role,
#             'users': users_data,
#         })


#     def post(self, request, *args, **kwargs):
#         data = request.POST
#         files = request.FILES.getlist('files')

#         form = CommunicationForm(data)
#         if not form.is_valid():
#             return JsonResponse({'success': False, 'errors': form.errors}, status=400)

#         # Recipients can be individuals or 'send_to_all' flags
#         try:
#             recipients_data = json.loads(data.get('recipients', '[]'))  # list of user ids
#             target_groups_data = json.loads(data.get('target_groups', '[]'))  # list of groups with branch, role, class_name, send_to_all flag
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'error': 'Invalid JSON format for recipients or target groups'}, status=400)

#         communication = form.save(commit=False)
#         communication.sender = request.user

#         scheduled_time_str = data.get('scheduled_time')
#         if scheduled_time_str:
#             try:
#                 dt = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
#                 communication.scheduled_time = make_aware(dt)
#             except ValueError:
#                 return JsonResponse({'success': False, 'error': 'Invalid scheduled_time format'}, status=400)

#         communication.save()

#         for f in files:
#             CommunicationAttachment.objects.create(communication=communication, file=f)

#         # Save recipients - individuals only
#         for recipient_id in recipients_data:
#             user = get_object_or_404(CustomUser, pk=recipient_id)
#             CommunicationRecipient.objects.create(communication=communication, recipient=user)

#         # Save target groups - with possible send_to_all flag
#         for group in target_groups_data:
#             branch = None
#             branch_id = group.get('branch')
#             if branch_id:
#                 branch = get_object_or_404(Branch, pk=branch_id)

#             send_to_all = group.get('send_to_all', False)

#             target_group = CommunicationTargetGroup.objects.create(
#                 communication=communication,
#                 role=group.get('role'),
#                 branch=branch,
#                 class_name=group.get('class_name'),
#                 send_to_all=send_to_all  # You might need to add this field to your model
#             )

#             # If sending to all in this group, optionally create recipients for all users in that group (optional)
#             # Or handle it later when sending notifications.

#         return JsonResponse({'success': True, 'message': 'Message created successfully'})



# @login_required
# @require_GET
# def ajax_get_users(request):
#     branch_id = request.GET.get('branch')
#     role = request.GET.get('role')
#     staff_type = request.GET.get('staff_type', 'all')

#     if not branch_id or not role:
#         return JsonResponse({'success': False, 'error': 'Branch and role are required'})

#     try:
#         branch = Branch.objects.get(pk=branch_id)
#     except Branch.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'Invalid branch'})

#     # Filter users by branch and role
#     users = CustomUser.objects.filter(branch=branch, role=role)

#     # Additional filter for staff
#     if role == 'staff':
#         if staff_type == 'teaching':
#             users = users.filter(is_teaching=True)
#         elif staff_type == 'non-teaching':
#             users = users.filter(is_teaching=False)

#     users_data = [{'id': u.id, 'full_name': u.get_full_name(), 'username': u.username} for u in users]

#     return JsonResponse({'success': True, 'users': users_data})



# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from django.utils import timezone
# from django.db import transaction

# from .models import Communication, CommunicationAttachment, CommunicationRecipient, CommunicationComment, SentMessageDelete
# from .forms import CommunicationForm, CommentForm

@login_required
def inbox(request):
    received = CommunicationRecipient.objects.filter(
        recipient=request.user, deleted=False
    ).select_related('communication').order_by('-communication__created_at')
    context = {'received_messages': received}
    return render(request, 'messaging/inbox.html', context)

@login_required
def sent_messages(request):
    sent = Communication.objects.filter(sender=request.user).order_by('-created_at')

    # Exclude messages deleted by sender
    deleted_message_ids = SentMessageDelete.objects.filter(sender=request.user, deleted=True).values_list('communication_id', flat=True)
    sent = sent.exclude(id__in=deleted_message_ids)

    context = {'sent_messages': sent}
    return render(request, 'messaging/sent.html', context)



# # views.py (inside CommunicationCreateView or message creation logic)
# from notifications.utils import send_email_notification

# def notify_recipients(communication):
#     recipients = communication.recipients.all()
#     subject = f"New {communication.message_type.title()} from {communication.sender.username}"
#     message = communication.body

#     emails = [r.recipient.email for r in recipients if r.recipient.email]
#     send_email_notification(subject, message, emails)




# # In your view or signal
# def notify_push_recipients(communication):
#     tokens = [r.recipient.profile.fcm_token for r in communication.recipients.all() if hasattr(r.recipient, 'profile') and r.recipient.profile.fcm_token]
#     title = f"{communication.message_type.title()} from {communication.sender.username}"
#     body = communication.short_body()
#     send_push_notification(title, body, tokens)



# notify_recipients(communication)
# notify_push_recipients(communication)



@login_required
def message_detail(request, pk):
    message = get_object_or_404(Communication, pk=pk)
    
    # Mark as read if recipient
    try:
        recipient_entry = CommunicationRecipient.objects.get(communication=message, recipient=request.user)
        recipient_entry.mark_as_read()
    except CommunicationRecipient.DoesNotExist:
        recipient_entry = None

    comments = message.comments.order_by('created_at')
    comment_form = CommentForm()

    context = {
        'message': message,
        'comments': comments,
        'comment_form': comment_form,
        'recipient_entry': recipient_entry,
    }
    return render(request, 'messaging/message_detail.html', context)


@login_required
def send_message(request):
    if request.method == 'POST':
        comm_form = CommunicationForm(request.POST)
        target_form = CommunicationTargetGroupForm(request.POST)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES)

        selected_user_ids = request.POST.getlist('selected_users')

        if comm_form.is_valid() and target_form.is_valid() and attachment_formset.is_valid():
            if not selected_user_ids:
                messages.error(request, "You must select at least one recipient.")
            else:
                communication = comm_form.save()
                target_group = target_form.save(commit=False)
                target_group.communication = communication
                target_group.save()
                target_form.save_m2m()

                # Save attachments
                attachment_formset.instance = communication
                attachment_formset.save()

                # Link selected users (you must have a model or method to save this)
                communication.recipients.set(User.objects.filter(id__in=selected_user_ids))

                messages.success(request, "Message sent successfully.")
                return redirect('some_view_name')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        comm_form = CommunicationForm()
        target_form = CommunicationTargetGroupForm()
        attachment_formset = AttachmentFormSet()

    context = {
        'comm_form': comm_form,
        'target_form': target_form,
        'attachment_formset': attachment_formset,
    }
    return render(request, 'communication/send_message.html', context)


@csrf_exempt
@login_required
def get_target_users(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        branch = data.get('branch')
        role = data.get('role')
        staff_type = data.get('staff_type')
        teaching_positions = data.get('teaching_positions', [])
        non_teaching_positions = data.get('non_teaching_positions', [])
        student_class = data.get('student_class')
        class_arm = data.get('class_arm')

        # Filter users based on your actual profile models here
        users = CustomUser.objects.none()

        if not branch or not role:
            return JsonResponse({'users': []})

        # Example filtering logic, adjust according to your model structure
        if role in ['superadmin', 'branch_admin', 'staff']:
            users = CustomUser.objects.filter(profile__branch_id=branch, profile__role=role)
            if staff_type:
                users = users.filter(profile__staff_type=staff_type)
            if teaching_positions:
                users = users.filter(profile__teaching_positions__id__in=teaching_positions)
            if non_teaching_positions:
                users = users.filter(profile__non_teaching_positions__id__in=non_teaching_positions)
        elif role == 'student':
            users = CustomUser.objects.filter(
                profile__branch_id=branch,
                profile__role=role,
                profile__student_class_id=student_class,
                profile__class_arm_id=class_arm,
            )
        else:
            users = CustomUser.objects.filter(profile__branch_id=branch, profile__role=role)

        users = users.distinct()[:100]  # Limit for performance

        user_list = [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.profile.role,
        } for u in users]

        return JsonResponse({'users': user_list})
    return JsonResponse({'error': 'Invalid request method'}, status=400)



def send_notification_email(recipient, communication):
    subject = f"New Message: {communication.title or 'Untitled'}"
    message = communication.body
    from_email = 'no-reply@example.com'
    recipient_list = [recipient.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=True)


@login_required
def add_comment(request, pk):
    message = get_object_or_404(Communication, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.communication = message
            comment.commenter = request.user
            comment.save()
            return redirect('messaging:message_detail', pk=pk)
    return redirect('messaging:message_detail', pk=pk)

@login_required
def delete_received_message(request, pk):
    recipient_entry = get_object_or_404(CommunicationRecipient, communication_id=pk, recipient=request.user)
    recipient_entry.deleted = True
    recipient_entry.save()
    return redirect('messaging:inbox')

@login_required
def delete_sent_message(request, pk):
    communication = get_object_or_404(Communication, pk=pk, sender=request.user)
    obj, created = SentMessageDelete.objects.get_or_create(communication=communication, sender=request.user)
    obj.deleted = True
    obj.save()
    return redirect('messaging:sent_messages')
