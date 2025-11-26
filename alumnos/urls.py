from django.urls import path
from . import views

app_name = 'alumnos'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # si ya la tenés
    path('crear/', views.crear_alumno, name='crear'),
    path('<int:pk>/editar/', views.editar_alumno, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_alumno, name='eliminar'),
    path('<int:pk>/enviar_pdf/', views.enviar_pdf_por_email, name='enviar_pdf'),
    # otras rutas...
]