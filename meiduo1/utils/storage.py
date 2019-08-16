from django.core.files.storage import Storage
from django.conf import settings


class MeiduoStorage(Storage):
    def url(self, name):
        # name===>文件名
        return settings.FDFS_IMAGE_URL + name