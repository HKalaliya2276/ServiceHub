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
    path('my-bookings/', views.customer_bookings, name='customer_bookings'),
    path('my-services/', views.my_services, name='my_services'),
    path('create/', views.create_service, name='create_service'),
    path('edit/<int:id>/', views.edit_service, name='edit_service'),
    path('delete/<int:id>/', views.delete_service, name='delete_service'),
    path('pay/<int:booking_id>/', views.make_payment, name='make_payment'),
    path('notifications/', views.notifications, name='notifications'),
    path('get-notifications/', views.get_notifications, name='get_notifications'),
    path('mark-read/<int:notif_id>/', views.mark_single_read, name='mark_single_read'),
    path('chat/<int:booking_id>/', views.chat_view, name='chat'),
    path('chat-history/<int:booking_id>/', views.get_chat_history, name='chat_history'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
