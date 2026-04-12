from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_service, name='add_service'),
    path('list/', views.service_list, name='service_list'),
    path('book/<int:service_id>/', views.book_service, name='book_service'),
    path('vendor-bookings/', views.vendor_bookings, name='vendor_bookings'),
    path('update-booking/<int:booking_id>/<str:status>/', views.update_booking_status, name='update_booking'),
    path('assign-delivery/<int:booking_id>/', views.assign_delivery, name='assign_delivery'),
    path('delivery-update/<int:booking_id>/<str:status>/', views.update_delivery_status, name='delivery_update'),
]