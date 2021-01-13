__author__ = "penghf"
__date__ = "20201014"

from enum import Enum
from enum import unique

'''
define error code
###通用错误码范围：0-500
###灯控：501-600
###大屏:601-700
###摄像头：701-900
###传感器(环境传感、倾斜度、温湿度、智能锁)：901-1000
###音柱、音频：1001-1100
###RFID：1101-1200
###智能电源：1201-1300
###智慧盒：1301-1500
###其他扩展设备：1501以上
*****备注*****
每个返回结果码，前面半部分为错误码，后半部分为操作结果
'''

@unique
class g_retValue(Enum):
    #common result value
    qjBoxOpcodeSucess             = 0#成功
    qjBoxOpcodeUnkownErr          = 1#未知错误
    qjBoxOpcodeInputParamErr      = 2#参数错误
    qjBoxOpcodeNoSupport          = 3#不支持
    qjBoxOpcodeTimeout            = 4#超时
    qjBoxOpcodeAccessFailure      = 5#访问失败
    qjBoxOpcodeCreateFailure      = 6#创建错误
    qjBoxOpcodeOpenFailure        = 7#打开失败(文件、设备)
    qjBoxOpcodeDataInvalid        = 8#数据无效
    qjBoxOpcodeNoReady            = 9#未就绪
    qjBoxOpcodeCmdInvalid         = 10#命令错误
    qjBoxOpcodeConnectFailure     = 11#链接失败
    qjBoxOpcodeNetReqNoSupport    = 12#请求不支持
    qjBoxOpcodeNetBusy            = 13#网络忙
    qjBoxOpcodeDevBusy            = 14#设备忙
    qjBoxOpcodeSrvNoRunning       = 15#服务未启动
    qjBoxOpcodePathNoExist        = 16#路径不存在
    qjBoxOpcodeCheckFailure       = 17#校验失败
    qjBoxOpcodeLoadConfFailure    = 18#加载配置失败
    qjBoxOpcodeCloseDevFailure    = 20#关闭设备失败
    qjBoxOpcodeNoInit             = 21#未初始化
    qjBoxOpcodeNoEnoughSpace      = 22#没有足够空间
    qjBoxOpcodeSaveConfFailure    = 23#保存配置失败
    qjBoxOpcodeRegisterFailure    = 24#注册失败
    qjBoxOpcodeVersionErr         = 25#版本错误
    qjBoxOpcodeSvrInitFailure     = 26#系统初始化失败
    qjBoxOpcodeDevRefuseAcc       = 27#设备拒绝访问
    qjBoxOpcodeAccNoExist         = 28#访问不存在
    qjBoxOpcodeDataFormatError    = 29#数据格式错误
    qjBoxOpcodeLackAuthority      = 30#没有权限
    qjBoxOpcodeExcept             = 31#程序捕获异常
    qjBoxOpcodeInAuto             = 32#设备处于自动模式
    qjBoxOpcodeInManual           = 33#设备处于手动模式
    qjBoxOpcodeDecompressionFailure = 34#解压失败
    qjBoxOpcodeInLogout           = 35#设备未认证
    qjBoxOpcodeReadOnly           = 36#只读
    qjBoxOpcodeDeviceReturnFailed = 37#设备返回执行失败
    #数据库 sql
    qjBoxOpcodeConSqlFailure      = 50#链接数据库失败
    qjBoxOpcodeHandleSqlFailure   = 51#操作数据库失败
    qjBoxOpcodeSqlConnInvalid     = 52#无效链接
    #net
    qjBoxOpcodeNetLocalIpInvalid  = 60#本地IP无效
    qjBoxOpcodeNetRemoteIpInvalid = 61#远程IP无效
    qjBoxOpcodeSslNoSupport       = 62#ssl 不支持
    #MQTT
    qjBoxOpcodeMQTopicNoFound     = 70#topic 不支持
    qjBoxOpcodeMQTopicExisted     = 71#topic 不存在
