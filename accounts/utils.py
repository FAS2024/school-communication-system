from django.core.mail import EmailMessage
from django.conf import settings
from .models import CommunicationRecipient

def send_communication_to_recipients(communication):
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


# def send_communication_to_recipients(communication):
#     recipients = CommunicationRecipient.objects.filter(communication=communication)
#     for r in recipients:
#         if r.recipient:
#             # Send to registered user
#             send_mail_to_user(r.recipient, communication)
#         elif r.email:
#             # Send to manual email address
#             send_mail_to_email(r.email, communication)
