import json

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection

from carts import constants
from goods.models import SKU
from utils import meiduo_json


class CartsView(View):
    def post(self, request):
        # 加入购物车
        # 接收
        parm_dict = json.loads(request.body.decode())
        sku_id = parm_dict.get('sku_id')

        count = parm_dict.get('count')
        # 验证
        if not all([sku_id, count]):
            return JsonResponse({'errmsg': '数据不完整'})
        try:
            count = int(count)
        except:
            return JsonResponse({'errmsg': '数量错误'})
        try:
            sku = SKU.objects.get(pk=sku_id)
        except:
            return JsonResponse({'errmsg': '数量错误'})
        if count < 1 or count > sku.stock:
            return JsonResponse({'errmsg': '数量不合法'})

        response = JsonResponse({'code': 0})

        # 处理：如果登录则存入redis，未登录则存入cookie
        # 3.1登录
        user = request.user
        user_id = user.id
        if user.is_authenticated:
            # 存redis
            redis_cli = get_redis_connection('cart')
            # 存hash
            redis_cli.hset('cart_%d' % user_id, sku_id, count)
            # 存set
            redis_cli.sadd('selected_%d' % user_id, sku_id)
            # 响应：
        else:
            # 存cookie
            # 存什么　构造数据存入的格式sku_id,count,selected
            # cookie中无购物车数据，新写cookie
            data_str = request.COOKIES.get('cart')
            if data_str is None:
                data_dict = {
                    sku_id: {
                        'count': count,
                        'selected': True,
                    }
                }
            else:  # 有购物车数据就先字符串转字典，再新加键值对
                data_dict = meiduo_json.loads_base64(data_str)
                data_dict[sku_id] = {
                    'count': count,
                    'selected': True,
                }

            # 怎么存
            # 注意点不要明文存，字典转成字符串
            data_str = meiduo_json.dumps_base64(data_dict)
            response.set_cookie('cart', data_str, constants.CART_COOKIE_EXPIRE)

            # 响应
        return response

    def get(self, request):
        if request.user.is_authenticated:
            # 处理
            user_id = request.user.id
            # 1.1读取购物车数据
            redis_cli = get_redis_connection('cart')
            # 读哈希
            sku_ids = redis_cli.hkeys('cart_%d' % user_id)
            # 读set
            selected_skus = redis_cli.smembers('selected_%d' % user_id)
            # 1.2查询得到实例
            cart_skus = []
            for sku_id in sku_ids:
                sku = SKU.objects.get(pk=int(sku_id))
                count = int(redis_cli.hget('cart_%d' % user_id, int(sku_id)))
                cart_skus.append({
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'price': str(sku.price),
                    'count': count,
                    'total': str(count * sku.price),
                    'selected': str(sku.id in selected_skus),
                })

            context = {
                'cart_sku': cart_skus
            }
            # 1.3构造前端需求数据格式
            # 响应
            return render(request, 'cart.html', context)
        else:  # 未登录
            # 处理
            # 3.1 读cookie
            data_str = request.COOKIES.get('cart')
            if not data_str:
                cart_skus = []
            else:
                data_dict = meiduo_json.loads_base64(data_str)
                # 获得所有的sku_id
                sku_ids = [sku_id for sku_id in data_dict]

                # 1.2查询得到实例
                user_id = request.user.id
                cart_skus = []
                for sku_id in sku_ids:
                    sku = SKU.objects.get(pk=sku_id)
                    count = data_dict[sku_id]['count']
                    cart_skus.append({
                        'id': sku.id,
                        'name': sku.name,
                        'default_image_url': sku.default_image.url,
                        'price': str(sku.price),
                        'count': count,
                        'total': str(count * sku.price),
                        'selected': str(data_dict[sku_id]['selected']),
                    })

            context = {
                'cart_sku': cart_skus
            }
            # 1.3构造前端需求数据格式
            # 响应
            return render(request, 'cart.html', context)

    def put(self, request):

        # 接收
        # parm_dict=json.loads(request.body.decode())
        # sku_id=parm_dict.get('sku_id')
        # count=parm_dict.get('count')
        # selected=parm_dict.get('selected')
        #
        #
        # #验证
        # #2.1非空
        # if not all([sku_id,count]):
        #     return JsonResponse({'errmsg':'数据不完整'})
        #
        # #2.1库存量满足与否
        # try:
        #     sku=SKU.objects.get(pk=sku_id)
        # except:
        #     return JsonResponse({'errmsg': '商品编号不合法'})
        # else:
        #     if sku.stock < count:
        #         return JsonResponse({'errmsg': '%s数量不合法'% sku.id})
        #
        # cart_sku = [{
        #     'id': sku_id,
        #     'name': sku.name,
        #     'default_image_url': sku.default_image.url,
        #     'price': str(sku.price),
        #     'count': count,
        #     'selected': str(selected),
        # }]
        # if request.user.is_authenticated:
        #     user=request.user
        #     #处理
        #     #3.1改hash
        #     redis_cli=get_redis_connection('cart')
        #     redis_pipeline=redis_cli.pipeline()
        #     redis_pipeline.hset('cart_%d'% user.id,sku_id,count)
        #     #3.2改set
        #     if selected:
        #         redis_pipeline.sadd('selected_%d'% user.id, sku_id)
        #     else:
        #         redis_pipeline.srem('selected_%d' % user.id, sku_id)
        #
        #     redis_pipeline.execute()
        #     #响应
        #
        #     return JsonResponse({'code':0, 'cart_sku':cart_sku})



        # 接收,put+json===>请求体非表单
        param_dict = json.loads(request.body.decode())
        sku_id = param_dict.get('sku_id')
        count = param_dict.get('count')
        selected = param_dict.get('selected')

        # 验证：Bool类型的数据不能进行非空验证
        if not all([sku_id, count]):
            return JsonResponse({'errmsg': '数据不完整'})
        try:
            count = int(count)
        except:
            return JsonResponse({'errmsg': '数量错误'})
        # 查询库存商品
        try:
            sku = SKU.objects.get(pk=sku_id)
        except:
            return JsonResponse({'errmsg': '库存商品编号无效'})
        # 数量不能大于当前商品的库存量
        if count < 1 or count > sku.stock:
            return JsonResponse({'errmsg': '数量不合法'})

        # 处理
        response = JsonResponse({
            'code': 0,
            'cart_sku': {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'total': str(count * sku.price),
                'selected': str(selected)
            }
        })

        if request.user.is_authenticated:
            # 已登录，改写redis中数据
            redis_cli = get_redis_connection('cart')
            user_id = request.user.id
            # hash
            redis_cli.hset('cart_%d' % user_id, sku_id, count)
            # set
            if selected:
                redis_cli.sadd('selected_%d' % user_id, sku_id)
            else:
                redis_cli.srem('selected_%d' % user_id, sku_id)
        else:
            # 处理　修改count和选中状态
            # 3.1 读cookie
            data_str = request.COOKIES.get('cart')
            data_dict = meiduo_json.loads_base64(data_str)
            data_dict[sku_id]['count'] = count
            data_dict[sku_id]['selected'] = selected
            # 3.2 写入cookie
            # 先把字典转成字符串
            data_str = meiduo_json.dumps_base64(data_dict)
            response.set_cookie('cart', data_str, constants.CART_COOKIE_EXPIRE)
            # 响应

        return response

    def delete(self, request):
        # 接收
        parm_dict = json.loads(request.body.decode())
        sku_id = parm_dict.get('sku_id')
        user_id = request.user.id
        # 验证
        if not all([sku_id]):
            return JsonResponse({'errmsg': '商品编号不合法'})
        # 处理
        if request.user.is_authenticated:

            redis_cli = get_redis_connection('cart')
            redis_pipeline = redis_cli.pipeline()
            # 3.1 删hash
            redis_pipeline.hdel('cart_%d' % user_id, sku_id)
            # 3.1 删set
            redis_pipeline.srem('selected_%d' % user_id, sku_id)
            #     #3.3再读一遍hash&set
            #     sku_ids = redis_cli.hkeys('cart_%d' % user_id)
            #     # 读set
            #     selected_skus = redis_cli.smembers('selected_%d' % user_id)
            #     # 1.2查询得到实例
            #     cart_skus = []
            #     for sku_id in sku_ids:
            #         sku = SKU.objects.get(pk=int(sku_id))
            #         count = int(redis_cli.hget('cart_%d' % user_id, int(sku_id)))
            #         cart_skus.append({
            #             'id': sku.id,
            #             'name': sku.name,
            #             'default_image_url': sku.default_image.url,
            #             'price': str(sku.price),
            #             'count': count,
            #             'total': str(count * sku.price),
            #             'selected': str(sku.id in selected_skus),
            #         })
            #
            #     context = {
            #         'cart_sku': cart_skus
            #     }
            #     # 1.3构造前端需求数据格式
            #     # 响应
            #     return render(request, 'cart.html', context)
            # else:  # 未登录
            #     pass
            redis_pipeline.execute()
            # 响应
            return JsonResponse({'code': 0})

        else:
            # 处理　就是删除cookie内容，写入response。
            # 读cookie
            data_str = request.COOKIES.get('cart')
            data_dict = meiduo_json.loads_base64(data_str)
            del data_dict[sku_id]
            # 3.2 写入cookie
            # 先把字典转成字符串
            data_str = meiduo_json.dumps_base64(data_dict)
            response = JsonResponse({'code': 0})
            response.set_cookie('cart', data_str, constants.CART_COOKIE_EXPIRE)
            return response
            # 响应


class SelectionView(View):
    def put(self, request):
        parm_dict = json.loads(request.body.decode())
        selected = parm_dict.get('selected')
        response=JsonResponse({'code': 0, 'errmsg': ''})
        if request.user.is_authenticated:
            # 接收

            # 验证（无验证需求）
            # 处理
            user_id = request.user.id
            # 3.1读出hash所有的sku_ids
            redis_cli = get_redis_connection('cart')
            # redis_pipeline = redis_cli.pipeline()
            sku_ids = [int(sku_id) for sku_id in redis_cli.hkeys('cart_%d' % user_id)]
            # 3.2存入set所有的sku_ids]
            for sku_id in sku_ids:
                redis_cli.sadd('selected_%d' % user_id, sku_id)
                # redis_pipeline.execute()
                # 响应

        else:
            #处理　读cookie，把所有商品改成selected
            # 3.1 读cookie
            data_str = request.COOKIES.get('cart')
            data_dict = meiduo_json.loads_base64(data_str)
            for data_dict1 in data_dict.values():
                data_dict1['selected']= selected
            # 3.2 写入cookie
            # 先把字典转成字符串
            data_str = meiduo_json.dumps_base64(data_dict)

            response.set_cookie('cart', data_str, constants.CART_COOKIE_EXPIRE)
            # 响应
            #响应

        return response


class SimpleView(View):
    def get(self,request):
        #处理读购物车数据，构造数据结构
        #登陆用户
        if request.user.is_authenticated:
            # 处理
            user_id = request.user.id
            # 1.1读取购物车数据
            redis_cli = get_redis_connection('cart')
            # 读哈希
            sku_ids = redis_cli.hkeys('cart_%d' % user_id)
            # 读set
            selected_skus = redis_cli.smembers('selected_%d' % user_id)
            # 1.2查询得到实例
            cart_skus = []
            for sku_id in sku_ids:
                sku = SKU.objects.get(pk=int(sku_id))
                count = int(redis_cli.hget('cart_%d' % user_id, int(sku_id)))
                cart_skus.append({
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'count': count,
                })

            # 1.3构造前端需求数据格式
            # 响应



        #未登陆用户
        else:  # 未登录
        # 处理
        # 3.1 读cookie
            data_str = request.COOKIES.get('cart')
            if not data_str:
                cart_skus = []
            else:
                data_dict = meiduo_json.loads_base64(data_str)
                # 获得所有的sku_id
                sku_ids = [sku_id for sku_id in data_dict]

                # 1.2查询得到实例
                user_id = request.user.id
                cart_skus = []
                for sku_id in sku_ids:
                    sku = SKU.objects.get(pk=sku_id)
                    count = data_dict[sku_id]['count']
                    cart_skus.append({
                        'id': sku.id,
                        'name': sku.name,
                        'default_image_url': sku.default_image.url,
                        'count': count,
                    })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'cart_skus': cart_skus
        })