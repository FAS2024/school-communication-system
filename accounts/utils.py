def filter_users_by_target_group_or_params(
    *,
    branch=None,
    role=None,
    staff_type=None,
    teaching_positions=None,
    non_teaching_positions=None,
    student_class=None,
    class_arm=None,
    search=None,
    sender_role=None,
    sender_branch_id=None,
    branch_id=None,
):  
    from .models import CustomUser
    from django.db.models import Q
    qs = CustomUser.objects.filter(is_active=True)

    # Branch filter logic based on sender role and requested branch
    if sender_role in ['superadmin', 'branch_admin', 'staff']:
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
    else:
        # students and parents can only see their own branch users
        if sender_branch_id:
            qs = qs.filter(branch_id=sender_branch_id)
        else:
            # fallback: no branch filter
            pass

    # If branch param is given directly (used by model method), override
    if branch:
        qs = qs.filter(branch=branch)

    # Role filter
    if role:
        qs = qs.filter(role=role)
    else:
        return CustomUser.objects.none()

    # Role-specific filters
    if role == 'student':
        if student_class:
            qs = qs.filter(student_class=student_class)
        if class_arm:
            qs = qs.filter(class_arm=class_arm)

    elif role == 'staff':
        if staff_type and staff_type != 'both':
            qs = qs.filter(staff_type=staff_type)

        if teaching_positions:
            qs = qs.filter(teaching_positions__in=teaching_positions)

        if non_teaching_positions:
            qs = qs.filter(non_teaching_positions__in=non_teaching_positions)

    # parents, branch_admin, superadmin: no extra filters here

    # Search filter
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    return qs.distinct()
