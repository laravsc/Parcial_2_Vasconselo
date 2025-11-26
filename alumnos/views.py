from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Alumno
from .forms import AlumnoForm

@login_required
def dashboard(request):
    alumnos = Alumno.objects.filter(usuario=request.user)
    return render(request, 'alumnos/dashboard.html', {'alumnos': alumnos})

@login_required
def crear_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.usuario = request.user
            alumno.save()
            messages.success(request, 'Alumno creado correctamente.')
            return redirect('alumnos:dashboard')
    else:
        form = AlumnoForm()
    return render(request, 'alumnos/alumno_form.html', {'form': form, 'crear': True})

@login_required
def editar_alumno(request, pk):
    alumno = get_object_or_404(Alumno, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = AlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alumno actualizado correctamente.')
            return redirect('alumnos:dashboard')
    else:
        form = AlumnoForm(instance=alumno)
    return render(request, 'alumnos/alumno_form.html', {'form': form, 'crear': False, 'alumno': alumno})

@login_required
def eliminar_alumno(request, pk):
    alumno = get_object_or_404(Alumno, pk=pk, usuario=request.user)
    if request.method == 'POST':
        alumno.delete()
        messages.success(request, 'Alumno eliminado.')
        return redirect('alumnos:dashboard')
    return render(request, 'alumnos/alumno_confirm_delete.html', {'alumno': alumno})