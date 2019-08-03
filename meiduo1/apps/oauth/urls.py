from django.conf.urls import url
from . import views

urlpatterns = [
    url('^qq/login/$', views.QQUrlView.as_view()),
    url('^oauth_callback$', views.QQOpenIdView.as_view()),

]