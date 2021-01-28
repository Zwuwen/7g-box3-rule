import sys
import os
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
import time
import redis
#from config import RULE_REDIS_HOST, RULE_REDIS_PORT
from log.log import MyLog
 
class RedisLock():
    def __init__(self, key):
        self.rdcon = redis.Redis(host='127.0.0.1', port=6379, password="", db=1)
        self._lock_key = f"rule_engine_locker_{key}"
 
    def acquire(self, timeout=120):
        try:
            end = time.time() + timeout
            while time.time() < end:
                if self.rdcon.setnx(self._lock_key, self._lock_key):
                    self.rdcon.expire(self._lock_key, timeout)
                    return None
                elif self.rdcon.ttl(self._lock_key) == -1:
                    # key 存在但没有设置剩余生存时间时,设置过期时间
                    self.rdcon.expire(self._lock_key, timeout)
                time.sleep(0.01)
        except Exception as e:
            msg = MyLog.color_red("redislock acquire has except: " + str(e))
            MyLog.logger.error(msg)
            #print("redislock acquire has except: " + str(e))
            pass
 
    def release(self):
        try:
            with self.rdcon.pipeline() as pipe:
                while True:
                    try:
                        # watch 锁, multi 后如果该 key 被其他客户端改变, 事务操作会抛出 WatchError 异常
                        pipe.watch(self._lock_key)
                        iden = pipe.get(self._lock_key)
                        if iden and iden.decode('utf-8') == self._lock_key:
                            # 事务开始
                            pipe.multi()
                            pipe.delete(self._lock_key)
                            pipe.execute()
                            pipe.unwatch()
                            #print("release success")
                            return None
                        pipe.unwatch()
                        break
                    except WatchError as e:
                        msg = MyLog.color_red("watch lock has except: " + str(e))
                        MyLog.logger.error(msg)
                #print("release falied")
                return None
        except Exception as e:
            msg = MyLog.color_red("redislock release has except: " + str(e))
            MyLog.logger.error(msg)
            #print("redislock release has except: " + str(e))
            pass

if __name__ == "__main__":
    lk = RedisLock("test")
    def body(val):
        lk.acquire()
        print(f"==={val}")
        time.sleep(2)
        lk.release()
        print(f"==={val} release")

    from threading import Timer
    for i in range(10):
        t = Timer(0, body, (i,))
        t.start()

    while True:
        time.sleep(60)