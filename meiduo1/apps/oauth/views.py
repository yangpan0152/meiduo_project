from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from weibo import APIClient

from users.models import User
from utils import meiduo_json
from .models import OAuthQQUser, OAuthWeiBoUser
from . import constants


class QQUrlView(View):
    def get(self, request):
        # 获取登录成功后的转向地址
        state = request.GET.get('next', '/')
        # 生成授权地址
        oauthqq = OAuthQQ(
            settings.QQ_CLIENT_ID,
            settings.QQ_CLIENT_SECRET,
            settings.QQ_REDIRECT_URI,
            state
        )
        url = oauthqq.get_qq_url()

        return JsonResponse({'login_url': url})


class QQOpenIdView(View):
    def get(self, request):
        # 获取登录成功后的转向地址
        state = request.GET.get('state', '/')
        # 生成授权地址
        oauthqq = OAuthQQ(
            settings.QQ_CLIENT_ID,
            settings.QQ_CLIENT_SECRET,
            settings.QQ_REDIRECT_URI,
            state
        )
        # 获取授权账号的openid
        code = request.GET.get('code')
        # 利用QQtool的方法发送请求获得token
        token = oauthqq.get_access_token(code)
        # 同上获得openid
        openid = oauthqq.get_open_id(token)
        # return JsonResponse({'openid': openid})

        # 检查是否存有这个openid，有就直接给首页，没有就返回一个绑定页面
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except:
            # 加密
            token = meiduo_json.dumps({'openid': openid}, constants.OPENID_EXPIRES)
            # 返回绑定页面和openid
            return render(request, 'oauth_callback.html', {'token': token})
        else:  # 非初次授权，就保持登陆，给个首页
            login(request, qq_user.user)
            response = redirect(request.GET.get('state', '/'))
            response.set_cookie('username', qq_user.user.username, max_age=60 * 60 * 24 * 14)
            # 合并购物车
            from carts.utils import merge_cart_cookie_to_redis
            response = merge_cart_cookie_to_redis(request, response)
            return response

    def post(self, request):
        # 用户在绑定用户页面点击保存按钮，前端发起一个axios请求，提供手机号，密码，短信验证码，openid
        # 接收
        param_dict = request.POST
        mobile = param_dict.get('mobile')
        pwd = param_dict.get('pwd')
        sms_request = param_dict.get('sms_code')
        token = param_dict.get('access_token')
        # 验证
        data_dict = meiduo_json.loads(token, constants.OPENID_EXPIRES)
        if data_dict is None:
            return render(request, 'oauth_callback.html', {'errmsg': 'qq授权已过期'})
        openid = data_dict.get('openid')
        # 处理
        # 根据手机号查询用户实例，
        try:
            user = User.objects.get(mobile=mobile)
        except:
            #   如果不存在则新建用户，绑定
            user = User.objects.create_user(mobile, password=pwd, mobile=mobile)
        else:
            #   如果存在则验证密码，
            if not user.check_password(pwd):
                #       如果错误则提示
                # return JsonResponse({'errmsg': '手机号存在，密码错误'}),并把openid返回去。
                return render(request, 'oauth_callback.html', {'errmsg': '手机号存在，密码错误', 'token': token})
                #   如果正确则绑定
                # 绑定，在OAuthQQUser这张表上创建一个实例，方便以后直接用QQ登陆。
        OAuthQQUser.objects.create(user_id=user.id, openid=openid)
        # 响应
        login(request, user)
        response = redirect(request.GET.get('state', '/'))
        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)
        # 合并购物车
        from carts.utils import merge_cart_cookie_to_redis
        response = merge_cart_cookie_to_redis(request, response)
        return response


class WeiBoUrlView(View):
    def get(self, request):
        # 获取登录成功后的转向地址
        state = request.GET.get('next', '/')
        # 生成授权地址
        client = APIClient(app_key=settings.APP_KEY, app_secret=settings.APP_SECRET,
                           redirect_uri=settings.REDIRECT_URL)
        login_url = client.get_authorize_url()

        return JsonResponse({'login_url': login_url})


class WeiBoUidView(View):
    def get(self, request):
        # 获取登录成功后的转向地址
        state = request.GET.get('state', '/')
        # 生成授权地址
        client = APIClient(app_key=settings.APP_KEY, app_secret=settings.APP_SECRET,
                           redirect_uri=settings.REDIRECT_URL)

        # 验证

        # 处理 获得uid,查询是否有这个user_id，
        code = request.GET.get('code')
        result = client.request_access_token(code)
        access_token = result.access_token
        uid = result.uid
        try:
            weibo_user = OAuthWeiBoUser.objects.get(uid=uid)
        except:
            # 加密
            token = meiduo_json.dumps({'uid': uid}, constants.UID_EXPIRES)
            # 返回绑定页面和openid
            return render(request, 'oauth_callback.html', {'token': token})
        else:  # 非初次授权，就保持登陆，给个首页
            login(request, weibo_user.user)
            response = redirect(request.GET.get('state', '/'))
            response.set_cookie('username', weibo_user.user.username, max_age=60 * 60 * 24 * 14)
            # 合并购物车
            from carts.utils import merge_cart_cookie_to_redis
            response = merge_cart_cookie_to_redis(request, response)
            return response

    def post(self, request):
        # 用户在绑定用户页面点击保存按钮，前端发起一个axios请求，提供手机号，密码，短信验证码，openid
        # 接收
        param_dict = request.POST
        mobile = param_dict.get('mobile')
        pwd = param_dict.get('pwd')
        sms_request = param_dict.get('sms_code')
        token = param_dict.get('access_token')
        # 验证
        data_dict = meiduo_json.loads(token, constants.OPENID_EXPIRES)
        if data_dict is None:
            return render(request, 'oauth_callback.html', {'errmsg': 'weibo授权已过期'})
        uid = data_dict.get('uid')
        # 处理
        # 根据手机号查询用户实例，
        try:
            user = User.objects.get(mobile=mobile)
        except:
            #   如果不存在则新建用户，绑定
            user = User.objects.create_user(mobile, password=pwd, mobile=mobile)
        else:
            #   如果存在则验证密码，
            if not user.check_password(pwd):
                #       如果错误则提示
                # return JsonResponse({'errmsg': '手机号存在，密码错误'}),并把openid返回去。
                return render(request, 'oauth_callback.html', {'errmsg': '手机号存在，密码错误', 'token': token})
                #   如果正确则绑定
                # 绑定，在OAuthQQUser这张表上创建一个实例，方便以后直接用QQ登陆。
        OAuthWeiBoUser.objects.create(user_id=user.id, uid=uid)
        # 响应
        login(request, user)
        response = redirect(request.GET.get('state', '/'))
        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)
        # 合并购物车
        from carts.utils import merge_cart_cookie_to_redis
        response = merge_cart_cookie_to_redis(request, response)
        return response




# class WeiBoUidView(View):
#     def get(self,request):
#         #接收
#         code = request.GET.get('code')
#         client = APIClient(app_key=settings.APP_KEY, app_secret=settings.APP_SECRET,
#                                    redirect_uri=settings.REDIRECT_URL)
#         # 获取登录成功后的转向地址
#         state = request.GET.get('state', '/')
#
#         #验证
#
#         #处理 获得uid,查询是否有这个user_id，
#         result = client.request_access_token(code)
#         access_token = result.access_token
#         uid = result.uid
#
#         try:
#             weibo_user = OAuthWeiBoUser.objects.get(uid=uid)
#         except:#处理 无则返回access_token
#             return JsonResponse({'access_token':uid,})
#
#         else:#查询绑定用户，构造数据
#             user=weibo_user.user
#             #响应
#             return JsonResponse({
#                 'user_id':user.id,
#                 'username': user.username,
#                 'token':uid,
#             })
#
#     def post(self, request):
#
# # 用户在绑定用户页面点击保存按钮，前端发起一个axios表单请求，提供手机号，密码，短信验证码，uid
#         # 接收
#         param_dict = request.POST
#         mobile = param_dict.get('mobile')
#         pwd = param_dict.get('pwd')
#         sms_request = param_dict.get('sms_code')
#         # token = param_dict.get('access_token')
#         # # 验证
#         # data_dict = meiduo_json.loads(token, constants.UID_EXPIRES)
#         # if data_dict is None:
#         #     return render(request, 'sina_callback.html', {'errmsg': 'weibo授权已过期'})
#         uid = param_dict.get('access_token')
#         # 处理
#         # 根据手机号查询用户实例，
#         try:
#             user = User.objects.get(mobile=mobile)
#         except:
#             #   如果不存在则新建用户，绑定
#             user = User.objects.create_user(mobile, password=pwd, mobile=mobile)
#         else:
#             #   如果存在则验证密码，
#             if not user.check_password(pwd):
#                 #       如果错误则提示
#                 # return JsonResponse({'errmsg': '手机号存在，密码错误'}),并把openid返回去。
#                 return render(request, 'sina_callback.html', {'errmsg': '手机号存在，密码错误', 'token': token})
#                 #   如果正确则绑定
#                 # 绑定，在OAuthWeiBoUser这张表上创建一个实例，方便以后直接用WeiBo登陆。
#         OAuthWeiBoUser.objects.create(user_id=user.id, uid=uid)
#         # 响应
#         login(request, user)
#         response = redirect(request.GET.get('state', '/'))
#         response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)
#         # 合并购物车
#         from carts.utils import merge_cart_cookie_to_redis
#         response = merge_cart_cookie_to_redis(request, response)
#         return response

