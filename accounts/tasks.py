from celery import shared_task
from django.utils import timezone
from .models import Communication, CommunicationRecipient
from .utils import send_communication_to_recipients


@shared_task
def send_scheduled_communications():
    due_comms = Communication.objects.filter(sent=False, scheduled_time__lte=timezone.now())
    for comm in due_comms:
        send_communication_to_recipients(comm)
        comm.sent = True
        comm.save()
