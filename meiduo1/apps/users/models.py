from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    mobile = models.CharField(max_length=11, verbose_name='手机号', unique=True)

    class Meta:
        db_table = 'tb_users'

    def __str__(self):
        return self.username
