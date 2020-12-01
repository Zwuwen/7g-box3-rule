import time
import os
import sys
cur_dir = os.getcwd()
pre_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(cur_dir)
sys.path.append(pre_dir)
from nameko_svr.rule_nameko import RuleNameko
from rule.rule_mng import RuleMng
from config import RULE_LOG_PATH, RULE_LOG_LEVEL
from log.log import MyLog

MyLog.init(is_enable_std=False, log_period = 7, level = RULE_LOG_LEVEL, path = RULE_LOG_PATH)

def main():
    msg = MyLog.color_green('+++++++++规则引擎启动+++++++++')
    MyLog.logger.info(msg)
    RuleNameko.open()
    RuleMng.timer_rule_decision()
    while True:
        time.sleep(3600)