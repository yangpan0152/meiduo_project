from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
import pickle
import base64


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


def dumps_base64(data_dict):
    # 1字典转字符串
    # 1.1字典转byte-like
    data_bytes = pickle.dumps(data_dict)
    # 1.2byte-like转byte
    data_64 = base64.b64encode(data_bytes)
    # 1.3返回byte转字符串
    data_str = data_64.decode()
    return data_str

def loads_base64(data_str):
    if data_str is None:
        data_dict={}
    else:
        #1.字符串先转byte
        data_64=data_str.encode()
        #1.byte再转byte-like
        data_bytes=base64.b64decode(data_64)

        #1.byte-like转字典
        data_dict = pickle.loads(data_bytes)
    return data_dict