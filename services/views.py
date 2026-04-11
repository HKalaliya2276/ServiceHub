from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Service

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