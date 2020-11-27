__date__ = '2020/10/24'
__author__ = 'wanghaiquan'
import eventlet
import os
import sys
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

class RuleNameko:
    url = None
    nameko_fd = None

    @staticmethod
    def open(url = {'AMQP_URI': 'amqp://guest:guest@127.0.0.1'}):
        if not RuleNameko.nameko_fd:
            RuleNameko.url = url
            eventlet.monkey_patch(all = False, os =True, select=True, socket=True, thread=False, time=True)
            RuleNameko.nameko_fd = ServiceRunner(config = url)
            RuleNameko.nameko_fd.add_service(RuleService)
            RuleNameko.nameko_fd.start()
        return True

class RuleService:
    name = "RuleService"
    dispatch = EventDispatcher()

    #=============service=========================
    '''添加规则
    payload=
    '{
        "rules":[
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
    }'
    '''
    @rpc
    def add_rule(self, payload:str)->int:
        MyLog.key('rpc call add_rule: %s'%(payload))
        return RuleMng.add_rule(payload)

    '''更新规则
    payload=
    '{
        "rules":[
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
    }'
    '''
    @rpc
    def update_rule(self, payload:str)->int:
        MyLog.key('rpc call update_rule: %s'%(payload))
        return RuleMng.update_rule(payload)

    '''获取指定uuid的规则
    入参 payload =
    '{
        "uuids":[
            "uuid1","uuid2"
        ]
    }'
    返回 1. 结果码
        2. 规则列表
        [
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
    def get_rule_by_uuid(self, payload:str)->(int, list):
        MyLog.key('rpc call get_rule_by_uuid: %s'%(payload))
        return RuleMng.get_rule_by_uuid(payload)

    '''获取所有uuid的规则
    返回 1. 结果码
        2. 规则字典
        [
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
    def get_all_rules(self)->(int, list):
        MyLog.key('rpc call get_all_rules')
        return RuleMng.get_all_rules()

    '''删除指定uuid的规则
        payload=
        '{
            "uuids":[
                "uuid1","uuid2"
            ]
        }'
    '''
    @rpc
    def delete_rule_by_uuid(self, payload:str)->int:
        MyLog.key('rpc call delete_rule_by_uuid: %s'%(payload))
        return RuleMng.delete_rule_by_uuid(payload)


    '''清空所有规则'''
    @rpc
    def clear_all_rule(self)->int:
        MyLog.key('rpc call clear_all_rule')
        return RuleMng.clear_all_rule()

    '''设置规则可用
        payload=
        '{
            "uuids":[
                "uuid1","uuid2"
            ]
        }'
    '''
    @rpc
    def enable_rule(self, payload:str)->int:
        MyLog.key('rpc call enable_rule: %s'%(payload))
        return RuleMng.enable_rule(payload)

    '''设置规则不可用
        payload=
        '{
            "uuids":[
                "uuid1","uuid2"
            ]
        }'
    '''
    @rpc
    def disable_rule(self, payload:str)->int:
        MyLog.key('rpc call disable_rule: %s'%(payload))
        return RuleMng.disable_rule(payload)

    '''停止联动规则执行
        payload=
        '{
            "uuids":[
                "uuid1","uuid2"
            ]
        }'
    '''
    @rpc
    def stop_linkage_rule_running(self, payload)->int:
        MyLog.key('rpc call stop_linkage_rule_running: %s'%(payload))
        #删除指令列表中指定uuid的指令
        return RuleMng.stop_linkage_rule_running(payload)

    '''外部联动
    payload=
    '{
        "services":[
            {
                "uuid":"",
                "priority": 55,
                "script":""
            }
        ]
    }'
    '''
    @rpc
    def outside_linkage(self, payload)->int:
        MyLog.key('rpc call outside_linkage: %s'%(payload))
        #添加联动指令到指令列表
        return RuleMng.outside_linkage(payload)

    '''临时手动
    payload=
    '{
        "services":[
            {
                "priority": 55,
                "script":""
            }
        ]
    }'
    '''
    @rpc
    def manual_control(self, payload)->int:
        MyLog.key('rpc call manual_control: %s'%(payload))
        return RuleMng.manual_control(payload)

    '''
    payload=
    '{
        "services":[
            {
                "productId":"",
                "devId":"",
                "service":""
            }
        ]
    }'
    '''
    @rpc
    def stop_manual_control(self, payload)->int:
        MyLog.key('rpc call stop_manual_control: %s'%(payload))
        # 删除指令队列中指定方法类型为manual的指令。
        return RuleMng.stop_manual_control(payload)


    '''
    事件通知
    product_id 产品ID
    dev_id 设备ID
    event 事件ID
    payload 事件报文的params的字符串
    '''
    @rpc
    def event_notice(self, product_id, dev_id, event, payload)->None:
        MyLog.key('rpc call event_notice, dev_id:%s, event:%s, payload:%s'%(dev_id, event, payload))
        if EventHandle.update_event(product_id, dev_id, event, payload):
            #根据dev_id，触发与其相关的联动脚本执行
            timer = Timer(0, RuleMng.run_linkage_rule_by_devid, [dev_id])
            timer.start()

    '''
    属性改变通知
    '''
    @rpc
    def attribute_notice(self, product_id, dev_id)->None:
        MyLog.key('rpc call attribute_notice, dev_id:%s'%(dev_id))
        timer = Timer(0, RuleMng.run_linkage_rule_by_devid, [dev_id])
        timer.start()
