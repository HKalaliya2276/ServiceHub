from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Booking, Service

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
    return render(request, 'service_list.html', {'services': services})


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