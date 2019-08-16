import os

from django.conf import settings
from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannelGroup, GoodsChannel, GoodsCategory
from .models import ContentCategory, Content
from utils.categories import get_categories


def generate_index():
    # ---------生成首页静态文件
    # 1.获取频道分类数据
    group_dict = get_categories()

    # 2.查询所有广告类别
    category_queryset = ContentCategory.objects.all()
    contents = {}
    for category in category_queryset:
        contents[category.key] = category.contents.order_by('sequence')

    context = {
        'group_dict': group_dict,
        'contents': contents
    }
    response = render(None, 'index.html', context)
    html_str = response.content.decode()
    # --------将静态文件写入文件中
    filename = os.path.join(settings.STATIC_FILES_DIRS, 'index.html')
    with open(filename, 'w') as f1:
        f1.write(html_str)

    print('ok')
