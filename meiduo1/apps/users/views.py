from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render, redirect
import json, re
from django.middleware.csrf import CsrfViewMiddleware
from django_redis import get_redis_connection

from goods.models import SKU
from users import constants
from users.models import User, Address
from django.contrib.auth.mixins import LoginRequiredMixin
from celery_tasks.email.tasks import send_verify_email
from utils import meiduo_json


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 注册
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

        # 2 验证
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
        if password2 != password:
            return JsonResponse({'errmsg': '两次输入的密码不一致'})
        # 2.6 手机格式验证
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return JsonResponse({'errmsg': '请输入正确的手机号码'})
        # 2.7 手机号验重
        if User.objects.filter(mobile=mobile).count() > 0:
            return JsonResponse({'errmsg': '手机号已存在'})

        # 3 处理
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
        response = JsonResponse({'errmsg': 'ok'})
        response.set_cookie('username', username, max_age=60 * 60 * 24 * 14)
        # 4 响应
        # 合并购物车
        from carts.utils import merge_cart_cookie_to_redis
        response=merge_cart_cookie_to_redis(request,response)
        return response


# 注册时验证用户名
class UsernameView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'count': count})


# 注册时验证手机号
class MobileView(View):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'count': count})


# 登陆功能模块
# 1. 用户获取登陆界面
class LoginView(View):
    def get(self, request):
        context = {
            'username': '',
            'pwd': '',
            'loginerror': ''
        }
        return render(request, 'login.html', context)

    # 2. 逻辑处理用户登陆需求
    def post(self, request):
        # 接收
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')

        # 验证
        # 2.1
        # 非空
        if not all([username, pwd]):
            # 因为不是用axios发起的请求，所以就返回一个页面，前端给的login.html中有个{{ loginerror }},一看就是
            # 渲染个页面，带模板数据字典
            return render(request, 'login.html', {'loginerror': '数据不完整'})
        # 2.2格式匹配(因为是用的前端表单提交，所以不用再验证格式)

        # 3.处理----先查有没有这个人，有的话再看密码对不对
        # try:
        #     user = User.objects.get(username=username)
        # except:
        #     context = {
        #         'username': username,
        #         'pwd': pwd,
        #         'loginerror': '用户不存在',
        #     }
        #     return render(request, 'login.html',context)
        #
        # if user.check_password(pwd):
        #     login(request, user)
        #     return redirect('/')
        # else:
        #     context = {
        #         'username': username,
        #         'pwd': pwd,
        #         'loginerror': '密码不正确'
        #     }
        #     return render(request, 'login.html', context)

        user = authenticate(username=username, password=pwd)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/index/')
            response = redirect(next_url)
            response.set_cookie('username', username, max_age=60 * 60 * 24 * 14)
            # 合并购物车
            from carts.utils import merge_cart_cookie_to_redis
            response=merge_cart_cookie_to_redis(request, response)

            return response
        else:
            context = {
                'username': username,
                'pwd': pwd,
                'loginerror': '用户不存在或者密码错误',
            }
            return render(request, 'login.html', context)

            # 响应



class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect('/index/')
        response.set_cookie('username', '', max_age=0)
        return response


class CenterView(LoginRequiredMixin, View):
    def get(self, request):
        # if request.user.is_authenticated:
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect('/login/')
        user = request.user
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'email': user.email,
            'email_active': user.email_active,
        }
        return render(request, 'user_center_info.html', context)


# 添加邮箱
class EmailView(LoginRequiredMixin, View):
    def put(self, request):  # put&post请求提交的数据放在请求体
        # 接收
        data_dict = json.loads(request.body.decode())
        email = data_dict.get('email')

        # 验证  非空和格式
        if not all([email]):
            return render(request, 'user_center_info.html', {'errmsg': '邮箱不能为空'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user_center_info.html', {'errmsg': '邮箱格式错误'})
        # 处理  添加邮箱修改用户email属性值
        user = request.user
        user.email = email
        user.save()
        # 发送验证码到邮箱激活,用celery来执行,QS中带有user.id，目的是让后端知道要激活哪个用户的邮箱，因为激活邮件可能很久才会发过来。
        user_params = meiduo_json.dumps({'user_id': user.id}, constants.EMAIL_EXPIRES)
        url = '%s?token=%s' % (settings.EMAIL_VERIFY_URL, user_params)
        send_verify_email.delay(email, url)

        # 响应
        return JsonResponse({'code': 0})


# 验证邮箱
class EmailVerifyView(View):
    def get(self, request):
        # 接收 #验证接收token，解密，获得user_id,找到用户，修改邮件激活属性
        token = request.GET.get('token')
        user_params = meiduo_json.loads(token, constants.EMAIL_EXPIRES)
        if user_params is None:
            return HttpResponse('激活信息过期，请重新发邮件')
        user_id = user_params.get('user_id')
        # 处理
        user = User.objects.get(pk=user_id)
        user.email_active = True
        user.save()
        # 响应
        return redirect('/info/')


# 返回收货地址页面
class AddressesView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_site.html')


class AddressesAddView(LoginRequiredMixin, View):
    def post(self, request):
        # 接收
        param_dict = json.loads(request.body.decode())
        title = param_dict.get('title')
        receiver = param_dict.get('receiver')
        province_id = param_dict.get('province_id')
        city_id = param_dict.get('city_id')
        district_id = param_dict.get('district_id')
        place = param_dict.get('place')
        mobile = param_dict.get('mobile')
        tel = param_dict.get('tel')
        email = param_dict.get('email')
        # 验证
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 1, 'errmsg': '信息不完整'})
        # 处理 新建地址记录
        address = Address.objects.create(
            user_id=request.user.id,
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        # 响应
        return JsonResponse({
            'code': 0,
            'address': address.to_dict()
        })

# 编辑收货地址
class AddressEditView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        # 接收
        param_dict = json.loads(request.body.decode())
        title = param_dict.get('title')
        receiver = param_dict.get('receiver')
        province_id = param_dict.get('province_id')
        city_id = param_dict.get('city_id')
        district_id = param_dict.get('district_id')
        place = param_dict.get('place')
        mobile = param_dict.get('mobile')
        tel = param_dict.get('tel')
        email = param_dict.get('email')

        # 验证
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 1, 'errmsg': '信息不完整'})

        # 处理
        # 1.查询当前需要修改的收货地址
        address = Address.objects.get(pk=address_id)
        # 2.逐个属性赋值
        address.title = title
        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.place = place
        address.mobile = mobile
        address.tel = tel
        address.email = email
        # 3.保存
        address.save()

        # 响应
        return JsonResponse({
            'code': 0,
            'address': address.to_dict()
        })

    def delete(self, request, address_id):
        # 查询
        address = Address.objects.get(pk=address_id)

        # 删除：逻辑删除===》修改
        address.is_deleted = True
        address.save()

        # 响应
        return JsonResponse({'code': 0})


class AddressDefaultView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        user = request.user
        user.default_address_id = address_id
        user.save()
        return JsonResponse({'code': 0})


class AddressTitleView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        title = json.loads(request.body.decode()).get('title')

        if not all([title]):
            return JsonResponse({'code': 1, 'errmsg': '标题不能为空'})

        address = Address.objects.get(pk=address_id)
        address.title = title
        address.save()

        return JsonResponse({'code': 0})


class PasswordView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        # 接收
        param_dict = request.POST
        old_pwd = param_dict.get('old_pwd')
        new_pwd = param_dict.get('new_pwd')
        new_cpwd = param_dict.get('new_cpwd')

        user = request.user

        # 验证
        if not all([old_pwd, new_pwd, new_cpwd]):
            return render(request, 'user_center_pass.html')
        # 正则表达式验证
        if new_pwd != new_cpwd:
            return render(request, 'user_center_pass.html')
        if old_pwd == new_pwd:
            return render(request, 'user_center_pass.html')
        if not user.check_password(old_pwd):
            return render(request, 'user_center_pass.html')

        # 处理
        user.set_password(new_pwd)
        user.save()

        # 响应:重新登录
        # return render(request, 'user_center_pass.html')
        logout(request)
        response = redirect('/login/')
        response.set_cookie('username', max_age=0)
        return response



class BrowseSKUView(LoginRequiredMixin, View):
    def post(self, request):#存浏览记录
        sku_id = json.loads(request.body.decode()).get('sku_id')

        user_id = request.user.id

        if not all([sku_id]):
            return JsonResponse({'errmsg': '数据不完整'})

        redis_cli = get_redis_connection('browse_history')
        # 删除
        redis_cli.lrem(user_id, 0, sku_id)

        # 添加
        redis_cli.lpush(user_id, sku_id)

        # 长度判断
        if redis_cli.llen(user_id) > 5:
            # 删除最后
            redis_cli.rpop(user_id)

        return JsonResponse({'code': 0})

    def get(self, request):#查询浏览记录
        # 处理
        # 查询到浏览记录列表
        user_id = request.user.id
        redis_cli = get_redis_connection('browse_history')
        sku_ids = redis_cli.lrange(user_id, 0, -1)

        # 拿出实例
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=int(sku_id))
            skus.append({
                'id': sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'price': sku.price,
            })



        # 返回字典
        return JsonResponse({'skus': skus})

