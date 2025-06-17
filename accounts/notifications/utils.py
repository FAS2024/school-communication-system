# from django.core.mail import send_mail

# def send_email_notification(subject, message, recipient_list):
#     send_mail(
#         subject,
#         message,
#         None,  # uses DEFAULT_FROM_EMAIL
#         recipient_list,
#         fail_silently=False,
#     )



# # notifications/utils.py
# from firebase_admin import messaging

# def send_push_notification(title, body, tokens):
#     message = messaging.MulticastMessage(
#         notification=messaging.Notification(title=title, body=body),
#         tokens=tokens,
#     )
#     response = messaging.send_multicast(message)
#     return response




# pip install firebase-admin
# #

# # yourapp/apps.py
# import firebase_admin
# from firebase_admin import credentials

# class YourAppConfig(AppConfig):
#     name = 'yourapp'

#     def ready(self):
#         cred = credentials.Certificate('path/to/firebase-creds.json')
#         if not firebase_admin._apps:
#             firebase_admin.initialize_app(cred)
