from django import forms
from .models import *

class ImageForm(forms.ModelForm):
    class Meta:
        model = ImageDummy
        fields = '__all__'
        error_messages = {
            'name': {
                'max_length': "Teks Watermark tidak boleh lebih dari 100 karakter.",
            },
        }
    
    visible = forms.IntegerField()