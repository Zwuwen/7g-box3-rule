import os
import sys
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
import json
import time
from db.redis_handle import RedisHandle
from log.log import MyLog

class EventHandle:
    @classmethod
    def update_event(cls, product_id, dev_id, event, payload):
        try:
            #将事件添加/更新到redis, key = 'product_id.dev_id.event'
            key = product_id + '.' + dev_id + '.' + event
            mapping = {}
            mapping['ts'] = time.time()
            mapping['payload'] = payload
            r = RedisHandle()
            return r.hmset_value(key, mapping)
        except Exception as e:
            msg = MyLog.color_red("update_event has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    @classmethod
    def get_event_timestamp(cls, product_id, dev_id, event):
        try:
            key = product_id + '.' + dev_id + '.' + event
            r = RedisHandle()
            ts_byte_list = r.hmget_value(key, 'ts')
            if ts_byte_list[0]:
                str_ts = ''.join([k.decode('utf-8') for k in ts_byte_list])
                float_ts = float(str_ts)
                MyLog.logger.info('get_event_timestamp key(%s) ts float_ts: %f'%(key, float_ts))
                return float_ts
            else:
                return None
        except Exception as e:
            msg = MyLog.color_red("get_event_timestamp has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    @classmethod
    def get_event_payload(cls, product_id, dev_id, event):
        try:
            key = product_id + '.' + dev_id + '.' + event
            r = RedisHandle()
            payload_byte_list = r.hmget_value(key, 'payload')
            if payload_byte_list[0]:
                payload = ''.join([k.decode('utf-8') for k in payload_byte_list])
                return payload
            else:
                return None
        except Exception as e:
            msg = MyLog.color_red("get_event_payload has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''
    key_dict为“productId.devId.events.traffic.p1.p2[3].p3”根据“.”截取后的列表
    '''
    @classmethod
    def get_event_value(cls, product_id, dev_id, event, key_list):
        MyLog.logger.info('get_event_value product_id:%s, dev_id:%s, event:%s'%(product_id, dev_id, event))
        try:
            event_payload = cls.get_event_payload(product_id, dev_id, event)
            if event_payload:
                event_payload_dict = json.loads(event_payload)
                for key_index in range(4, len(key_list)):
                    key = key_list[key_index]
                    name, index = cls.get_array_name_and_index(key)
                    if index != None:
                        event_payload_dict = event_payload_dict[name][index]
                    else:
                        event_payload_dict = event_payload_dict[key]
                return event_payload_dict
            return None
        except Exception as e:
            msg = MyLog.color_red("get_event_value has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''
    如果表示为数组，获取数组下表值.非数组返回None
    p2[2]得到2
    '''
    @classmethod
    def get_array_name_and_index(cls, string):
        try:
            if string[len(string) - 1] == ']':
                start_index = string.find('[')
                return string[0 : start_index], int(string[start_index+1 : len(string) - 1])
            else:
                return None, None
        except Exception as e:
            msg = MyLog.color_red("get_array_name_and_index has except: " + str(e))
            MyLog.logger.error(msg)
            return None, None

if __name__ == "__main__":
    key_str = '"productId.devId.events.traffic.p1.p11[1]'
    key_list = key_str.split('.')
    value = EventHandle.get_event_value(0,0,0,key_list)