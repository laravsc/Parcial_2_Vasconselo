from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def dashboard_redirect(request):
    return render(request, 'dashboard_public.html')
