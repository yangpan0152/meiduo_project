import json
from datetime import date

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from utils.categories import get_categories
from .models import GoodsCategory, GoodsVisitCount
from .models import SKU
from django.http import JsonResponse
from utils.breadcrumb import get_breadcrumb

class ListView(View):
    def get(self, request, category_id, page_num):
        group_dict = get_categories()

        # 面包屑导航 (就是显示当前三级分类所在的二级分类，一级分类)
        try:
            cat3 = GoodsCategory.objects.get(pk=category_id)
        except:
            return render(request, '404.html')
        user = request.user
        # else:
        #     breadcrumb = {
        #         'cat1': {
        #             'name': cat3.parent.parent.name,
        #             'url': cat3.parent.parent.chl_level1.all()[0].url,
        #         },
        #         'cat2': cat3.parent,
        #         'cat3': cat3,
        #     }

        breadcrumb=get_breadcrumb(cat3)

        queryset = SKU.objects.filter(category_id=category_id, is_launched=True)
        # 排序
        sort = request.GET.get('sort', 'default')
        if sort == 'price1':
            queryset = queryset.order_by('price')
        elif sort == 'price2':
            queryset = queryset.order_by('-price')
        elif sort == 'hot':
            queryset = queryset.order_by('-sales')
        else:
            queryset = queryset.order_by('-create_time')

        # 分页
        p = Paginator(queryset, 5)
        page = p.page(page_num)

        context = {
            'group_dict': group_dict,
            'breadcrumb': breadcrumb,
            'category': cat3,
            'sort': sort,
            'page_skus': page,
            'page_num': page_num,
            'total_page': p.num_pages,
        }
        response = render(request, 'list.html', context)
        response.set_cookie('username', user.username, 60 * 60)
        return response


class HotView(View):
    def get(self, request, category_id):
        # 显示销量最高的两个商品
        queryset = SKU.objects.filter(category_id=category_id)
        queryset = queryset.order_by('-sales')[0:2]
        hot_sku_list = []
        # 构造前端需要的格式
        for sku in queryset:
            hot_sku_list.append({
                "id": sku.id,
                "default_image_url": sku.default_image.url,
                "name": sku.name,
                "price": sku.price,
                # "category":
            })
        response = JsonResponse({'hot_sku_list': hot_sku_list})
        response.set_cookie('username', request.user.username, 60 * 60)
        return response


class DetailView(View):
    def get(self,request,sku_id):
        try:
            sku=SKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'errmsg':'商品信息缺失'})
        #商品频道查询
        group_dict=get_categories()
        #面包屑导航
        breadcrumb=get_breadcrumb(sku.category)
        #构建规格信息
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

            # 渲染页面
        context = {
            'group_dict': group_dict,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
            'spu': sku.spu,
            'category_id': sku.category.id
        }
        return render(request, 'detail.html', context)


class GoodsVisitView(View):
    def post(self, request, category_id):
        today = date.today()
        try:
            visit = GoodsVisitCount.objects.get(category_id=category_id, date=today)
        except:
            # 今天第一次访问指定的第三级分类，则新建
            GoodsVisitCount.objects.create(category_id=category_id, count=1)
        else:
            # 今天非第一次访问指定的第三级分类，则+1
            visit.count += 1
            visit.save()

        return JsonResponse({'code': 0})




        #




