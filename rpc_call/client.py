from inspect import Parameter
from nameko.standalone.rpc import ClusterRpcProxy
from nameko.rpc import rpc
from common.ret_value import g_retValue
from log.log import MyLog
import json

url = {'AMQP_URI': 'amqp://guest:guest@127.0.0.1'}

class EventReport:
    '''上报规则开始执行'''
    @staticmethod
    def report_rule_start_event(uuid):
        try:
            msg = MyLog.color_green('上报规则开始事件 uuid=%s'%(uuid))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('ruleStart', uuid=uuid)
        except Exception as e:
            msg = MyLog.color_red("report_rule_start_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''上报规则结束执行事件'''
    @staticmethod
    def report_rule_end_event(uuid):
        try:
            msg = MyLog.color_green('上报规则结束事件 uuid=%s'%(uuid))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('ruleEnd', uuid=uuid)
        except Exception as e:
            msg = MyLog.color_red("report_rule_end_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''上报规则指令执行结果事件'''
    @staticmethod
    def report_rule_command_status_event(uuid, dev_id, command, result_code):
        try:
            msg = MyLog.color_green('上报规则指令执行结果 uuid=%s, dev_id=%s, command=%s, resultCode=%d'%(uuid, dev_id, command, result_code))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('ruleCommandStatus', uuid=uuid, devId=dev_id, command=command, resultCode=result_code)
        except Exception as e:
            msg = MyLog.color_red("report_rule_command_status_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''上报规则指令被高优先级规则指令抢占事件'''
    @staticmethod
    def report_rule_command_cover_event(dev_id, command, be_cover_rule_uuid, cover_rule_uuid):
        try:
            msg = MyLog.color_green('上报指令被高优先级抢占事件 dev_id=%s, command=%s, be_cover_rule_uuid=%s, cover_rule_uuid=%s'\
                %(dev_id, command, be_cover_rule_uuid, cover_rule_uuid))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('ruleCommandCover',\
                    devId=dev_id, command=command, beCoverRuleUuid=be_cover_rule_uuid, coverRuleUuid=cover_rule_uuid)
        except Exception as e:
            msg = MyLog.color_red("report_rule_command_cover_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''上报用户自定义事件'''
    @staticmethod
    def report_linkage_custom_event(eventId, srcList):
        try:
            msg = MyLog.color_green('上报用户自定义事件 eventid=%s'%(eventId))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('customEvent', eventId=eventId, srcList=srcList)
        except Exception as e:
            msg = MyLog.color_red("report_linkage_custom_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''上报指令默认参数执行结果事件'''
    @staticmethod
    def report_default_command_status_event(dev_id, command, result_code):
        try:
            msg = MyLog.color_green('上报指令执行默认参数结果事件 dev_id=%s, command=%s, result_code=%d'%(dev_id, command, result_code))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('ruleDefaultCommandStatus', devId=dev_id, command=command, resultCode=result_code)
        except Exception as e:
            msg = MyLog.color_red("report_default_command_status_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''上报指令优先级低，忽略执行事件'''
    @staticmethod
    def report_rule_command_ignore_event(dev_id, command, uuid, higher_priority_uuid):
        try:
            msg = MyLog.color_green('上报指令忽略执行事件 dev_id=%s, command=%s, uuid=%s, higher_priority_uuid=%s'%(dev_id, command, uuid, higher_priority_uuid))
            MyLog.logger.info(msg)
            with ClusterRpcProxy(url) as rpc:
                resp = rpc.GW.raiseEvent('ruleCommandIgnore', devId=dev_id, command=command, uuid=uuid, higherPriorityUuid=higher_priority_uuid)
        except Exception as e:
            msg = MyLog.color_red("report_rule_command_ignore_event has except: " + str(e))
            MyLog.logger.error(msg)
            return None


class DevCall:
    '''
    通过RPC向设备服务获取指定设备的属性
    '''
    @staticmethod
    def get_attributes(dev_id, attr_name):
        try:
            with ClusterRpcProxy(url) as rpc:
                dev_svr_name = rpc.mng_srv.get_srv_name_from_sn(dev_id)
                if dev_svr_name:
                    msg = MyLog.color_green('RPC调用设备(%s)获取属性值(%s)'%(dev_id, attr_name))
                    MyLog.logger.info(msg)
                    function_name = 'rpc.' + dev_svr_name +'.property_read'
                    result, value = eval(function_name)(dev_id, attr_name)
                    if result == g_retValue.qjBoxOpcodeSucess.value:
                        return value
                    else:
                        return None
        except Exception as e:
            msg = MyLog.color_red("get_attributes has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    '''
    通过RPC调用设备服务
    '''
    @staticmethod
    def call_service(dev_id, service_name, params=None)->int:
        try:
            with ClusterRpcProxy(url) as rpc:
                MyLog.logger.info('查询服务名称')
                dev_svr_name = rpc.mng_srv.get_srv_name_from_sn(dev_id)
                msg = MyLog.color_green('设备(%s)的服务名为%s'%(dev_id, dev_svr_name))
                MyLog.logger.info(msg)
                if dev_svr_name:
                    if params:
                        msg = MyLog.color_green('RPC调用设备(%s)服务(%s),参数:%s'%(dev_id, service_name, json.dumps(params)))
                        MyLog.logger.info(msg)
                        function_name = 'rpc.' + dev_svr_name + '.ioctl'
                        return eval(function_name)(dev_id, service_name, params)
                    else:
                        msg = MyLog.color_green('RPC调用设备(%s)服务(%s),默认参数'%(dev_id, service_name))
                        MyLog.logger.info(msg)
                        function_name = 'rpc.' + dev_svr_name + '.set_default'
                        return eval(function_name)(dev_id, service_name)

        except Exception as e:
            msg = MyLog.color_red("call_service has except: " + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value