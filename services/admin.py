from django.contrib import admin
from .models import Service
from .models import Booking

admin.site.register(Service)
admin.site.register(Booking)