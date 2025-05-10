from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = "home"),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_login, name='logout'),
    # path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('dashboard/branch_admin/', views.branch_admin_dashboard, name='branch_admin_dashboard'),
    path('dashboard/superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    
    
    
    path('register/user/', views.register_user, name='register_user'),
    
    
    # Teaching Position
    path('teaching_positions/', views.teaching_position_list, name='teaching_position_list'),
    path('teaching_positions/create/', views.teaching_position_create, name='teaching_position_create'),
    path('teaching_positions/<int:pk>/edit/', views.teaching_position_edit, name='teaching_position_edit'),
    path('teaching_positions/<int:pk>/delete/', views.teaching_position_delete, name='teaching_position_delete'),

    #  Non Teaching Position 
    path('non_teaching_positions/', views.non_teaching_position_list, name='non_teaching_position_list'),
    path('non_teaching_positions/create/', views.non_teaching_position_create, name='non_teaching_position_create'),
    path('non_teaching_positions/<int:pk>/edit/', views.non_teaching_position_edit, name='non_teaching_position_edit'),
    path('non_teaching_positions/<int:pk>/delete/', views.non_teaching_position_delete, name='non_teaching_position_delete'), 
    
    
    
    # Staff
    path('create-staff/', views.create_staff, name='create_staff'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:staff_id>/edit/', views.update_staff_profile, name='update_staff_profile'),
    path('staff/<int:user_id>/profile/', views.staff_detail, name='staff_detail'),
    path('staff/<int:user_id>/delete/', views.delete_staff, name='delete_staff'),


    # Branch 
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/edit/', views.BranchUpdateView.as_view(), name='branch_edit'),
    path('branches/<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch_detail'),
]

