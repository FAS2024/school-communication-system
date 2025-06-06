from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.timezone import now
import re


def send_communication_to_recipients(communication):
    from .models import CommunicationRecipient
    subject = communication.title or (communication.body[:50] + '...')
    message = communication.body
    from_email = communication.sender.email if communication.sender and communication.sender.email else settings.DEFAULT_FROM_EMAIL

    recipients = CommunicationRecipient.objects.filter(communication=communication)

    for recipient in recipients:
        if recipient.recipient:
            # Skip in-app recipients (handled elsewhere)
            continue

        elif recipient.email:
            try:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[recipient.email],
                )
                # Attach all files related to the communication
                for attachment in communication.attachments.all():
                    content_type = getattr(attachment.file.file, 'content_type', None) or 'application/octet-stream'
                    email.attach(attachment.file.name, attachment.file.read(), content_type)
                
                email.send(fail_silently=False)
            except Exception as e:
                print(f"Failed to send to {recipient.email}: {e}")

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
