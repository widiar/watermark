from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from .forms import *
from .models import *
from django.conf import settings
import os
from time import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import cv2
import numpy as np
import pytesseract

def isValid(s):
    return len(s) == len(s.encode())

# Create your views here.
class HalamanDepanView(View):
    template_name = 'index.html'
    form_class = ImageForm

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            teks = form.cleaned_data['name']
            visible = form.cleaned_data['visible']
            file = form.save()
            media_dir = settings.MEDIA_ROOT
            namefile = "dummy" + str(time()) + ".png"
            file_path = os.path.join(media_dir, namefile)

            #cek valid ktp
            img = np.array(Image.open(file.file.path))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            th, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
            pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/bin/tesseract'
            result = pytesseract.image_to_string((threshed), lang="ind")
            if "NIK" in result and "Nama" in result and "Tempat/Tgi Lahir" in result:
                print("Valid")
            else:
                os.remove(file.file.path)
                ImageDummy.objects.get(id=file.id).delete()
                return JsonResponse({
                    "status": 401
                })

            if visible == 1:
                #convert teks ke image
                pathWatermark = os.path.join(media_dir, 'watermark' + str(time()) + ".png")
                imageWatermark = Image.new('RGBA', (len(teks) * 25, 80), color=(0, 0, 0,0))
                drawImage = ImageDraw.Draw(imageWatermark)
                urlFont = 'https://github.com/widiar/watermark/blob/main/font/Montserrat-Bold.ttf?raw=true'
                reqFont = requests.get(urlFont)
                font = ImageFont.truetype(BytesIO(reqFont.content), size=32)
                drawImage.text((10, 10), teks, font=font, fill=(255, 255, 255))
                imageWatermark.save(pathWatermark)

                #insert image watermark
                alpha = 0.1
                beta = 1-alpha
                watermark = cv2.imread(pathWatermark, cv2.IMREAD_UNCHANGED)
                (wH, wW) = watermark.shape[:2]
                (B, G, R, A) = cv2.split(watermark)
                B = cv2.bitwise_and(B, B, mask=A)
                G = cv2.bitwise_and(G, G, mask=A)
                R = cv2.bitwise_and(R, R, mask=A)
                watermark = cv2.merge([B, G, R, A])

                image = cv2.imread(file.file.path)
                (h, w) = image.shape[:2]
                image = np.dstack([image, np.ones((h, w), dtype="uint8") * 255])
                overlay = np.zeros([h, w, 4], dtype="uint8")
                overlay[h - wH - 10:h - 10, w - wW - 10:w-10] = watermark

                output = image.copy()
                cv2.addWeighted(overlay, alpha, output, beta, 0, output)
                cv2.imwrite(file.file.path, output)
                cv2.destroyAllWindows()

                print(file.file.path, pathWatermark)

                os.remove(pathWatermark)

            # CONVERT TEKS TO BINER
            teks += ']'
            teksBiner = ''
            for x in bytearray(teks, "utf8"):
                teksBiner += f'{x:08b}'

            # MEMBACA PIXEL IMAGE MENJADI BINER DAN MENGGABUNGKAN DENGAN TEKSBINER
            indexTeksBiner = 0
            ktp = Image.open(file.file.path)
            ktpImageData = list(ktp.getdata())
            for i in range(0, len(ktpImageData)):
                tmpPixel = ktpImageData[i]
                tmpListTuple = []
                for j in tmpPixel:
                    if indexTeksBiner < len(teksBiner):
                        tmpBiner = f'{j:08b}'
                        newPixel = int(tmpBiner[:-1] + teksBiner[indexTeksBiner], 2)
                        tmpListTuple.append(newPixel)
                        indexTeksBiner += 1
                    elif len(tmpListTuple) < 3:
                        tmpListTuple.append(j)
                
                if tmpListTuple:
                    ktpImageData[i] = tuple(tmpListTuple)

            newKtp = Image.new(ktp.mode, ktp.size)
            newKtp.putdata(ktpImageData)
            newKtp.save(file_path, quality=100)
            
            os.remove(file.file.path)
            ImageDummy.objects.get(id=file.id).delete()

            return JsonResponse({
                "status": 200,
                "data": settings.MEDIA_URL + namefile
            })
        else:
             return JsonResponse({
                "status": 400,
                "data": form.errors
            })



class ReadKTPView(View):
    template_name = 'index.html'
    form_class = ImageForm

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            file = form.save()

            ktpImage = Image.open(file.file.path)
            ktpImageData = list(ktpImage.getdata())

            # READ BINER DI PIXEL KTP
            index = 0
            tmpText = ''
            textBiner = []
            stop = False
            for i in range(0, len(ktpImageData)):
                pixel = ktpImageData[i]
                for p in pixel:
                    binerPixel = f'{p:08b}'
                    if index == 8:
                        textBiner.append(tmpText)
                        if tmpText == '01011101':
                            stop = True
                        tmpText = ''
                        index = 0
                    tmpText += binerPixel[-1]
                    index += 1
                if stop:
                    break
            
            teks = ''
            for t in textBiner:
                teks += chr(int(t, 2))
            if(isValid(teks[:-1])):
                textWatermark = teks[:-1]
            else:
                textWatermark = "Tidak dapat menemukan teks watermark"

            os.remove(file.file.path)
            ImageDummy.objects.get(id=file.id).delete()
            return JsonResponse({
                "data": textWatermark
            })
        else:
             return JsonResponse({
                "data": form.errors
            })

def deleteAfterClick(request):
    if request.method == 'POST':
        media_dir = settings.MEDIA_ROOT
        nameFile = request.POST.get('filename')
        file_path = os.path.join(media_dir, nameFile)
        os.remove(file_path)
        return JsonResponse({
            'status': 200
        })