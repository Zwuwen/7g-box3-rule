#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# @Time    : 2021/3/22 15:36
# @Author  : noti
# @Site    : 
# @File    : dev_cmd_record.py
# @Software: rule_engine

from collections import defaultdict
from command.command_info import CommandInfo
from log.log import MyLog
from db.sqlite_interface import SqliteInterface


class CmdRecorder:
    """

    {dev_id1:{cmd1,cmd2,cmd3,cmd4}, dev_id2:{cmd1, cmd2, cmd3, cmd4}}

    """
    dev_run_cmd = defaultdict(set)

    @classmethod
    def update_cmd(cls, dev_id, cmd_info: CommandInfo):
        """

        Args:
            dev_id:
            cmd_info:

        Returns:

        """
        try:
            MyLog.logger.debug(f'update_cmd()')
            if cmd_info.default_param:
                cls.__rm_cmd(dev_id, cmd_info)
            else:
                cls.__add_cmd(dev_id, cmd_info)

            MyLog.logger.info(f'🏃‍♂️dev_run_cmd:{cls.dev_run_cmd}')
        except Exception as e:
            MyLog.logger.error(f'update_cmd except:{e}')

    @classmethod
    def __add_cmd(cls, dev_id, cmd_info: CommandInfo):
        cmd = cmd_info.command

        if cmd and cmd not in cls.dev_run_cmd[dev_id]:
            cls.dev_run_cmd[dev_id].add(cmd)
            cls.__commit_data_db(dev_id=dev_id)

    @classmethod
    def __rm_cmd(cls, dev_id, cmd_info: CommandInfo):
        cmd = cmd_info.command

        if cmd and cmd in cls.dev_run_cmd[dev_id]:
            cls.dev_run_cmd[dev_id].discard(cmd)

            if not cls.dev_run_cmd[dev_id]:
                MyLog.logger.debug(f'pop dev_id:{dev_id}')
                cls.dev_run_cmd.pop(dev_id)
                cls.__remove_data_db(dev_id=dev_id)
            else:
                cls.__commit_data_db(dev_id=dev_id)

    @classmethod
    def load_data(cls):
        """

        Returns:

        """
        cls.dev_run_cmd = cls.__get_run_cmd_data_db()
        MyLog.logger.info(f'load_data, dev_run_cmd:{cls.dev_run_cmd}')

    @classmethod
    def clear_data(cls):
        """

        Returns:

        """
        try:
            for dev_id in cls.dev_run_cmd:
                cls.__remove_data_db(dev_id=dev_id)

            cls.dev_run_cmd.clear()
            MyLog.logger.info(f'clear_data, dev_run_cmd:{cls.dev_run_cmd}')
        except Exception as e:
            MyLog.logger.error(f'clear_data except:{e}')

    @classmethod
    def __commit_data_db(cls, dev_id):
        try:
            SqliteInterface.add_run_cmd(dev_id=dev_id, cmd_list=cls.dev_run_cmd[dev_id])
        except Exception as db_exc:
            MyLog.logger.error(f'💉 commit db exception:{db_exc}')

    @classmethod
    def __remove_data_db(cls, dev_id):
        try:
            SqliteInterface.del_run_cmd_record(dev_id=dev_id)
        except Exception as db_exc:
            MyLog.logger.error(f'💉 remove db exception:{db_exc}')

    @classmethod
    def __get_run_cmd_data_db(cls):
        try:
            return SqliteInterface.get_run_cmd()
        except Exception as db_exc:
            MyLog.logger.error(f'💉 get db exception:{db_exc}')

