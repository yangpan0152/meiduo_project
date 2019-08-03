from celery import Celery
import os

# 设置django项目的环境变量
os.environ["DJANGO_SETTINGS_MODULE"] = "meiduo1.settings.dev"

# 创建实例
app = Celery('meiduo1')

# 加载配置
app.config_from_object('celery_tasks.config')

# 任务注册
app.autodiscover_tasks([
    'celery_tasks.sms',
    'celery_tasks.email',

])