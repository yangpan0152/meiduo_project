from celery_tasks.main import app
from libs.yuntongxun.sms import CCP


@app.task(name='send_sms')
def send_sms(to, datas, temp_id):
    # 将耗时代码定义在这里
    ccp = CCP()
    ccp.send_template_sms(to, datas, temp_id)