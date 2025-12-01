from django import forms

class ScraperForm(forms.Form):
    palabra = forms.CharField(label="Buscar en Wikipedia")