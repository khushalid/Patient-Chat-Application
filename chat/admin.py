from django.contrib import admin
from .models import Chat, Message, Patient, Doctor, Appointment



admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(Chat)
admin.site.register(Message)