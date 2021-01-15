import os
import sys
import time
#from sqlalchemy import exc
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
import json
from command.dev_command_queue_mng import DevCommandQueueMng
from rule.event_handle import EventHandle
from rpc_call.client import DevCall
from log.log import MyLog

'''
productId.devId.events.traffic.type
productId.devId.properties.bri
'''
def get_value(attr_list:list, payload):
    MyLog.logger.info('script_fun get_value')
    try:
        key_list = payload.split(".")
        if key_list[2] == 'properties':
            value = get_attribute_value(key_list)
            attr_list.append(payload)
            return value
        elif key_list[2] == 'events':
            value = EventHandle.get_event_value(key_list[0], key_list[1], key_list[3], key_list)
            return value
        else:
            return None
    except Exception as e:
        msg = MyLog.color_red('get_value has except: ' + str(e))
        MyLog.logger.error(msg)
        return None

'''productId.devId.events.traffic'''
def get_event_time_from_now(payload):
    try:
        MyLog.logger.info("get_event_time_from_now payload: %s"%(payload))
        key_list = payload.split(".")
        if key_list[2] != 'events':
            msg = MyLog.color_red("payload error")
            MyLog.logger.error(msg)
            return 2592000
        ts = EventHandle.get_event_timestamp(key_list[0], key_list[1], key_list[3])
        if ts is None:
            return 2592000
        current_ts = time.time()
        t = current_ts - ts
        MyLog.logger.info('get_event_time_from_now: %f'%(t))
        return t
    except Exception as e:
        msg = MyLog.color_red('get_event_time_from_now has except: ' + str(e))
        MyLog.logger.error(msg)
        return 2592000

def get_command_list_by_dev_id(dev_command_list, dev_id):
    for dev_command in dev_command_list:
        if 'dev_id' in dev_command and dev_command['dev_id'] == dev_id:
            return dev_command['command_list']
    return None

''' service:   "productId.devId.services.service"
    dev_command_list = [{'product_id': '', 'dev_id': "", "command_list":[{'service':'', 'param':'', "time":10}]}]
'''
def call_service(dev_command_list, service, duration, **param)->None:
    try:
        key_list = service.split(".")
        product_id = key_list[0]
        dev_id = key_list[1]
        command = {}
        command['service'] = key_list[3]
        command['param'] = param
        if duration == 0:
            # 0代表永久执行，在这里赋值时间为1年
            command['time'] = 31536000
        else:
            command['time'] = duration

        command_list = get_command_list_by_dev_id(dev_command_list, dev_id)
        if command_list:
            command_list.append(command)
        else:
            command_list = []
            command_list.append(command)
            dev_command = {}
            dev_command['product_id'] = product_id
            dev_command['dev_id'] = dev_id
            dev_command['command_list'] = command_list
            dev_command_list.append(dev_command)
    except Exception as e:
        msg = MyLog.color_red('call_service has except: ' + str(e))
        MyLog.logger.error(msg)


'''
    event_list = [{"event_id":"", "src_dev_list":[{"productId":"p_id", "deviceId":"d_id"}]}]
'''
def raise_event(event_list, event_id, srcList):
    try:
        event_dict = {}
        event_dict['event_id'] = event_id
        src_dev_list_dict = json.loads(srcList)
        event_dict['src_dev_list'] = src_dev_list_dict
        event_list.append(event_dict)
    except Exception as e:
        msg = MyLog.color_red('raise_event has except: ' + str(e))
        MyLog.logger.error(msg)

def get_attribute_value(key_list):
    try:
        dev_id = key_list[1]
        attr_name = key_list[3]
        attrs_dict = DevCall.get_attributes(dev_id, attr_name)
        if attrs_dict:
            for key_index in range(4, len(key_list)):
                key = key_list[key_index]
                name, index = EventHandle.get_array_name_and_index(key)
                if index:
                    attrs_dict = attrs_dict[name][index]
                else:
                    attrs_dict = attrs_dict[key]
            return attrs_dict
        else:
            return None
    except Exception as e:
        msg = MyLog.color_red('get_attribute_value has except: ' + str(e))
        MyLog.logger.error(msg)
        return None
