from django.db import models
from django.utils import timezone
from services.models import MainServices, Child_services

class Slot(models.Model):
    STATUS_CHOICES = (
        ("available", "Available"),
        ("booked", "Booked"),
        ("completed", "Completed"),
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    main_service = models.ForeignKey(
        MainServices,
        on_delete=models.CASCADE,
        related_name="slots"
    )

    child_service = models.ForeignKey(
        Child_services,
        on_delete=models.CASCADE,
        related_name="slots"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available"
    )

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("date", "start_time", "child_service")

    def __str__(self):
        return f"{self.date} | {self.start_time} - {self.end_time} ({self.status})"

