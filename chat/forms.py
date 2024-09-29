from django import forms
from .models import Patient, Chat, Message

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'contact_number', 
                  'address', 'email', 'medical_condition', 'medication_regimen',
                  'last_appointment', 'next_appointment', 'doctor_name']

class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ['user']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message', 'is_user', 'chat', 'timestamp']
