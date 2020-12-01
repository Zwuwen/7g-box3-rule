__date__ = '2020/10/29'
__author__ = 'wanghaiquan'
import os
import sys
from threading import Timer
import time
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
from command.dev_command_queue import DevCommandQueue
from rpc_call.client import EventReport, DevCall
from common.ret_value import g_retValue
from command.command_info import CommandInfo
from log.log import MyLog
'''
[{"dev_id":'', "dev_command_queue":DevCommandQueue, "timer": threading.timer}]
1. 设备id
2. 以设备为单位的指令列表对象 DevCommandQueue
3. 该设备的指令执行定时器
'''
g_dev_command_queue_list = []


class DevCommandQueueMng:
    ''' 指令执行
        成功返回True，失败返回False
    '''
    @staticmethod
    def command_exe(dev_id, command:CommandInfo)->int:
        MyLog.logger.info('指令执行 设备id:%s, 指令名称:%s, 规则:%s'%(dev_id, command.command, command.uuid))
        try:
            #先获取指令名称
            command_name = command.command
            #从该设备的指令队列中查询该指令名称正在执行的指令
            dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
            running_command = dev_command_queue.get_current_running_command(command_name)
            need_exe = False
            need_report_rule_command_cover_event = False
            if running_command:
                #判断是否为同一个规则指令，如果不是才允许执行
                MyLog.logger.info('running_command: %s, command:%s'%(running_command.uuid, command.uuid))
                if running_command.uuid != command.uuid:
                    need_exe = True
                    if not running_command.default_param:
                        need_report_rule_command_cover_event = True
            else:
                need_exe = True

            result = g_retValue.qjBoxOpcodeSucess.value
            if need_exe:
                if command.default_param:
                    #执行默认参数
                    msg = MyLog.color_green('下发默认参数指令(%s)给设备(%s)服务, 指令优先级:%d'%(command.command, dev_id, command.priority))
                    MyLog.logger.info(msg)
                    result, data = DevCall.call_service(dev_id, command.command)
                    msg = MyLog.color_green('下发默认参数指令(%s)给设备(%s)服务, 返回:%d'%(command.command, dev_id, result))
                    MyLog.logger.info(msg)
                    EventReport.report_default_command_status_event(dev_id, command.command, result)
                else:
                    #执行规则配置参数
                    msg = MyLog.color_green('下发规则(%s)指令(%s)给设备(%s)服务, 指令优先级:%d'%(command.uuid, command.command, dev_id, command.priority))
                    MyLog.logger.info(msg)
                    result, data = DevCall.call_service(dev_id, command.command, command.params)
                    msg = MyLog.color_green('下发规则(%s)指令(%s)给设备(%s)服务, 返回:%d'%(command.uuid, command.command, dev_id, result))
                    MyLog.logger.info(msg)
                    #上报ruleCommandStatus event
                    EventReport.report_rule_command_status_event(command.uuid, dev_id, command.command, result)

                if result == g_retValue.qjBoxOpcodeSucess.value:
                    dev_command_queue.set_current_running_command(command_name, command)

                if need_report_rule_command_cover_event and result == g_retValue.qjBoxOpcodeSucess.value:
                    EventReport.report_rule_command_cover_event(dev_id, command.command, running_command.uuid, command.uuid)

            return result
        except Exception as e:
            msg = MyLog.color_red('command_exe has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''针对一个设备做一次指令决策执行'''
    @staticmethod
    def dev_exe(dev_id)->None:
        MyLog.logger.info('设备(%s)所有指令执行决策'%(dev_id))
        dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
        need_run_command_list = dev_command_queue.get_highest_priority_command_list()
        MyLog.logger.info('设备(%s) need_run_command_list size:%d'%(dev_id, len(need_run_command_list)))
        is_all_success = True
        for run_command in need_run_command_list:
            MyLog.logger.info('设备(%s)run command: %s'%(dev_id,run_command.command))
            if g_retValue.qjBoxOpcodeSucess.value == DevCommandQueueMng.command_exe(dev_id, run_command):
                # 如果当前最高等级的规则类型不为联动，就要清除该指令队列中存在的类型为联动的指令
                if run_command.type != 'linkage':
                    dev_command_queue.clear_linkage_command(run_command.command)
            else:
                is_all_success = False
        #如果所有指令执行成功，那么重置定时器为所有指令中下一次最近的时间，如果有失败，那就定时60秒后重试。
        if is_all_success:
            DevCommandQueueMng.__reset_dev_timer(dev_id)
        else:
            DevCommandQueueMng.__reset_dev_timer_by_time(dev_id, 60)

    '''重置设备的指令执行定时器'''
    @staticmethod
    def __reset_dev_timer(dev_id)->None:
        dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
        nearest_ts = dev_command_queue.get_nearest_ts()
        ts = time.time()
        MyLog.logger.info('指令执行 nearest_ts: %f, ts: %f'%(nearest_ts, ts))
        if nearest_ts > ts:
            #重置定时器时间
            t = nearest_ts - ts
            MyLog.logger.info('重置设备(%s)的指令执行定时器，倒计时: %f'%(dev_id, t))
            timer = Timer(t, DevCommandQueueMng.dev_exe, args=(dev_id,))
            timer.start()
            DevCommandQueueMng.update_dev_timer(dev_id, timer)

    '''重置设备的指令执行定时器'''
    @staticmethod
    def __reset_dev_timer_by_time(dev_id, t)->None:
        MyLog.logger.info('重置设备(%s)的指令执行定时器，指定倒计时: %f'%(dev_id, t))
        timer = Timer(t, DevCommandQueueMng.dev_exe, args=(dev_id,))
        timer.start()
        DevCommandQueueMng.update_dev_timer(dev_id, timer)

    '''所有设备进行一次指令决策执行'''
    @staticmethod
    def all_dev_exe()->None:
        for d in g_dev_command_queue_list:
            DevCommandQueueMng.dev_exe(d['dev_id'])

    '''对指定的设备列表各自进行一次指令决策执行'''
    @staticmethod
    def dev_list_exe(dev_id_list)->None:
        tmp_list = list(set(dev_id_list))
        for dev_id in tmp_list:
            DevCommandQueueMng.dev_exe(dev_id)

    '''添加定时规则指令列表'''
    @staticmethod
    def add_timer_command(product_id, dev_id, command_list)->None:
        MyLog.logger.info('添加定时指令 产品ID:%s, 设备ID:%s'%(product_id, dev_id))
        dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
        if not dev_command_queue:
            dict = {}
            dict["dev_id"] = dev_id
            dev_command_queue = DevCommandQueue(product_id, dev_id)
            dict["dev_command_queue"] = dev_command_queue
            g_dev_command_queue_list.append(dict)

        highest_priority_command_list = dev_command_queue.get_highest_priority_command_list()
        for command in command_list:
            for highest_priority_command in highest_priority_command_list:
                if command.command == highest_priority_command.command:
                    if command.priority <= highest_priority_command.priority:
                        EventReport.report_rule_command_ignore_event(dev_id, command.command, command.uuid, highest_priority_command.uuid)
                    break

        dev_command_queue.add_timer_command_list(command_list)

    ''' 添加联动规则指令列表、添加平台联动指令列表
        每个指令:先与队列指令中当前指令的最高优先级进行对比，
        如果优先级比最高优先级高，执行指令
        指令执行成功，删除该指令队列中为联动规则的指令，
        然后执行指令并添加到指令队列中
        否则直接丢弃
    '''
    @staticmethod
    def add_linkage_command(product_id, dev_id, command_list)->None:
        need_add_to_command_queue_list = []
        dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
        if not dev_command_queue:
            dict = {}
            dict["dev_id"] = dev_id
            dev_command_queue = DevCommandQueue(product_id, dev_id)
            dict["dev_command_queue"] = dev_command_queue
            g_dev_command_queue_list.append(dict)

        highest_priority_command_list = dev_command_queue.get_highest_priority_command_list()
        for command in command_list:
            need_exe = True
            for highest_priority_command in highest_priority_command_list:
                if command.command == highest_priority_command.command:
                    MyLog.logger.info('command.command = %s, command.priority = %d, highest_priority_command.priority = %d'%(command.command, command.priority, highest_priority_command.priority))
                    if command.priority <= highest_priority_command.priority:
                        EventReport.report_rule_command_ignore_event(dev_id, command.command, command.uuid, highest_priority_command.uuid)
                        need_exe = False
                    break

            if need_exe:
                if g_retValue.qjBoxOpcodeSucess.value == DevCommandQueueMng.command_exe(dev_id, command):
                    dev_command_queue.clear_linkage_command(command.command)
                    need_add_to_command_queue_list.append(command)

        if need_add_to_command_queue_list:
            MyLog.logger.info('dev_command_queue.add_linkage_command_list size: %d'%(len(need_add_to_command_queue_list)))
            dev_command_queue.add_linkage_command_list(need_add_to_command_queue_list)
            name_list = dev_command_queue.get_all_command_name_list()
            DevCommandQueueMng.__reset_dev_timer(dev_id)

    '''
    添加临时手动指令
    每个指令:先与队列指令中当前指令的最高优先级进行对比，
    如果优先级比最高优先级高，执行指令
    指令执行成功，删除该指令队列中为联动规则的指令，
    然后执行指令并添加到指令队列中
    '''
    @staticmethod
    def add_manual_command(product_id, dev_id, command_list)->None:
        need_add_to_command_queue_list = []
        dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
        if not dev_command_queue:
            dict = {}
            dict["dev_id"] = dev_id
            dev_command_queue = DevCommandQueue(product_id, dev_id)
            dict["dev_command_queue"] = dev_command_queue
            g_dev_command_queue_list.append(dict)

        highest_priority_command_list = dev_command_queue.get_highest_priority_command_list()
        for command in command_list:
            command.uuid = 'manual'
            need_exe = True
            for highest_priority_command in highest_priority_command_list:
                if command.command == highest_priority_command.command:
                    if command.priority <= highest_priority_command.priority:
                        EventReport.report_rule_command_ignore_event(dev_id, command.command, command.uuid, highest_priority_command.uuid)
                        need_exe = False
                    break

            if need_exe:
                if g_retValue.qjBoxOpcodeSucess.value == DevCommandQueueMng.command_exe(dev_id, command):
                    # 如果执行临时手动指令，则联动指令已被顶替失效，删除
                    dev_command_queue.clear_linkage_command(command.command)

            need_add_to_command_queue_list.append(command)
        if need_add_to_command_queue_list:
            dev_command_queue.add_manual_command_list(need_add_to_command_queue_list)
            DevCommandQueueMng.__reset_dev_timer(dev_id)

    '''清空指定规则uuid的所有指令'''
    @staticmethod
    def clear_command_by_rule_uuid(uuid_list)->None:
        tmp_list = list(set(uuid_list))
        for dev_command_queue_obj in g_dev_command_queue_list:
            dev_command_queue:DevCommandQueue = dev_command_queue_obj['dev_command_queue']
            dev_command_queue.clear_command_by_rule_uuid(tmp_list)

    '''清除指定设备指定服务的手动控制指令'''
    @staticmethod
    def clear_manual_command(product_id, dev_id, command_name)->None:
        dev_command_queue = DevCommandQueueMng.get_dev_command_queue(dev_id)
        if dev_command_queue:
            dev_command_queue.clear_manual_command(command_name)

    '''清空所有规则'''
    @staticmethod
    def clear_all_command()->None:
        for dev_command_queue_obj in g_dev_command_queue_list:
            dev_command_queue:DevCommandQueue = dev_command_queue_obj['dev_command_queue']
            dev_command_queue.clear_all_command()
        DevCommandQueueMng.all_dev_exe()

    '''获取指定设备的指令列表对象'''
    @staticmethod
    def get_dev_command_queue(dev_id)->DevCommandQueue:
        for d in g_dev_command_queue_list:
            if dev_id == d['dev_id']:
                if 'dev_command_queue' in d:
                    return d['dev_command_queue']
                return None
        return None

    '''获取指定设备的定时器'''
    @staticmethod
    def get_dev_timer(dev_id)->Timer:
        for d in g_dev_command_queue_list:
            if dev_id == d['dev_id']:
                if 'timer' in d:
                    return d['timer']
                return None
        return None

    '''更新指定设备的定时器'''
    @staticmethod
    def update_dev_timer(dev_id, timer:Timer)->None:
        for d in g_dev_command_queue_list:
            if dev_id == d['dev_id']:
                if 'timer' in d:
                    tm:Timer = d['timer']
                    tm.cancel()
                d['timer'] = timer