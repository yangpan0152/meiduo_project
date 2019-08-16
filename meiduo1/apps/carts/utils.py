from django_redis import get_redis_connection

from utils import meiduo_json


def merge_cart_cookie_to_redis(request,response):
    #处理　读出cookie中数据，存入redis,删除cookie。
    #读cookie
    data_str = request.COOKIES.get('cart')
    data_dict = meiduo_json.loads_base64(data_str)
    #获取sku_id,count,slected
    sku_ids = data_dict.keys()

    #存redis
    user = request.user
    user_id = user.id
    # 存redis
    redis_cli = get_redis_connection('cart')
    redis_pipeline=redis_cli.pipeline()
    # 存hash
    for sku_id in sku_ids:
        count=data_dict[sku_id]['count']
        selecteds=data_dict[sku_id]['selected']
        redis_pipeline.hset('cart_%d' % user_id, sku_id, count)
    # 存set
        if selecteds:
            redis_pipeline.sadd('selected_%d' % user_id, sku_id)
        else:
            redis_pipeline.srem('selected_%d' % user_id, sku_id)
        redis_pipeline.execute()

    #删cookie
    response.delete_cookie('cart')
    #响应
    return response