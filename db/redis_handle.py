import sys
import os
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
import redis
from config import RULE_REDIS_HOST, RULE_REDIS_PORT

class RedisHandle:
    def __init__(self):
        if not hasattr(RedisHandle, "__redis_pool"):
            self.__redis_pool = redis.ConnectionPool(host=RULE_REDIS_HOST, port=RULE_REDIS_PORT)

    def __new__(cls, *args, **kwargs):
        #单例
        if not hasattr(RedisHandle, "_instance"):
            RedisHandle._instance = object.__new__(cls)
        return RedisHandle._instance

    def set_value(self, key, value, timeout_ms=0):
        ret = False
        r = redis.Redis(connection_pool=self.__redis_pool)
        if r:
            if timeout_ms == 0:
                ret = r.set(key, value)
            else:
                ret = r.set(key, value, px=timeout_ms)
        return ret

    def get_value(self, key):
        r = redis.Redis(connection_pool=self.__redis_pool)
        return r.get(key)

    def hmset_value(self, key, mapping):
        ret = False
        r = redis.Redis(connection_pool=self.__redis_pool)
        if r:
            ret = r.hmset(key, mapping)
        return ret

    def hmget_value(self, key, field):
        ret = False
        r = redis.Redis(connection_pool=self.__redis_pool)
        if r:
            return r.hmget(key, field)
        return None

    def del_key(self, key):
        ret = False
        r = redis.Redis(connection_pool=self.__redis_pool)
        if r:
            return r.delete(key)
        return None
