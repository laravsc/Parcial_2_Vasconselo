from django import forms
from .models import Alumno

class AlumnoForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'documento', 'email', 'fecha_nacimiento']