from django.db import models
from django.contrib.auth.models import AbstractUser

from utils.models import BaseModel


class User(AbstractUser):
    mobile = models.CharField(max_length=11, verbose_name='手机号', unique=True)
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    default_address = models.ForeignKey('Address', related_name='users', verbose_name='默认收货地址', null=True)

    class Meta:
        db_table = 'tb_users'

    def __str__(self):
        return self.username



class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'receiver': self.receiver,
            'province': self.province.name,
            'province_id': self.province_id,
            'city': self.city.name,
            'city_id': self.city_id,
            'district': self.district.name,
            'district_id': self.district_id,
            'place': self.place,
            'mobile': self.mobile,
            'tel': self.tel,
            'email': self.email
        }
