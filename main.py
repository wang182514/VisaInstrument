import time

import pyvisa
from Instrument import *
# 1. 创建连接管理器
rm = pyvisa.ResourceManager('@py')

# 2. 查看可用设备（找到你的仪器地址）
print('可用设备:', rm.list_resources())

sa = N9020A('192.168.1.2')
sa.set_mode_sa()
print(sa.sa_marker_peak())
print(f"error: {sa.check_error()}") #error: +0,"No error"
sa.close()
