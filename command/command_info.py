__date__ = '2020/10/28'
__author__ = 'wanghaiquan'

#指令信息实体类
class CommandInfo:
    #规则uuid，指令名称，指令参数，开始时间戳，结束时间戳，优先级，类型("timer","linkage", "manual")，是否为默认参数
    def __init__(self, uuid=None, command=None, params=None, start_ts=0, end_ts=0, priority=0, type='', default_param=False, effective=True):
        self.__default_param = default_param
        if self.__default_param:
            self.__uuid = 'default'
        else:
            self.__uuid = uuid
        self.__command = command
        self.__params = params
        self.__start_ts = start_ts
        self.__end_ts = end_ts
        self.__priority = priority
        self.__type = type
        self.__effective = effective


    @property
    def default_param(self):
        return self.__default_param

    @default_param.setter
    def default_param(self, dft):
        self.__default_param = dft

    @property
    def uuid(self):
        return self.__uuid

    @uuid.setter
    def uuid(self, uuid):
        self.__uuid = uuid

    @property
    def command(self):
        return self.__command

    @command.setter
    def command(self, command):
        self.__command = command

    @property
    def params(self):
        return self.__params

    @params.setter
    def params(self, params):
        self.__params = params

    @property
    def start_ts(self):
        return self.__start_ts

    @start_ts.setter
    def start_ts(self, start_ts):
        self.__start_ts = start_ts

    @property
    def end_ts(self):
        return self.__end_ts

    @end_ts.setter
    def end_ts(self, end_ts):
        self.__end_ts = end_ts

    @property
    def priority(self):
        return self.__priority

    @priority.setter
    def priority(self, priority):
        self.__priority = priority

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type):
        self.__type = type

    @property
    def effective(self):
        return self.__effective

    @effective.setter
    def effective(self, effective):
        self.__effective = effective



