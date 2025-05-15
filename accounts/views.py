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
from django.contrib.auth.mixins import LoginRequiredMixin
from . import utility
from django.db import transaction
from django.core.exceptions import PermissionDenied

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


# @login_required
# @user_passes_test(utility.is_branchadmin_or_superadmin)
# def create_student(request):
#     if request.method == 'POST':
#         form = StudentCreationForm(request.POST, request.FILES, request=request)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Student created successfully.")
#             return redirect('student_list')
#         else:
#             messages.error(request, "Please correct the errors below.")
#     else:
#         form = StudentCreationForm(request=request)

#     context = {
#         'form': form,
#         'title': 'Create New Student'
#     }
#     return render(request, 'student_form.html', context)



# @login_required
# @user_passes_test(utility.is_branchadmin_or_superadmin)
# def update_student(request, student_id):
#     student = get_object_or_404(StudentProfile, id=student_id)

#     if request.user.role == 'branch_admin' and student.user.branch != request.user.branch:
#         messages.error(request, "You do not have permission to edit this student.")
#         return redirect('student_list')

#     if request.method == 'POST':
#         form = StudentCreationForm(request.POST, request.FILES, instance=student, request=request)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Student updated successfully.")
#             return redirect('student_list')
#         else:
#             messages.error(request, "Please correct the errors below.")
#     else:
#         form = StudentCreationForm(instance=student, request=request)

#     context = {
#         'form': form,
#         'title': 'Update Student'
#     }
#     return render(request, 'student_form.html', context)



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

            return redirect('student_list')
    else:
        user_form = StudentCreationForm(user=request.user)
        profile_form = StudentProfileForm(user=request.user)

    return render(request, 'student_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
@transaction.atomic
def update_student(request, student_id):
    user_instance = get_object_or_404(CustomUser, pk=student_id, role='student')
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

            return redirect('student_detail', student_id=user.pk)
    else:
        user_form = StudentCreationForm(instance=user_instance, user=request.user)
        profile_form = StudentProfileForm(instance=profile_instance, user=request.user)

    return render(request, 'student_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@method_decorator([login_required, user_passes_test(utility.is_branchadmin_or_superadmin)], name='dispatch')
class StudentListView(ListView):
    model = StudentProfile
    template_name = 'student_list.html'
    context_object_name = 'students'

    def get_queryset(self):
        """
        Filter students based on the branch of the user.
        """
        if self.request.user.role == 'branchadmin':
            return StudentProfile.objects.filter(user__branch=self.request.user.branch)
        return StudentProfile.objects.all()  # Superadmin can view all students
    
    

@method_decorator([login_required, user_passes_test(utility.is_branchadmin_or_superadmin)], name='dispatch')
class StudentDetailView(DetailView):
    model = StudentProfile
    template_name = 'student_detail.html'
    context_object_name = 'student'

    def get_object(self, queryset=None):
        """
        Get the student profile based on the primary key (pk).
        """
        return StudentProfile.objects.get(id=self.kwargs['pk'])


@method_decorator([login_required, user_passes_test(utility.is_branchadmin_or_superadmin)], name='dispatch')
class StudentDeleteView(DeleteView):
    model = StudentProfile
    template_name = 'student_confirm_delete.html'
    context_object_name = 'student'
    success_url = reverse_lazy('student_list')

    def get_object(self, queryset=None):
        """
        Get the student profile to be deleted.
        """
        return StudentProfile.objects.get(id=self.kwargs['pk'])
    

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
