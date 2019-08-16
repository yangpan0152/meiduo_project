from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view()),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileView.as_view()),
    url(r'^login/$', views.LoginView.as_view()),
    url(r'^logout/$', views.LogoutView.as_view()),
    url(r'^info/$', views.CenterView.as_view()),
    url(r'^emails/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.EmailVerifyView.as_view()),
    url(r'^addresses/$', views.AddressesView.as_view()),
    url(r'^addresses/create/$', views.AddressesAddView.as_view()),
    url('^addresses/(?P<address_id>\d+)/$', views.AddressEditView.as_view()),
    url('^addresses/(?P<address_id>\d+)/default/$', views.AddressDefaultView.as_view()),
    url('^addresses/(?P<address_id>\d+)/title/$', views.AddressTitleView.as_view()),
    url('^password/$', views.PasswordView.as_view()),
    url('^browse_histories/$', views.BrowseSKUView.as_view()),

]