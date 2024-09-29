from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Chat with {self.user.username}"

class Message(models.Model):
    message = models.TextField()
    is_user = models.BooleanField(default=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

class Doctor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.specialty})"

class Patient(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    contact_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    medication_regimen = models.TextField(blank=True, null=True)
    medication_frequency = models.CharField(max_length=15, null=True)

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="patient")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    medical_condition = models.TextField(blank=True, null=True)
    last_appointment = models.DateTimeField(default=timezone.now, null=True)
    next_appointment = models.DateTimeField(default=timezone.now, null=True)
    reason = models.CharField(max_length=255, null=True)
    doctor_notes = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"Appointment for {self.patient.user.first_name} with {self.doctor.first_name} on {self.next_appointment}"
