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

    
    # Students
    path('student/create/', views.create_student, name='student_create'),
    # path('student/update/<int:student_id>/', views.update_student, name='student_update'),
    path('student/update/<int:pk>/', views.update_student, name='student_update'),
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    
    
    # Student Class
    path('student_classes/', views.student_class_list, name='student_class_list'),
    path('student_class/create/', views.student_class_create, name='student_class_create'),
    path('student_class/<int:pk>/update/', views.student_class_update, name='student_class_update'),
    path('student_class/<int:pk>/delete/', views.student_class_delete, name='student_class_delete'),


    # Parents
    path('parent/create/', views.ParentCreateView.as_view(), name='parent_create'),
    path('parent/update/<int:pk>/', views.ParentUpdateView.as_view(), name='parent_update'),
    path('parents/', views.ParentListView.as_view(), name='parent_list'),
    path('parent/<int:pk>/', views.ParentDetailView.as_view(), name='parent_detail'),
    path('parents/<int:pk>/delete/', views.ParentDeleteView.as_view(), name='parent_delete'),
    
    
    # Branch 
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/edit/', views.BranchUpdateView.as_view(), name='branch_edit'),
    path('branches/<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch_detail'),
    

    #  Class Arms
    path('create/', views.create_class_arm, name='create_class_arm'),
    path('update/<int:pk>/', views.update_class_arm, name='update_class_arm'),
    path('delete/<int:pk>/', views.delete_class_arm, name='delete_class_arm'),
    path('list/', views.class_arm_list, name='class_arm_list'),
    
    
    
    # Communication
    # path('communications/create/', views.CommunicationCreateView.as_view(), name='communication-create'),
    # path('communications/create/ajax/', views.CommunicationCreateAjaxView.as_view(), name='communication-create-ajax'),
    
    # path('inbox/', views.inbox, name='inbox'),
    # path('sent/', views.sent_messages, name='sent_messages'),
    # path('message/<int:pk>/', views.message_detail, name='message_detail'),
    # path('send-message/', views.CommunicationCreateView.as_view(), name='send_message'),
    # path('ajax/get-target-users/', views.get_recipients, name='get_target_users'),
    # path('message/<int:pk>/comment/', views.add_comment, name='add_comment'),
    # path('message/<int:pk>/delete_received/', views.delete_received_message, name='delete_received_message'),
    # path('message/<int:pk>/delete_sent/', views.delete_sent_message, name='delete_sent_message'),


    path('communications/', views.communication_index, name='communication_index'),
    # path('communications/ajax/get_student_classes/', views.get_student_classes, name='get_student_classes'),
    # path('communications/ajax/get_class_arms/', views.get_class_arms, name='get_class_arms'),
    path('communications/ajax/get_filtered_users/', views.get_filtered_users, name='get_filtered_users'),
    path('communications/get-user-by-id/', views.get_user_by_id, name='get_user_by_id'),
    path('communications/send/', views.SendCommunicationView.as_view(), name='send_communication'),
    path('communications/sent/', views.communication_success, name='communication_success'),
    path('communications/scheduled/', views.communication_scheduled, name='communication_scheduled'),
    path('communications/inbox/', views.inbox_view, name='inbox'),
    path('communications/inbox/read/<int:pk>/', views.read_message, name='read_message'),
    path('communication/<int:pk>/delete/', views.delete_message, name='delete_message'),
    path('communication/attachments/download/<int:pk>/', views.download_attachment, name='download_attachment'),
    path('communications/outbox/', views.outbox_view, name='outbox'),
    path('communications/outbox/read/<int:pk>/', views.read_sent_message, name='read_sent_message'),
    path('communications/outbox/delete/<int:pk>/', views.delete_sent_message, name='delete_sent_message'),
    path('communications/inbox/delete-all/', views.delete_all_inbox_messages, name='delete_all_inbox_messages'),
    path('communications/sent/delete-all/', views.delete_all_sent_messages, name='delete_all_outbox_messages'),
    path('communications/reply/<int:recipient_id>/', views.submit_reply, name='submit_reply'),
    path('communications/scheduled/', views.scheduled_messages_view, name='scheduled_messages'),
    path('communications/drafts/', views.draft_messages_view, name='draft_messages'),
    path('communications/drafts/<int:pk>/edit/', views.EditDraftMessageView.as_view(), name='edit_draft_message'),
    path('communications/drafts/<int:pk>/delete/', views.delete_draft_message, name='delete_draft_message'),
    path('communications/drafts/delete_all/', views.DeleteAllDraftMessagesView.as_view(), name='delete_all_draft_messages'),

    # ////////////////////////////////////
    path('communications/create/', views.CommunicationCreateEditView.as_view(), name='communication_create'),
    path('communications/<int:pk>/edit/', views.CommunicationCreateEditView.as_view(), name='communication_edit_draft'),
]

