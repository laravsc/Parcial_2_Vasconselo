from django.contrib import admin
from .models import Alumno

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'documento', 'email', 'usuario', 'created_at')
    search_fields = ('nombre', 'apellido', 'documento', 'email')
    list_filter = ('created_at',)