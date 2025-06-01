# def get_filtered_recipients(self, target_group_data):
#     from .models import CustomUser,StudentProfile
#     from django.db.models import Q
#     qs = CustomUser.objects.filter(is_active=True)


#     user = self.user

#     branch_id = target_group_data.get('branch')
#     role_name = target_group_data.get('role')
#     staff_type = target_group_data.get('staff_type')
#     teaching_positions_ids = target_group_data.get('teaching_positions')
#     non_teaching_positions_ids = target_group_data.get('non_teaching_positions')
#     student_class_id = target_group_data.get('student_class')
#     class_arm_id = target_group_data.get('class_arm')
#     search = target_group_data.get('search')

#     def filter_staff(qs):
#         if staff_type:
#             qs = qs.filter(staff_type=staff_type)
#         if teaching_positions_ids:
#             qs = qs.filter(teaching_positions__id__in=teaching_positions_ids)
#         if non_teaching_positions_ids:
#             qs = qs.filter(non_teaching_positions__id__in=non_teaching_positions_ids)
#         return qs

#     def filter_students(qs):
#         if student_class_id:
#             qs = qs.filter(studentprofile__current_class_id=student_class_id)
#         if class_arm_id:
#             qs = qs.filter(studentprofile__current_class_arm_id=class_arm_id)
#         return qs

#     def apply_role_filters(qs):
#         if role_name:
#             qs = qs.filter(role=role_name)

#         if role_name in ['staff', 'branch_admin'] or role_name is None:
#             qs = filter_staff(qs)
#         if role_name == 'student' or role_name is None:
#             qs = filter_students(qs)

#         return qs

#     if user.role == 'student':
#         qs = CustomUser.objects.filter(
#             branch_id=user.branch_id,
#             role__in=['student', 'staff', 'branch_admin']
#         ).exclude(id=user.id)
#         if not role_name:
#             return CustomUser.objects.none()
#         qs = apply_role_filters(qs)

#     elif user.role == 'parent':
#         children = StudentProfile.objects.filter(parent__user=user)
#         child_class_ids = children.values_list('current_class_id', flat=True)

#         children_users = CustomUser.objects.filter(id__in=children.values_list('user_id', flat=True))
#         class_teacher_users = CustomUser.objects.filter(role='staff', class_teacher_of__id__in=child_class_ids)
#         branch_admins = CustomUser.objects.filter(role='branch_admin', branch_id=user.branch_id)

#         qs = (children_users | class_teacher_users | branch_admins).distinct()
#         if not role_name:
#             return CustomUser.objects.none()
#         qs = apply_role_filters(qs)

#     elif user.role in ['staff', 'branch_admin', 'superadmin']:
#         if not (role_name or branch_id):
#             return CustomUser.objects.none()
#         qs = CustomUser.objects.all()
#         if branch_id:
#             qs = qs.filter(branch_id=branch_id)
#         qs = apply_role_filters(qs)

#     else:
#         return CustomUser.objects.none()

#     # Apply search filter if present
#     if search:
#         qs = qs.filter(
#             Q(first_name__icontains=search) |
#             Q(last_name__icontains=search) |
#             Q(email__icontains=search)
#         )

#     return qs.exclude(id=user.id).distinct()





# def filter_users_by_target_group_or_params(
#     *,
#     branch=None,
#     role=None,
#     staff_type=None,
#     teaching_positions=None,
#     non_teaching_positions=None,
#     student_class=None,
#     class_arm=None,
#     search=None,
#     sender_role=None,
#     sender_branch_id=None,
#     branch_id=None,
# ):  
#     from .models import CustomUser
#     from django.db.models import Q
#     qs = CustomUser.objects.filter(is_active=True)

#     # Branch filter logic based on sender role and requested branch
#     if sender_role in ['superadmin', 'branch_admin', 'staff']:
#         if branch_id:
#             qs = qs.filter(branch_id=branch_id)
#     else:
#         # students and parents can only see their own branch users
#         if sender_branch_id:
#             qs = qs.filter(branch_id=sender_branch_id)
#         else:
#             # fallback: no branch filter
#             pass

#     # If branch param is given directly (used by model method), override
#     if branch:
#         qs = qs.filter(branch=branch)

#     # Role filter
#     if role:
#         qs = qs.filter(role=role)
#     else:
#         return CustomUser.objects.none()

#     # Role-specific filters
#     if role == 'student':
#         if student_class:
#             qs = qs.filter(student_class=student_class)
#         if class_arm:
#             qs = qs.filter(class_arm=class_arm)

#     elif role == 'staff':
#         if staff_type and staff_type != 'both':
#             qs = qs.filter(staff_type=staff_type)

#         if teaching_positions:
#             qs = qs.filter(teaching_positions__in=teaching_positions)

#         if non_teaching_positions:
#             qs = qs.filter(non_teaching_positions__in=non_teaching_positions)

#     # parents, branch_admin, superadmin: no extra filters here

#     # Search filter
#     if search:
#         qs = qs.filter(
#             Q(first_name__icontains=search) |
#             Q(last_name__icontains=search) |
#             Q(email__icontains=search)
#         )

#     return qs.distinct()
