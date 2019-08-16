from django.conf.urls import url
from . import views

urlpatterns = [
url(r'^orders/settlement/$', views.OrderSettleView.as_view()),
url(r'^orders/commit/$', views.OrderCommitView.as_view()),
url(r'^orders/success/$', views.SuccessView.as_view()),
]