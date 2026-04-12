from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import UserRegisterForm
from django.contrib.auth import logout

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard') 
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_redirect(request):
    user = request.user

    if user.role == 'customer':
        return redirect('customer_dashboard')

    elif user.role == 'vendor':
        return redirect('vendor_dashboard')

    elif user.role == 'delivery':
        return redirect('delivery_dashboard')

    return redirect('login')


@login_required
def customer_dashboard(request):
    return render(request, 'customer_dashboard.html')


@login_required
def vendor_dashboard(request):
    return render(request, 'vendor_dashboard.html')


@login_required
def delivery_dashboard(request):
    deliveries = request.user.deliveries.all()
    return render(request, 'delivery_dashboard.html', {'deliveries': deliveries})