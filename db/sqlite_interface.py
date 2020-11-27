__date__ = '2020/10/23'
__author__ = 'wanghaiquan'
import os
import sys
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
from db.sqlite_mng import SqliteMng

#sqlit3数据库的操作接口
class SqliteInterface:
    __sql = SqliteMng()

    @classmethod
    #添加规则
    def add_rule(cls, uuid, enable, type, priority, date_list, time_list, src_dev_list, dst_dev_list, script_path, py_path)->bool:
        return cls.__sql.add_rule(uuid, enable, type, priority, date_list, time_list, src_dev_list, dst_dev_list, script_path, py_path)

    @classmethod
    #根据uuid获取规则
    def get_rule(cls, uuid):
        return cls.__sql.get_rule(uuid)

    @classmethod
    #规则是否存在
    def rule_exist(cls, uuid)->bool:
        return cls.__sql.rule_exist(uuid)

    @classmethod
    #获取所有的uuid
    def get_all_uuids(cls):
        return cls.__sql.get_all_uuids()

    @classmethod
    #根据uuid删除规则
    def delete_rule(cls, uuid_dict)->bool:
        return cls.__sql.delete_rule(uuid_dict)

    @classmethod
    #清空所有规则
    def clear_all_rule(cls)->bool:
        return cls.__sql.clear_all_rule()

    @classmethod
    #规则设置为可用
    def set_rule_enable(cls, uuid_dict)->bool:
        return cls.__sql.set_rule_enable(uuid_dict)

    @classmethod
    #规则设置为不可用
    def set_rule_disable(cls, uuid_dict)->bool:
        return cls.__sql.set_rule_disable(uuid_dict)

    #获取规则的优先级
    @classmethod
    def get_priority_by_uuid(cls, uuid)->int:
        return cls.__sql.get_priority_by_uuid(uuid)

    #根据当前的日期时间获取所有日期时间符合的规则uuid列表
    @classmethod
    def get_current_timer_rule(cls)->list:
        return cls.__sql.get_current_timer_rule()

    #获取所有可用的定时策略的时间列表
    @classmethod
    def get_all_enable_timer_rule_time_list(cls)->list:
        return cls.__sql.get_all_enable_timer_rule_time_list()

    #通过uuid获取规则的日期时间列表
    @classmethod
    def get_date_time_by_uuid(cls, uuid):
        return cls.__sql.get_date_time_by_uuid(uuid)

    #通过触发源设备ID查找当前可用的包含触发源设备的联动规则
    @classmethod
    def get_current_linkage_rule_by_src_devid(cls, src_dev_id)->list:
        return cls.__sql.get_current_linkage_rule_by_src_devid(src_dev_id)

if __name__ == "__main__":
    from common.time_compare import quite_sort_time_list
    js = '''if (ref("productId.devId.properties.property1[0].brightness") > 1 && ref("productId.devId.properties.property2") < 1 && ref("productId.devId.events.event")) {
    call_service("productId.devId.services.service", "param1");
} else {
    raise_event("productId.another_devId.events.event", "param1");
}'''
    date_list = [{"startDate":"2020-10-01", "endDate":"2020-10-07"},{"startDate":"2020-10-10", "endDate":"2020-10-11"}]
    time_list = [{"startTime":"00:00:00", "endTime":"08:00:00"},{"startTime":"21:00:00", "endTime":"23:00:00"}]
    src_dev_list = ["s1", "s2"]
    dst_dev_list = ["d1", "d2"]
    SqliteInterface.add_rule("1111", True, "timer", 99, date_list, time_list, src_dev_list, dst_dev_list, "./rule.js", "./rule.py")

    date_list2 = [{"startDate":"2020-10-01", "endDate":"2020-10-28"},{"startDate":"2020-11-01", "endDate":"2020-11-07"}]
    time_list2 = [{"startTime":"20:00:00", "endTime":"23:00:00"}, {"startTime":"10:00:00", "endTime":"15:00:00"}]
    src_dev_list2 = ["s3", "s4"]
    dst_dev_list2 = ["d3", "d4"]
    SqliteInterface.add_rule("222", True, "timer", 99, date_list2, time_list2, src_dev_list2, dst_dev_list2, "./rule.js", "./rule.py")
    uuid_list = SqliteInterface.get_current_timer_rule()
    for uuid in uuid_list:
        print(uuid)

    rule_time_list = SqliteInterface.get_current_timer_rule()

    quite_sort_time_list(rule_time_list, 0, len(rule_time_list)-1)
    for time in rule_time_list:
        print(time)
    
    #SqliteInterface.delete_rule("1111")