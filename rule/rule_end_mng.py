__date__ = '2020/11/06'
__author__ = 'wanghaiquan'
'''
存储规则到期时间
提供添加，删除接口
使用一个定时器定时处理到期的规则，上报规则结束事件
'''
from threading import Timer
import time
from rpc_call.client import EventReport
from command.dev_command_queue_mng import DevCommandQueueMng
from log.log import MyLog

#记录正在执行的规则uuid:结束时间戳字典列表 [{"uuid":"", "end_ts":12345}]
g_running_rule_endtime_list = []
g_running_rule_endtime_handle_timer = None


def running_rule_endtime_handle():
    MyLog.logger.info("运行中的规则结束处理")
    current_ts = time.time()
    smallest_ts = 0
    uuid_list = []
    for rule in g_running_rule_endtime_list:
        if rule['end_ts'] < current_ts:
            MyLog.logger.info("规则(%s)结束"%(rule['uuid']))
            g_running_rule_endtime_list.remove(rule)
            uuid_list.append(rule['uuid'])
            # 上报规则结束事件
            EventReport.report_rule_end_event(rule['uuid'])
        else:
            if smallest_ts == 0:
                smallest_ts = rule['end_ts']
            elif rule['end_ts'] < smallest_ts:
                smallest_ts = rule['end_ts']

    if uuid_list:
        # 删除结束规则的指令
        DevCommandQueueMng.clear_command_by_rule_uuid(uuid_list)
        # 所有设备队列重新执行指令决策
        DevCommandQueueMng.all_dev_exe()

    global g_running_rule_endtime_handle_timer
    if g_running_rule_endtime_handle_timer:
        g_running_rule_endtime_handle_timer.cancel()

    ts = smallest_ts - current_ts
    if ts > 0:
        g_running_rule_endtime_handle_timer = Timer(ts, running_rule_endtime_handle)
        g_running_rule_endtime_handle_timer.start()

'''uuid_end_ts_list = [{"uuid":"", "end_ts":12345}]'''
def add_running_rule_endtime(uuid_end_ts_list):
    for add in uuid_end_ts_list:
        is_new = True
        for l in g_running_rule_endtime_list:
            if add['uuid'] == l['uuid']:
                l['end_ts'] = add['end_ts']
                is_new = False
                break
        if is_new:
            new = {}
            new['uuid'] = add['uuid']
            new['end_ts'] = add['end_ts']
            g_running_rule_endtime_list.append(new)

    global g_running_rule_endtime_handle_timer
    if g_running_rule_endtime_handle_timer:
        g_running_rule_endtime_handle_timer.cancel()

    g_running_rule_endtime_handle_timer = Timer(0, running_rule_endtime_handle)
    g_running_rule_endtime_handle_timer.start()

def remove_running_rule_endtime(uuid_list):
    for uuid in uuid_list:
        for rule in g_running_rule_endtime_list:
            if rule['uuid'] == uuid:
                g_running_rule_endtime_list.remove(rule)
                EventReport.report_rule_end_event(rule['uuid'])
                break

    global g_running_rule_endtime_handle_timer
    if g_running_rule_endtime_handle_timer:
        g_running_rule_endtime_handle_timer.cancel()

    g_running_rule_endtime_handle_timer = Timer(0, running_rule_endtime_handle)
    g_running_rule_endtime_handle_timer.start()

def clear_all_running_rule_endtime():
    for rule in g_running_rule_endtime_list:
        g_running_rule_endtime_list.remove(rule)
        EventReport.report_rule_end_event(rule['uuid'])
        break

    global g_running_rule_endtime_handle_timer
    if g_running_rule_endtime_handle_timer:
        g_running_rule_endtime_handle_timer.cancel()

    g_running_rule_endtime_handle_timer = Timer(0, running_rule_endtime_handle)
    g_running_rule_endtime_handle_timer.start()