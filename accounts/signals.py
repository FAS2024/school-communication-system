from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, StaffProfile

@receiver(post_save, sender=CustomUser)
def create_staff_profile(sender, instance, created, **kwargs):
    if created and instance.role in ['superadmin', 'branch_admin', 'staff']:
        StaffProfile.objects.create(user=instance)


# @receiver(post_save, sender=Communication)
# def send_notification(sender, instance, created, **kwargs):
#     if created and instance.message_type == 'notification':
#         # Send notifications to recipients
#         for recipient in instance.recipients.all():
#             send_email_or_push_notification(recipient.recipient, instance)




# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Communication
# from .tasks import send_all_notifications

# @receiver(post_save, sender=Communication)
# def communication_created_handler(sender, instance, created, **kwargs):
#     if created and not instance.is_draft:
        # send_all_notifications.delay(instance.id)



