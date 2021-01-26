__date__ = '2020/10/24'
__author__ = 'wanghaiquan'
import eventlet
import os
import sys
import json
import time
from threading import Timer
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko.runners import ServiceRunner
from rule.rule_mng import RuleMng
from rule.event_handle import EventHandle
from log.log import MyLog
from common.ret_value import g_retValue
service_is_ready = False
start_ts = time.time()
class RuleNameko:
    url = None
    nameko_fd = None

    @staticmethod
    def open(url = {'AMQP_URI': 'amqp://guest:guest@127.0.0.1'}):
        if not RuleNameko.nameko_fd:
            RuleNameko.url = url
            eventlet.monkey_patch(all = False, os =True, select=True, socket=True, thread=True, time=True)
            RuleNameko.nameko_fd = ServiceRunner(config = url)
            RuleNameko.nameko_fd.add_service(RuleService)
            RuleNameko.nameko_fd.start()
            global service_is_ready
            service_is_ready = False
        return True

def service_ready():
    global service_is_ready
    global start_ts
    if service_is_ready:
        return True
    elif time.time() - start_ts > 5:
        service_is_ready = True
        msg = MyLog.color_green('rule engine rpc service ready')
        MyLog.logger.info(msg)
        return True
    else:
        return False

def set_service_ready():
    global service_is_ready
    service_is_ready = True

class RuleService:
    name = "RuleService"
    dispatch = EventDispatcher()

    #=============service=========================
    '''添加规则
    rules = [
        {
            "uuid":"",
            "enable": true,
            "type": "timer",
            "priority": 55,
            "date":[
                {
                    "startDate":"2020-10-01",
                    "endDate":"2020-10-08"
                }
            ],
            "time":[
                {
                    "startTime":"00:00:00",
                    "endTime":"18:00:00"
                }
            ],
            "srcDevice":[
                "s1","s2"
            ],
            "dstDevice":[
                "d1","d2"
            ],
            "script":""
        }
    ]
    '''

    @rpc
    def add_rule(self, rules)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(rules)
        msg = MyLog.color_green('rpc call add_rule: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.add_rule(rules)

    '''更新规则
    rules = [
        {
            "uuid":"",
            "enable": true,
            "type": "timer",
            "priority": 55,
            "date":[
                {
                    "startDate":"2020-10-01",
                    "endDate":"2020-10-08"
                }
            ],
            "time":[
                {
                    "startTime":"00:00:00",
                    "endTime":"18:00:00"
                }
            ],
            "srcDevice":[
                "s1","s2"
            ],
            "dstDevice":[
                "d1","d2"
            ],
            "script":""
        }
    ]
    '''
    @rpc
    def update_rule(self, rules)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(rules)
        msg = MyLog.color_green('rpc call update_rule: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.update_rule(rules)

    '''获取指定uuid的规则
    入参 
        uuids = [
            "uuid1","uuid2"
        ]
    }
    返回 1. 结果码
        2. 规则列表
        {
            rules:[
                {
                    "uuid":"",
                    "enable": true,
                    "type": "timer",
                    "priority": 55,
                    "date":[
                        {
                            "startDate":"2020-10-01",
                            "endDate":"2020-10-08"
                        }
                    ],
                    "time":[
                        {
                            "startTime":"00:00:00",
                            "endTime":"18:00:00"
                        }
                    ],
                    "srcDevice":[
                        "s1","s2"
                    ],
                    "dstDevice":[
                        "d1","d2"
                    ],
                    "script":""
                }
            ]
        }
    '''
    @rpc
    def get_rule_by_uuid(self, uuids)->(int, dict):
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value, {}
        payload = json.dumps(uuids)
        msg = MyLog.color_green('rpc call get_rule_by_uuid: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.get_rule_by_uuid(uuids)

    '''获取所有uuid的规则
    返回 1. 结果码
        2. 规则字典
        {
            rules:[
                {
                    "uuid":"",
                    "enable": true,
                    "type": "timer",
                    "priority": 55,
                    "date":[
                        {
                            "startDate":"2020-10-01",
                            "endDate":"2020-10-08"
                        }
                    ],
                    "time":[
                        {
                            "startTime":"00:00:00",
                            "endTime":"18:00:00"
                        }
                    ],
                    "srcDevice":[
                        "s1","s2"
                    ],
                    "dstDevice":[
                        "d1","d2"
                    ],
                    "script":""
                }
            ]
        }
    '''
    @rpc
    def get_all_rules(self)->(int, dict):
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value, {}
        msg = MyLog.color_green('rpc call get_all_rules')
        MyLog.logger.info(msg)
        return RuleMng.get_all_rules()

    '''删除指定uuid的规则
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @rpc
    def delete_rule_by_uuid(self, uuids)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(uuids)
        msg = MyLog.color_green('rpc call delete_rule_by_uuid: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.delete_rule_by_uuid(uuids)


    '''清空所有规则'''
    @rpc
    def clear_all_rule(self)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        msg = MyLog.color_green('rpc call clear_all_rule')
        MyLog.logger.info(msg)
        return RuleMng.clear_all_rule()

    '''设置规则可用
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @rpc
    def enable_rule(self, uuids)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(uuids)
        msg = MyLog.color_green('rpc call enable_rule: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.enable_rule(uuids)

    '''设置规则不可用
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @rpc
    def disable_rule(self, uuids)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(uuids)
        msg = MyLog.color_green('rpc call disable_rule: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.disable_rule(uuids)

    '''停止联动规则执行
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @rpc
    def stop_linkage_rule_running(self, uuids)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(uuids)
        msg = MyLog.color_green('rpc call stop_linkage_rule_running: %s'%(payload))
        MyLog.logger.info(msg)
        #删除指令列表中指定uuid的指令
        return RuleMng.stop_linkage_rule_running(uuids)

    '''外部联动
    services = [
        {
            "uuid":"",
            "priority": 55,
            "script":""
        }
    ]
    '''
    @rpc
    def outside_linkage(self, services)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(services)
        msg = MyLog.color_green('rpc call outside_linkage: %s'%(payload))
        MyLog.logger.info(msg)
        #添加联动指令到指令列表
        return RuleMng.outside_linkage(services)

    '''临时手动
    services = [
        {
            "priority": 55,
            "script":""
        }
    ]
    '''
    @rpc
    def manual_control(self, services)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(services)
        msg = MyLog.color_green('rpc call manual_control: %s'%(payload))
        MyLog.logger.info(msg)
        return RuleMng.manual_control(services)

    '''
    services = [
        {
            "productId":"",
            "devId":"",
            "service":""
        }
    ]
    '''
    @rpc
    def stop_manual_control(self, services)->int:
        if not service_ready():
            return g_retValue.qjBoxOpcodeSucess.value
        payload = json.dumps(services)
        msg = MyLog.color_green('rpc call stop_manual_control: %s'%(payload))
        MyLog.logger.info(msg)
        # 删除指令队列中指定方法类型为manual的指令。
        return RuleMng.stop_manual_control(services)


    '''
    事件通知
    product_id 产品ID
    dev_id 设备ID
    event 事件ID
    payload 事件报文的params的字符串
    '''
    @rpc
    def event_notice(self, product_id, dev_id, event, payload)->None:
        if not service_ready():
            return None
        msg = MyLog.color_green('rpc call event_notice, dev_id:%s, event:%s, payload:%s'%(dev_id, event, payload))
        MyLog.logger.info(msg)
        if EventHandle.update_event(product_id, dev_id, event, payload):
            #根据dev_id，触发与其相关的联动脚本执行
            timer = Timer(0, RuleMng.run_linkage_rule_by_devid, args=(dev_id, None, ))
            timer.start()

    '''
    属性改变通知
    '''
    @rpc
    def attribute_notice(self, product_id, dev_id, attrs)->None:
        if not service_ready():
            return None
        msg = MyLog.color_green('rpc call attribute_notice, dev_id:%s'%(dev_id))
        MyLog.logger.debug(msg)
        timer = Timer(0, RuleMng.run_linkage_rule_by_devid, args=(dev_id, attrs, ))
        timer.start()

    '''
    设置规则引擎日志打印级别
    '''
    @rpc
    def set_log_level(self, level)->None:
        if not service_ready():
            return None
        MyLog.set_level(level)

    '''
    查询规则引擎就绪状态
    '''
    @rpc
    def rule_engine_ready(self)->bool:
        return service_ready()