from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Alumno
from .forms import AlumnoForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.core.mail import EmailMessage, BadHeaderError
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

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
    """
    Genera PDF en memoria con la info del alumno y lo envía por email.
    - Corrige el redirect a 'alumnos:dashboard'
    - Maneja excepciones de email y las informa con messages + logger
    """
    # Asegurarse que el alumno exista y pertenezca al usuario
    alumno = get_object_or_404(Alumno, id=alumno_id, usuario=request.user)

    # --- Generar PDF en memoria ---
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 800, "Ficha del Alumno")
    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Nombre: {alumno.nombre}")
    p.drawString(50, 750, f"Apellido: {alumno.apellido}")
    email_text = getattr(alumno, "email", "---")
    p.drawString(50, 730, f"Email: {email_text}")
    p.drawString(50, 710, f"Creado por: {request.user.username}")

    p.showPage()
    p.save()

    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # --- Preparar correo ---
    subject = "PDF del alumno"
    body = f"Adjunto PDF de la ficha del alumno {alumno.nombre} {alumno.apellido}."
    from_email = None  # dejar que Django tome DEFAULT_FROM_EMAIL
    # Destinatarios: usar el correo del alumno si existe, sino el del usuario
    destinatarios = []
    if email_text and email_text != '---':
        destinatarios.append(email_text)
    if request.user.email and request.user.email not in destinatarios:
        destinatarios.append(request.user.email)

    if not destinatarios:
        # Si no hay a quién enviar, informamos y volvemos al dashboard
        messages.error(request, "No hay destinatarios válidos para enviar el PDF (sin email asociado).")
        return redirect("alumnos:dashboard")

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=destinatarios,
    )
    email.attach("alumno.pdf", pdf_bytes, "application/pdf")

    # --- Intentar enviar y manejar errores ---
    try:
        email.send(fail_silently=False)
    except BadHeaderError as e:
        logger.exception("BadHeaderError al enviar PDF: %s", e)
        messages.error(request, "Error enviando email: header inválido.")
        return redirect("alumnos:dashboard")
    except Exception as e:
        # Loguear error y mostrar mensaje claro al usuario
        logger.exception("Error al enviar email con PDF: %s", e)
        messages.error(request, "Ocurrió un error al intentar enviar el email. Revisá la configuración SMTP.")
        # opcional: mostrar mensaje con detalles mínimos en dev (no desplegar en prod)
        messages.info(request, f"Detalle técnico: {str(e)}")
        return redirect("alumnos:dashboard")

    # Si llegamos acá, fue enviado (o al menos el backend no lanzó excepción)
    messages.success(request, f"PDF enviado a: {', '.join(destinatarios)}")
    return redirect("alumnos:dashboard")

