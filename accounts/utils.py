from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.timezone import now
import re
import logging

logger = logging.getLogger(__name__)

# def send_communication_to_recipients(communication):
#     from .models import CommunicationRecipient
#     from django.contrib.auth import get_user_model

#     User = get_user_model()

#     subject = communication.title or (communication.body[:50] + '...')
#     message = communication.body
#     from_email = (
#         communication.sender.email
#         if communication.sender and communication.sender.email
#         else settings.DEFAULT_FROM_EMAIL
#     )

#     # Prefetch recipients and attachments
#     recipients = CommunicationRecipient.objects.filter(communication=communication)
#     attachments = list(communication.attachments.all())
#     registered_emails = set(
#         email.lower() for email in User.objects.values_list('email', flat=True)
#     )

#     for recipient in recipients:
#         if recipient.recipient:
#             # Skip sending email for in-app users (they'll view in dashboard)
#             logger.debug(f"Skipping in-app recipient: {recipient.recipient}")
#             continue

#         if recipient.email:
#             if recipient.email.lower() in registered_emails:
#                 logger.info(f"Skipping {recipient.email} (registered user)")
#                 continue

#             try:
#                 email = EmailMessage(
#                     subject=subject,
#                     body=message,
#                     from_email=from_email,
#                     to=[recipient.email],
#                 )

#                 for attachment in attachments:
#                     try:
#                         content_type = getattr(attachment.file.file, 'content_type', 'application/octet-stream')
#                         email.attach(attachment.basename, attachment.file.read(), content_type)
#                     except Exception as e:
#                         logger.warning(f"Attachment issue for {recipient.email}: {e}")

#                 email.send(fail_silently=False)
#                 recipient.delivered = True
#                 recipient.delivered_at = now()
#                 recipient.save()
#                 logger.info(f"Email sent to {recipient.email}")

#             except Exception as e:
#                 logger.error(f"Failed to send to {recipient.email}: {e}", exc_info=True)

def send_communication_to_recipients(communication, selected_recipients=None, manual_emails=None):
    from .models import CommunicationRecipient
    from django.contrib.auth import get_user_model
    from django.core.mail import EmailMessage
    from django.utils.timezone import now
    from django.conf import settings
    from django.db import transaction
    import logging

    logger = logging.getLogger(__name__)
    User = get_user_model()

    subject = communication.title or (communication.body[:50] + '...')
    message = communication.body
    from_email = (
        communication.sender.email
        if communication.sender and communication.sender.email
        else settings.DEFAULT_FROM_EMAIL
    )

    # Step 1: Save recipients if provided
    if selected_recipients or manual_emails:
        with transaction.atomic():
            if selected_recipients:
                for recipient in selected_recipients:
                    CommunicationRecipient.objects.create(
                        communication=communication,
                        recipient=recipient
                    )
            if manual_emails:
                for email in manual_emails:
                    CommunicationRecipient.objects.create(
                        communication=communication,
                        email=email
                    )

    # Step 2: Send to manual emails (not in-app users)
    recipients = CommunicationRecipient.objects.filter(communication=communication)
    attachments = list(communication.attachments.all())

    registered_emails = set(
        email.lower() for email in User.objects.values_list('email', flat=True)
    )

    for recipient in recipients:
        if recipient.recipient:
            logger.debug(f"Skipping in-app recipient: {recipient.recipient}")
            continue

        if recipient.email:
            if recipient.email.lower() in registered_emails:
                logger.info(f"Skipping {recipient.email} (registered user)")
                continue

            try:
                email_msg = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[recipient.email],
                )

                for attachment in attachments:
                    try:
                        content_type = getattr(attachment.file.file, 'content_type', 'application/octet-stream')
                        email_msg.attach(attachment.basename, attachment.file.read(), content_type)
                    except Exception as e:
                        logger.warning(f"Attachment issue for {recipient.email}: {e}")

                email_msg.send(fail_silently=False)
                recipient.delivered = True
                recipient.delivered_at = now()
                recipient.save()
                logger.info(f"Email sent to {recipient.email}")

            except Exception as e:
                logger.error(f"Failed to send to {recipient.email}: {e}", exc_info=True)



def generate_profile_number(role_prefix, model_class):
    year = now().year
    base_pattern = f"LAGS/{role_prefix}/{year}/"

    # Determine the profile number field name dynamically
    # Convention: For StaffProfile -> staff_number
    #             For ParentProfile -> parent_number
    #             For StudentProfile -> student_number
    # You can extend this mapping if needed
    field_map = {
        'StaffProfile': 'staff_number',
        'ParentProfile': 'parent_number',
        'StudentProfile': 'student_number',
    }
    number_field = field_map.get(model_class.__name__)
    if not number_field:
        raise ValueError(f"Model class '{model_class.__name__}' not supported for profile number generation")

    # Filter existing profiles by prefix and year, using the correct field
    filter_kwargs = {f"{number_field}__startswith": base_pattern}
    last_profile = model_class.objects.filter(**filter_kwargs).order_by(f"-{number_field}").first()

    if last_profile and getattr(last_profile, number_field):
        last_number_str = getattr(last_profile, number_field)
        match = re.search(r'(\d+)$', last_number_str)
        if match:
            last_number = int(match.group(1))
            new_number = last_number + 1
        else:
            new_number = 1
    else:
        new_number = 1

    return f"{base_pattern}{str(new_number).zfill(4)}"


def get_prefix_for_user(user):
    if hasattr(user, 'role'):
        if user.role == 'staff':
            return 'STA'
        elif user.role in ['branch_admin', 'superadmin']:
            return 'ADM'
        elif user.role == 'parent':
            return 'PAR'
        elif user.role == 'student':
            return 'STU'
    return 'UNK'  # Unknown role fallback



# def generate_profile_number(prefix, model_class):
#     year = now().year
#     count = model_class.objects.filter(created_at__year=year).count() + 1
#     return f"LAGS/{prefix}/{year}/{str(count).zfill(4)}"
