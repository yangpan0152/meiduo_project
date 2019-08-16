import json
from datetime import datetime

from django.db import transaction
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class OrderSettleView(LoginRequiredMixin, View):
    def get(self, request):
        # 1.查询收货地址
        user = request.user
        addresses = user.addresses.filter(is_deleted=False)

        # 2.查询购物车中选中的商品====>redis
        redis_cli = get_redis_connection('cart')
        # hash
        data_dict = redis_cli.hgetall('cart_%d' % user.id)
        data_dict = {int(key): int(value) for key, value in data_dict.items()}
        # set
        sku_ids = redis_cli.smembers('selected_%d' % user.id)
        sku_ids = [int(sku_id) for sku_id in sku_ids]
        # 2.1查询sku实例
        skus = SKU.objects.filter(pk__in=sku_ids)
        # 2.2构造前端需要的格式
        sku_list = []
        total_count = 0
        total_money = 0
        for sku in skus:
            count = data_dict[sku.id]
            total_count += count
            total = count * sku.price
            total_money += total
            sku_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price,
                'count': count,
                'total': total
            })

        # 3.计算总数量、总金额、运费、实付款
        total_dict = {
            'count': total_count,
            'money': total_money,
            'freight': 10,
            'pay': total_money + 10
        }

        context = {
            'addresses': addresses,
            'default_address_id': user.default_address_id,
            'sku_list': sku_list,
            'total_dict': total_dict
        }

        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredMixin,View):
    def post(self, request):
        user = request.user
        # 接收
        param_dict = json.loads(request.body.decode())
        address_id = param_dict.get('address_id')
        pay_method = param_dict.get('pay_method')

        # 验证
        if not all([address_id, pay_method]):
            return JsonResponse({'errmsg': '数据不完整'})
        # address_id是当前用户的一个收货地址
        if user.addresses.filter(pk=address_id).count() < 1:
            return JsonResponse({'errmsg': '收货地址无效'})
        # 支付方式
        if pay_method not in [1, 2]:
            return JsonResponse({'errmsg': '支付方式无效'})

        # 处理
        # 1.获取购物车中选中的商品
        redis_cli = get_redis_connection('cart')
        cart_dict = redis_cli.hgetall('cart_%d' % user.id)
        cart_dict = {int(sku_id): int(count) for sku_id, count in cart_dict.items()}
        sku_ids = redis_cli.smembers('selected_%d' % user.id)
        sku_ids = [int(sku_id) for sku_id in sku_ids]

        with transaction.atomic():
            sid = transaction.savepoint()
            # 2.创建订单实例OrderInfo
            order_id = '%s%010d' % (datetime.now().strftime('%Y%m%d%H%M%S'), user.id)
            status = 1
            if pay_method == 1:
                # 如果用户选择支付方式为货到付款则状态设置为待发货
                status = 2
            order = OrderInfo.objects.create(
                order_id=order_id,
                user_id=user.id,
                address_id=address_id,
                total_count=0,
                total_amount=0,
                freight=10,
                pay_method=pay_method,
                status=status
            )

            # 3.查询购买的商品实例
            skus = SKU.objects.filter(pk__in=sku_ids)

            # 4.遍历购买商品
            total_count = 0
            total_amount = 0
            for sku in skus:
                count = cart_dict[sku.id]
                # 4.1判断库存是否足够，如果不足则提示
                if sku.stock < count:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'code': 1, 'errmsg': '编号[%d]库存不足' % sku.id})
                # 4.2如果足够，则

                # time.sleep(5)

                # 4.3修改库存、销量
                # sku.stock -= count
                # sku.sales += count
                # sku.save()

                # 使用乐观锁进行修改：在修改前进行判断
                new_stock = sku.stock - count
                new_sales = sku.sales + count
                result = SKU.objects.filter(pk=sku.id, stock=sku.stock).update(stock=new_stock, sales=new_sales)
                if result == 0:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'code': 1, 'errmsg': '编号[%d]库存不足' % sku.id})

                # 4.4创建订单商品实例OrderGoods
                OrderGoods.objects.create(
                    order_id=order_id,
                    sku_id=sku.id,
                    count=count,
                    price=sku.price
                )
                # 4.5累加：总数量、总金额
                total_count += count
                total_amount += count * sku.price

            # 5.修改订单实例的总数量、总金额
            order.total_count = total_count
            order.total_amount = total_amount
            order.save()

            transaction.savepoint_commit(sid)

        # 6.删除购物车中选中的商品
        redis_cli.delete('selected_%d' % user.id)
        redis_cli.hdel('cart_%d' % user.id, *sku_ids)

        # 响应
        return JsonResponse({'code': 0, 'order_id': order_id})


class SuccessView(LoginRequiredMixin, View):
    def get(self, request):
        param_dict = request.GET
        order_id = param_dict.get('order_id')
        payment_amount = param_dict.get('payment_amount')
        pay_method = param_dict.get('pay_method')

        if not all([order_id, payment_amount, pay_method]):
            return HttpResponse('订单保存失败')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }

        return render(request, 'order_success.html', context)






