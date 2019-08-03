from django.conf.urls import url
from . import views

urlpatterns = [
 url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageView.as_view()),
 url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SmsView.as_view()),
]