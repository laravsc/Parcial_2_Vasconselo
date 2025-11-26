from django.urls import path
from . import views

app_name = 'alumnos'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('crear/', views.crear_alumno, name='crear'),
    path('<int:pk>/editar/', views.editar_alumno, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_alumno, name='eliminar'),
]