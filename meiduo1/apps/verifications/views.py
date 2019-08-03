from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from libs.captcha.captcha import captcha
from . import constants
from users.models import User
import random
from libs.yuntongxun.sms import CCP
from celery_tasks.sms.tasks import send_sms


class ImageView(View):
    def get(self, request, uuid):
        name, text, image = captcha.generate_captcha()

        # 在redis中存这个text,接下来验证要对比

        redis_cli = get_redis_connection('verify')
        redis_cli.setex(uuid, constants.IMAGE_EXPIRES, text)
        return HttpResponse(image, content_type='image/png')


class SmsView(View):
    def get(self, request, mobile):

        #1 接收
        image_request = request.GET.get('image_code')  # 用户填写的图片验证码文本,放在查询字符串里了
        uuid = request.GET.get('image_code_id')  # 在redis中存储图片验证码文本的键，放在查询字符串里了
        #2 验证ccp = CCP()
        # ccp.send_template_sms(mobile, [str(code), 5], 1)
        # print(code)
        #2.1 非空
        if not all([image_request, uuid]):
            return JsonResponse({'errmsg': '信息填写不完整'})
        #2.2 手机号是否重复
        if User.objects.filter(mobile=mobile).count() > 0:
            return JsonResponse({'errmsg': '手机号已存在'})
        # 2.3 图片验证码是否正确
        redis_cli = get_redis_connection('verify')
        image_redis = redis_cli.get(uuid)
        if not image_redis:
            return JsonResponse({'errmsg': '图片验证码已过期'})
        if image_request.lower() != image_redis.decode().lower():
            return JsonResponse({'errmsg': '图片验证码错误'})
        # 2.4是否60秒内已经向此手机号发过短信,避免用户刷新注册页面后反复获取短信验证码
        flag = redis_cli.get('%s_flag' % mobile)
        if flag:
            return JsonResponse({'errmsg': '请稍候再发短信'})


        # 处理：
        # 3.1生成6位随机数
        code = random.randint(100000, 999999)

        # 3.2存入redis，用于注册时验证,
        # redis_cli.setex(mobile, constants.SMS_EXPIRES, code)
        # # 发送标记，避免向同一个手机频繁发短信
        # redis_cli.setex('%s_flag' % mobile, constants.SMS_FLAG_EXPIRES, 1)

        # 优化：如果需要执行多条指令，可以使用管道，只与服务器交互一次
        redis_pl = redis_cli.pipeline()
        redis_pl.setex(mobile, constants.SMS_EXPIRES, code)
        redis_pl.setex('%s_flag' % mobile, constants.SMS_FLAG_EXPIRES, 1)
        redis_pl.execute()
        #响应
        # 3.3发短信
        # ccp = CCP()
        # ccp.send_template_sms('18665287955', [str(code), 5], 1)
        # print(code)
        send_sms.delay(mobile, [str(code), 5], 1)


        #4 响应
        return JsonResponse({'code': 0})
