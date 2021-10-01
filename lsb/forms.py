from django import forms
from .models import *

class ImageForm(forms.ModelForm):
    class Meta:
        model = ImageDummy
        fields = '__all__'