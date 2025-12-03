from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistroForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

def registro(request):
    form = RegistroForm()
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registro exitoso. Ahora podés iniciar sesión.")
            return redirect('accounts:login')

    return render(request, 'accounts/registro.html', {'form': form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        request.session.flush()
        return redirect('accounts:login')

    return redirect('accounts:login')