import sys
import os
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
import time
import redis
from config import RULE_REDIS_HOST, RULE_REDIS_PORT
 
class RedisLock():
    def __init__(self, key):
        self.rdcon = redis.Redis(host=RULE_REDIS_HOST, port=RULE_REDIS_PORT, password="", db=1)
        self._lock = 0
        self._lock_key = f"rule_engine_locker_{key}"
 
    def acquire(self, timeout=30):
        while True:
            if self._lock != 1:
                timestamp = time.time() + timeout + 1
                self._lock = self.rdcon.setnx(self._lock_key, timestamp)
                if self._lock == 1 or (time.time() > float(self.rdcon.get(self._lock_key)) and time.time() > float(self.rdcon.getset(self._lock_key, timestamp))):
                    break
            time.sleep(0.3)
 
    def release(self):
        self.rdcon.delete(self._lock_key)
        self._lock = 0
