from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannelGroup, GoodsChannel, GoodsCategory
from .models import ContentCategory, Content
from utils.categories import get_categories


class IndexView(View):
    def get(self, request):
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

        return render(request, 'index.html', context)