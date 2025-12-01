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

    if request.method == "POST":
        form = ScraperForm(request.POST)
        if form.is_valid():
            palabra = form.cleaned_data["palabra"]
            url = f"https://es.wikipedia.org/wiki/{palabra}"
            
            respuesta = requests.get(url)

            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.text, "html.parser")

                parrafos = soup.select("p")
                texto = parrafos[0].get_text().strip() if parrafos else "Sin información."

                resultados.append({
                    "titulo": palabra,
                    "descripcion": texto,
                    "url": url
                })
    else:
        form = ScraperForm()

    return render(request, "scraper/buscar.html", {"form": form, "resultados": resultados})


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