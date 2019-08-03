import re
from django.contrib.auth.backends import ModelBackend
from django.shortcuts import render, redirect

from users.models import User


class Meiduo_Auth_Backend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if re.match(r'^1[345789]\d{9}$', username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except:
            return None
        else:
            if user.check_password(password):
                return user
            else:
                return None
