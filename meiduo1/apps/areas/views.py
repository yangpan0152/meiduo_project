from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.core.cache import cache

from areas import constants
from areas.models import Area


class AreaView(View):
    def get(self, request):
        # 如果查询参数提供area_id查询这个地区及子地区
        # 如果没有带areq_id，说明查询的是省份
        area_id = request.GET.get('area_id')

        if area_id:
            city_dict = cache.get('city_'+area_id)
            if not city_dict:
                try:
                    city = Area.objects.get(pk=area_id)
                except:
                    return JsonResponse({"code": 1, "errmsg": '地区编号无效'})
                    # 遍历，转字典
                subs = []
                for sub in city.subs.all():
                    subs.append({
                        "id": sub.id,
                        "name": sub.name,
                    })
                city_dict = {
                    "id": city.id,
                    "name": city.name,
                    "subs": subs
                }
                cache.set('city_'+area_id,city_dict,constants.PROVINCE_EXPIRES)
            return JsonResponse({"code": 0,
                             "sub_data":city_dict
                             })
        else:
            province_list = cache.get("province_list")
            if not province_list:
                queryset = Area.objects.filter(parent__isnull=True)
                # 构造前端要求的数据及格式
                province_list = []
                for province in queryset:
                    province_list.append({
                        "id": province.id,
                        "name": province.name,
                    })
                    # 将查询到的省份数据存入redis
                cache.set("province_list", province_list, constants.PROVINCE_EXPIRES)
            return JsonResponse({"code": 0, "province_list": province_list})
