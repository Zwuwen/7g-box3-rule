#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# @Time    : 2021/3/25 17:31
# @Author  : noti
# @Site    : 
# @File    : dev_attribute_mng.py
# @Software: rule_engine

from command.dev_cmd_record import CmdRecorder
from log.log import MyLog
from rpc_call.client import DevCall


class DevAttributeMng:
    dev_now_attributes = dict()

    @classmethod
    def restore_devices_when_start_up(cls):
        """

        Returns:

        """
        try:
            MyLog.logger.debug(f'restore_devices_when_start_up()')
            CmdRecorder.load_data()
            for dev_id, cmd_list in CmdRecorder.dev_run_cmd.items():
                cls.__restore_device_status(dev_id=dev_id, cmd_list=cmd_list)
            CmdRecorder.clear_data()
            MyLog.logger.debug(f'restore_devices_when_start_up finish')
        except Exception as e:
            MyLog.logger.error(f'restore_device_when_start up except:{e}')

    @classmethod
    def __restore_device_status(cls, dev_id, cmd_list):
        """

        Args:
            dev_id:
            cmd_list:

        Returns:

        """
        MyLog.logger.debug(f'restore_device_status{dev_id, cmd_list}')
        for cmd in cmd_list:
            DevCall.call_service(dev_id, cmd, type='linkage', default=True)
        MyLog.logger.debug(f'restore_device_status{dev_id, cmd_list}...return')

    @classmethod
    def update_dev_now_attributes(cls, dev_id, attr_dict):
        """

        Args:
            dev_id:
            attr_dict:

        Returns:

        """

        # MyLog.logger.debug(f'update_dev_now_attributes{dev_id, attr_dict}')

        # MyLog.logger.debug(f'before:dev_now_attributes: {cls.dev_now_attributes}')
        try:
            attr_dict_b = cls.dev_now_attributes.get(dev_id, {})
            attr_dict_n = {**attr_dict_b, **attr_dict}
            cls.dev_now_attributes[dev_id] = attr_dict_n

            # MyLog.logger.debug(f'✔️dev_now_attributes: {cls.dev_now_attributes}')
            MyLog.logger.debug(f'update_dev_now_attributes:return')
        except Exception as e:
            MyLog.logger.error(f'update_dev_now_attributes except:{e}')

    @classmethod
    def get_dev_attr_value(cls, dev_id, attr_name):
        """

        Args:
            dev_id:
            attr_name:

        Returns:

        """
        MyLog.logger.debug(f'get_dev_attr_item{dev_id, attr_name}')
        attr_value = cls.dev_now_attributes.get(dev_id, {}).get(attr_name, None)
        MyLog.logger.debug(f'get_dev_attr_item{dev_id, attr_name}...return:{attr_value}')

        return attr_value
