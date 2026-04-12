from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Booking, Service
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

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

    Booking.objects.create(
        customer=request.user,
        service=service
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