from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings


def dumps(data_dict, expires):
    # 加密
    serializer = Serializer(settings.SECRET_KEY, expires)
    s = serializer.dumps(data_dict).decode()
    return s


def loads(s, expires):
    # 解密
    serializer = Serializer(settings.SECRET_KEY, expires)
    try:
        data_dict = serializer.loads(s)
    except:
        # 如果字符串被修改过，或过期，则抛异常
        return None
    else:
        return data_dict
