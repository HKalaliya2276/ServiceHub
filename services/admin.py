from django.contrib import admin
from .models import Service
from .models import Booking
from .models import Notification

admin.site.register(Service)
admin.site.register(Booking)
admin.site.register(Notification)