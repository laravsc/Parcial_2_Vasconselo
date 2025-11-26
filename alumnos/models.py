from django.db import models
from django.contrib.auth.models import User

class Alumno(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alumnos')
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    documento = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.documento or 'sin doc'})"