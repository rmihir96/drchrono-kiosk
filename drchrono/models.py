from django.db import models

# Add your models here


class Appointments(models.Model):

    patient_id = models.IntegerField()
    appointment_id = models.CharField(unique=True, max_length=100)
    scheduled_time = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)
    arrival_time = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, default=None)
    time_waited = models.DurationField(null=True)
    reference_time = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, default=None)
    status = models.CharField(max_length=100, default='')