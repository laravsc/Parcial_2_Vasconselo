import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
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

    palabra = request.GET.get("palabra")
    descripcion = request.GET.get("descripcion")
    url = request.GET.get("url")

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750

    p.setFont("Helvetica", 14)
    p.drawString(50, y, f"Resultados Wikipedia: {palabra}")

    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(50, y, descripcion[:900])

    y -= 40
    p.drawString(50, y, f"URL: {url}")

    p.showPage()
    p.save()
    buffer.seek(0)

    email = EmailMessage(
        subject="Resultados de Wikipedia",
        body=f"Aquí están los resultados para la palabra: {palabra}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.user.email],
    )

    email.attach(f"wiki_{palabra}.pdf", buffer.read(), "application/pdf")
    email.send()

    return render(request, "scraper/enviado.html")

def scraper_resultados(request):
    palabra = request.GET.get("palabra")
    descripcion = request.GET.get("descripcion")
    url = request.GET.get("url")

    return render(request, "scraper/resultados.html", {
        "palabra": palabra,
        "descripcion": descripcion,
        "url": url
    })