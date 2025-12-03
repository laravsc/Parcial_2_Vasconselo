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
    """Dashboard principal con métricas"""
    alumnos = Alumno.objects.filter(usuario=request.user)
    total_alumnos = alumnos.count()
    alumnos_recientes = alumnos.order_by('-created_at')[:5]
    
    # Si necesitas otros cálculos, puedes agregarlos aquí
    alumnos_activos = total_alumnos  # Por ahora, todos están activos
    pendientes = 0  # Puedes modificar esto según tu lógica
    
    return render(request, 'alumnos/dashboard.html', {
        'total_alumnos': total_alumnos,
        'alumnos_activos': alumnos_activos,
        'pendientes': pendientes,
        'alumnos_recientes': alumnos_recientes,
    })

@login_required
def gestion_alumnos(request):
    """Lista completa de alumnos"""
    alumnos = Alumno.objects.filter(usuario=request.user)
    return render(request, 'alumnos/gestion_alumnos.html', {'alumnos': alumnos})

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
            return redirect('alumnos:gestion_alumnos')
    else:
        form = AlumnoForm(instance=alumno)
    return render(request, 'alumnos/alumno_form.html', {'form': form, 'crear': False, 'alumno': alumno})

@login_required
def eliminar_alumno(request, pk):
    alumno = get_object_or_404(Alumno, pk=pk, usuario=request.user)
    if request.method == 'POST':
        alumno.delete()
        messages.success(request, 'Alumno eliminado.')
        return redirect('alumnos:gestion_alumnos')
    return render(request, 'alumnos/alumno_confirm_delete.html', {'alumno': alumno})

@login_required
def enviar_pdf(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id, usuario=request.user)

    # Generar PDF en memoria
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 800, "Ficha del Alumno")
    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Nombre: {alumno.nombre}")
    p.drawString(50, 750, f"Apellido: {alumno.apellido}")
    email_text = getattr(alumno, "email", "---")
    p.drawString(50, 730, f"Email: {email_text}")
    p.drawString(50, 710, f"Documento: {alumno.documento or 'No especificado'}")
    p.drawString(50, 690, f"Fecha Nacimiento: {alumno.fecha_nacimiento or 'No especificada'}")
    p.drawString(50, 670, f"Creado por: {request.user.username}")

    p.showPage()
    p.save()

    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Preparar correo
    subject = f"Ficha del Alumno - {alumno.nombre} {alumno.apellido}"
    body = f"Adjunto PDF con la ficha del alumno {alumno.nombre} {alumno.apellido}."
    from_email = None
    
    destinatarios = []
    if email_text and email_text != '---':
        destinatarios.append(email_text)
    if request.user.email and request.user.email not in destinatarios:
        destinatarios.append(request.user.email)

    if not destinatarios:
        messages.error(request, "No hay destinatarios válidos para enviar el PDF (sin email asociado).")
        return redirect("alumnos:gestion_alumnos")

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=destinatarios,
    )
    email.attach("alumno.pdf", pdf_bytes, "application/pdf")

    try:
        email.send(fail_silently=False)
    except BadHeaderError as e:
        logger.exception("BadHeaderError al enviar PDF: %s", e)
        messages.error(request, "Error enviando email: header inválido.")
        return redirect("alumnos:gestion_alumnos")
    except Exception as e:
        logger.exception("Error al enviar email con PDF: %s", e)
        messages.error(request, "Ocurrió un error al intentar enviar el email. Revisá la configuración SMTP.")
        messages.info(request, f"Detalle técnico: {str(e)}")
        return redirect("alumnos:gestion_alumnos")

    messages.success(request, f"PDF enviado a: {', '.join(destinatarios)}")
    return redirect("alumnos:gestion_alumnos")

