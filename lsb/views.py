from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from .forms import *
from .models import *
from django.conf import settings
import os
import numpy as np
import binascii
from time import time

# Create your views here.
class HalamanDepanView(View):
    template_name = 'index.html'
    form_class = ImageForm

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            file = form.save()
            media_dir = settings.MEDIA_ROOT
            # print(datetime.now())
            namefile = "dummy" + str(time()) + ".jpg"
            file_path = os.path.join(media_dir, namefile)
            img = open(file.file.path, "r")
            byteFile = np.fromfile(img, dtype=np.ubyte) # dapetin hasil byte int8 
            img.close()
            # CONVERT BINARY TO HEX
            #looping untuk mendapatkan seluruh hasil biner kemudian di konvert ke hexa
            hexa = ''
            biner = ''
            for x in byteFile:
                biner += f'{x:08b}' + ' '
                zz = hex(x)[2:]
                if len(zz) < 2:
                    zz = '0'+zz
                hexa += zz
            #----------
            with open(file_path, 'wb') as f:
                f.write(binascii.unhexlify(hexa))
            
            os.remove(file.file.path)
            ImageDummy.objects.get(id=file.id).delete()

            return JsonResponse({
                "data": settings.MEDIA_URL + namefile
            })
        else:
             return JsonResponse({
                "data": form.errors
            })
            