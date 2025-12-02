import requests
import re
from bs4 import BeautifulSoup
from django.shortcuts import render
from django.contrib import messages
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
from io import BytesIO

from .forms import ScraperForm

def buscar(request):
    resultados = []
    palabra = ""

    # Obtener la palabra venga por POST (form) o por GET (?palabra=...)
    if request.method == "POST":
        form = ScraperForm(request.POST)
        if form.is_valid():
            palabra = form.cleaned_data.get("palabra", "").strip()
    else:
        # GET: puede venir como /scraper/?palabra=Python
        palabra = request.GET.get("palabra", "").strip()
        form = ScraperForm(initial={"palabra": palabra} if palabra else None)

    # Si no se creó el form por POST, asegurarnos de tenerlo
    if 'form' not in locals():
        form = ScraperForm()

    if palabra:
        # Normalizar para URL: espacios -> '_' y url-encode
        palabra_safe = palabra.replace(" ", "_")
        url = f"https://es.wikipedia.org/wiki/{palabra_safe}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; MiScraper/1.0; +http://example.com)"
            }
            respuesta = requests.get(url, headers=headers, timeout=8)
        except requests.RequestException as e:
            resultados.append({
                "titulo": palabra,
                "descripcion": f"Error al solicitar Wikipedia: {e}",
                "url": url
            })
        else:
            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.text, "html.parser")
                # Tomamos el primer párrafo no vacío
                parrafos = [p.get_text().strip() for p in soup.select("p") if p.get_text().strip()]
                descripcion = parrafos[0] if parrafos else "Sin información."
                resultados.append({
                    "titulo": palabra,
                    "descripcion": descripcion,
                    "url": url
                })
            elif respuesta.status_code == 404:
                resultados.append({
                    "titulo": palabra,
                    "descripcion": "No existe la página en Wikipedia.",
                    "url": url
                })
            else:
                resultados.append({
                    "titulo": palabra,
                    "descripcion": f"Respuesta inesperada: status {respuesta.status_code}",
                    "url": url
                })

    return render(request, "scraper/buscar.html", {
        "form": form,
        "resultados": resultados,
        "palabra": palabra
    })


def enviar_resultados(request):
    
    # datos recibidos por querystring (cuando se llamó desde la tabla de resultados)
    palabra = request.GET.get("palabra") or request.POST.get("palabra")
    descripcion = request.GET.get("descripcion") or request.POST.get("descripcion")
    url = request.GET.get("url") or request.POST.get("url")

    # Valor por defecto para el input destinatario: email del usuario logueado (si existe)
    default_dest = request.user.email if request.user.is_authenticated else ""

    if request.method == "POST":
        # El formulario envía un campo 'destinatarios' con emails separados por comas o punto y coma
        dest_text = request.POST.get("destinatarios", "").strip()
        # Normalizar: split por comas o punto y coma, quitar espacios vacíos
        destinatarios = [e.strip() for e in re.split(r"[;,]+", dest_text) if e.strip()]
        # Asegurarnos de que el usuario logueado reciba el mail (si tiene email)
        if request.user.is_authenticated and request.user.email:
            if request.user.email not in destinatarios:
                destinatarios.append(request.user.email)

        if not destinatarios:
            messages.error(request, "Ingresá al menos un correo destinatario.")
            return render(request, "scraper/enviar_form.html", {
                "palabra": palabra,
                "descripcion": descripcion,
                "url": url,
                "default_dest": dest_text
            })

        # Generar PDF en memoria
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        y = 750
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"Resultados Wikipedia: {palabra or 'Sin título'}")
        y -= 30
        p.setFont("Helvetica", 10)

        if descripcion:
            max_chars = 900
            text = descripcion[:max_chars]

            import textwrap
            lines = textwrap.wrap(text, width=90)
            for line in lines:
                if y < 80:
                    p.showPage()
                    y = 750
                    p.setFont("Helvetica", 10)
                p.drawString(50, y, line)
                y -= 14
        # agregar la URL al final
        if y < 120:
            p.showPage()
            y = 750
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, y-10, f"Fuente: {url or 'N/A'}")

        p.showPage()
        p.save()
        buffer.seek(0)
        pdf_bytes = buffer.read()
        buffer.close()

        # Enviar email con adjunto a todos los destinatarios
        subject = f"Resultados Wikipedia: {palabra or ''}"
        body = f"A continuación se adjunta el PDF con los resultados para: {palabra or ''}\n\nFuente: {url or ''}"
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        email.attach(f"wiki_{(palabra or 'resultados')}.pdf", pdf_bytes, "application/pdf")
        email.send()

        messages.success(request, f"PDF enviado a: {', '.join(destinatarios)}")
        return render(request, "scraper/enviado.html", {"palabra": palabra, "destinatarios": destinatarios})

    # GET: mostrar formulario con campo destinatarios
    return render(request, "scraper/enviar_form.html", {
        "palabra": palabra,
        "descripcion": descripcion,
        "url": url,
        "default_dest": default_dest
    })

def scraper_resultados(request):
    palabra = request.GET.get("palabra")
    descripcion = request.GET.get("descripcion")
    url = request.GET.get("url")

    return render(request, "scraper/resultados.html", {
        "palabra": palabra,
        "descripcion": descripcion,
        "url": url
    })