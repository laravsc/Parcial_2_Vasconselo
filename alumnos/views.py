from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Alumno
from .forms import AlumnoForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.core.mail import EmailMessage
from io import BytesIO

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

@login_required
def enviar_pdf(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id, usuario=request.user)

    # Crear PDF en memoria
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    p.setFont("Helvetica", 14)
    p.drawString(50, 800, "Ficha del Alumno")
    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Nombre: {alumno.nombre}")
    p.drawString(50, 750, f"Apellido: {alumno.apellido}")
    p.drawString(50, 730, f"Email: {alumno.email if hasattr(alumno, 'email') else '---'}")
    p.drawString(50, 710, f"Creado por: {request.user.username}")

    p.showPage()
    p.save()

    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()

    # Enviar email al docente
    email = EmailMessage(
        subject="PDF del alumno",
        body="Adjunto PDF del alumno solicitado.",
        from_email="noreply@miapp.com",
        to=["ematevez@gmail.com"],
    )
    email.attach("alumno.pdf", pdf, "application/pdf")
    email.send()

    messages.success(request, "PDF enviado correctamente al docente.")
    return redirect("dashboard")