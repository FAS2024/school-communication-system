def is_branchadmin_or_superadmin(user):
    return user.is_authenticated and (user.role == 'superadmin' or user.role == 'branch_admin')



def is_student(user):
    return user.is_authenticated and user.role == 'student'
