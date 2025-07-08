from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Communication
from .utils import send_communication_to_recipients
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def send_scheduled_communications():
    due_comms = Communication.objects.filter(
        sent=False,
        scheduled_time__lte=timezone.now(),
        is_draft=False
    )

    for comm in due_comms:
        try:
            logger.info(f"Sending scheduled message ID {comm.id} titled '{comm.title}' from sender {comm.sender}'")

            # Reconstruct recipients
            selected_recipients = User.objects.filter(id__in=comm.selected_recipient_ids or [])
            manual_emails = comm.manual_emails or []

            # Pass them to the sender
            send_communication_to_recipients(
                communication=comm,
                selected_recipients=selected_recipients,
                manual_emails=manual_emails
            )

            # Mark as sent
            comm.sent = True
            comm.sent_at = timezone.now()
            comm.save()

            logger.info(f"Marked communication ID {comm.id} as sent at {comm.sent_at}")
        except Exception as e:
            logger.error(f"Failed to send scheduled communication ID {comm.id}: {e}", exc_info=True)

