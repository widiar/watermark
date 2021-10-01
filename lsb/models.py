from django.db import models

# Create your models here.
class ImageDummy(models.Model):
    name = models.CharField(max_length=100)
    file = models.ImageField(upload_to='ktp/')