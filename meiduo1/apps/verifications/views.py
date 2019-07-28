from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from libs.captcha.captcha import captcha


class ImageView(View):
    def get(self, request, uuid):
        name, text, image = captcha.generate_captcha()

        return HttpResponse(image, content_type='image/png')
