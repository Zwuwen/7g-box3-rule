__date__ = '2020/10/26'
__author__ = 'wanghaiquan'
from datetime import datetime, timedelta
import json
import os
import time
import sys
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
sys.path.append('/tmp')
sys.path.append('/')
import importlib
import shutil
from db.sqlite_interface import SqliteInterface
from script.script_conver import conver_to_py, write_file
from common.time_compare import compare_time
from command.dev_command_queue_mng import DevCommandQueueMng
from command.command_info import CommandInfo
from rpc_call.client import EventReport
from threading import Timer
from rule.rule_end_mng import *
from common.ret_value import g_retValue
from config import RULE_JS_SCRIPT_FOLDER, RULE_PY_SCRIPT_FOLDER, RULE_PY_MODEL_PATH
from log.log import MyLog
g_rule_timer = None
class RuleMng:
    '''定时规则决策，筛选符合事件要求的规则，并将规则指令下发给指令管理器，计算出下一次规则决策时间并返回'''
    @classmethod
    def timer_rule_decision(cls)->None:
        try:
            MyLog.logger.info('进行定时规则决策')
            #计算出下一次最近的执行时间戳,启动定时器
            next_decision_time = cls.get_closest_timestamp()
            if next_decision_time > 0.0:
                RuleMng.start_new_rule_decision_timer(next_decision_time)
            #获取符合要求的uuid列表
            uuid_list = SqliteInterface.get_current_timer_rule()
            #执行规则，将规则指令下发给指令管理器
            MyLog.logger.info('uuid_list size: ' + str(len(uuid_list)))
            dev_id_list = []
            rule_endtime_list = []
            for uuid in uuid_list:
                MyLog.logger.info('===开始执行规则(%s)==='%(uuid))
                priority = SqliteInterface.get_priority_by_uuid(uuid)
                if priority < 0:
                    continue
                py_model = RULE_PY_MODEL_PATH + uuid
                EventReport.report_rule_start_event(uuid)
                #记录规则结束时间戳到全局变量g_running_rule，等待结束上报结束事件
                start_ts, end_ts = cls.get_rule_timestamp(uuid)
                MyLog.logger.info('规则(%s)结束时间戳:%d'%(uuid, end_ts))
                if end_ts > 0:
                    rule_endtime_list.append({'uuid': uuid, "end_ts": end_ts})
                #执行脚本
                file = importlib.import_module(py_model)
                importlib.reload(file)
                #dev_command_list = [{'product_id': '', 'dev_id': "", "command_list":[{'service':'', 'param': , 'time': 10}]}]
                #event_list = event_list = [{"event_id":"", "src_dev_list":[{"productId":"p_id", "deviceId":"d_id"}]}]
                dev_command_list, event_list, attr_list = file.script_fun()
                ts = time.time()
                for dev_command in dev_command_list:
                    command_info_list = []
                    for command in dev_command['command_list']:
                        command_info = CommandInfo(uuid, command['service'], command['param'], ts, ts + command['time'], priority, 'timer')
                        command_info_list.append(command_info)
                    if command_info_list:
                        DevCommandQueueMng.add_timer_command(dev_command['product_id'], dev_command['dev_id'], command_info_list)
                        dev_id_list.append(dev_command['dev_id'])
                        DevCommandQueueMng.dev_exe_by_command_list(dev_command['dev_id'], command_info_list)

                for custom_event in event_list:
                    EventReport.report_linkage_custom_event(custom_event['event_id'], custom_event['src_dev_list'])
                MyLog.logger.info('===结束执行规则(%s)==='%(uuid))

            add_running_rule_endtime(rule_endtime_list)
        except Exception as e:
            msg = MyLog.color_red("timer_rule_decision has except: " + str(e))
            MyLog.logger.error(msg)

    '''获取指定规则的开始时间戳和结束时间戳'''
    @classmethod
    def get_rule_timestamp(cls, uuid)->(float, float):
        date_list, time_list = SqliteInterface.get_date_time_by_uuid(uuid)
        if not date_list or not time_list:
            msg = MyLog.color_red("get_rule_timestamp has not date_list or time_list")
            MyLog.logger.error(msg)
            return 0, 0

        now_datetime = datetime.now()
        now_time = now_datetime.time()
        is_find_time = False
        for t in time_list:
            if compare_time(t['start_time'], now_time) and compare_time(now_time, t['end_time']):
                #规则时间段没有跨天
                end_time = t['end_time']
                start_time = t['start_time']
                end_datetime = datetime(now_datetime.year, now_datetime.month, now_datetime.day, end_time.hour, end_time.minute, end_time.second)
                start_datetime = datetime(now_datetime.year, now_datetime.month, now_datetime.day, start_time.hour, start_time.minute, start_time.second)
                is_find_time = True
                break
            elif compare_time(t['end_time'], t['start_time']) and\
                (compare_time(t['start_time'], now_time) or compare_time(now_time, t['end_time'])):
                #规则时间段跨天
                today_is_end_day = False
                end_time = t['end_time']
                start_time = t['start_time']
                for date in date_list:
                    if now_datetime.year == date['end_date'].year and now_datetime.month == date['end_date'].month and now_datetime.day == date['end_date'].day:
                        #如果当天为规则日期的最后一天，并且时间段跨天，那么规则要在0点的时候结束
                        today_is_end_day = True
                        break
                if today_is_end_day:
                    end_datetime = datetime(now_datetime.year, now_datetime.month, now_datetime.day, 23, 59, 59)
                else:
                    next_day = datetime.now() + timedelta(days=1)
                    end_datetime = datetime(next_day.year, next_day.month, next_day.day, end_time.hour, end_time.minute, end_time.second)
                start_datetime = datetime(now_datetime.year, now_datetime.month, now_datetime.day, start_time.hour, start_time.minute, start_time.second)
                is_find_time = True
                break

        if is_find_time:
            start_timestamp = datetime.timestamp(start_datetime)
            end_timestamp = datetime.timestamp(end_datetime)
            return start_timestamp, end_timestamp
        else:
            msg = MyLog.color_red("get_rule_timestamp not find corresponding time")
            MyLog.logger.error(msg)
            return 0, 0

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
    @classmethod
    def add_rule(cls, rules)->int:
        try:
            for rule_dict in rules:
                ret = cls.__check_rule_param(rule_dict)
                if ret != g_retValue.qjBoxOpcodeSucess.value:
                    msg = MyLog.color_red('check_rule_param failed')
                    MyLog.logger.error(msg)
                    return ret

                if SqliteInterface.rule_exist(rule_dict['uuid']):
                    msg = MyLog.color_red("rule(%s) has exist"%(rule_dict['uuid']))
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value



            for rule_dict in rules:
                if not os.path.exists(RULE_JS_SCRIPT_FOLDER):
                    os.makedirs(RULE_JS_SCRIPT_FOLDER)
                if not os.path.exists(RULE_PY_SCRIPT_FOLDER):
                    os.makedirs(RULE_PY_SCRIPT_FOLDER)
                #将平台下发的规则脚本转换成py脚本，并将两个脚本内容都保存到文件，以uuid为文件名。
                js_path = RULE_JS_SCRIPT_FOLDER + "/" + rule_dict['uuid'] + '.js'
                py_path = RULE_PY_SCRIPT_FOLDER + "/" + rule_dict['uuid'] + '.py'
                MyLog.logger.info("js_path:%s"%(js_path))
                MyLog.logger.info("py_path:%s"%(py_path))
                write_file(rule_dict['script'], js_path)
                conver_to_py(rule_dict['script'], py_path)

                #将规则插入数据库
                SqliteInterface.add_rule(rule_dict['uuid'], rule_dict['enable'], rule_dict['type'], rule_dict['priority'], rule_dict['date'], rule_dict['time'],
                rule_dict['srcDevice'], rule_dict['dstDevice'], js_path, py_path)

            #规则决策
            RuleMng.start_new_rule_decision_timer(0)
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('add_rule has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''获取指定uuid的规则
    入参
        uuids = [
            "uuid1","uuid2"
        ]

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
    @classmethod
    def get_rule_by_uuid(cls, uuids)->(int, dict):
        try:
            rules = {}
            rule_list = []
            for uuid in uuids:
                rule_dict = {}
                ret, get_rule_dict = SqliteInterface.get_rule(uuid)
                if ret:
                    rule_dict['uuid'] = uuid
                    rule_dict['enable'] = get_rule_dict['enable']
                    rule_dict['type'] = get_rule_dict['type']
                    rule_dict['priority'] = get_rule_dict['priority']
                    rule_dict['date'] = []
                    rule_dict['time'] = []
                    rule_dict['srcDevice'] = []
                    rule_dict['dstDevice'] = []
                    for date in get_rule_dict['date_list']:
                        date_dict = {}
                        date_dict['startDate'] = date['start_date']
                        date_dict['endDate'] = date['end_date']
                        rule_dict['date'].append(date_dict)

                    for time in get_rule_dict['time_list']:
                        time_dict = {}
                        time_dict['startTime'] = time['start_time']
                        time_dict['endTime'] = time['end_time']
                        rule_dict['time'].append(time_dict)

                    for dev in get_rule_dict['src_dev_list']:
                        rule_dict['srcDevice'].append(dev)

                    for dev in get_rule_dict['dst_dev_list']:
                        rule_dict['dstDevice'].append(dev)

                    script_path = get_rule_dict['script_path']
                    if os.path.exists(script_path):
                        with open(script_path, 'r', encoding='utf-8') as fp:
                            rule_dict['script'] = fp.read()

                    rule_list.append(rule_dict)
                    rules["rules"] = rule_list
            return g_retValue.qjBoxOpcodeSucess.value, rules
        except Exception as e:
            return g_retValue.qjBoxOpcodeExcept.value, None

    '''获取所有uuid的规则
    返回 1. 结果码
        2. 规则字典
    {
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
    }
    '''
    @classmethod
    def get_all_rules(cls)->(int, dict):
        ret, uuid_list = SqliteInterface.get_all_uuids()
        if ret:
            return RuleMng.get_rule_by_uuid(uuid_list)
        else:
            return g_retValue.qjBoxOpcodeHandleSqlFailure.value, None

    '''删除指定uuid的规则
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @classmethod
    def delete_rule_by_uuid(cls, uuids)->int:
        try:
            #数据库删除规则
            SqliteInterface.delete_rule(uuids)
            #删除规则脚本
            for uuid in uuids:
                js_path = RULE_JS_SCRIPT_FOLDER + "/" + uuid + '.js'
                py_path = RULE_PY_SCRIPT_FOLDER + "/" + uuid + '.py'
                pyc_path = RULE_PY_SCRIPT_FOLDER + "/" + uuid + '.pyc'
                if os.path.exists(js_path):
                    os.remove(js_path)
                if os.path.exists(py_path):
                    os.remove(py_path)
                if os.path.exists(pyc_path):
                    os.remove(pyc_path)
            #从正在运行的队列中删除
            remove_running_rule_endtime(uuids)
            DevCommandQueueMng.clear_command_by_rule_uuid(uuids)
            DevCommandQueueMng.all_dev_exe()
            #规则决策
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('delete_rule_by_uuid has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

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
    @classmethod
    def update_rule(cls, rules)->int:
        try:
            uuid_list = []
            for rule_dict in rules:
                ret = cls.__check_rule_param(rule_dict)
                if ret != g_retValue.qjBoxOpcodeSucess.value:
                    msg = MyLog.color_red('check_rule_param failed')
                    MyLog.logger.error(msg)
                    return ret

                uuid_list.append(rule_dict['uuid'])
            #数据库删除规则
            SqliteInterface.delete_rule(uuid_list)
            #删除规则脚本
            for uuid in uuid_list:
                js_path = RULE_JS_SCRIPT_FOLDER + "/" + uuid + '.js'
                py_path = RULE_PY_SCRIPT_FOLDER + "/" + uuid + '.py'
                pyc_path = RULE_PY_SCRIPT_FOLDER + "/" + uuid + '.pyc'
                if os.path.exists(js_path):
                    os.remove(js_path)
                if os.path.exists(py_path):
                    os.remove(py_path)
                if os.path.exists(pyc_path):
                    os.remove(pyc_path)
            #从正在运行的队列中删除
            remove_running_rule_endtime(uuid_list)
            #删除指令队列中的相关指令
            DevCommandQueueMng.clear_command_by_rule_uuid(uuid_list)
            DevCommandQueueMng.all_dev_exe()
            #重新添加规则
            ret = RuleMng.add_rule(rules)
            return ret
        except Exception as e:
            msg = MyLog.color_red('update_rule has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''清空所有规则'''
    @classmethod
    def clear_all_rule(cls)->int:
        try:
            #数据库清空规则
            SqliteInterface.clear_all_rule()
            #清空规则脚本
            js_path = RULE_JS_SCRIPT_FOLDER
            py_path = RULE_PY_SCRIPT_FOLDER
            if os.path.isdir(js_path):
                shutil.rmtree(js_path)
            if os.path.isdir(py_path):
                shutil.rmtree(py_path)

            DevCommandQueueMng.clear_all_command()
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('clear_all_rule has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''设置规则可用
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @classmethod
    def enable_rule(cls, uuids):
        try:
            if not uuids:
                msg = MyLog.color_red("uuids is empty")
                MyLog.logger.error(msg)
                return g_retValue.qjBoxOpcodeInputParamErr.value
            for uuid in uuids:
                if not SqliteInterface.rule_exist(uuid):
                    msg = MyLog.color_red("rule(%s) has not exist"%(uuid))
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value
            #更新数据库
            SqliteInterface.set_rule_enable(uuids)
            #规则决策
            RuleMng.start_new_rule_decision_timer(0)
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('enable_rule has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''设置规则不可用
    uuids = [
        "uuid1","uuid2"
    ]
    '''
    @classmethod
    def disable_rule(cls, uuids)->int:
        try:
            if not uuids:
                msg = MyLog.color_red("uuids is empty")
                MyLog.logger.error(msg)
                return g_retValue.qjBoxOpcodeInputParamErr.value
            for uuid in uuids:
                if not SqliteInterface.rule_exist(uuid):
                    msg = MyLog.color_red("rule(%s) has not exist"%(uuid))
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value
            #数据库删除规则
            SqliteInterface.set_rule_disable(uuids)

            #从正在运行的队列中删除
            remove_running_rule_endtime(uuids)
            DevCommandQueueMng.clear_command_by_rule_uuid(uuids)
            DevCommandQueueMng.all_dev_exe()

            #规则决策
            RuleMng.start_new_rule_decision_timer(0)
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('disable_rule has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    @classmethod
    def run_linkage_rule_by_devid(cls, dev_id, attrs)->None:
        try:
            MyLog.logger.info(f'##########run_linkage_rule_by_devid({dev_id} attrs: {attrs})############')
            uuid_list = SqliteInterface.get_current_linkage_rule_by_src_devid(dev_id)
            msg = f"get_current_linkage_rule_by_src_devid({dev_id}, sizeof uuid_list = {len(uuid_list)})"
            MyLog.logger.debug(msg)
            for uuid in uuid_list:
                py_path = RULE_PY_SCRIPT_FOLDER + "/" + uuid + '.py'
                if not os.path.exists(py_path):
                    msg = MyLog.color_red("run_linkage_rule_by_devid: py(%s) is not exist"%(py_path))
                    MyLog.logger.error(msg)
                    continue
                #执行脚本
                py_import_path = RULE_PY_MODEL_PATH + uuid
                MyLog.logger.debug('py_import_path: ' + py_import_path)
                file = importlib.import_module(py_import_path)
                importlib.reload(file)
                MyLog.logger.debug('run script fun')
                #dev_command_list = [{'product_id': '', 'dev_id': "", "command_list":[{'service':'', 'param':'', 'time':10 }]}]
                dev_command_list, event_list, attr_list = file.script_fun()
                msg = f'dev_command_list size: {len(dev_command_list)}, event_list size: {len(event_list)}'
                MyLog.logger.debug(msg)
                if attrs:
                    allow_exe = RuleMng.attrs_has_one_in_changed(dev_id, attr_list, attrs)
                else:
                    allow_exe = True
                MyLog.logger.debug(f'allow exe: {allow_exe}')
                if allow_exe and (dev_command_list or event_list):
                    priority = SqliteInterface.get_priority_by_uuid(uuid)
                    if priority < 0:
                        continue
                    current_ts = time.time()
                    # 上报规则开始执行
                    EventReport.report_rule_start_event(uuid)
                    continue_time = 1
                    for dev_command in dev_command_list:
                        command_info_list = []
                        for command in dev_command['command_list']:
                            if continue_time < command['time']:
                                continue_time = command['time']
                            command_info = CommandInfo(uuid, command['service'], command['param'], current_ts, current_ts + command['time'], priority, 'linkage')
                            command_info_list.append(command_info)
                        if command_info_list:
                            DevCommandQueueMng.add_linkage_command(dev_command['product_id'], dev_command['dev_id'], command_info_list)

                    end_ts = current_ts + continue_time
                    uuid_endtime_list = [{'uuid': uuid, 'end_ts': end_ts}]
                    add_running_rule_endtime(uuid_endtime_list)

                    for custom_event in event_list:
                        EventReport.report_linkage_custom_event(custom_event['event_id'], custom_event['src_dev_list'])
        except Exception as e:
            msg = MyLog.color_red('run_linkage_rule_by_devid has except: ' + str(e))
            MyLog.logger.error(msg)

    #停止联动规则执行
    @classmethod
    def stop_linkage_rule_running(cls, uuids)->int:
        try:
            for uuid in uuids:
                rule_type = SqliteInterface.get_type_by_uuid(uuid)
                if not rule_type or rule_type != 'linkage':
                    msg = MyLog.color_red("stop_linkage_rule_running the type of input uuid is invalid")
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

            DevCommandQueueMng.clear_command_by_rule_uuid(uuids)
            remove_running_rule_endtime(uuids)
            DevCommandQueueMng.all_dev_exe()

            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('stop_linkage_rule_running has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''外部联动
    services = [
            {
                "uuid":"",
                "priority": 55,
                "script":""
            }
        ]
    '''
    @classmethod
    def outside_linkage(cls, services)->int:
        try:
            keys = {'uuid', 'priority', 'script'}
            for service_dict in services:
                if not cls.__check_keys_exists(service_dict, keys):
                    #返回参数错误
                    msg = MyLog.color_red('必要参数不存在')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                if type(service_dict['uuid']) != str or service_dict['uuid'] == '':
                    msg = MyLog.color_red('uuid param is invalid')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                if type(service_dict['script']) != str or service_dict['script'] == '':
                    msg = MyLog.color_red('script param is invalid')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                if type(service_dict['priority']) != int or service_dict['priority'] < 1 or service_dict['priority'] > 99:
                    msg = MyLog.color_red('priority param is invalid')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

            for service_dict in services:
                uuid = service_dict['uuid']
                py_path = "/tmp/" + uuid + '.py'
                pyc_path = "/tmp/" + uuid + '.pyc'
                conver_to_py(service_dict['script'], py_path)
                if not os.path.exists(py_path):
                    msg = MyLog.color_red("outside_linkage: py(%s) is not exist"%(py_path))
                    MyLog.logger.error(msg)
                    continue
                #执行脚本
                file = importlib.import_module(uuid)
                importlib.reload(file)
                #dev_command_list = [{'product_id': '', 'dev_id': "", "command_list":[{'service':'', 'param':'', 'time':10 }]}]
                dev_command_list, event_list, attr_list = file.script_fun()
                MyLog.logger.debug('dev_command_list size: %d'%(len(dev_command_list)))
                if dev_command_list or event_list:
                    current_ts = time.time()
                    # 上报规则开始执行
                    EventReport.report_rule_start_event(uuid)
                    continue_time = 1
                    for dev_command in dev_command_list:
                        command_info_list = []
                        for command in dev_command['command_list']:
                            if continue_time < command['time']:
                                continue_time = command['time']
                            command_info = CommandInfo(uuid, command['service'], command['param'], current_ts, current_ts + command['time'], service_dict['priority'], 'linkage')
                            MyLog.logger.debug("append command priority = %d"%(service_dict['priority']))
                            command_info_list.append(command_info)
                        if command_info_list:
                            MyLog.logger.debug('#add_linkage_command')
                            DevCommandQueueMng.add_linkage_command(dev_command['product_id'], dev_command['dev_id'], command_info_list)

                    end_ts = current_ts + continue_time
                    uuid_endtime_list = [{'uuid': uuid, 'end_ts': end_ts}]
                    add_running_rule_endtime(uuid_endtime_list)

                    for custom_event in event_list:
                        EventReport.report_linkage_custom_event(custom_event['event_id'], custom_event['src_dev_list'])
                if os.path.exists(py_path):
                    os.remove(py_path)
                if os.path.exists(pyc_path):
                    os.remove(pyc_path)
                return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('outside_linkage in rule_mng has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value


    '''临时手动
    services = [
            {
                "priority": 55,
                "script":""
            }
        ]
    '''
    #临时手动
    @classmethod
    def manual_control(cls, services)->int:
        try:
            keys = {'priority', 'script'}
            for service_dict in services:
                if not cls.__check_keys_exists(service_dict, keys):
                    #返回参数错误
                    msg = MyLog.color_red('必要参数不存在')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                if type(service_dict['script']) != str or service_dict['script'] == '':
                    msg = MyLog.color_red('script param is invalid')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                if type(service_dict['priority']) != int or service_dict['priority'] < 1 or service_dict['priority'] > 99:
                    msg = MyLog.color_red('priority param is invalid')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

            for service_dict in services:
                current_ts = time.time()
                py_file_name = '%d'%(current_ts * 1000000) 
                py_path = "/tmp/" + py_file_name + '.py'
                pyc_path = "/tmp/" + py_file_name + '.pyc'
                conver_to_py(service_dict['script'], py_path)
                #执行脚本
                file = importlib.import_module(py_file_name)
                importlib.reload(file)
                #dev_command_list = [{'product_id': '', 'dev_id': "", "command_list":[{'service':'', 'param':'', "time":10}]}]
                dev_command_list, event_list, attr_list = file.script_fun()
                if dev_command_list:
                    current_ts = time.time()
                    for dev_command in dev_command_list:
                        command_info_list = []
                        for command in dev_command['command_list']:
                            command_info = CommandInfo('manual', command['service'], command['param'], current_ts, current_ts + command['time'], service_dict['priority'], 'manual')
                            command_info_list.append(command_info)

                        if command_info_list:
                            DevCommandQueueMng.add_manual_command(dev_command['product_id'], dev_command['dev_id'], command_info_list)
                if os.path.exists(py_path):
                    os.remove(py_path)
                if os.path.exists(pyc_path):
                    os.remove(pyc_path)
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('manual_control in rule_mng has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    '''
    停止临时手动控制
    services = [
            {
                "productId":"",
                "devId":"",
                "service":""
            }
        ]
    '''
    @classmethod
    def stop_manual_control(cls, services)->int:
        try:
            keys = {'productId', 'devId', 'service'}
            for service_dict in services:
                if not cls.__check_keys_exists(service_dict, keys):
                    #字段不存在
                    msg = MyLog.color_red('必要参数不存在')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                pid = service_dict['productId']
                did = service_dict['devId']
                srv = service_dict['service']

                if type(pid) != str or type(did) != str or type(srv) != str:
                    #数据类型错误
                    msg = MyLog.color_red('参数数据类型错误')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

                if pid == "" or did == "" or srv == "":
                    #数据值为空
                    msg = MyLog.color_red('参数字符串数据为空字符串')
                    MyLog.logger.error(msg)
                    return g_retValue.qjBoxOpcodeInputParamErr.value

            dev_id_list = []
            for service_dict in services:
                DevCommandQueueMng.clear_manual_command(service_dict['productId'], service_dict['devId'], service_dict['service'])
                dev_id_list.append(service_dict['devId'])
            DevCommandQueueMng.dev_list_exe(dev_id_list)
            return g_retValue.qjBoxOpcodeSucess.value
        except Exception as e:
            msg = MyLog.color_red('stop_manual_control in rule_mng has except: ' + str(e))
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeExcept.value

    #校验keys中的可以是否都在字典的key值中存在，支持用.来表示层级关系，比如'a.b'表示{"a":{"b":1}}
    @classmethod
    def __check_keys_exists(cls, dict, keys)->bool:
        for key in keys:
            sub_keys = key.split('.')
            d = dict
            for sub_key in sub_keys:
                if type(d).__name__ == 'list':
                    d = d[0].get(sub_key)
                else:
                    d = d.get(sub_key)
                if d is None:
                    return False
        return True

    #计算出下一次最近的执行时间戳，即所有enable规则的开始时间和结束时间中距离当前时间最近的时间点
    @classmethod
    def get_closest_timestamp(cls)->float:
        time_list = SqliteInterface.get_all_enable_timer_rule_time_list()
        if not time_list:
            MyLog.logger.debug("time_list is none")
            return 0.0

        now_datetime = datetime.now()
        now_time = now_datetime.time()
        closest_time = None
        smallest_time = time_list[0]
        for time in time_list:
            #在当前时间点之后 且 小于之前的最小值
            if compare_time(now_time, time):
                if closest_time == None:
                    closest_time = time
                else:
                    if compare_time(time, closest_time):
                        closest_time = time

            if compare_time(time, smallest_time):
                smallest_time = time

        if closest_time == None:
            #下一天最早的时间
            MyLog.logger.debug("time is in next day")
            next_day = datetime.now() + timedelta(days=1)
            closest_datetime = datetime(next_day.year, next_day.month, next_day.day, smallest_time.hour, smallest_time.minute, smallest_time.second, smallest_time.microsecond)
        else:
            closest_datetime = datetime(now_datetime.year, now_datetime.month, now_datetime.day, closest_time.hour, closest_time.minute, closest_time.second, smallest_time.microsecond)

        closest_timestamp = datetime.timestamp(closest_datetime)
        now_timestamp = datetime.timestamp(now_datetime)
        t = closest_timestamp - now_timestamp
        return t

    #启动新的规则决策执行的定时器
    @classmethod
    def start_new_rule_decision_timer(cls, ts):
        MyLog.logger.info('启动一个新的规则决策定时器，倒计时: ' + str(ts) + ' 秒')
        global g_rule_timer
        if g_rule_timer:
            g_rule_timer.cancel()
        g_rule_timer = Timer(ts, RuleMng.timer_rule_decision)
        g_rule_timer.start()

    '''
    #判断规则的指定设备的属性条件列表中是否有某个属性在设备服务上报的属性变化中
    #在change_attrs中查找attrs里面的属性，attrs有任何一个属性在
    #change_attrs中能够找到即返回True，否则返回False
    dev_id: 设备ID
    attr_list: ["productId.devId.properties.bri"]
    change_attrs: {"attr1":1, "attr2":"2"}
    '''
    @classmethod
    def attrs_has_one_in_changed(cls, dev_id:str, attr_list:list, change_attrs:dict):
        for attr_str in attr_list:
            key_list = attr_str.split(".")
            if key_list[2] == "properties" and key_list[1] == dev_id:
                attr_dict = change_attrs
                find = True
                if len(key_list) < 4:
                    find = False
                else:
                    MyLog.logger.debug(f"key_list: {key_list}")
                    for attr_index in range(3, len(key_list)):
                        attr_name = key_list[attr_index]
                        MyLog.logger.debug(f"attr_index: {attr_name}")
                        name, index = RuleMng.get_array_name_and_index(attr_name)
                        MyLog.logger.debug(f"name:{name}, index:{index}")
                        if index:
                            if name in attr_dict.keys() and type(attr_dict[name] == 'list'):
                                attr_dict = attr_dict[name][index]
                            else:
                                find = False
                                break
                        else:
                            MyLog.logger.debug(f"name: {attr_name}")
                            MyLog.logger.debug(f"attr_dict: {attr_dict}")
                            if attr_name in attr_dict.keys():
                                attr_dict = attr_dict[attr_name]
                            else:
                                find = False
                                break
                if find:
                    return True
        return False

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

    @classmethod
    def __check_rule_param(cls, rule_dict)->int:
        keys = {'uuid', 'enable', 'type', 'priority', 'date', 'date.startDate', 'date.endDate', 'time', "time.startTime", "time.endTime",
            'srcDevice', 'dstDevice', 'script'}

        if 'date' not in rule_dict.keys() or type(rule_dict['date']) != list or len(rule_dict['date']) == 0:
            msg = MyLog.color_red('date param invalid')
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if 'time' not in rule_dict.keys() or type(rule_dict['time']) != list or len(rule_dict['time']) == 0:
            msg = MyLog.color_red('time param invalid')
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if not cls.__check_keys_exists(rule_dict, keys):
            #返回参数错误
            msg = MyLog.color_red('key param not exist')
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        #判断数据类型和值
        if type(rule_dict['uuid']) != str or rule_dict['uuid'] == '':
            msg = MyLog.color_red('rule uuid param is invalid')
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if type(rule_dict["enable"]) != bool:
            msg = MyLog.color_red("rule enable is not boolean")
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if type(rule_dict["type"]) != str or (rule_dict["type"] != "timer" and rule_dict["type"] != "linkage"):
            msg = MyLog.color_red("rule type is invalid")
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if type(rule_dict["priority"]) != int or rule_dict["priority"] < 1 or rule_dict["priority"] > 99:
            msg = MyLog.color_red("priority param is invalid")
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if type(rule_dict['script']) != str or rule_dict['script'] == '':
            msg = MyLog.color_red('rule script param is invalid')
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if rule_dict["type"] == "linkage" and not rule_dict["srcDevice"]:
            msg = MyLog.color_red("linkage rule, srcDevice is empty")
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        if not rule_dict["dstDevice"]:
            msg = MyLog.color_red("dstDevice is empty")
            MyLog.logger.error(msg)
            return g_retValue.qjBoxOpcodeInputParamErr.value

        return g_retValue.qjBoxOpcodeSucess.value