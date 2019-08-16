# from goods.models import GoodsChannelGroup

# def get_categories():
#     #频道分类数据
#     #1.0 查询所有的频道组
#     group_queryset= GoodsChannelGroup.objects.all()
#     group_dict={} # 键：频道编号
#     for group in group_queryset:
#         #构造频道结构
#         group_dict[group.id]={'channels':[],'cat2':[]}
#         #1.1 查寻当前频道一级分类
#         channel_queryset=group.channels.order_by('sequence')
#         for channel in channel_queryset:
#             #存入字典，用于页面输出
#             group_dict[group.id]['channels'].append({
#                 'url':channel.url,
#                 'name':channel.category.name
#             })
#
#         #1.2 查询当前这个一级分类下的所有二级分类，并保存
#             cat1=channel.category
#             for cat2 in cat1.subs.all():
#                 group_dict[group.id]['cat2'].append(cat2)
#
#     return group_dict
from django.shortcuts import render

from goods.models import GoodsChannelGroup, GoodsCategory


def get_categories():
    # 频道分类数据
    # 1.0查询所有频道
    group_queryset = GoodsChannelGroup.objects.all()
    group_dict = {}  # 键：频道编号
    '''
    {
        1:{
            一级分类：[],
            二级分类：[]
        },
        2:,
        3:
        ....
    }
    '''
    for group in group_queryset:
        # 构造频道结构
        group_dict[group.id] = {'channels': [], 'cat2': []}
        # 1.1查询当前频道的一级分类
        channel_queryset = group.channels.order_by('sequence')
        for channel in channel_queryset:
            # 存入字典，用于页面输出
            group_dict[group.id]['channels'].append({
                'url': channel.url,  # 一级分类链接
                'name': channel.category.name  # 一级分类名称
            })
            # 1.2查询当前频道的二级分类，并保存
            cat1 = channel.category
            for cat2 in cat1.subs.all():
                group_dict[group.id]['cat2'].append(cat2)

    return group_dict


def get_breadcrumb(request,category_id):
    try:
        cat3 = GoodsCategory.objects.get(pk=category_id)
    except:
        return render(request, '404.html')
    else:
        breadcrumb = {
            'cat1': {
                'name': cat3.parent.parent.name,
                'url': cat3.parent.parent.chl_level1.all()[0].url,
            },
            'cat2': cat3.parent,
            'cat3': cat3,
        }
    return breadcrumb