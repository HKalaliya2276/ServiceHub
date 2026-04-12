from django.db import models
from users.models import User
from django.utils import timezone

class Service(models.Model):
    vendor      = models.ForeignKey(User, on_delete=models.CASCADE)
    title       = models.CharField(max_length=100)
    description = models.TextField()
    price       = models.FloatField()
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class Booking(models.Model):
    customer     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_bookings')
    service      = models.ForeignKey(Service, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(default=timezone.now)
    status       = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.customer.username} - {self.service.title}"