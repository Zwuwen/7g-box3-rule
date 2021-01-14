__date__ = '2020/10/28'
__author__ = 'wanghaiquan'
import os
import sys
import time
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
from threading import Lock
from command.command_info import CommandInfo
from log.log import MyLog

#设备指令队列，DevCommandQueue表示一个设备的所有指令
class DevCommandQueue:
    def __init__(self, product_id, dev_id):
        self.__product_id = product_id
        self.__dev_id = dev_id
        #每个指令一个子队列[{"command_name":"", "command_queue":[], "current_command":CommandInfo}]
        self.__queues = []
        self.__lock = Lock()

    @property
    def dev_id(self)->str:
        return self.__dev_id

    @property
    def product_id(self)->str:
        return self.__product_id

    #添加定时规则指令列表
    def add_timer_command_list(self, command_list)->None:
        self.__lock.acquire()
        MyLog.logger.info('添加定时指令列表到队列，列表长度: %d'%(len(command_list)))
        for command in command_list:
            command.type = 'timer'
            is_new_command = True
            for queue in self.__queues:
                if 'command_name' in queue and queue['command_name'] == command.command:
                    MyLog.logger.info(f"添加定时指令({command.command})到指令列表, uuid:{command.uuid} priority:{command.priority}")
                    #判断是否已经有相同uuid的指令存在
                    uuid_has_exist = False
                    is_new_command = False
                    for c in queue['command_queue']:
                        if c.uuid == command.uuid:
                            uuid_has_exist = True
                            #更新
                            c = command
                            MyLog.logger.info(f"更新定时指令({command.command})")
                            break

                    if not uuid_has_exist:
                        #新加
                        MyLog.logger.info(f"新加定时指令({command.command})")
                        queue['command_queue'].append(command)
                    break
            if is_new_command:
                MyLog.logger.info(f"新指令({command.command})队列")
                new_command_sub_queue = {}
                new_command_sub_queue['command_name'] = command.command
                new_command_sub_queue['command_queue'] = []
                new_command_sub_queue['current_command'] = CommandInfo(command=command.command, default_param=True)
                new_command_sub_queue['command_queue'].append(command)
                self.__queues.append(new_command_sub_queue)
        self.__lock.release()

    #添加联动规则指令列表
    def add_linkage_command_list(self, command_list)->None:
        self.__lock.acquire()
        for command in command_list:
            command.type = 'linkage'
            is_new_command = True
            for queue in self.__queues:
                if 'command_name' in queue and queue['command_name'] == command.command:
                    #判断是否已经有相同uuid的指令存在
                    uuid_has_exist = False
                    is_new_command = False
                    for c in queue['command_queue']:
                        if c.uuid == command.uuid:
                            uuid_has_exist = True
                            #更新
                            c = command
                            break

                    if not uuid_has_exist:
                        #新加
                        queue['command_queue'].append(command)
            if is_new_command:
                new_command_sub_queue = {}
                new_command_sub_queue['command_name'] = command.command
                new_command_sub_queue['command_queue'] = []
                new_command_sub_queue['current_command'] = CommandInfo(command=command.command, default_param=True)
                new_command_sub_queue['command_queue'].append(command)
                self.__queues.append(new_command_sub_queue)
        self.__lock.release()

    #添加临时手动指令列表
    #每个指令一个子队列[{"command_name":"", "command_queue":[], "current_command":CommandInfo}]
    def add_manual_command_list(self, command_list)->None:
        self.__lock.acquire()
        for command in command_list:
            command.type = 'manual'
            command.uuid = 'manual'
            is_new_command = True
            for queue in self.__queues:
                if 'command_name' in queue and queue['command_name'] == command.command:
                    #判断是否已经有相同uuid的指令存在
                    uuid_has_exist = False
                    is_new_command = False
                    for c in queue['command_queue']:
                        if c.uuid == command.uuid:
                            uuid_has_exist = True
                            #更新
                            c = command
                            break

                    if not uuid_has_exist:
                        #新加
                        queue['command_queue'].append(command)
            if is_new_command:
                new_command_sub_queue = {}
                new_command_sub_queue['command_name'] = command.command
                new_command_sub_queue['command_queue'] = []
                new_command_sub_queue['current_command'] = CommandInfo(command=command.command, default_param=True)
                new_command_sub_queue['command_queue'].append(command)
                self.__queues.append(new_command_sub_queue)
        self.__lock.release()

    #设置某类指令当前正在执行哪个指令
    #[{"command_name":"", "command_queue":[], "current_command":CommandInfo}]
    def set_current_running_command(self, command_name, command)->None:
        self.__lock.acquire()
        is_command_exist = False
        for queue in self.__queues:
            if queue['command_name'] == command_name:
                queue['current_command'] = command
                is_command_exist = True
                break
        if not is_command_exist:
            new_command_sub_queue = {}
            new_command_sub_queue['command_name'] = command.command
            new_command_sub_queue['command_queue'] = []
            new_command_sub_queue['current_command'] = command
            new_command_sub_queue['command_queue'].append(command)
            self.__queues.append(new_command_sub_queue)
        self.__lock.release()

    #获取当前某个指令名称正在执行的指令
    def get_current_running_command(self, command_name)->CommandInfo:
        self.__lock.acquire()
        for queue in self.__queues:
            if queue['command_name'] == command_name:
                self.__lock.release()
                return queue['current_command']
        self.__lock.release()
        return None

    #获取指令名称列表
    def get_all_command_name_list(self)->list:
        command_name_list = []
        self.__lock.acquire()
        for queue in self.__queues:
            if 'command_name' in queue:
                command_name_list.append(queue['command_name'])
        self.__lock.release()
        return command_name_list

    #获取每种指令中优先级最高的指令
    def get_highest_priority_command_list(self)->list:
        command_list = []
        self.__lock.acquire()
        for queue in self.__queues:
            command = self.get_highest_priority_command_by_command_name(queue['command_name'])
            if command:
                MyLog.logger.info('获取设备(%s)指令队列中最高优先级的指令(%s), 规则uuid为: %s, 优先级为:%d'\
                %(self.__dev_id, queue['command_name'], command.uuid, command.priority))
                command_list.append(command)
            else:
                msg = MyLog.color_red("command is None")
                MyLog.logger.error(msg)
        self.__lock.release()
        return command_list

    ''' 根据指令获取当前时间点可以执行的优先级最高的指令
        如果该指令队列存在，但队列为空，则返回默认指令 '''
    def get_highest_priority_command_by_command_name(self, command_name)->CommandInfo:
        ts = time.time()
        MyLog.logger.info("get_highest_priority_command_by_command_name: %s"%(command_name))
        for queue in self.__queues:
            highest_command:CommandInfo = None
            if 'command_name' in queue and queue['command_name'] == command_name:
                command_queue:list = queue["command_queue"]
                if command_queue:
                    MyLog.logger.info(f"find the highest priority command({command_name})")
                    del_command_list = []
                    for command in command_queue:
                        if command.start_ts > ts or command.end_ts < ts:
                            #指令不在有效期内，删除
                            del_command_list.append(command)
                            continue
                        if highest_command == None or command.priority > highest_command.priority:
                            MyLog.logger.info(f"new highest_command uuid:{command.uuid}, priority:{command.priority}, type:{command.type}")
                            highest_command = command
                    for del_command in del_command_list:
                        command_queue.remove(del_command)
                    if highest_command == None:
                        break
                    else:
                        return highest_command
        MyLog.logger.info(f"device({self.__dev_id}) has no command({command_name}) found")
        default_command = CommandInfo(command=command_name, default_param=True)
        return default_command

    ''' 获取距离当前时间点最近指令时间点（start_ts，end_ts）
        成功返回最近的时间戳，失败返回0 '''
    def get_nearest_ts(self)->float:
        self.__lock.acquire()
        ts = time.time()
        nearest_ts = 2236761304
        for queue in self.__queues:
            if 'command_queue' in queue:
                command_queue:list = queue["command_queue"]
                for command in command_queue:
                    if command.start_ts > ts:
                        if command.start_ts < nearest_ts:
                            nearest_ts = command.start_ts
                    elif command.end_ts > ts:
                        if command.end_ts < nearest_ts:
                            nearest_ts = command.end_ts
        if nearest_ts == ts:
            self.__lock.release()
            return 0
        else:
            self.__lock.release()
            return nearest_ts

    #清空指定规则的所有指令
    #[{"command_name":"", "command_queue":[], "current_command":CommandInfo}]
    def clear_command_by_rule_uuid(self, uuid_list)->None:
        self.__lock.acquire()
        for uuid in uuid_list:
            for queue in self.__queues:
                command_queue:list = queue['command_queue']
                for command in command_queue:
                    if command.uuid == uuid:
                        command_queue.remove(command)
        self.__lock.release()

    #清空所有指令
    def clear_all_command(self)->None:
        self.__lock.acquire()
        for queue in self.__queues:
            command_queue:list = queue['command_queue']
            command_queue.clear()
        self.__lock.release()

    #删除指定服务的手动指令
    def clear_manual_command(self, command_name)->None:
        self.__lock.acquire()
        for queue in self.__queues:
            if queue['command_name'] == command_name:
                command_queue:list = queue['command_queue']
                for command in command_queue:
                    if command.type == 'manual':
                        command_queue.remove(command)
                break
        self.__lock.release()

    #删除指定指令名称队列中的联动规则的指令
    def clear_linkage_command(self, command_name)->None:
        self.__lock.acquire()
        for queue in self.__queues:
            if queue['command_name'] == command_name:
                command_queue:list = queue['command_queue']
                for command in command_queue:
                    if command.type == 'linkage':
                        command_queue.remove(command)
                break
        self.__lock.release()

if __name__ == "__main__":
    c1 = CommandInfo('uuid1', 'command_name1', 'params1', 1603887074, 1603897074, 99)
    c2 = CommandInfo('uuid2', 'command_name1', 'params2', 1603887074, 1603897074, 50)
    cq = DevCommandQueue('product_id', 'dev id 1')
    command_list = []
    command_list.append(c1)
    command_list.append(c2)
    cq.add_timer_command_list(command_list)
    c = cq.get_highest_priority_command_by_command_name('command_name1')
    if c:
        print(c.priority)
    else:
        print("c is none")


