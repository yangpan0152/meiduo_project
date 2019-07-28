from django.contrib.auth import login
from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
import json, re
from django.middleware.csrf import CsrfViewMiddleware
from users.models import User


class RegisterView(View):
    def get(self,request):
        return render(request, 'register.html')

    def post(self,request):
        #注册
        # 1.接收
        # {"username":"py111","password":"1234567890","password2":"1234567890",
        # "mobile":"13123456789","sms_code":"123456","allow":true}
        params = json.loads(request.body.decode())
        username = params.get('username')
        password = params.get('password')
        password2 = params.get('password2')
        mobile = params.get('mobile')
        sms_code = params.get('sms_code')
        allow = params.get('allow')

        #2 验证
        # 2.1非空
        if not all([username, password, password2, mobile, sms_code, allow]):
            return JsonResponse({'errmsg': '数据不完整'})
        # 2.2格式匹配
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'errmsg': '请输入5-20个字符的用户名'})
        # 2.3用户名是否重复
        if User.objects.filter(username=username).count() > 0:
            return JsonResponse({'errmsg': '用户名已存在'})
        # 2.4 密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'errmsg': '请输入8-20位的密码'})
        # 2.5 密码核对
        if password2!=password:
            return JsonResponse({'errmsg': '两次输入的密码不一致'})
        # 2.6 手机格式验证
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return JsonResponse({'errmsg': '请输入正确的手机号码'})
        #2.7 手机号验重
        if User.objects.filter(mobile=mobile).count() > 0:
            return JsonResponse({'errmsg': '手机号已存在'})

        #3 处理
        # User.objects.create(
        #     username=username,
        #     password=password,
        #     mobile=mobile
        # )
        # 3.1 注册
        user = User.objects.create_user(
            username=username,
            password=password,
            mobile=mobile
        )
        # 3.2 保持登陆状态
        # request.session['user_id'] = user.id
        login(request, user)
        #4 响应

        return JsonResponse({'errmsg': 'ok'})


class UsernameView(View):
    def get(self,request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'count':count})


class MobileView(View):
    def get(self,request,mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'count': count})
