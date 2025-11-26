import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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

@login_required
def enviar_pdf_por_email(request, pk):
    """
    Solo acepta POST para evitar que un simple GET dispare envíos.
    Genera PDF en memoria y lo adjunta al email.
    """
    alumno = get_object_or_404(Alumno, pk=pk, usuario=request.user)

    if request.method != 'POST':
        messages.error(request, "Acción no permitida.")
        return redirect('alumnos:dashboard')

    # Generar PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 80, "Ficha del Alumno")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 120, f"Nombre: {alumno.nombre}")
    p.drawString(50, height - 140, f"Apellido: {alumno.apellido}")
    if alumno.documento:
        p.drawString(50, height - 160, f"Documento: {alumno.documento}")
    if alumno.email:
        p.drawString(50, height - 180, f"Email: {alumno.email}")
    if alumno.fecha_nacimiento:
        p.drawString(50, height - 200, f"Fecha de Nacimiento: {alumno.fecha_nacimiento.strftime('%Y-%m-%d')}")

    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 50, f"Generado por: {request.user.username}")
    p.showPage()
    p.save()
    buffer.seek(0)

    # Preparar destinatario (por defecto al usuario si alumno no tiene email)
    destinatario = [alumno.email] if alumno.email else [request.user.email]

    subject = f"Ficha PDF: {alumno.nombre} {alumno.apellido}"
    body = f"Adjunto el PDF con la ficha del alumno {alumno.nombre} {alumno.apellido}."

    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, destinatario)
    email.attach(f"alumno_{alumno.pk}.pdf", buffer.getvalue(), "application/pdf")

    try:
        email.send(fail_silently=False)
        messages.success(request, "PDF generado y enviado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al enviar email: {e}")

    buffer.close()
    return redirect('alumnos:dashboard')