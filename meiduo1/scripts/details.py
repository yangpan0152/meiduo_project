import os
import sys

sys.path.insert(0, '../')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo1.settings.dev")

# Django 初始化
import django

django.setup()
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from goods.models import SKU
from utils.breadcrumb import get_breadcrumb
from utils.categories import get_categories


def generate_detail_html(sku):
    # 商品频道查询
    group_dict = get_categories()
    # 面包屑导航
    breadcrumb = get_breadcrumb(sku.category)
    # 构建规格信息
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
    response = render(None, 'detail.html', context)
    return response.content.decode()


if __name__ == '__main__':

    skus = SKU.objects.all()
    for sku in skus:
        html_str = generate_detail_html(sku)

        filename = os.path.join(settings.STATIC_FILES_DIRS, 'details/%d.html' % sku.id)
        with open(filename, 'w') as f1:
            f1.write(html_str)

    print('ok')
