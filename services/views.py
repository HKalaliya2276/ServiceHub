from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Booking, Notification, Service
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from rapidfuzz import fuzz
from django.http import JsonResponse, HttpResponseForbidden
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Booking, Notification, Service, ChatMessage
from django.db.models import Sum

User = get_user_model()

@login_required
def add_service(request):
    if request.user.role != 'vendor':
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')

        Service.objects.create(
            vendor=request.user,
            title=title,
            description=description,
            price=price
        )

        return redirect('vendor_dashboard')

    return render(request, 'add_service.html')


@login_required
def service_list(request):
    services = Service.objects.all().order_by('-created_at')

    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if query:
        services = services.filter(title__icontains=query)

    if min_price:
        services = services.filter(price__gte=min_price)

    if max_price:
        services = services.filter(price__lte=max_price)

    paginator = Paginator(services, 5)  # 5 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'service_list.html', {'page_obj': page_obj})


@login_required
def book_service(request, service_id):
    service = Service.objects.get(id=service_id)

    if request.user.role != 'customer':
        return redirect('dashboard')

    booking = Booking.objects.create(
        customer=request.user,
        service=service
    )

    Notification.objects.create(
    user=service.vendor,
    message=f"New booking for {service.title}",
    link=f"/services/vendor-bookings/#booking-{booking.id}",
    is_read=False
)

    return redirect('customer_dashboard')


@login_required
def vendor_bookings(request):
    if request.user.role != 'vendor':
        return redirect('dashboard')

    bookings = Booking.objects.filter(service__vendor=request.user)

    return render(request, 'vendor_bookings.html', {'bookings': bookings})


@login_required
def my_services(request):
    services = Service.objects.filter(vendor=request.user)
    return render(request, 'my_services.html', {'services': services})


@login_required
def create_service(request):
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')

        Service.objects.create(
            vendor=request.user,
            title=title,
            description=description,
            price=price
        )
        return redirect('my_services')

    return render(request, 'services/create_service.html')


@login_required
def edit_service(request, id):
    service = Service.objects.get(id=id)   

    if service.vendor != request.user:    
        return HttpResponse("Unauthorized", status=403)

    if request.method == "POST":
        service.title = request.POST.get('title')
        service.description = request.POST.get('description')
        service.price = request.POST.get('price')
        service.save()

        return redirect('my_services')

    return render(request, 'edit_service.html', {'service': service})

@login_required
def delete_service(request, id):
    service = Service.objects.get(id=id)   

    if service.vendor != request.user:    
        return HttpResponse("Unauthorized", status=403)

    service.delete()
    return redirect('my_services')


@login_required
def update_booking_status(request, booking_id, status):
    if request.user.role != 'vendor':
        return redirect('dashboard')

    booking = Booking.objects.get(id=booking_id)

    # Security check
    if booking.service.vendor != request.user:
        return redirect('dashboard')

    booking.status = status
    booking.save()

    Notification.objects.create(
    user=booking.customer,
    message=f"Your booking for {booking.service.title} is {status}",
    link=f"/services/my-bookings/#booking-{booking.id}"
)

    return redirect('vendor_bookings')


@login_required
def assign_delivery(request, booking_id):
    if request.user.role != 'vendor':
        return redirect('dashboard')

    booking = Booking.objects.get(id=booking_id)

    if booking.service.vendor != request.user:
        return redirect('dashboard')

    # Get all delivery boys
    delivery_boys = User.objects.filter(role='delivery')

    if request.method == 'POST':
        delivery_id = request.POST.get('delivery_id')
        delivery_user = User.objects.get(id=delivery_id)

        booking.delivery_boy = delivery_user
        booking.save()

        Notification.objects.create(
        user=delivery_user,
        message=f"You have been assigned a delivery for {booking.service.title}",
        link=f"/delivery/#booking-{booking.id}"
        )

        return redirect('vendor_bookings')

    return render(request, 'assign_delivery.html', {
        'booking': booking,
        'delivery_boys': delivery_boys
    })


@login_required
def update_delivery_status(request, booking_id, status):
    if request.user.role != 'delivery':
        return redirect('dashboard')

    booking = Booking.objects.get(id=booking_id)

    # Security check
    if booking.delivery_boy != request.user:
        return redirect('dashboard')

    booking.status = status
    booking.save()

    return redirect('delivery_dashboard')


@login_required
def customer_bookings(request):
    if request.user.role != 'customer':
        return redirect('dashboard')

    bookings = Booking.objects.filter(customer=request.user).order_by('-booking_date')

    return render(request, 'customer_bookings.html', {'bookings': bookings})


@login_required
def make_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.customer != request.user:
        return redirect('dashboard')

    # Fake payment success
    booking.payment_status = 'paid'
    booking.status = 'accepted'
    booking.save()

    return redirect('customer_bookings')


@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'notifications.html', {'notifications': user_notifications})

# 🔥 Get unread notifications
@login_required
def get_notifications(request):
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    data = []

    for n in unread_notifications:
        data.append({
            'id': n.id,
            'message': n.message,
            'link': n.link if n.link else "#"
        })

    return JsonResponse({
        'notifications': data,
        'unread_count': unread_notifications.count()
    })


# 🔥 Mark as read
@login_required
def mark_single_read(request, notif_id):
    try:
        notif = Notification.objects.get(id=notif_id, user=request.user)
    except Notification.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Notification not found.'
        }, status=404)

    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read'])

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        'status': 'success',
        'message': 'Notification marked as read.',
        'unread_count': unread_count
    })


@login_required
def get_chat_history(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.user != booking.customer and request.user != booking.service.vendor:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    messages = ChatMessage.objects.filter(booking=booking).order_by('-timestamp')[:50]
    data = []
    for msg in messages:
        data.append({
            'sender': msg.sender.username,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    return JsonResponse({'messages': data[::-1]})  # Oldest first for UI

@login_required
def chat_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.user != booking.customer and request.user != booking.service.vendor:
        return HttpResponseForbidden("You can only chat about your bookings/services.")
    
    other_user = booking.service.vendor if request.user == booking.customer else booking.customer
    context = {
        'booking': booking,
        'other_user': other_user,
        'service_title': booking.service.title
    }
    return render(request, 'chat.html', context)


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    total_users = User.objects.count()
    total_services = Service.objects.count()
    total_bookings = Booking.objects.count()

    # Revenue = only paid bookings
    revenue = Booking.objects.filter(payment_status='paid').aggregate(
        total=Sum('service__price')
    )['total'] or 0

    recent_bookings = Booking.objects.select_related('service', 'customer').order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_services': total_services,
        'total_bookings': total_bookings,
        'revenue': revenue,
        'recent_bookings': recent_bookings
    }

    return render(request, 'admin_dashboard.html', context)