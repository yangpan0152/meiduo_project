from django.conf.urls import url
from . import views

urlpatterns = [
    url('^qq/login/$', views.QQUrlView.as_view()),
    url('^oauth_callback$', views.QQOpenIdView.as_view()),
    url('^weibo/login/$', views.WeiBoUrlView.as_view()),
    url('^sina_callback$', views.WeiBoUidView.as_view()),

]