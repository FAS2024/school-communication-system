from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, StaffProfile

@receiver(post_save, sender=CustomUser)
def create_staff_profile(sender, instance, created, **kwargs):
    if created and instance.role in ['superadmin', 'branch_admin', 'staff']:
        StaffProfile.objects.create(user=instance)
