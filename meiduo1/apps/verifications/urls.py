from django.conf.urls import url
from . import views

urlpatterns = [
 url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageView.as_view()),
]