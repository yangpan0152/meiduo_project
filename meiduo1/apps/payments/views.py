from alipay import AliPay
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from orders.models import OrderInfo
from payments.models import AliPayment


class AlipayUrlView(View):
    def get(self,request,order_id):

        try:
            order=OrderInfo.objects.get(pk=order_id)
        except:
            return render(request,'404.html')
        # 创建支付宝实例
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=settings.ALIPAY_PRIVATE_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_PATH,
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),#支付宝使用的语言没有decimal类型
            subject=settings.ALIPAY_TITLE,
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 响应，拼接完整的支付地址
        alipay_url = settings.ALIPAY_GATE + order_string
        return JsonResponse({'code': 0, 'alipay_url': alipay_url})




class AlipayVerifyView(View):
    def get(self, request):
        # 1.创建alipay实例
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=settings.ALIPAY_PRIVATE_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_PATH,
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 2.调用验证方法，验证是否支付成功
        data = request.GET.dict()
        signature = data.pop('sign')
        result = alipay.verify(data, signature)

        # 3.如果支付失败，则提示
        if not result:
            return render(request, 'pay_success.html', {'code': 1})

        # 4.如果支付成功，则提示交易编号
        trade_no = data.get('trade_no')
        order_id = data.get('out_trade_no')

        # 5.保存支付宝编号
        AliPayment.objects.create(
            order_id=order_id,
            trade_id=trade_no
        )

        # 6.修改订单状态
        order = OrderInfo.objects.get(pk=order_id)
        order.status = 2
        order.save()


        return render(request, 'pay_success.html', {
            'trade_no': trade_no
        })

