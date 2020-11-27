'''
日志处理模块
'''
import logging, os, time
import logging.handlers

g_logLevel = {
    'debug': 10,
    'info': 20,
    'warnning': 30,
    'error': 40    
}

class MyLog:
    path = None
    splock = None   #日志读写锁    
    logger = None   #log对象
    f_handle = None #log文件句柄
    log_period = 3  #日志保存时间周期    
    console_handle = None #终端句柄

    @classmethod
    def init(cls, is_enable_std, log_period, level, is_del = False, path = None):
        '''
        is_del: 删除日志路径判断
        is_enable_std: 是否日志输出终端
        log_period: log保存的时间周期
        level: 日志等级，debug, info, warnning, error
        path: 日志保存的目录
        '''
        if not isinstance(path,str):
            return False
        #删除目录
        if is_del is True and os.path.exists(path):
            os.system('rm -rf %s'%path)

        if not os.path.exists(path):
            os.makedirs(path)

        if level not in g_logLevel.keys():
            return False

        logging.basicConfig()
        log_format = logging.Formatter("%(asctime)s-%(message)s @%(levelname)s-%(filename)s[%(lineno)d]")
        #日志文件
        log = path + '/log'
        cls.logger = logging.getLogger('rule')
        # when是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：S（秒）、M(分)、H（时）、D（天）
        log_handler = logging.handlers.TimedRotatingFileHandler(log, when = 'D', backupCount = log_period, encoding="utf-8")
        #log_handler.suffix = "%Y-%m-%d.log"
        cls.logger.setLevel(g_logLevel[level])
        log_handler.setFormatter(log_format)
        cls.logger.addHandler(log_handler)
        
        #console
        if is_enable_std:
            console_handle = logging.StreamHandler()
            console_handle.setLevel(g_logLevel[level])
            console_handle.setFormatter(log_format)
            cls.logger.addHandler(console_handle)

        return True

    @classmethod
    def debug(cls, string):
        cls.logger.debug(string)

    @classmethod
    def key(cls, string):
        new_str = '\033[32m' + string + '\033[0m'
        cls.logger.info(new_str)

    @classmethod
    def info(cls, string):
        cls.logger.info(string)

    @classmethod
    def warning(cls, string):
        cls.logger.warning(string)

    @classmethod
    def error(cls, string):
        new_str = '\033[31m' + string + '\033[0m'
        cls.logger.error(new_str)

if __name__ == "__main__":
    MyLog.init(is_enable_std=True, log_period = 3, level = 'debug', 
        path = './')
    MyLog.key('123')
    MyLog.error('567890')