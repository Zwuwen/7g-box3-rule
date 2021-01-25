import sqlite3
import sys
import os
import datetime
import time
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, relationship
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
from config import RULE_SQLITE3_FILE_PATH, RULE_SQLITE3_FILE_NAME
from db.sqlite_create import *
from log.log import MyLog

class SqliteMng:
    def __init__(self):
        if not hasattr(SqliteMng, "__sqlite_eng"):
            if not os.path.exists(RULE_SQLITE3_FILE_PATH):
                os.makedirs(RULE_SQLITE3_FILE_PATH)
            database = "sqlite:///%s?check_same_thread=False"%(RULE_SQLITE3_FILE_PATH + RULE_SQLITE3_FILE_NAME)
            self.__sqlite_eng = create_engine(database, encoding = 'utf-8', echo = False)
            create_all_tbl(self.__sqlite_eng)
            self.__session_class = sessionmaker(bind = self.__sqlite_eng)
            self.__session = self.__session_class()

    def __new__(cls, *args, **kwargs):
        #单例
        if not hasattr(SqliteMng, "_instance"):
            SqliteMng._instance = object.__new__(cls)
        return SqliteMng._instance

    def add_rule(self, uuid, enable, type, priority, date_list, time_list, src_dev_list, dst_dev_list, script_path, py_path):
        try:
            if (type != 'timer' and type != 'linkage') or (priority < 0 or priority > 99):
                #参数错误
                msg = MyLog.color_red('添加规则参数错误')
                MyLog.logger.error(msg)
                return False
            ret = self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).all()
            if (ret):
                #资源已存在
                msg = MyLog.color_red('规则uuid已存在')
                MyLog.logger.error(msg)
                return False
            element = rule_main_tbl(uuid=uuid, enable=enable, type=type, priority=priority, script_path=script_path, py_path=py_path)
            self.__session.add(element)

            for d in date_list:
                start_d = datetime.datetime.strptime(d['startDate'], "%Y-%m-%d")
                end_d = datetime.datetime.strptime(d['endDate'], "%Y-%m-%d")
                element = rule_date_tbl(uuid=uuid, start_date=start_d, end_date=end_d)
                self.__session.add(element)

            for t in time_list:
                start_h, start_m, start_s = map(int, t['startTime'].split(':'))
                end_h, end_m, end_s = map(int, t['endTime'].split(':'))
                start_t = datetime.time(start_h, start_m, start_s)
                end_t = datetime.time(end_h, end_m, end_s)
                element = rule_time_tbl(uuid=uuid, start_time=start_t, end_time=end_t)
                self.__session.add(element)

            for s in src_dev_list:
                element = rule_src_device_tbl(uuid=uuid, src_device=s)
                self.__session.add(element)

            for ds in dst_dev_list:
                element = rule_dst_device_tbl(uuid=uuid, dst_device=ds)
                self.__session.add(element)

            self.__session.commit()
            return True
        except Exception as e:
            msg = MyLog.color_red("add_rule has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    def rule_exist(self, uuid):
        try:
            main_sql = self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).all()
            if main_sql:
                return True
            else:
                return False
        except Exception as e:
            msg = MyLog.color_red("rule_exist has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    def get_rule(self, uuid):
        try:
            date_list = []
            time_list = []
            src_dev_list = []
            dst_dev_list = []
            enable = True
            type = ''
            priority = -1
            script_path = ''
            main_sql = self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).all()
            if main_sql:
                if main_sql[0].enable == 0:
                    enable = False
    
                type = main_sql[0].type
                priority = main_sql[0].priority
                script_path = main_sql[0].script_path
            else:
                return False, None

            date_sql = self.__session.query(rule_date_tbl).filter(rule_date_tbl.uuid == uuid).all()
            for date in date_sql:
                date_dict = {}
                date_dict['start_date'] = str(date.start_date)
                date_dict['end_date'] = str(date.end_date)
                date_list.append(date_dict)

            time_sql = self.__session.query(rule_time_tbl).filter(rule_time_tbl.uuid == uuid).all()
            for time in time_sql:
                time_dict = {}
                time_dict['start_time'] = time.start_time
                time_dict['end_time'] = time.end_time
                time_list.append(time_dict)

            src_dev_sql = self.__session.query(rule_src_device_tbl).filter(rule_src_device_tbl.uuid == uuid).all()
            for dev in src_dev_sql:
                src_dev_list.append(dev.src_device)

            dst_dev_sql = self.__session.query(rule_dst_device_tbl).filter(rule_dst_device_tbl.uuid == uuid).all()
            for dev in dst_dev_sql:
                dst_dev_list.append(dev.dst_device)

            return True, {'enable':enable, 'type':type, 'priority':priority, 'date_list':date_list, \
                'time_list':time_list, 'src_dev_list':src_dev_list, 'dst_dev_list':dst_dev_list, 'script_path':script_path}
        except Exception as e:
            msg = MyLog.color_red("get_rule has except: " + str(e))
            MyLog.logger.error(msg)
            return False, None

    def get_all_uuids(self):
        try:
            uuid_list = []
            sql = self.__session.query(rule_main_tbl).all()
            for info in sql:
                uuid_list.append(info.uuid)
            return True, uuid_list
        except Exception as e:
            msg = MyLog.color_red("get_all_uuids has except: " + str(e))
            MyLog.logger.error(msg)
            return False, None

    def delete_rule(self, uuid_dict):
        try:
            for uuid in uuid_dict:
                self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).delete()
                self.__session.query(rule_date_tbl).filter(rule_date_tbl.uuid == uuid).delete()
                self.__session.query(rule_time_tbl).filter(rule_time_tbl.uuid == uuid).delete()
                self.__session.query(rule_src_device_tbl).filter(rule_src_device_tbl.uuid == uuid).delete()
                self.__session.query(rule_dst_device_tbl).filter(rule_dst_device_tbl.uuid == uuid).delete()
            self.__session.commit()
            return True
        except Exception as e:
            msg = MyLog.color_red("delete_rule has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    def clear_all_rule(self):
        try:
            self.__session.query(rule_main_tbl).delete()
            self.__session.query(rule_date_tbl).delete()
            self.__session.query(rule_time_tbl).delete()
            self.__session.query(rule_src_device_tbl).delete()
            self.__session.query(rule_dst_device_tbl).delete()
            self.__session.commit()
            return True
        except Exception as e:
            msg = MyLog.color_red("clear_all_rule has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    def set_rule_enable(self, uuid_dict):
        try:
            for uuid in uuid_dict:
                self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).update({'enable':True})
            self.__session.commit()
            return True
        except Exception as e:
            msg = MyLog.color_red("set_rule_enable has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    def set_rule_disable(self, uuid_dict):
        try:
            for uuid in uuid_dict:
                self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).update({'enable':False})
            self.__session.commit()
            return True
        except Exception as e:
            msg = MyLog.color_red("set_rule_disable has except: " + str(e))
            MyLog.logger.error(msg)
            return False

    #获取指定规则的优先级，成功返回优先级，失败返回-1
    def get_priority_by_uuid(self, uuid)->int:
        try:
            main_sql = self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).all()
            for info in main_sql:
                return info.priority
            return -1
        except Exception as e:
            msg = MyLog.color_red("get_priority_by_uuid has except: " + str(e))
            MyLog.logger.error(msg)
            return -1

    #获取指定规则的类型
    def get_type_by_uuid(self, uuid)->str:
        try:
            main_sql = self.__session.query(rule_main_tbl).filter(rule_main_tbl.uuid == uuid).all()
            for info in main_sql:
                return info.type
            return None
        except Exception as e:
            msg = MyLog.color_red("get_type_by_uuid has except: " + str(e))
            MyLog.logger.error(msg)
            return None

    #筛选出当前时间点可以执行的定时规则，筛选条件：规则enable并且当前的日期时间在规则时间内
    def get_current_timer_rule(self):
        uuid_list = []
        try:
            current_date = datetime.date.today()
            current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")
            str_date = '当前日期: ' + str(current_date)
            str_time = '当前时间: ' + str(current_time)
            MyLog.logger.info(str_date)
            MyLog.logger.info(str_time)
            rule_filter = {
                and_(
                    and_(
                        rule_main_tbl.enable == True,
                        rule_main_tbl.type == 'timer',
                        rule_date_tbl.start_date <= current_date, 
                        current_date <= rule_date_tbl.end_date
                    ),
                    or_(
                        and_(
                            rule_time_tbl.start_time <= current_time, 
                            current_time <= rule_time_tbl.end_time
                        ),
                        and_(#跨天
                            rule_time_tbl.start_time >= rule_time_tbl.end_time, 
                            current_time >= rule_time_tbl.start_time
                        ),
                        and_(#跨天
                            rule_time_tbl.start_time >= rule_time_tbl.end_time, 
                            current_time <= rule_time_tbl.end_time
                        )
                    )
                )
            }
            main_sql = self.__session.query(rule_main_tbl).join(rule_date_tbl, rule_date_tbl.uuid==rule_main_tbl.uuid)\
            .join(rule_time_tbl, rule_time_tbl.uuid==rule_main_tbl.uuid)\
            .filter(*rule_filter).all()
            for info in main_sql:
                MyLog.logger.info('查找到当前时间点可用的规则，规则uuid为: ' + info.uuid)
                uuid_list.append(info.uuid)

            return uuid_list
        except Exception as e:
            msg = MyLog.color_red("get_current_timer_rule has except: " + str(e))
            MyLog.logger.error(msg)
            return []


    #筛选出所有可用的定时规则的时间列表
    def get_all_enable_timer_rule_time_list(self):
        time_list = []
        try:
            main_sql = self.__session.query(rule_main_tbl)\
            .join(rule_time_tbl, rule_time_tbl.uuid==rule_main_tbl.uuid)\
            .filter(rule_main_tbl.enable == True, rule_main_tbl.type == 'timer').all()

            for info in main_sql:
                time_sql = self.__session.query(rule_time_tbl).filter(rule_time_tbl.uuid == info.uuid).all()
                for time in time_sql:
                    time_list.append(time.start_time)
                    time_list.append(time.end_time)
            return time_list
        except Exception as e:
            msg = MyLog.color_red("get_all_enable_timer_rule_time_list has except: " + str(e))
            MyLog.logger.error(msg)
            return []

    #通过uuid获取规则的日期时间列表
    def get_date_time_by_uuid(self, uuid):
        date_list = []
        time_list = []
        try:
            date_sql = self.__session.query(rule_date_tbl).filter(rule_date_tbl.uuid == uuid).all()
            for date in date_sql:
                date_dict = {}
                date_dict['start_date'] = date.start_date
                date_dict['end_date'] = date.end_date
                date_list.append(date_dict)
            time_sql = self.__session.query(rule_time_tbl).filter(rule_time_tbl.uuid == uuid).all()
            for time in time_sql:
                time_dict = {}
                time_dict['start_time'] = time.start_time
                time_dict['end_time'] = time.end_time
                time_list.append(time_dict)
            return date_list, time_list
        except Exception as e:
            msg = MyLog.color_red("get_date_time_by_uuid has except: " + str(e))
            MyLog.logger.error(msg)
            return date_list, time_list

    #筛选出触发原设备包含指定设备id并且当前时间点可以执行的联动规则，筛选条件：规则enable并且当前的日期时间在规则时间内
    def get_current_linkage_rule_by_src_devid(self, src_dev_id):
        uuid_list = []
        try:
            current_date = datetime.date.today()
            current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")
            MyLog.logger.info("current time: %s"%(current_time))
            rule_filter = {
                and_(
                    and_(
                        rule_main_tbl.enable == True,
                        rule_main_tbl.type == 'linkage',
                        rule_date_tbl.start_date <= current_date, 
                        current_date <= rule_date_tbl.end_date
                    ),
                    and_(
                        rule_src_device_tbl.src_device == src_dev_id
                    ),
                    or_(
                        and_(
                            rule_time_tbl.start_time <= current_time, 
                            current_time <= rule_time_tbl.end_time
                        ),
                        and_(#跨天
                            rule_time_tbl.start_time >= rule_time_tbl.end_time, 
                            current_time >= rule_time_tbl.start_time
                        ),
                        and_(#跨天
                            rule_time_tbl.start_time >= rule_time_tbl.end_time, 
                            current_time <= rule_time_tbl.end_time
                        )
                    )
                )
            }
            main_sql = self.__session.query(rule_main_tbl).join(rule_date_tbl, rule_date_tbl.uuid==rule_main_tbl.uuid)\
            .join(rule_time_tbl, rule_time_tbl.uuid==rule_main_tbl.uuid)\
            .join(rule_src_device_tbl, rule_src_device_tbl.uuid==rule_main_tbl.uuid)\
            .filter(*rule_filter).all()
            for info in main_sql:
                uuid_list.append(info.uuid)

            return uuid_list
        except Exception as e:
            msg = MyLog.color_red("get_current_linkage_rule_by_src_devid has except: " + str(e))
            MyLog.logger.error(msg)
            return []