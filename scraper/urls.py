from django.urls import path
from . import views

app_name = "scraper"

urlpatterns = [
    path("", views.buscar, name="buscar"),
    path("resultados/", views.scraper_resultados, name="resultados"),
    path("enviar/", views.enviar_resultados, name="enviar"),
]